# ArthaInvest Fintech CRM - Deployment Guide

## Quick Start (Development)

### Local Setup (5 minutes)
```bash
cd FinTech-CRM
npm install
cp .env.example .env
npm run db:migrate
npm run dev
```

Visit `http://localhost:3001` and login with default credentials:
- Email: `admin@arthainvest.com`
- Password: `demo123`

---

## Production Deployment

### Option 1: Docker Compose (Recommended for Most Cases)

#### Prerequisites
- Docker & Docker Compose installed
- Domain name (for SSL)

#### Setup
1. Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: arthainvest_crm
      POSTGRES_USER: crm_user
      POSTGRES_PASSWORD: secure_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: .
    environment:
      DATABASE_URL: postgresql://crm_user:secure_password_here@postgres:5432/arthainvest_crm
      JWT_SECRET: your-super-secret-jwt-key
      NODE_ENV: production
      PORT: 3000
    ports:
      - "3000:3000"
    depends_on:
      - postgres

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    environment:
      NEXT_PUBLIC_API_URL: https://api.arthainvest.com
    ports:
      - "3001:3001"
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
```

2. Deploy:
```bash
docker-compose up -d
```

---

### Option 2: Cloud Platforms

#### A. Render.com (Easiest)

**Backend Deployment:**
1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repo
4. Set environment variables:
   - `DATABASE_URL` → Use Render PostgreSQL
   - `JWT_SECRET` → Generate random string
   - `NODE_ENV` → production
5. Deploy

**Database:**
1. Create PostgreSQL database on Render
2. Run migrations from dashboard

**Frontend on Netlify/Vercel:**
```bash
npm run build
# Deploy `out/` folder
```

#### B. Heroku (Legacy but Still Works)

```bash
# Install Heroku CLI
npm install -g heroku

# Login
heroku login

# Create app
heroku create arthainvest-crm

# Set environment variables
heroku config:set DATABASE_URL=postgresql://...
heroku config:set JWT_SECRET=your-secret

# Deploy
git push heroku main

# Run migrations
heroku run "npm run db:migrate"
```

#### C. AWS (Scalable)

**RDS for PostgreSQL:**
```bash
# Create RDS instance through AWS Console
# Copy connection string to .env
```

**EC2 for Backend:**
```bash
# SSH into EC2 instance
ssh -i key.pem ec2-user@your-instance

# Install Node
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Clone and setup
git clone your-repo
cd FinTech-CRM
npm install
npm run build
npm start
```

**CloudFront for CDN:**
- Set up CloudFront distribution pointing to API
- Add S3 for static assets

#### D. DigitalOcean App Platform

1. Create new App on DigitalOcean
2. Connect GitHub
3. Set environment variables
4. Deploy database from DigitalOcean Marketplace
5. Deploy backend and frontend services

---

## Database Backup & Recovery

### Automatic Backups
```bash
# Create weekly backup script (backup.sh)
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL > backups/arthainvest_crm_$TIMESTAMP.sql
gzip backups/arthainvest_crm_$TIMESTAMP.sql

# Upload to S3
aws s3 cp backups/arthainvest_crm_$TIMESTAMP.sql.gz s3://arthainvest-backups/

# Cron job (every Sunday at 2 AM)
0 2 * * 0 /home/user/backup.sh
```

### Restore from Backup
```bash
gunzip backup.sql.gz
psql $DATABASE_URL < backup.sql
```

---

## SSL/HTTPS Configuration

### With Let's Encrypt (Free)
```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d arthainvest.com -d www.arthainvest.com

# Auto-renew
sudo systemctl enable certbot.timer
```

### Update Nginx
```nginx
server {
    listen 443 ssl http2;
    server_name arthainvest.com;

    ssl_certificate /etc/letsencrypt/live/arthainvest.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/arthainvest.com/privkey.pem;

    location / {
        proxy_pass http://frontend:3001;
    }

    location /api {
        proxy_pass http://backend:3000;
    }
}

server {
    listen 80;
    server_name arthainvest.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Performance Tuning

### PostgreSQL
```sql
-- Increase shared buffers
ALTER SYSTEM SET shared_buffers = '256MB';

-- Connection pooling (PgBouncer)
apt-get install pgbouncer

-- Add to pgbouncer.ini
[databases]
arthainvest_crm = host=localhost port=5432 dbname=arthainvest_crm

-- Restart
systemctl restart pgbouncer
```

### Redis Caching
```bash
# Install Redis
apt-get install redis-server

# Update .env
REDIS_URL=redis://localhost:6379

# Update backend to use Redis for sessions/caching
```

### Nginx Compression
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1024;
```

---

## Monitoring & Logging

### Application Logging
```javascript
// server/index.js - Add logging
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});
```

### Error Tracking (Sentry)
```bash
npm install @sentry/node

# Update server/index.js
import * as Sentry from "@sentry/node";
Sentry.init({ dsn: process.env.SENTRY_DSN });
```

### Uptime Monitoring
- Use UptimeRobot (free tier)
- Monitor `/health` endpoint every 5 minutes
- Get alerts if down

### Server Metrics
```bash
# Install Prometheus
apt-get install prometheus

# Monitor with Grafana
apt-get install grafana-server
```

---

## Email Configuration

### Gmail SMTP
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

### SendGrid
```env
SENDGRID_API_KEY=your-sendgrid-key
```

### AWS SES
```env
AWS_SES_REGION=us-east-1
AWS_SES_ACCESS_KEY=...
AWS_SES_SECRET_KEY=...
```

---

## WhatsApp & Call Integration

### Twilio Setup
```bash
# Buy Twilio number for calls
# Install Twilio SDK
npm install twilio

# Add to server/config/twilio.js
const twilio = require('twilio');
const client = new twilio(process.env.TWILIO_ACCOUNT_SID, process.env.TWILIO_AUTH_TOKEN);
```

### WhatsApp Business API
1. Set up Meta Business Account
2. Get WhatsApp Business Phone Number
3. Configure Webhook for incoming messages
4. Verify API credentials in `.env`

---

## Team Member Onboarding

### Create Admin Account
```bash
# SSH into server
psql arthainvest_crm

INSERT INTO users (id, email, password_hash, first_name, last_name, role)
VALUES (gen_random_uuid(), 'admin@arthainvest.com', 'demo123', 'Admin', 'User', 'ADMIN');
```

### User Roles
- **ADMIN**: Full system access, user management
- **TEAM_LEADER**: Manage team, assign leads, view reports
- **EMPLOYEE**: Sales rep access, assigned contacts only
- **VIEWER**: Read-only access

---

## Maintenance Checklist

### Weekly
- [ ] Check error logs
- [ ] Monitor database size
- [ ] Verify backups completed
- [ ] Check SSL certificate expiry (30 days warning)

### Monthly
- [ ] Review security logs
- [ ] Update dependencies (`npm update`)
- [ ] Analyze performance metrics
- [ ] Test backup restore

### Quarterly
- [ ] Security audit
- [ ] Database optimization
- [ ] Update documentation
- [ ] Load testing

### Annually
- [ ] Full system review
- [ ] Plan upgrades
- [ ] Compliance audit
- [ ] Team training

---

## Troubleshooting

### Database Connection Issues
```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check logs
journalctl -u postgresql -n 100

# Restart service
systemctl restart postgresql
```

### API Not Responding
```bash
# Check process
ps aux | grep node

# Check port
lsof -i :3000

# Check logs
pm2 logs
```

### High Memory Usage
```bash
# Monitor
free -h

# Find memory hogs
ps aux | sort -k4 -rn | head -10

# Restart service
systemctl restart crm-backend
```

---

## Disaster Recovery

### Automated Failover
```bash
# Set up 2 backend servers with load balancer
# Database replication to standby
# Monitor and auto-failover on primary failure
```

### Regular Testing
- Test restore from backup monthly
- Document recovery procedures
- Train team on DR process
- Update contact information for support

---

## Security Hardening

### System Level
```bash
# Enable firewall
sudo ufw enable
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# SSH hardening
# - Disable password auth
# - Use key-based only
# - Change default port
```

### Application Level
- [ ] Enable 2FA for admin users
- [ ] Set strong password requirements
- [ ] Enable API rate limiting
- [ ] Regular security audits
- [ ] Keep dependencies updated

---

## Support & Contacts

- **Technical Issues**: support@arthainvest.com
- **On-call**: +91-XXXX-XXX-XXX
- **Status Page**: status.arthainvest.com

---

**Last Updated**: 2026-08-18
**Version**: 1.0.0
