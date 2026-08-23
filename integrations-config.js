// ArthaInvest CRM - Third-Party Integrations Configuration
// AI Automation + WhatsApp + LinkedIn + Apollo Integration

const integrations = {
  // ===== AI AUTOMATION INTEGRATIONS =====
  claude: {
    enabled: true,
    provider: 'Anthropic Claude',
    apiKey: process.env.CLAUDE_API_KEY || 'sk-ant-xxxx',
    model: 'claude-opus-5',
    capabilities: [
      'Lead scoring & analysis',
      'Call transcription & summarization',
      'Email draft generation',
      'Content creation (blogs, campaigns)',
      'Deal analysis & recommendations',
      'Customer insights & patterns'
    ],
    endpoints: {
      leadAnalysis: '/integrations/claude/analyze-lead',
      callSummary: '/integrations/claude/summarize-call',
      emailDraft: '/integrations/claude/generate-email',
      contentCreate: '/integrations/claude/create-content',
      dealAnalysis: '/integrations/claude/analyze-deal'
    }
  },

  chatgpt: {
    enabled: true,
    provider: 'OpenAI ChatGPT',
    apiKey: process.env.OPENAI_API_KEY || 'sk-xxxx',
    model: 'gpt-4',
    capabilities: [
      'Marketing copy generation',
      'Social media content',
      'Customer response automation',
      'Sales objection handling',
      'Product descriptions',
      'FAQ generation'
    ],
    endpoints: {
      marketingCopy: '/integrations/chatgpt/generate-copy',
      socialContent: '/integrations/chatgpt/social-post',
      responseAuto: '/integrations/chatgpt/auto-response',
      objectionHandle: '/integrations/chatgpt/handle-objection',
      productDesc: '/integrations/chatgpt/product-description'
    }
  },

  // ===== WHATSAPP INTEGRATION =====
  whatsapp: {
    enabled: true,
    provider: 'WhatsApp Business API',
    apiKey: process.env.WHATSAPP_API_KEY || 'whatsapp_key_xxxx',
    phoneNumber: process.env.WHATSAPP_PHONE || '+91-XXXXXXXXXX',
    capabilities: [
      'Send campaign messages',
      'Customer notifications',
      'Lead follow-ups',
      'Document sharing',
      'Interactive forms',
      'Automated responses',
      'Media uploads (images, PDFs)'
    ],
    features: {
      campaigns: {
        path: '/integrations/whatsapp/campaigns',
        method: 'POST',
        params: ['phone_numbers', 'message', 'template_id', 'media']
      },
      notifications: {
        path: '/integrations/whatsapp/notify',
        method: 'POST',
        params: ['lead_id', 'notification_type', 'message']
      },
      followup: {
        path: '/integrations/whatsapp/followup',
        method: 'POST',
        params: ['contact_id', 'deal_id', 'message', 'schedule_time']
      },
      documents: {
        path: '/integrations/whatsapp/send-document',
        method: 'POST',
        params: ['contact_id', 'document_type', 'file_url']
      }
    },
    templates: [
      'lead_qualification',
      'deal_update',
      'invoice_notification',
      'appointment_reminder',
      'document_request',
      'payment_reminder'
    ]
  },

  // ===== LINKEDIN INTEGRATION =====
  linkedin: {
    enabled: true,
    provider: 'LinkedIn API',
    clientId: process.env.LINKEDIN_CLIENT_ID || 'linkedin_client_xxxx',
    clientSecret: process.env.LINKEDIN_CLIENT_SECRET || 'linkedin_secret_xxxx',
    capabilities: [
      'Lead research & enrichment',
      'Company insights',
      'Contact information',
      'Job change notifications',
      'Outreach messaging',
      'Profile analytics',
      'Sales navigator integration'
    ],
    features: {
      leadEnrichment: {
        path: '/integrations/linkedin/enrich-lead',
        method: 'POST',
        params: ['lead_id', 'email', 'name', 'company']
      },
      companyInsights: {
        path: '/integrations/linkedin/company-info',
        method: 'GET',
        params: ['company_name', 'company_id']
      },
      outreach: {
        path: '/integrations/linkedin/send-message',
        method: 'POST',
        params: ['recipient_id', 'message', 'subject']
      },
      jobChanges: {
        path: '/integrations/linkedin/job-change-alerts',
        method: 'GET',
        params: ['contact_ids']
      }
    },
    dataSync: {
      frequency: 'daily',
      autoEnrich: true,
      updateContacts: true
    }
  },

  // ===== APOLLO INTEGRATION =====
  apollo: {
    enabled: true,
    provider: 'Apollo.io',
    apiKey: process.env.APOLLO_API_KEY || 'apollo_key_xxxx',
    capabilities: [
      'Database of 250M+ contacts',
      'Email verification',
      'Company enrichment',
      'Contact discovery',
      'Sequence automation',
      'Engagement tracking',
      'Lead scoring'
    ],
    features: {
      contactSearch: {
        path: '/integrations/apollo/search-contacts',
        method: 'POST',
        params: ['company', 'title', 'industry', 'location']
      },
      emailFinder: {
        path: '/integrations/apollo/find-email',
        method: 'POST',
        params: ['first_name', 'last_name', 'company', 'domain']
      },
      companyEnrich: {
        path: '/integrations/apollo/enrich-company',
        method: 'POST',
        params: ['company_name', 'website']
      },
      emailVerify: {
        path: '/integrations/apollo/verify-email',
        method: 'POST',
        params: ['email']
      },
      sequenceCreate: {
        path: '/integrations/apollo/create-sequence',
        method: 'POST',
        params: ['name', 'contacts', 'steps']
      },
      engagementTrack: {
        path: '/integrations/apollo/track-engagement',
        method: 'GET',
        params: ['lead_id', 'date_range']
      }
    }
  }
};

module.exports = integrations;
