// ArthaInvest CRM - Marketing Module with Integrations
// Canva, Claude AI, ChatGPT, Google Drive integrations

const marketingConfig = {
  // Canva Integration
  canva: {
    connected: false,
    apiKey: '',
    templates: {
      'Instagram Post': 'canva_instagram_template_001',
      'LinkedIn Post': 'canva_linkedin_template_001',
      'Facebook Ad': 'canva_facebook_ad_template_001',
      'Email Banner': 'canva_email_banner_template_001',
      'Product Showcase': 'canva_product_template_001',
      'Client Testimonial': 'canva_testimonial_template_001'
    }
  },

  // Claude AI Integration
  claude: {
    connected: false,
    apiKey: '',
    models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
    capabilities: ['Content Generation', 'Email Copy', 'Social Media Posts', 'Ad Copy', 'Blog Ideas']
  },

  // ChatGPT Integration
  chatgpt: {
    connected: false,
    apiKey: '',
    models: ['gpt-4', 'gpt-3.5-turbo'],
    capabilities: ['Content Generation', 'Email Copy', 'Social Media Posts', 'Ad Copy', 'Blog Ideas']
  },

  // Google Drive Integration
  gdrive: {
    connected: false,
    apiKey: '',
    folderId: '',
    folders: {
      'Creative Assets': 'folder_creative_assets',
      'Brand Guidelines': 'folder_brand_guidelines',
      'Campaign Archives': 'folder_campaigns',
      'Client Approvals': 'folder_approvals',
      'Final Deliverables': 'folder_deliverables'
    }
  }
};

// Marketing Campaign Manager
const campaigns = [
  {
    id: 1,
    name: 'Insurance Awareness - Q3 2026',
    type: 'Educational',
    status: 'Active',
    channel: ['Instagram', 'LinkedIn', 'Email'],
    createdBy: 'vikram',
    startDate: '2026-08-01',
    endDate: '2026-09-30',
    budget: '₹50,000',
    assets: 12,
    engagement: '3.2K'
  },
  {
    id: 2,
    name: 'Mutual Fund Investment Guide',
    type: 'Educational',
    status: 'Planning',
    channel: ['Blog', 'YouTube', 'LinkedIn'],
    createdBy: 'vikram',
    startDate: '2026-09-01',
    endDate: '2026-09-30',
    budget: '₹30,000',
    assets: 5,
    engagement: '1.1K'
  },
  {
    id: 3,
    name: 'Loan DSA Promotion',
    type: 'Promotional',
    status: 'Active',
    channel: ['WhatsApp', 'Email', 'SMS'],
    createdBy: 'amit',
    startDate: '2026-08-15',
    endDate: '2026-08-31',
    budget: '₹25,000',
    assets: 8,
    engagement: '2.5K'
  }
];

// Digital Content Library
const contentLibrary = {
  designs: [
    { id: 1, name: 'Insurance_PostCard_Aug2026.png', type: 'Image', size: '2.4 MB', created: '2026-08-08', creator: 'vikram' },
    { id: 2, name: 'MF_EmailBanner_2026.psd', type: 'Design', size: '45 MB', created: '2026-08-07', creator: 'vikram' },
    { id: 3, name: 'LinkedIn_Profile_Banner.png', type: 'Image', size: '1.8 MB', created: '2026-08-06', creator: 'vikram' },
  ],
  videos: [
    { id: 1, name: 'Insurance_Explainer_Video.mp4', type: 'Video', size: '125 MB', duration: '2:45', created: '2026-08-05', creator: 'vikram' },
    { id: 2, name: 'Client_Testimonial_Rajesh.mp4', type: 'Video', size: '85 MB', duration: '1:30', created: '2026-08-03', creator: 'rajesh' },
  ],
  documents: [
    { id: 1, name: 'Brand_Guidelines_2026.pdf', type: 'PDF', size: '8.5 MB', created: '2026-08-01', creator: 'vikram' },
    { id: 2, name: 'Marketing_Strategy_Q3.docx', type: 'Document', size: '2.1 MB', created: '2026-07-25', creator: 'vikram' },
  ]
};

// AI Content Generation Templates
const aiPrompts = {
  'Instagram Caption - Insurance': `Create an engaging Instagram caption for our insurance product. Include emoji, call-to-action, and relevant hashtags. Make it personal and relatable.`,

  'LinkedIn Article - Wealth Planning': `Write a professional LinkedIn article about wealth planning for millennials. Include statistics, actionable tips, and call-to-action. 300-400 words.`,

  'Email Subject Lines - Campaign': `Generate 5 compelling email subject lines for our mutual fund investment campaign. Make them catchy and click-worthy.`,

  'Social Media Post - Loan DSA': `Create 3 social media post copies for our loan DSA promotion. Use different angles (benefits, testimonials, process).`,

  'Blog Post Outline - Financial Planning': `Create a detailed outline for a blog post on "10 Steps to Secure Your Family's Financial Future". Include SEO keywords.`,

  'Ad Copy - Insurance Product': `Write compelling ad copy for our insurance product targeting age group 25-45. Focus on peace of mind and family security.`
};

// Marketing Analytics
const analytics = {
  socialMedia: {
    instagram: { followers: 2400, engagement: '3.2%', posts: 45, reach: '125K' },
    linkedin: { followers: 8500, engagement: '2.8%', posts: 120, reach: '320K' },
    facebook: { followers: 15000, engagement: '1.9%', posts: 85, reach: '450K' }
  },
  email: {
    subscribers: 5200,
    openRate: '28.5%',
    clickRate: '4.2%',
    campaigns: 24
  },
  website: {
    visitors: '12.5K',
    avgSessionDuration: '3m 45s',
    bounceRate: '32%',
    conversions: '185'
  }
};

// Get marketing campaigns
function getMarketingCampaigns() {
  return campaigns;
}

// Create new campaign
function createCampaign(campaignData) {
  const newCampaign = {
    id: campaigns.length + 1,
    ...campaignData,
    createdBy: getCurrentUser().username,
    assets: 0,
    engagement: '0'
  };
  campaigns.push(newCampaign);
  return newCampaign;
}

// Get content library
function getContentLibrary() {
  return contentLibrary;
}

// Upload content to Google Drive (simulated)
function uploadToGoogleDrive(file, folder) {
  return {
    success: true,
    message: `File "${file.name}" uploaded to ${folder}`,
    fileId: 'drive_' + Date.now(),
    url: `https://drive.google.com/file/d/drive_${Date.now()}/view`
  };
}

// Connect Canva
function connectCanva(apiKey) {
  marketingConfig.canva.apiKey = apiKey;
  marketingConfig.canva.connected = true;
  return { success: true, message: 'Canva connected successfully' };
}

// Connect Claude
function connectClaude(apiKey) {
  marketingConfig.claude.apiKey = apiKey;
  marketingConfig.claude.connected = true;
  return { success: true, message: 'Claude AI connected successfully' };
}

// Connect ChatGPT
function connectChatGPT(apiKey) {
  marketingConfig.chatgpt.apiKey = apiKey;
  marketingConfig.chatgpt.connected = true;
  return { success: true, message: 'ChatGPT connected successfully' };
}

// Connect Google Drive
function connectGoogleDrive(apiKey, folderId) {
  marketingConfig.gdrive.apiKey = apiKey;
  marketingConfig.gdrive.folderId = folderId;
  marketingConfig.gdrive.connected = true;
  return { success: true, message: 'Google Drive connected successfully' };
}

// Get AI content prompt
function getAIPrompt(promptType) {
  return aiPrompts[promptType] || '';
}

// Get marketing analytics
function getMarketingAnalytics() {
  return analytics;
}

// Check integration status
function getIntegrationStatus() {
  return {
    canva: marketingConfig.canva.connected,
    claude: marketingConfig.claude.connected,
    chatgpt: marketingConfig.chatgpt.connected,
    gdrive: marketingConfig.gdrive.connected
  };
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    getMarketingCampaigns,
    createCampaign,
    getContentLibrary,
    uploadToGoogleDrive,
    connectCanva,
    connectClaude,
    connectChatGPT,
    connectGoogleDrive,
    getAIPrompt,
    getMarketingAnalytics,
    getIntegrationStatus,
    aiPrompts
  };
}
