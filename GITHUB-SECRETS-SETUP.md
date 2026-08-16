# GitHub Secrets Setup Guide for CI/CD Deployment

## Overview

This guide explains how to configure GitHub Secrets for automated deployment via GitHub Actions.

---

## 📋 Required Secrets

### 1. **Docker Registry Credentials**

**Purpose:** Push Docker images to Docker Hub

**Steps:**

1. Go to https://hub.docker.com/settings/security
2. Create a new access token (NOT your password)
3. Copy the token

**Secret Details:**
- **Name:** `DOCKER_USERNAME`
- **Value:** Your Docker Hub username
- **Visibility:** Private

4. Create second secret:
- **Name:** `DOCKER_PASSWORD`
- **Value:** Your Docker Hub access token
- **Visibility:** Private

**Example:**
```
DOCKER_USERNAME: arthainvest
DOCKER_PASSWORD: dckr_pat_xxxxxxxxxxxxxxxxxxxx
```

---

### 2. **Production Server Credentials**

**Purpose:** SSH into production server for deployment

#### **A. SSH Public/Private Key Pair**

If you don't have SSH keys:

```bash
# Generate SSH key pair (on your local machine)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/arthainvest_deploy -N ""

# This creates:
# ~/.ssh/arthainvest_deploy (private key)
# ~/.ssh/arthainvest_deploy.pub (public key)
```

#### **B. Setup on Production Server**

```bash
# SSH into production server
ssh deploy@arthainvestcapital.com

# Create .ssh directory if not exists
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Copy your public key to authorized_keys
echo "YOUR_PUBLIC_KEY_CONTENT" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Verify (should show your key)
cat ~/.ssh/authorized_keys
```

#### **C. Add GitHub Secrets**

**Secret 1:**
- **Name:** `PRODUCTION_HOST`
- **Value:** `arthainvestcapital.com` or server IP
- **Visibility:** Private

**Secret 2:**
- **Name:** `PRODUCTION_USER`
- **Value:** `deploy`
- **Visibility:** Private

**Secret 3:**
- **Name:** `PRODUCTION_SSH_PORT`
- **Value:** `22` (or custom SSH port)
- **Visibility:** Private

**Secret 4:**
- **Name:** `PRODUCTION_SSH_KEY`
- **Value:** Copy entire contents of `~/.ssh/arthainvest_deploy` (private key)
- **Visibility:** Private

```bash
# Get private key content (from your local machine)
cat ~/.ssh/arthainvest_deploy
```

---

### 3. **Slack Integration (Optional but Recommended)**

**Purpose:** Send deployment notifications to Slack

#### **A. Create Slack Webhook**

1. Go to https://api.slack.com/apps
2. Create New App → From scratch
3. Name it "ArthaInvest Deployments"
4. Select your workspace
5. In left menu: "Incoming Webhooks"
6. Toggle "Activate Incoming Webhooks"
7. Click "Add New Webhook to Workspace"
8. Select channel (e.g., #deployments)
9. Copy the Webhook URL

#### **B. Add GitHub Secret**

- **Name:** `SLACK_WEBHOOK`
- **Value:** Your webhook URL
- **Visibility:** Private

**Example:**
```
https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Note: Replace YOUR/WEBHOOK/URL with your actual webhook URL from Slack API

---

## 🔑 How to Add Secrets to GitHub

### **Method 1: Web Interface (Easiest)**

1. Go to your GitHub repository: https://github.com/arthainvest/arthainvest-crm
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**
5. Enter:
   - **Name:** `DOCKER_USERNAME`
   - **Value:** Your username
6. Click **Add secret**
7. Repeat for all secrets

### **Method 2: GitHub CLI**

```bash
# Install GitHub CLI if not already installed
# https://cli.github.com/

# Login to GitHub
gh auth login

# Add secrets
gh secret set DOCKER_USERNAME -b "your-username"
gh secret set DOCKER_PASSWORD -b "your-token"
gh secret set PRODUCTION_HOST -b "arthainvestcapital.com"
gh secret set PRODUCTION_USER -b "deploy"
gh secret set PRODUCTION_SSH_PORT -b "22"
gh secret set PRODUCTION_SSH_KEY < ~/.ssh/arthainvest_deploy
gh secret set SLACK_WEBHOOK -b "https://hooks.slack.com/..."

# List all secrets
gh secret list
```

---

## 📝 Complete Secrets Checklist

| Secret Name | Value | Required | Example |
|-------------|-------|----------|---------|
| `DOCKER_USERNAME` | Docker Hub username | ✅ | `arthainvest` |
| `DOCKER_PASSWORD` | Docker Hub token | ✅ | `dckr_pat_...` |
| `PRODUCTION_HOST` | Domain/IP | ✅ | `arthainvestcapital.com` |
| `PRODUCTION_USER` | SSH user | ✅ | `deploy` |
| `PRODUCTION_SSH_PORT` | SSH port | ✅ | `22` |
| `PRODUCTION_SSH_KEY` | Private SSH key | ✅ | (full key content) |
| `SLACK_WEBHOOK` | Slack webhook URL | ❌ | `https://hooks.slack.com/...` |

---

## 🧪 Testing Secrets

### **Test Docker Credentials**

```bash
# Log in to Docker
docker login -u YOUR_USERNAME -p YOUR_TOKEN

# Try to push (will fail if token wrong)
docker push arthainvest/crm-app:test
```

### **Test SSH Access**

```bash
# Use private key to SSH
ssh -i ~/.ssh/arthainvest_deploy deploy@arthainvestcapital.com

# Should connect without password prompt
```

### **Test Slack Webhook**

```bash
# Send test message
curl -X POST 'YOUR_SLACK_WEBHOOK_URL' \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Testing Slack integration",
    "attachments": [{
      "color": "good",
      "title": "Test Message",
      "text": "If you see this, webhooks are working!"
    }]
  }'
```

---

## 🔄 Automatic Deployment Workflow

Once secrets are configured, the GitHub Actions workflow will:

1. **Trigger:** Push code to `production` branch
   ```bash
   git push origin production
   ```

2. **Actions Runs:**
   - Builds Docker image
   - Pushes to Docker registry
   - SSHes into production server
   - Pulls latest code
   - Pulls Docker images
   - Restarts containers
   - Runs database migrations
   - Sends Slack notification

3. **Status:** Check at https://github.com/arthainvest/arthainvest-crm/actions

---

## 🚨 Security Best Practices

✅ **DO:**
- Use access tokens instead of passwords
- Keep SSH keys private (never commit)
- Rotate keys periodically
- Use strong SSH key passwords locally
- Review audit logs regularly
- Limit secret visibility to needed actions

❌ **DON'T:**
- Commit secrets to git
- Share secrets via email/chat
- Use same credentials across environments
- Store secrets in `.env` files
- Hardcode secrets in CI/CD files

---

## 🔐 Rotating Secrets

### **When to Rotate:**
- Quarterly security review
- Key compromise suspected
- Employee departure
- Failed deployment attempt

### **How to Rotate:**

1. **Generate new credentials**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/arthainvest_deploy_new
   ```

2. **Update servers/services with new credentials**

3. **Update GitHub Secrets**
   - Settings → Secrets → Update secret

4. **Test deployment**
   ```bash
   git commit --allow-empty -m "test: trigger deployment"
   git push origin production
   ```

5. **Revoke old credentials** (after successful deployment)

---

## 🆘 Troubleshooting

### **"Permission denied (publickey)" Error**

**Solution:**
1. Verify SSH key in GitHub secret matches server's `~/.ssh/authorized_keys`
2. Check file permissions:
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   ```
3. Test SSH connection:
   ```bash
   ssh -i ~/.ssh/arthainvest_deploy deploy@arthainvestcapital.com
   ```

### **Docker Push Fails**

**Solution:**
1. Verify Docker credentials
   ```bash
   docker login -u $DOCKER_USERNAME -p $DOCKER_PASSWORD
   ```
2. Check token hasn't expired
3. Verify repository exists on Docker Hub

### **Deployment Doesn't Trigger**

**Solution:**
1. Check branch name matches workflow (`production`)
2. Verify workflow file exists: `.github/workflows/deploy-production.yml`
3. Check Actions are enabled in repository settings
4. Review Actions logs for errors

### **Slack Webhook Not Working**

**Solution:**
1. Verify webhook URL is correct
2. Test with curl command
3. Check Slack channel still exists
4. Regenerate webhook if webhook is old

---

## 📖 Additional Resources

- **GitHub Secrets Documentation:** https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions
- **GitHub Actions:** https://docs.github.com/en/actions
- **SSH Key Setup:** https://docs.github.com/en/authentication/connecting-to-github-with-ssh
- **Docker Authentication:** https://docs.docker.com/docker-hub/access-tokens/

---

## ✅ Verification Checklist

After setting up secrets:

- [ ] `DOCKER_USERNAME` set
- [ ] `DOCKER_PASSWORD` set
- [ ] `PRODUCTION_HOST` set
- [ ] `PRODUCTION_USER` set
- [ ] `PRODUCTION_SSH_PORT` set
- [ ] `PRODUCTION_SSH_KEY` set
- [ ] `SLACK_WEBHOOK` set (optional)
- [ ] Can connect via SSH: `ssh -i ~/.ssh/arthainvest_deploy deploy@arthainvestcapital.com`
- [ ] Can push to Docker: `docker push arthainvest/crm-app:test`
- [ ] Workflow file exists and is valid
- [ ] Test deployment triggered successfully

---

**Next Step:** Trigger a test deployment by pushing to the `production` branch and monitor GitHub Actions logs.

