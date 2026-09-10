import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import {
  getChatWebSocketUrl, getChatConversations, getChatMessages, sendChatMessageRest, createChatConversation,
  markChatConversationRead, editChatMessage, deleteChatMessage, uploadChatAttachment, getLead, getContact, getDeal, getTask,
} from '../services/api';

// Sentinel cached in place of a real record when the fetch failed (404/deleted/error) - lets
// MessageBubble render "No longer available" instead of hanging on "Loading..." forever, for
// both leadCache and contactCache below.
const RECORD_NOT_FOUND = { __notFound: true };

const currentUserId = Number(localStorage.getItem('userId'));

// First React Context in this frontend - justified because the single WebSocket connection and
// presence/unread state need to be visible in the nav bar (a future unread badge) and inside the
// chat page at the same time, which a page-local useState can't reach.
const ChatContext = createContext(null);

// Exponential backoff for reconnects, capped at 15s - a Render free-tier restart (deploy,
// crash, or the 15-minute inactivity spin-down) can drop this connection at any time, and this
// must not hammer the server with a tight retry loop when that happens.
const RECONNECT_DELAYS_MS = [1000, 2000, 4000, 8000, 15000];
const HEARTBEAT_INTERVAL_MS = 20000;

export function ChatProvider({ children }) {
  const [conversations, setConversations] = useState([]);
  const [presenceMap, setPresenceMap] = useState({}); // user_id -> boolean online
  const [messagesByConversation, setMessagesByConversation] = useState({}); // id -> array
  const [typingMap, setTypingMap] = useState({}); // conversation_id -> [user_ids currently typing]
  const [readReceipts, setReadReceipts] = useState({}); // conversation_id -> { user_id: up_to_message_id }
  const [connected, setConnected] = useState(false);
  const [leadCache, setLeadCache] = useState({}); // lead_id -> lead record, so N messages linked to the same lead only ever fetch it once
  const [contactCache, setContactCache] = useState({}); // contact_id -> contact record, same shape as leadCache (Phase 2B-ii) - kept as an independent cache rather than merged into leadCache, since a Lead and a Contact are different record types with different fields even though the fetch-once-and-cache mechanics are identical.
  const [dealCache, setDealCache] = useState({}); // deal_id -> deal record, same shape again (Phase 2B-iii) - third independent cache, not a generic one, per the same rationale.
  const [taskCache, setTaskCache] = useState({}); // task_id -> task record, same shape again (Phase 2B-iv) - fourth independent cache, not a generic one, per the same rationale.

  const wsRef = useRef(null);
  const leadFetchesInFlightRef = useRef(new Set());
  const contactFetchesInFlightRef = useRef(new Set());
  const dealFetchesInFlightRef = useRef(new Set());
  const taskFetchesInFlightRef = useRef(new Set());
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef(null);
  const heartbeatTimerRef = useRef(null);
  const lastSyncRef = useRef(null); // ISO-ish timestamp string of the last successful conversations sync

  const token = localStorage.getItem('token');

  const refreshConversations = useCallback(async () => {
    if (!token) return;
    try {
      const data = await getChatConversations(token);
      setConversations(Array.isArray(data) ? data : []);
      lastSyncRef.current = new Date().toISOString().slice(0, 19).replace('T', ' ');
    } catch (err) {
      console.error('Error fetching conversations:', err);
    }
  }, [token]);

  const loadMessages = useCallback(async (conversationId) => {
    if (!token) return [];
    try {
      const data = await getChatMessages(token, conversationId);
      setMessagesByConversation((prev) => ({ ...prev, [conversationId]: Array.isArray(data) ? data : [] }));
      return data;
    } catch (err) {
      console.error('Error fetching messages:', err);
      return [];
    }
  }, [token]);

  // Reconnect + REST catch-up: on any reconnect, re-fetch the conversation list (catches new
  // conversations/last-message updates missed while disconnected) and re-fetch history for any
  // conversation already open in this session (catches messages missed for that thread
  // specifically), keyed by the highest message id already seen - never trusts the WebSocket
  // alone as the source of truth for "did I miss anything."
  const catchUp = useCallback(async () => {
    await refreshConversations();
    const openConversationIds = Object.keys(messagesByConversation);
    for (const conversationId of openConversationIds) {
      const existing = messagesByConversation[conversationId] || [];
      const lastSeenId = existing.length ? existing[existing.length - 1].id : 0;
      try {
        const missed = await getChatMessages(token, conversationId, { afterId: lastSeenId });
        if (missed.length) {
          setMessagesByConversation((prev) => ({
            ...prev,
            [conversationId]: [...(prev[conversationId] || []), ...missed],
          }));
        }
      } catch (err) {
        console.error('Error catching up on conversation', conversationId, err);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshConversations, token]);

  const handleServerEvent = useCallback((event) => {
    if (event.event === 'new_message') {
      const msg = event.data;
      setMessagesByConversation((prev) => {
        // Default to [] rather than bailing out when the conversation hasn't been loaded yet
        // in this session - a WS echo can otherwise arrive before loadMessages()'s REST fetch
        // resolves (e.g. right after creating a brand-new conversation and sending the first
        // message), silently dropping the just-sent message from view even though it saved
        // correctly. If the full history arrives afterward via loadMessages(), it replaces
        // this array wholesale anyway, so a partial array here is never stale for long.
        const existing = prev[msg.conversation_id] || [];
        if (existing.some((m) => m.id === msg.id)) return prev; // already have it (e.g. sender's own echo already added optimistically)
        return { ...prev, [msg.conversation_id]: [...existing, msg] };
      });
      setConversations((prev) => prev.map((c) => (
        c.id === msg.conversation_id
          ? {
              ...c,
              last_message_body: msg.body,
              last_message_sender_id: msg.sender_id,
              last_message_at: msg.created_at,
              // Only bump unread for messages from someone else - my own sent messages
              // shouldn't count as "unread" in my own conversation list.
              unread_count: msg.sender_id === currentUserId ? c.unread_count : (c.unread_count || 0) + 1,
            }
          : c
      )));
      // A new message means whoever was typing has finished, at least for this message.
      setTypingMap((prev) => ({ ...prev, [msg.conversation_id]: (prev[msg.conversation_id] || []).filter((id) => id !== msg.sender_id) }));
    } else if (event.event === 'presence') {
      const { user_id: userId, status } = event.data;
      setPresenceMap((prev) => ({ ...prev, [userId]: status === 'online' }));
    } else if (event.event === 'typing') {
      const { conversation_id: convId, user_id: userId, is_typing: isTyping } = event.data;
      setTypingMap((prev) => {
        const current = prev[convId] || [];
        const next = isTyping ? [...new Set([...current, userId])] : current.filter((id) => id !== userId);
        return { ...prev, [convId]: next };
      });
    } else if (event.event === 'read_receipt') {
      const { conversation_id: convId, user_id: userId, up_to_message_id: upToId } = event.data;
      setReadReceipts((prev) => ({ ...prev, [convId]: { ...(prev[convId] || {}), [userId]: upToId } }));
    } else if (event.event === 'message_edited' || event.event === 'message_deleted') {
      // Conversation-list preview isn't patched here - if the edited/deleted message happened
      // to be the last one, the next reconnect's refreshConversations() catches it up. Not
      // worth a wrong guess about which was "last" from inside a single message event.
      const msg = event.data;
      setMessagesByConversation((prev) => {
        const existing = prev[msg.conversation_id];
        if (!existing) return prev;
        return { ...prev, [msg.conversation_id]: existing.map((m) => (m.id === msg.id ? msg : m)) };
      });
    }
    // 'pong'/'error' need no state change here.
  }, []);

  const connectWebSocket = useCallback(() => {
    if (!token) return;
    const ws = new WebSocket(getChatWebSocketUrl(token));
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      reconnectAttemptRef.current = 0;
      catchUp();
      heartbeatTimerRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ event: 'ping' }));
      }, HEARTBEAT_INTERVAL_MS);
    };

    ws.onmessage = (rawEvent) => {
      try {
        handleServerEvent(JSON.parse(rawEvent.data));
      } catch (err) {
        console.error('Error parsing chat WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      clearInterval(heartbeatTimerRef.current);
      const delay = RECONNECT_DELAYS_MS[Math.min(reconnectAttemptRef.current, RECONNECT_DELAYS_MS.length - 1)];
      reconnectAttemptRef.current += 1;
      reconnectTimerRef.current = setTimeout(connectWebSocket, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, handleServerEvent, catchUp]);

  useEffect(() => {
    if (!token) return undefined;
    refreshConversations();
    connectWebSocket();
    return () => {
      clearTimeout(reconnectTimerRef.current);
      clearInterval(heartbeatTimerRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null; // don't reconnect on a deliberate unmount/logout
        wsRef.current.close();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const sendMessage = useCallback(async (conversationId, body, replyToMessageId = null, leadId = null, contactId = null, dealId = null, taskId = null) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Fire-and-forget - the server broadcasts the committed row back over this same socket
      // (handleServerEvent above appends it once the 'new_message' event round-trips).
      wsRef.current.send(JSON.stringify({
        event: 'send_message',
        data: { conversation_id: conversationId, body, reply_to_message_id: replyToMessageId, lead_id: leadId, contact_id: contactId, deal_id: dealId, task_id: taskId },
      }));
      return;
    }
    // WebSocket not connected (e.g. mid-reconnect after a Render restart) - REST fallback goes
    // through the same backend _create_message() path. Unlike the WS path, the sender has no
    // live socket to receive their own broadcast back on, so append the response directly.
    const message = await sendChatMessageRest(token, conversationId, body, replyToMessageId, leadId, contactId, dealId, taskId);
    setMessagesByConversation((prev) => {
      const existing = prev[conversationId] || [];
      if (existing.some((m) => m.id === message.id)) return prev;
      return { ...prev, [conversationId]: [...existing, message] };
    });
  }, [token]);

  // Phase 2B-i: fetches a lead once and caches it by id, so a thread with N messages linked to
  // the same lead (e.g. a long back-and-forth about one prospect) issues exactly one request,
  // not N - both the cache-hit check and the in-flight guard live here rather than in
  // MessageBubble, since multiple bubbles for the same lead can mount around the same tick.
  // On a fetch failure (the lead was deleted, or a transient error), the sentinel is cached
  // instead of leaving the id permanently uncached - without this, MessageBubble's card would
  // retry-and-fail (or just show "Loading...") forever, since a falsy cache miss looks
  // identical to "never tried yet" (Phase 2B-ii fix, applied here to both leads and contacts).
  const getLeadInfo = useCallback((leadId) => {
    if (!leadId || leadCache[leadId] || leadFetchesInFlightRef.current.has(leadId)) return;
    leadFetchesInFlightRef.current.add(leadId);
    getLead(leadId, token)
      .then((lead) => setLeadCache((prev) => ({ ...prev, [leadId]: lead })))
      .catch((err) => {
        console.error('Error fetching lead for chat card:', err);
        setLeadCache((prev) => ({ ...prev, [leadId]: RECORD_NOT_FOUND }));
      })
      .finally(() => leadFetchesInFlightRef.current.delete(leadId));
  }, [token, leadCache]);

  // Phase 2B-ii: same fetch-once-and-cache mechanics as getLeadInfo, against the independent
  // contactCache - not unified into one generic "linked record" fetcher, since Lead and Contact
  // are different record shapes fetched from different endpoints (see the 2B-ii design notes).
  const getContactInfo = useCallback((contactId) => {
    if (!contactId || contactCache[contactId] || contactFetchesInFlightRef.current.has(contactId)) return;
    contactFetchesInFlightRef.current.add(contactId);
    getContact(contactId, token)
      .then((contact) => setContactCache((prev) => ({ ...prev, [contactId]: contact })))
      .catch((err) => {
        console.error('Error fetching contact for chat card:', err);
        setContactCache((prev) => ({ ...prev, [contactId]: RECORD_NOT_FOUND }));
      })
      .finally(() => contactFetchesInFlightRef.current.delete(contactId));
  }, [token, contactCache]);

  // Phase 2B-iii: same fetch-once-and-cache mechanics again, against the independent
  // dealCache - third instance of the identical pattern, not a generic fetcher.
  const getDealInfo = useCallback((dealId) => {
    if (!dealId || dealCache[dealId] || dealFetchesInFlightRef.current.has(dealId)) return;
    dealFetchesInFlightRef.current.add(dealId);
    getDeal(dealId, token)
      .then((deal) => setDealCache((prev) => ({ ...prev, [dealId]: deal })))
      .catch((err) => {
        console.error('Error fetching deal for chat card:', err);
        setDealCache((prev) => ({ ...prev, [dealId]: RECORD_NOT_FOUND }));
      })
      .finally(() => dealFetchesInFlightRef.current.delete(dealId));
  }, [token, dealCache]);

  // Phase 2B-iv: same fetch-once-and-cache mechanics again, against the independent
  // taskCache - fourth instance of the identical pattern, not a generic fetcher.
  const getTaskInfo = useCallback((taskId) => {
    if (!taskId || taskCache[taskId] || taskFetchesInFlightRef.current.has(taskId)) return;
    taskFetchesInFlightRef.current.add(taskId);
    getTask(taskId, token)
      .then((task) => setTaskCache((prev) => ({ ...prev, [taskId]: task })))
      .catch((err) => {
        console.error('Error fetching task for chat card:', err);
        setTaskCache((prev) => ({ ...prev, [taskId]: RECORD_NOT_FOUND }));
      })
      .finally(() => taskFetchesInFlightRef.current.delete(taskId));
  }, [token, taskCache]);

  const editMessage = useCallback(async (messageId, conversationId, body) => {
    const updated = await editChatMessage(token, messageId, body);
    setMessagesByConversation((prev) => {
      const existing = prev[conversationId];
      if (!existing) return prev;
      return { ...prev, [conversationId]: existing.map((m) => (m.id === messageId ? updated : m)) };
    });
    return updated;
  }, [token]);

  const removeMessage = useCallback(async (messageId, conversationId) => {
    const updated = await deleteChatMessage(token, messageId);
    setMessagesByConversation((prev) => {
      const existing = prev[conversationId];
      if (!existing) return prev;
      return { ...prev, [conversationId]: existing.map((m) => (m.id === messageId ? updated : m)) };
    });
    return updated;
  }, [token]);

  const uploadAttachment = useCallback(async (conversationId, file, body = '') => {
    const message = await uploadChatAttachment(token, conversationId, file, body);
    // The uploader also gets their own new_message broadcast back over their live socket (the
    // backend broadcasts to every member including the sender), so no optimistic append here -
    // matches how sendMessage's WS path behaves. If the socket happens to be down, the message
    // still appears on the next reconnect's catch-up fetch, same safety net as everywhere else.
    return message;
  }, [token]);

  const startConversation = useCallback(async (type, memberUserIds, name = null) => {
    const conv = await createChatConversation(token, type, memberUserIds, name);
    setConversations((prev) => (prev.some((c) => c.id === conv.id) ? prev : [conv, ...prev]));
    return conv;
  }, [token]);

  const sendTyping = useCallback((conversationId, isTyping) => {
    // WS-only, no REST fallback - a typing indicator is purely ephemeral, so if the socket is
    // down there's nothing useful to deliver by the time a REST call would land anyway.
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ event: isTyping ? 'typing_start' : 'typing_stop', data: { conversation_id: conversationId } }));
    }
  }, []);

  const markRead = useCallback(async (conversationId, upToMessageId) => {
    setConversations((prev) => prev.map((c) => (c.id === conversationId ? { ...c, unread_count: 0 } : c)));
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ event: 'mark_read', data: { conversation_id: conversationId, up_to_message_id: upToMessageId } }));
      return;
    }
    try {
      await markChatConversationRead(token, conversationId, upToMessageId);
    } catch (err) {
      console.error('Error marking conversation read:', err);
    }
  }, [token]);

  const value = {
    conversations, presenceMap, messagesByConversation, typingMap, readReceipts, connected,
    refreshConversations, loadMessages, sendMessage, startConversation, sendTyping, markRead,
    editMessage, removeMessage, uploadAttachment, leadCache, getLeadInfo, contactCache, getContactInfo,
    dealCache, getDealInfo, taskCache, getTaskInfo,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be used within a ChatProvider');
  return ctx;
}
