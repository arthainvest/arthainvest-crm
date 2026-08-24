import React, { useState, useEffect } from 'react';
import {
  getCampaigns, createCampaign, updateCampaign, deleteCampaign, syncMailchimp,
  getSettings, getLinkedInConnectUrl, postToLinkedIn, generateMarketingContent
} from '../services/api';
import '../styles/Marketing.css';

// Occasion-themed gradient colors + a big decorative emoji, used by the client-side creative
// generator below. This is NOT Canva - there's no Canva/design-tool API integration here (that
// needs a Canva Developer app + Connect/Autofill API, a separate project). This is a real,
// working alternative built with the browser's own Canvas API: composites a background,
// optional uploaded logo (or a text wordmark if none is uploaded), the occasion, and the
// caption text into a downloadable PNG - entirely client-side, no server round-trip.
const OCCASION_THEMES = {
  'Diwali': { colors: ['#8B0000', '#FF8C00'], emoji: '🪔' },
  'Holi': { colors: ['#FF1493', '#00BFFF'], emoji: '🎨' },
  'Raksha Bandhan': { colors: ['#D2691E', '#FFD700'], emoji: '🎉' },
  'Ganesh Chaturthi': { colors: ['#FF6347', '#FFA500'], emoji: '🙏' },
  'Navratri / Dussehra': { colors: ['#C71585', '#FF4500'], emoji: '🪔' },
  'Independence Day': { colors: ['#FF9933', '#138808'], emoji: '🇮🇳' },
  'Republic Day': { colors: ['#FF9933', '#000080'], emoji: '🇮🇳' },
  'New Year': { colors: ['#4B0082', '#9400D3'], emoji: '🎊' },
  'Makar Sankranti': { colors: ['#FFD700', '#FF8C00'], emoji: '🪁' },
  'Eid': { colors: ['#006400', '#FFD700'], emoji: '🌙' },
  'Christmas': { colors: ['#8B0000', '#006400'], emoji: '🎄' },
};
const DEFAULT_THEME = { colors: ['#667eea', '#764ba2'], emoji: '✨' };

const drawCreative = (canvas, { occasion, content, companyName, logoImg }) => {
  const size = 1080;
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');
  const theme = OCCASION_THEMES[occasion] || DEFAULT_THEME;

  const grad = ctx.createLinearGradient(0, 0, size, size);
  grad.addColorStop(0, theme.colors[0]);
  grad.addColorStop(1, theme.colors[1]);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, size, size);

  ctx.strokeStyle = 'rgba(255,255,255,0.6)';
  ctx.lineWidth = 6;
  ctx.strokeRect(30, 30, size - 60, size - 60);

  ctx.textAlign = 'center';
  if (logoImg) {
    const logoH = 110;
    const logoW = logoImg.width * (logoH / logoImg.height);
    ctx.drawImage(logoImg, (size - logoW) / 2, 55, logoW, logoH);
  } else {
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 56px Arial, sans-serif';
    ctx.fillText(companyName || 'ArthaInvest', size / 2, 135);
  }

  ctx.font = '120px Arial, sans-serif';
  ctx.fillText(theme.emoji, size / 2, 320);

  ctx.font = '38px Arial, sans-serif';
  ctx.fillStyle = '#ffffff';
  ctx.shadowColor = 'rgba(0,0,0,0.35)';
  ctx.shadowBlur = 6;
  const maxWidth = size - 160;
  const words = (content || '').replace(/\s+/g, ' ').trim().split(' ');
  let line = '';
  const lines = [];
  for (const w of words) {
    const test = line ? `${line} ${w}` : w;
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line);
      line = w;
    } else {
      line = test;
    }
  }
  if (line) lines.push(line);
  const capped = lines.slice(0, 9);
  const lineHeight = 50;
  const startY = size / 2 - (capped.length * lineHeight) / 2 + 40;
  capped.forEach((l, i) => ctx.fillText(l, size / 2, startY + i * lineHeight));
  ctx.shadowBlur = 0;

  ctx.font = 'italic 26px Arial, sans-serif';
  ctx.fillStyle = 'rgba(255,255,255,0.9)';
  ctx.fillText('Your Trusted Insurance & Loan Partner', size / 2, size - 70);
};

const emptyCampaignForm = { name: '', type: 'Email', status: 'Active', recipients: '' };

// Ready-to-send captions for the occasions that matter most to an Indian insurance/loan
// distributor's clients - work instantly with no AI/billing required. "Generate with AI"
// still gives a personalized version once Claude billing is funded; this is the fallback
// that's usable today.
const FESTIVE_TEMPLATES = {
  'Diwali': "✨ Wishing you and your family a very Happy Diwali! May this festival of lights bring prosperity, good health, and financial security to your home. ArthaInvest is always here for your insurance & loan needs. 🪔",
  'Holi': "🎨 Happy Holi! May your life be as colorful and joyful as this festival. Wishing you and your family a safe and happy celebration. - ArthaInvest",
  'Raksha Bandhan': "🎉 Happy Raksha Bandhan! On this special day, we're reminded that protecting what matters most is what we do too - your family's financial security. Warm wishes from ArthaInvest.",
  'Ganesh Chaturthi': "🙏 Ganpati Bappa Morya! Wishing you and your family a blessed Ganesh Chaturthi, filled with happiness and new beginnings. - ArthaInvest",
  'Independence Day': "🇮🇳 Happy Independence Day! Celebrating the freedom we cherish - and helping you build the financial freedom you deserve. Jai Hind! - ArthaInvest",
  'New Year': "🎊 Wishing you a very Happy New Year! May this year bring you good health, happiness, and financial growth. Looking forward to serving you again this year. - ArthaInvest",
  'Republic Day': "🇮🇳 Happy Republic Day! Wishing you a day filled with pride and gratitude. - ArthaInvest",
  'Policy Renewal Reminder': "Hi, this is a friendly reminder that your policy renewal is coming up soon. Renewing on time keeps your coverage active with no gap in protection. Reply here or call us and we'll take care of it for you. - ArthaInvest",
  'Loan EMI Reminder': "Hi, this is a reminder that your loan EMI is due soon. Please ensure sufficient balance in your account to avoid any late fee. Reach out if you'd like to discuss your repayment schedule. - ArthaInvest",
};

const OCCASION_OPTIONS = [
  'Diwali', 'Holi', 'Raksha Bandhan', 'Ganesh Chaturthi', 'Navratri / Dussehra',
  'Independence Day', 'Republic Day', 'New Year', 'Makar Sankranti', 'Eid', 'Christmas',
  'Policy Renewal Reminder', 'Loan EMI Reminder', 'Product Promotion', 'Client Appreciation', 'Custom'
];

export default function Marketing() {
  const [campaigns, setCampaigns] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [campaignForm, setCampaignForm] = useState(emptyCampaignForm);
  const [mailchimpSyncing, setMailchimpSyncing] = useState(false);

  const [linkedInConnected, setLinkedInConnected] = useState(false);
  const [linkedInConnecting, setLinkedInConnecting] = useState(false);
  const [linkedInPostText, setLinkedInPostText] = useState('');
  const [linkedInPosting, setLinkedInPosting] = useState(false);

  // AI Content Studio
  const [studioOccasion, setStudioOccasion] = useState('Diwali');
  const [studioCustomOccasion, setStudioCustomOccasion] = useState('');
  const [studioPlatform, setStudioPlatform] = useState('WhatsApp');
  const [studioNotes, setStudioNotes] = useState('');
  const [studioContent, setStudioContent] = useState('');
  const [studioGenerating, setStudioGenerating] = useState(false);
  const [studioMessage, setStudioMessage] = useState(null);

  // Creative Generator (Canva alternative)
  const [logoImg, setLogoImg] = useState(null);
  const [logoFileName, setLogoFileName] = useState('');
  const [creativeUrl, setCreativeUrl] = useState(null);
  const [companyName, setCompanyName] = useState('ArthaInvest');

  const token = localStorage.getItem('token');

  const effectiveOccasion = studioOccasion === 'Custom' ? studioCustomOccasion.trim() : studioOccasion;

  const handleUseFestiveTemplate = () => {
    const template = FESTIVE_TEMPLATES[studioOccasion];
    if (!template) {
      setStudioMessage('No ready-made template for this occasion yet - try "Generate with AI" instead.');
      return;
    }
    setStudioContent(template);
    setStudioMessage('Template filled in below - edit as needed, or copy it to use.');
  };

  const handleGenerateContent = async () => {
    if (!effectiveOccasion) {
      setStudioMessage('Enter an occasion or topic first.');
      return;
    }
    setStudioGenerating(true);
    setStudioMessage(null);
    try {
      const result = await generateMarketingContent(token, effectiveOccasion, studioPlatform, studioNotes);
      if (result.configured && result.content) {
        setStudioContent(result.content);
      }
      setStudioMessage(result.message);
    } catch (error) {
      console.error('Error generating marketing content:', error);
      setStudioMessage('Failed to generate content. Please try again.');
    } finally {
      setStudioGenerating(false);
    }
  };

  const handleCopyContent = async () => {
    if (!studioContent.trim()) return;
    try {
      await navigator.clipboard.writeText(studioContent);
      setStudioMessage('Copied to clipboard.');
    } catch (error) {
      console.error('Error copying content:', error);
      setStudioMessage('Could not copy automatically - select and copy the text manually.');
    }
  };

  const handleUseInLinkedInPost = () => {
    if (!studioContent.trim()) return;
    setLinkedInPostText(studioContent);
    setStudioMessage('Loaded into the LinkedIn post box above - scroll up to post it.');
  };

  const handleMailchimpSync = async () => {
    setMailchimpSyncing(true);
    try {
      const result = await syncMailchimp(token);
      alert(result.message);
    } catch (error) {
      console.error('Error syncing Mailchimp:', error);
      alert('Failed to sync with Mailchimp. Please try again.');
    } finally {
      setMailchimpSyncing(false);
    }
  };

  const fetchLinkedInStatus = async () => {
    try {
      const settings = await getSettings(token);
      setLinkedInConnected(!!settings.linkedin_connected);
      if (settings.company) setCompanyName(settings.company);
    } catch (error) {
      console.error('Error fetching LinkedIn status:', error);
    }
  };

  const handleLogoUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setLogoFileName(file.name);
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => setLogoImg(img);
      img.src = event.target.result;
    };
    reader.readAsDataURL(file);
  };

  const handleCreateImage = () => {
    if (!studioContent.trim()) {
      setStudioMessage('Generate or select content first, then create the image.');
      return;
    }
    const canvas = document.createElement('canvas');
    drawCreative(canvas, { occasion: studioOccasion, content: studioContent, companyName, logoImg });
    setCreativeUrl(canvas.toDataURL('image/png'));
  };

  const handleConnectLinkedIn = async () => {
    setLinkedInConnecting(true);
    try {
      const result = await getLinkedInConnectUrl(token);
      if (result.configured && result.auth_url) {
        window.location.href = result.auth_url;
        return;
      }
      alert(result.message);
    } catch (error) {
      console.error('Error starting LinkedIn connect:', error);
      alert('Failed to start LinkedIn connection. Please try again.');
    } finally {
      setLinkedInConnecting(false);
    }
  };

  const handlePostToLinkedIn = async () => {
    if (!linkedInPostText.trim()) return;
    setLinkedInPosting(true);
    try {
      const result = await postToLinkedIn(token, linkedInPostText);
      alert(result.message);
      if (result.configured && result.post_urn) {
        setLinkedInPostText('');
      }
    } catch (error) {
      console.error('Error posting to LinkedIn:', error);
      alert('Failed to post to LinkedIn. Please try again.');
    } finally {
      setLinkedInPosting(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
    fetchLinkedInStatus();

    // LinkedIn's OAuth redirect lands back here with ?linkedin=connected|error - surface it
    // once, then clean the URL so a refresh doesn't re-show the same message.
    const params = new URLSearchParams(window.location.search);
    const linkedinResult = params.get('linkedin');
    if (linkedinResult === 'connected') {
      alert('LinkedIn connected successfully.');
      window.history.replaceState({}, '', window.location.pathname);
    } else if (linkedinResult === 'error') {
      alert('LinkedIn connection failed - please try again.');
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  const fetchCampaigns = async () => {
    try {
      const data = await getCampaigns(token);
      setCampaigns(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching campaigns:', error);
    }
  };

  const handleNewCampaignClick = () => {
    setEditingId(null);
    setCampaignForm(emptyCampaignForm);
    setShowForm(true);
  };

  const handleEditClick = (campaign) => {
    setEditingId(campaign.id);
    setCampaignForm({
      name: campaign.name,
      type: campaign.type,
      status: campaign.status,
      recipients: campaign.recipients
    });
    setShowForm(true);
  };

  const handleSaveCampaign = async (e) => {
    e.preventDefault();
    if (!campaignForm.name.trim()) return;

    try {
      if (editingId) {
        await updateCampaign(token, editingId, {
          name: campaignForm.name,
          type: campaignForm.type,
          status: campaignForm.status,
          recipients: Number(campaignForm.recipients) || 0
        });
      } else {
        await createCampaign(token, {
          name: campaignForm.name,
          type: campaignForm.type,
          status: campaignForm.status,
          recipients: Number(campaignForm.recipients) || 0
        });
      }
      setShowForm(false);
      setCampaignForm(emptyCampaignForm);
      setEditingId(null);
      fetchCampaigns();
    } catch (error) {
      console.error('Error saving campaign:', error);
      alert('Failed to save campaign. Please try again.');
    }
  };

  const handleDeleteCampaign = async (id) => {
    if (!window.confirm('Are you sure you want to delete this campaign?')) return;
    try {
      await deleteCampaign(token, id);
      setCampaigns((prev) => prev.filter((c) => c.id !== id));
    } catch (error) {
      console.error('Error deleting campaign:', error);
      alert('Failed to delete campaign. Please try again.');
    }
  };

  const totalCampaigns = campaigns.length;
  const activeCampaigns = campaigns.filter((c) => c.status === 'Active').length;
  const totalRecipients = campaigns.reduce((sum, c) => sum + (c.recipients || 0), 0);
  const avgEngagement = totalCampaigns > 0
    ? Math.round(campaigns.reduce((sum, c) => sum + (c.engagement || 0), 0) / totalCampaigns)
    : 0;

  return (
    <div className="marketing-container">
      <div className="marketing-header">
        <h1>Marketing Campaigns</h1>
        <button className="btn-primary" onClick={handleNewCampaignClick}>+ New Campaign</button>
      </div>

      <div className="mailchimp-card">
        <div className="mailchimp-info">
          <span className="mailchimp-icon">🐒</span>
          <div>
            <h3>Email Marketing (Mailchimp)</h3>
            <p>Sync your contacts into a Mailchimp audience for email campaigns.</p>
          </div>
        </div>
        <button className="btn-secondary" onClick={handleMailchimpSync} disabled={mailchimpSyncing}>
          {mailchimpSyncing ? 'Syncing…' : 'Sync Contacts to Mailchimp'}
        </button>
      </div>

      <div className="linkedin-card">
        <div className="linkedin-info">
          <span className="linkedin-icon">💼</span>
          <div>
            <h3>LinkedIn</h3>
            <p>
              {linkedInConnected
                ? 'Connected - post updates straight to your LinkedIn profile.'
                : 'Connect your LinkedIn account to post updates from here.'}
            </p>
          </div>
        </div>
        {!linkedInConnected ? (
          <button className="btn-secondary linkedin-btn" onClick={handleConnectLinkedIn} disabled={linkedInConnecting}>
            {linkedInConnecting ? 'Redirecting…' : 'Connect LinkedIn'}
          </button>
        ) : (
          <div className="linkedin-post-box">
            <textarea
              placeholder="Write an update to post to LinkedIn..."
              value={linkedInPostText}
              onChange={(e) => setLinkedInPostText(e.target.value)}
              rows={3}
            />
            <button className="btn-secondary linkedin-btn" onClick={handlePostToLinkedIn} disabled={linkedInPosting || !linkedInPostText.trim()}>
              {linkedInPosting ? 'Posting…' : 'Post to LinkedIn'}
            </button>
          </div>
        )}
      </div>

      <div className="content-studio-card">
        <div className="content-studio-header">
          <span className="content-studio-icon">🎨</span>
          <div>
            <h3>AI Content Studio</h3>
            <p>Draft festive greetings and promotional content with Claude AI, or start from a ready-made festival template - no AI needed for those.</p>
          </div>
        </div>

        <div className="content-studio-form">
          <div className="content-studio-row">
            <div className="form-group">
              <label>Occasion</label>
              <select value={studioOccasion} onChange={(e) => setStudioOccasion(e.target.value)}>
                {OCCASION_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Platform</label>
              <select value={studioPlatform} onChange={(e) => setStudioPlatform(e.target.value)}>
                <option value="WhatsApp">WhatsApp</option>
                <option value="Email">Email</option>
                <option value="LinkedIn">LinkedIn</option>
                <option value="SMS">SMS</option>
              </select>
            </div>
          </div>

          {studioOccasion === 'Custom' && (
            <div className="form-group">
              <label>Custom occasion / topic</label>
              <input
                type="text"
                placeholder="e.g. Onam, new office branch launch..."
                value={studioCustomOccasion}
                onChange={(e) => setStudioCustomOccasion(e.target.value)}
              />
            </div>
          )}

          <div className="form-group">
            <label>Extra notes (optional)</label>
            <input
              type="text"
              placeholder="e.g. mention our new health insurance plan"
              value={studioNotes}
              onChange={(e) => setStudioNotes(e.target.value)}
            />
          </div>

          <div className="content-studio-actions">
            <button type="button" className="btn-secondary" onClick={handleUseFestiveTemplate} disabled={studioOccasion === 'Custom'}>
              📋 Use Festive Template
            </button>
            <button type="button" className="btn-secondary content-studio-ai-btn" onClick={handleGenerateContent} disabled={studioGenerating}>
              {studioGenerating ? '✨ Generating…' : '✨ Generate with AI'}
            </button>
          </div>

          {studioMessage && <p className="content-studio-message">{studioMessage}</p>}

          <div className="form-group">
            <label>Content</label>
            <textarea
              rows={5}
              placeholder="Generated or template content will appear here - fully editable."
              value={studioContent}
              onChange={(e) => setStudioContent(e.target.value)}
            />
          </div>

          {studioContent.trim() && (
            <div className="content-studio-actions">
              <button type="button" className="btn-secondary" onClick={handleCopyContent}>📄 Copy</button>
              {studioPlatform === 'LinkedIn' && linkedInConnected && (
                <button type="button" className="btn-secondary linkedin-btn" onClick={handleUseInLinkedInPost}>
                  💼 Use in LinkedIn Post
                </button>
              )}
            </div>
          )}

          <div className="creative-generator">
            <h4>🎨 Create a shareable image</h4>
            <p className="creative-generator-hint">
              Turns the content above into a branded image you can download and post to WhatsApp Status, Instagram, or anywhere else.
              This composites your logo + text on the browser side - it's not Canva or ChatGPT's image tools, which would need a separate paid integration, but it's real and works right now.
            </p>
            <div className="creative-generator-row">
              <label className="btn-secondary creative-upload-btn">
                🖼️ {logoFileName || 'Upload Logo (optional)'}
                <input type="file" accept="image/*" onChange={handleLogoUpload} style={{ display: 'none' }} />
              </label>
              <button type="button" className="btn-secondary content-studio-ai-btn" onClick={handleCreateImage}>
                🎨 Create Image
              </button>
            </div>
            {!logoImg && <p className="creative-generator-hint">No logo uploaded - will use an "{companyName}" text wordmark instead.</p>}

            {creativeUrl && (
              <div className="creative-preview">
                <img src={creativeUrl} alt="Generated creative" />
                <a
                  className="btn-secondary linkedin-btn creative-download-btn"
                  href={creativeUrl}
                  download={`arthainvest-${(studioOccasion || 'creative').toLowerCase().replace(/[^a-z0-9]+/g, '-')}.png`}
                >
                  ⬇ Download Image
                </a>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{totalCampaigns}</div>
          <div className="stat-label">Total Campaigns</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{activeCampaigns}</div>
          <div className="stat-label">Active</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{totalRecipients.toLocaleString('en-IN')}</div>
          <div className="stat-label">Total Recipients</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{avgEngagement}%</div>
          <div className="stat-label">Avg Engagement</div>
        </div>
      </div>

      {campaigns.length === 0 ? (
        <p className="no-data">No campaigns yet. Create one to get started.</p>
      ) : (
        <div className="campaigns-grid">
          {campaigns.map(campaign => (
            <div key={campaign.id} className={`campaign-card ${campaign.status.toLowerCase()}`}>
              <div className="campaign-header">
                <h3>{campaign.name}</h3>
                <span className={`status-badge ${campaign.status.toLowerCase()}`}>{campaign.status}</span>
              </div>

              <div className="campaign-info">
                <p><strong>Type:</strong> {campaign.type}</p>
                <p><strong>Recipients:</strong> {campaign.recipients}</p>
                <p><strong>Engagement:</strong> {campaign.engagement}%</p>
              </div>

              <div className="campaign-progress">
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${campaign.progress}%` }}></div>
                </div>
                <p className="progress-text">{campaign.progress}% Complete</p>
              </div>

              <div className="campaign-actions">
                <button className="btn-small" onClick={() => handleEditClick(campaign)}>Edit</button>
                <button className="btn-small delete" onClick={() => handleDeleteCampaign(campaign.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingId ? 'Edit Campaign' : 'New Campaign'}</h2>
              <button className="btn-close" onClick={() => setShowForm(false)}>×</button>
            </div>

            <form onSubmit={handleSaveCampaign}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Campaign Name *</label>
                  <input
                    type="text"
                    required
                    value={campaignForm.name}
                    onChange={(e) => setCampaignForm({ ...campaignForm, name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Type</label>
                  <select
                    value={campaignForm.type}
                    onChange={(e) => setCampaignForm({ ...campaignForm, type: e.target.value })}
                  >
                    <option value="Email">Email</option>
                    <option value="WhatsApp">WhatsApp</option>
                    <option value="SMS">SMS</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Status</label>
                  <select
                    value={campaignForm.status}
                    onChange={(e) => setCampaignForm({ ...campaignForm, status: e.target.value })}
                  >
                    <option value="Active">Active</option>
                    <option value="Completed">Completed</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Recipients</label>
                  <input
                    type="number"
                    min="0"
                    value={campaignForm.recipients}
                    onChange={(e) => setCampaignForm({ ...campaignForm, recipients: e.target.value })}
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button type="submit" className="btn-primary">
                  {editingId ? 'Save Changes' : 'Create Campaign'}
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
