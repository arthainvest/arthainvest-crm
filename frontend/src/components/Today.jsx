import React, { useState, useEffect } from 'react';
import {
  getTasks, createTask, updateTask, deleteTask,
  getMeetings, createMeeting, updateMeeting, deleteMeeting,
  getLeads, getContactsList, getTeam
} from '../services/api';
import '../styles/Today.css';

// toISOString() converts to UTC first, which silently rolls the date back a day for any
// timezone ahead of UTC (e.g. IST, UTC+5:30) whenever local midnight is used as the anchor -
// exactly what shiftDate() below does. Build the string from local date components instead.
const formatDateISO = (d) => {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const emptyTaskForm = { title: '', assigned_team_member_id: '' };
const emptyMeetingForm = { title: '', meeting_time: '', lead_id: '', contact_id: '', location: '', notes: '', assigned_team_member_id: '' };

export default function Today() {
  const [selectedDate, setSelectedDate] = useState(() => formatDateISO(new Date()));
  const [activeTab, setActiveTab] = useState('tasks');
  const [tasks, setTasks] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [leads, setLeads] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [showMeetingForm, setShowMeetingForm] = useState(false);
  const [taskForm, setTaskForm] = useState(emptyTaskForm);
  const [meetingForm, setMeetingForm] = useState(emptyMeetingForm);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchTasks();
    fetchMeetings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate]);

  useEffect(() => {
    getLeads(token).then((d) => setLeads(Array.isArray(d) ? d : [])).catch((err) => console.error('Error fetching leads:', err));
    getContactsList(token).then((d) => setContacts(Array.isArray(d) ? d : [])).catch((err) => console.error('Error fetching contacts:', err));
    getTeam(token).then((d) => setTeamMembers(Array.isArray(d) ? d : [])).catch((err) => console.error('Error fetching team:', err));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchTasks = async () => {
    try {
      const data = await getTasks(token, selectedDate);
      setTasks(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching tasks:', err);
    }
  };

  const fetchMeetings = async () => {
    try {
      const data = await getMeetings(token, selectedDate);
      setMeetings(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching meetings:', err);
    }
  };

  const shiftDate = (deltaDays) => {
    // Functional update so rapid consecutive clicks (or React batching two clicks into one
    // render) each read the latest date instead of both computing from the same stale
    // `selectedDate` closure and only moving by one day's worth combined.
    setSelectedDate((prev) => {
      const d = new Date(`${prev}T00:00:00`);
      d.setDate(d.getDate() + deltaDays);
      return formatDateISO(d);
    });
  };

  const todayISO = formatDateISO(new Date());
  const dateLabel = selectedDate === todayISO
    ? 'Today'
    : new Date(`${selectedDate}T00:00:00`).toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  const handleToggleTaskComplete = async (task) => {
    const previous = tasks;
    setTasks((prev) => prev.map((t) => (t.id === task.id ? { ...t, completed: !t.completed } : t)));
    try {
      await updateTask(token, task.id, { completed: !task.completed });
    } catch (err) {
      console.error('Error updating task:', err);
      setTasks(previous);
      alert('Failed to update task. Please try again.');
    }
  };

  const handleDeleteTask = async (id) => {
    if (!window.confirm('Delete this task?')) return;
    try {
      await deleteTask(token, id);
      setTasks((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      console.error('Error deleting task:', err);
      alert('Failed to delete task. Please try again.');
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    if (!taskForm.title.trim()) return;
    try {
      await createTask(token, {
        title: taskForm.title,
        due_date: selectedDate,
        assigned_team_member_id: taskForm.assigned_team_member_id ? Number(taskForm.assigned_team_member_id) : null
      });
      setShowTaskForm(false);
      setTaskForm(emptyTaskForm);
      fetchTasks();
    } catch (err) {
      console.error('Error creating task:', err);
      alert('Failed to create task. Please try again.');
    }
  };

  const handleDeleteMeeting = async (id) => {
    if (!window.confirm('Cancel this meeting?')) return;
    try {
      await deleteMeeting(token, id);
      setMeetings((prev) => prev.filter((m) => m.id !== id));
    } catch (err) {
      console.error('Error deleting meeting:', err);
      alert('Failed to delete meeting. Please try again.');
    }
  };

  const handleMarkConducted = async (meeting) => {
    const previous = meetings;
    setMeetings((prev) => prev.map((m) => (m.id === meeting.id ? { ...m, status: 'Conducted' } : m)));
    try {
      await updateMeeting(token, meeting.id, { status: 'Conducted' });
    } catch (err) {
      console.error('Error updating meeting:', err);
      setMeetings(previous);
      alert('Failed to update meeting. Please try again.');
    }
  };

  const handleAddMeeting = async (e) => {
    e.preventDefault();
    if (!meetingForm.title.trim()) return;
    try {
      await createMeeting(token, {
        title: meetingForm.title,
        meeting_date: selectedDate,
        meeting_time: meetingForm.meeting_time || null,
        lead_id: meetingForm.lead_id ? Number(meetingForm.lead_id) : null,
        contact_id: meetingForm.contact_id ? Number(meetingForm.contact_id) : null,
        location: meetingForm.location || null,
        notes: meetingForm.notes || null,
        assigned_team_member_id: meetingForm.assigned_team_member_id ? Number(meetingForm.assigned_team_member_id) : null
      });
      setShowMeetingForm(false);
      setMeetingForm(emptyMeetingForm);
      fetchMeetings();
    } catch (err) {
      console.error('Error creating meeting:', err);
      alert('Failed to create meeting. Please try again.');
    }
  };

  return (
    <div className="today-container">
      <div className="today-header">
        <button className="today-nav-arrow" onClick={() => shiftDate(-1)} title="Previous day">←</button>
        <h1 className="today-date-label">{dateLabel}</h1>
        <button className="today-nav-arrow" onClick={() => shiftDate(1)} title="Next day">→</button>
      </div>

      <div className="today-tabs">
        <button className={`today-tab ${activeTab === 'tasks' ? 'active' : ''}`} onClick={() => setActiveTab('tasks')}>
          Tasks{tasks.length > 0 ? ` (${tasks.length})` : ''}
        </button>
        <button className={`today-tab ${activeTab === 'meetings' ? 'active' : ''}`} onClick={() => setActiveTab('meetings')}>
          Meetings{meetings.length > 0 ? ` (${meetings.length})` : ''}
        </button>
      </div>

      <div className="today-section-header">
        <h2>{activeTab === 'tasks' ? 'Tasks' : 'Meetings'}</h2>
        <button
          className="today-add-link"
          onClick={() => (activeTab === 'tasks' ? setShowTaskForm(true) : setShowMeetingForm(true))}
        >
          + Add {activeTab === 'tasks' ? 'Task' : 'Meeting'}
        </button>
      </div>

      <div className="today-list">
        {activeTab === 'tasks' ? (
          tasks.length === 0 ? (
            <p className="today-empty">No tasks scheduled</p>
          ) : (
            tasks.map((task) => (
              <div key={task.id} className={`today-task-row ${task.completed ? 'completed' : ''}`}>
                <label className="today-task-checkbox">
                  <input type="checkbox" checked={task.completed} onChange={() => handleToggleTaskComplete(task)} />
                  <span>{task.title}</span>
                </label>
                {task.assigned_team_member_name && (
                  <span className="today-assignee-badge">{task.assigned_team_member_name}</span>
                )}
                <button className="today-delete-btn" onClick={() => handleDeleteTask(task.id)} title="Delete">🗑️</button>
              </div>
            ))
          )
        ) : meetings.length === 0 ? (
          <p className="today-empty">No meetings scheduled</p>
        ) : (
          meetings.map((meeting) => (
            <div key={meeting.id} className="today-meeting-row">
              <div className="today-meeting-time">{meeting.meeting_time || '--:--'}</div>
              <div className="today-meeting-info">
                <div className="today-meeting-title">{meeting.title}</div>
                <div className="today-meeting-meta">
                  {(meeting.lead_name || meeting.contact_name) && <span>👤 {meeting.lead_name || meeting.contact_name}</span>}
                  {meeting.location && <span>📍 {meeting.location}</span>}
                  {meeting.assigned_team_member_name && <span>🧑 {meeting.assigned_team_member_name}</span>}
                </div>
              </div>
              <div className="today-meeting-actions">
                <span className={`today-status-badge status-${meeting.status.toLowerCase()}`}>{meeting.status}</span>
                {meeting.status === 'Scheduled' && (
                  <button className="today-small-btn" onClick={() => handleMarkConducted(meeting)}>Mark Conducted</button>
                )}
                <button className="today-delete-btn" onClick={() => handleDeleteMeeting(meeting.id)} title="Delete">🗑️</button>
              </div>
            </div>
          ))
        )}
      </div>

      {showTaskForm && (
        <div className="modal-overlay" onClick={() => setShowTaskForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add Task - {dateLabel}</h2>
              <button className="btn-close" onClick={() => setShowTaskForm(false)}>×</button>
            </div>
            <form onSubmit={handleAddTask}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Task *</label>
                  <input
                    type="text"
                    required
                    value={taskForm.title}
                    onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Assign To</label>
                  <select
                    value={taskForm.assigned_team_member_id}
                    onChange={(e) => setTaskForm({ ...taskForm, assigned_team_member_id: e.target.value })}
                  >
                    <option value="">-- Unassigned --</option>
                    {teamMembers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">Add Task</button>
                <button type="button" className="btn-secondary" onClick={() => setShowTaskForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showMeetingForm && (
        <div className="modal-overlay" onClick={() => setShowMeetingForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add Meeting - {dateLabel}</h2>
              <button className="btn-close" onClick={() => setShowMeetingForm(false)}>×</button>
            </div>
            <form onSubmit={handleAddMeeting}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Title *</label>
                  <input
                    type="text"
                    required
                    value={meetingForm.title}
                    onChange={(e) => setMeetingForm({ ...meetingForm, title: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Time</label>
                  <input
                    type="time"
                    value={meetingForm.meeting_time}
                    onChange={(e) => setMeetingForm({ ...meetingForm, meeting_time: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>With Lead</label>
                  <select
                    value={meetingForm.lead_id}
                    onChange={(e) => setMeetingForm({ ...meetingForm, lead_id: e.target.value, contact_id: '' })}
                  >
                    <option value="">-- None --</option>
                    {leads.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>With Contact</label>
                  <select
                    value={meetingForm.contact_id}
                    onChange={(e) => setMeetingForm({ ...meetingForm, contact_id: e.target.value, lead_id: '' })}
                  >
                    <option value="">-- None --</option>
                    {contacts.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Location / Link</label>
                  <input
                    type="text"
                    value={meetingForm.location}
                    onChange={(e) => setMeetingForm({ ...meetingForm, location: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Notes</label>
                  <textarea
                    rows={3}
                    value={meetingForm.notes}
                    onChange={(e) => setMeetingForm({ ...meetingForm, notes: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Assign To</label>
                  <select
                    value={meetingForm.assigned_team_member_id}
                    onChange={(e) => setMeetingForm({ ...meetingForm, assigned_team_member_id: e.target.value })}
                  >
                    <option value="">-- Unassigned --</option>
                    {teamMembers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">Add Meeting</button>
                <button type="button" className="btn-secondary" onClick={() => setShowMeetingForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
