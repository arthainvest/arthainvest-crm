# ArthaInvest CRM - Production Deployment Guide

## Overview

This document outlines the deployment process for ArthaInvest CRM to production using Docker and docker-compose.

## Prerequisites

- Docker (v20.10+)
- Docker Compose (v2.0+)
- Git
- SSH access to production server
- Domain: arthainvestcapital.com
- SSL certificates for HTTPS

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  NGINX (Reverse Proxy)              │
│         Port 80 (HTTP → HTTPS redirect)             │
│         Port 443 (HTTPS with SSL/TLS)               │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│          Express.js Application Server              │
│         (ArthaInvest CRM v3.0.0)                   │
│         Port 3000 (Internal)                        │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│           PostgreSQL Database                       │
│         (Persistent Storage)                        │
│         Port 5432 (Internal)                        │
└─────────────────────────────────────────────────────┘
```

## Deployment Steps

### 1. Prepare Production Environment

```bash
# Clone repository to production server
git clone https://github.com/arthainvest/arthainvest-crm.git
cd arthainvest-crm

# Checkout production branch
git checkout production

# Create necessary directories
mkdir -p ssl logs uploads backups
```

### 2. Configure Environment Variables

Edit `.env.production` and update the following:

```bash
# Database credentials
DB_PASSWORD=CHANGE_TO_STRONG_PASSWORD

# JWT Secret
JWT_SECRET=CHANGE_TO_RANDOM_SECURE_KEY

# Optional: Email configuration
SMTP_PASSWORD=your-app-password

# Optional: AWS S3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

### 3. Set Up SSL Certificates

#### Option A: Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone \
  -d arthainvestcapital.com \
  -d www.arthainvestcapital.com

# Copy certificates to ssl directory
sudo cp /etc/letsencrypt/live/arthainvestcapital.com/fullchain.pem ssl/arthainvestcapital.com.crt
sudo cp /etc/letsencrypt/live/arthainvestcapital.com/privkey.pem ssl/arthainvestcapital.com.key
sudo chown $USER:$USER ssl/*
```

#### Option B: Using Self-Signed Certificate (Dev/Testing Only)

```bash
openssl req -x509 -newkey rsa:4096 -keyout ssl/arthainvestcapital.com.key \
  -out ssl/arthainvestcapital.com.crt -days 365 -nodes
```

### 4. Deploy Using Script

```bash
# Make deployment script executable
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

### 5. Manual Deployment

```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app

# Run migrations (if needed)
docker-compose exec app npm run migrate

# Health check
curl http://localhost:3000/health
```

## Monitoring

### Check Container Status

```bash
# View running containers
docker-compose ps

# View logs in real-time
docker-compose logs -f app

# View specific service logs
docker-compose logs nginx
docker-compose logs postgres
```

### Database Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U arthainvest arthainvest_crm > backup.sql

# Restore database
docker-compose exec -T postgres psql -U arthainvest arthainvest_crm < backup.sql
```

### Database Maintenance

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U arthainvest -d arthainvest_crm

# Some useful commands:
\dt                    # List tables
\du                    # List users
SELECT * FROM users;   # Query users table
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs app

# Remove and restart
docker-compose down
docker-compose up -d
```

### Database connection error

```bash
# Check PostgreSQL health
docker-compose exec postgres pg_isready -U arthainvest

# Verify credentials
docker-compose exec postgres psql -U arthainvest -c "SELECT 1;"
```

### Port already in use

```bash
# Find process using port
sudo lsof -i :3000

# Kill process
sudo kill -9 <PID>

# Restart containers
docker-compose restart
```

### Application not responding

```bash
# Check application logs
docker-compose logs app --tail=50

# Restart application
docker-compose restart app

# Check health endpoint
curl -v http://localhost:3000/health
```

## Scaling

### Horizontal Scaling (Multiple App Instances)

Update `docker-compose.yml` to run multiple app instances:

```yaml
services:
  app1:
    # ... same config as app
    ports:
      - "3001:3000"
  
  app2:
    # ... same config as app
    ports:
      - "3002:3000"
```

Update nginx to load balance between instances.

### Vertical Scaling (Resource Limits)

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## Continuous Deployment (CI/CD)

GitHub Actions workflow automatically:
1. Builds Docker image
2. Pushes to registry
3. Deploys to production server
4. Runs health checks

Trigger deployment by pushing to `production` branch:

```bash
git checkout production
git merge develop
git push origin production
```

## Security Checklist

- [ ] Update all passwords in `.env.production`
- [ ] Configure SSL certificates
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Configure log rotation
- [ ] Set up monitoring alerts
- [ ] Review security headers in nginx
- [ ] Implement rate limiting
- [ ] Set up automated security updates
- [ ] Configure CORS properly

## Backup & Recovery

### Automated Backups

```bash
# Add cron job for daily backups
crontab -e

# Add this line (backup daily at 2 AM)
0 2 * * * cd ~/arthainvest-crm && docker-compose exec -T postgres pg_dump -U arthainvest arthainvest_crm > backups/backup_$(date +\%Y\%m\%d).sql
```

### Recovery Procedure

```bash
# List available backups
ls -la backups/

# Restore from backup
docker-compose down
docker volume rm arthainvest-crm_postgres_data
docker-compose up -d postgres
docker-compose exec -T postgres psql -U arthainvest arthainvest_crm < backups/backup_20240101.sql
docker-compose up -d app
```

## Performance Tuning

### Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_deals_status ON deals(status);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM leads WHERE created_at > NOW() - INTERVAL '30 days';
```

### Caching Configuration

Enable Redis for caching (optional):

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
```

## Maintenance

### Regular Tasks

- [ ] Monitor disk space
- [ ] Update Docker images
- [ ] Review logs for errors
- [ ] Test backup/recovery
- [ ] Update SSL certificates (before expiry)
- [ ] Security patches

### Update Procedure

```bash
# Pull latest code
git pull origin production

# Rebuild and restart
docker-compose down
docker-compose build --pull --no-cache
docker-compose up -d

# Verify deployment
docker-compose ps
curl http://localhost:3000/health
```

## Support & Escalation

For deployment issues:
1. Check logs: `docker-compose logs app`
2. Verify health: `curl http://localhost:3000/health`
3. Review configuration: Check `.env.production`
4. Contact DevOps team

## Additional Resources

- Docker Documentation: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- PostgreSQL: https://www.postgresql.org/docs/
- Nginx: https://nginx.org/en/docs/
- Let's Encrypt: https://letsencrypt.org/

---

**Last Updated:** 2026-08-16
**Version:** 1.0
**Maintainer:** ArthaInvest DevOps Team
