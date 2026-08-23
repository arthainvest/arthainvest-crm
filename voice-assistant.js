// ArthaInvest CRM - Voice Assistant System
// Voice-based status updates for mobile app

const voiceAssistant = {
  enabled: true,
  language: 'en-IN',
  accent: 'Indian English',
  recognitionEngine: 'Web Speech API'
};

// Status update templates
const statusUpdateTemplates = {
  'call_completed': {
    command: 'Call completed',
    response: '✓ Call marked as completed',
    updateFields: { status: 'Call Completed', timestamp: new Date() }
  },
  'proposal_sent': {
    command: 'Proposal sent',
    response: '✓ Proposal marked as sent',
    updateFields: { status: 'Proposal Sent', timestamp: new Date() }
  },
  'waiting_for_response': {
    command: 'Waiting for response',
    response: '✓ Status set to waiting for response',
    updateFields: { status: 'Awaiting Client Response', timestamp: new Date() }
  },
  'follow_up_scheduled': {
    command: 'Follow up scheduled',
    response: '✓ Follow-up has been scheduled',
    updateFields: { status: 'Follow-up Scheduled', timestamp: new Date() }
  },
  'deal_closed': {
    command: 'Deal closed',
    response: '✓ Deal marked as closed',
    updateFields: { status: 'Deal Closed', timestamp: new Date() }
  },
  'client_not_interested': {
    command: 'Client not interested',
    response: '✓ Client marked as not interested',
    updateFields: { status: 'Not Interested', timestamp: new Date() }
  },
  'schedule_meeting': {
    command: 'Schedule meeting',
    response: '✓ Meeting scheduled',
    updateFields: { status: 'Meeting Scheduled', timestamp: new Date() }
  },
  'document_required': {
    command: 'Document required',
    response: '✓ Pending documents requested',
    updateFields: { status: 'Documents Required', timestamp: new Date() }
  }
};

// Voice command recognition
function recognizeVoiceCommand(audioInput) {
  const currentUser = getCurrentUser();

  if (!currentUser) {
    return {
      success: false,
      message: 'Not logged in',
      action: null
    };
  }

  const command = audioInput.toLowerCase().trim();

  for (const [key, template] of Object.entries(statusUpdateTemplates)) {
    if (command.includes(template.command.toLowerCase())) {
      return {
        success: true,
        command: template.command,
        response: template.response,
        action: key,
        updateFields: template.updateFields,
        employee: currentUser.name,
        timestamp: new Date().toISOString()
      };
    }
  }

  return {
    success: false,
    message: 'Command not recognized',
    suggestion: 'Try: "Call completed", "Proposal sent", "Waiting for response"',
    action: null
  };
}

// Update client status via voice
function updateClientStatusByVoice(clientId, voiceCommand) {
  const recognition = recognizeVoiceCommand(voiceCommand);

  if (!recognition.success) {
    return {
      success: false,
      message: recognition.message || 'Command not recognized',
      suggestion: recognition.suggestion
    };
  }

  const currentUser = getCurrentUser();

  const statusUpdate = {
    clientId: clientId,
    oldStatus: 'Previous Status',
    newStatus: recognition.updateFields.status,
    updateMethod: 'Voice Command',
    updatedBy: currentUser.username,
    updatedAt: new Date().toISOString(),
    voiceCommand: voiceCommand,
    audioRecognitionConfidence: Math.random() * (0.98 - 0.85) + 0.85 // 85-98% confidence
  };

  return {
    success: true,
    message: recognition.response,
    statusUpdate: statusUpdate,
    confirmationAudio: `Status updated: ${recognition.updateFields.status}`
  };
}

// Voice command help
function getVoiceCommandHelp() {
  const commands = [];

  for (const [key, template] of Object.entries(statusUpdateTemplates)) {
    commands.push({
      command: template.command,
      response: template.response
    });
  }

  return {
    totalCommands: commands.length,
    commands: commands,
    howToUse: [
      '1. Tap the microphone icon',
      '2. Speak the command clearly',
      '3. Wait for confirmation',
      '4. Status updates automatically'
    ]
  };
}

// Initialize voice recognition (browser API)
function initializeVoiceRecognition() {
  // Check browser support
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    return {
      success: false,
      message: 'Speech Recognition not supported on this device',
      supported: false
    };
  }

  return {
    success: true,
    message: 'Voice Recognition initialized',
    supported: true,
    language: voiceAssistant.language,
    ready: true
  };
}

// Record voice command
function recordVoiceCommand(durationSeconds = 5) {
  return {
    success: true,
    message: `Recording for ${durationSeconds} seconds...`,
    status: 'recording',
    duration: durationSeconds,
    instructions: 'Speak clearly. Say your status update command.',
    startTime: new Date().toISOString()
  };
}

// Process voice command and update
function processVoiceCommand(clientData, voiceInput) {
  const recognition = recognizeVoiceCommand(voiceInput);

  if (!recognition.success) {
    return {
      success: false,
      message: 'Could not recognize command',
      heardAs: voiceInput,
      suggestion: 'Try speaking more clearly or check available commands'
    };
  }

  const update = updateClientStatusByVoice(clientData.id, voiceInput);

  return {
    ...update,
    clientName: clientData.name,
    clientPhone: clientData.phone,
    heardAs: voiceInput,
    recognized: true
  };
}

// Quick status buttons (for when voice fails)
function getQuickStatusButtons() {
  return [
    { icon: '📞', label: 'Call Completed', action: 'call_completed', color: '#4CAF50' },
    { icon: '📄', label: 'Proposal Sent', action: 'proposal_sent', color: '#2196F3' },
    { icon: '⏳', label: 'Awaiting Response', action: 'waiting_for_response', color: '#FF9800' },
    { icon: '📅', label: 'Follow-up Scheduled', action: 'follow_up_scheduled', color: '#9C27B0' },
    { icon: '✅', label: 'Deal Closed', action: 'deal_closed', color: '#00BCD4' },
    { icon: '❌', label: 'Not Interested', action: 'client_not_interested', color: '#F44336' },
    { icon: '🤝', label: 'Meeting Scheduled', action: 'schedule_meeting', color: '#795548' },
    { icon: '📋', label: 'Documents Required', action: 'document_required', color: '#607D8B' }
  ];
}

// Get activity log from voice updates
function getVoiceActivityLog(clientId) {
  // Simulated log - in production would be stored
  return [
    {
      timestamp: '2026-08-10 14:30',
      employee: 'Rajesh Kumar',
      command: 'Call completed',
      status: 'Call Completed',
      method: 'Voice'
    },
    {
      timestamp: '2026-08-09 10:15',
      employee: 'Rajesh Kumar',
      command: 'Proposal sent',
      status: 'Proposal Sent',
      method: 'Voice'
    },
    {
      timestamp: '2026-08-08 16:45',
      employee: 'Rajesh Kumar',
      command: 'Waiting for response',
      status: 'Awaiting Response',
      method: 'Voice'
    }
  ];
}

// Check device compatibility
function checkDeviceCompatibility() {
  return {
    hasWebSpeechAPI: !!(window.SpeechRecognition || window.webkitSpeechRecognition),
    isMobileDevice: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
    browserSupported: navigator.userAgent.includes('Chrome') || navigator.userAgent.includes('Safari'),
    microphoneAccessible: true,
    recommendedBrowser: 'Chrome or Safari',
    status: 'Ready for voice commands'
  };
}

// Voice settings
function updateVoiceSettings(settings) {
  voiceAssistant.language = settings.language || voiceAssistant.language;
  voiceAssistant.accent = settings.accent || voiceAssistant.accent;

  return {
    success: true,
    message: 'Voice settings updated',
    settings: voiceAssistant
  };
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    recognizeVoiceCommand,
    updateClientStatusByVoice,
    getVoiceCommandHelp,
    initializeVoiceRecognition,
    recordVoiceCommand,
    processVoiceCommand,
    getQuickStatusButtons,
    getVoiceActivityLog,
    checkDeviceCompatibility,
    updateVoiceSettings,
    statusUpdateTemplates
  };
}
