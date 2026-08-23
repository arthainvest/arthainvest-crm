# 🐳 ArthaInvest Enterprise CRM - Docker Deployment Guide

## Complete Docker Setup for Production Deployment

---

## 📋 Prerequisites

### System Requirements
- **Docker:** v20.10+ installed
- **Docker Compose:** v1.29+ installed
- **Disk Space:** 2GB minimum
- **RAM:** 2GB minimum
- **Network:** Port 3000 accessible

### Installation Links
- **Windows/Mac:** https://www.docker.com/products/docker-desktop
- **Linux:** `apt-get install docker.io docker-compose`

---

## 🚀 Quick Start (3 Steps)

### Step 1: Clone Repository
```bash
git clone https://github.com/arthainvest/arthainvest-crm.git
cd arthainvest-crm
```

### Step 2: Build Docker Image
```bash
docker-compose build
```

### Step 3: Start Container
```bash
docker-compose up -d
```

**Access at:** http://localhost:3000

**Login:**
```
Email: admin@arthainvest.com
Password: admin123
```

---

## 📦 Docker Commands Reference

### Start Container (Detached Mode)
```bash
docker-compose up -d
```

### View Running Containers
```bash
docker ps
```

### View Logs
```bash
docker-compose logs -f
```

### Stop Container
```bash
docker-compose down
```

### Restart Container
```bash
docker-compose restart
```

### Remove Container & Image
```bash
docker-compose down --rmi all
```

### Build Image
```bash
docker build -t arthainvest-crm:latest .
```

### Run Container Manually
```bash
docker run -d \
  --name arthainvest-crm \
  -p 3000:3000 \
  -v $(pwd)/arthainvest-enterprise.db:/app/arthainvest-enterprise.db \
  -v $(pwd)/uploads:/app/uploads \
  arthainvest-crm:latest
```

---

## 🔧 Production Configuration

### Environment Variables
Edit `docker-compose.yml` to customize:

```yaml
environment:
  - NODE_ENV=production
  - PORT=3000
  - DATABASE_URL=arthainvest-enterprise.db
  - JWT_SECRET=your-secret-key-here
  - LOG_LEVEL=info
```

### Port Mapping
Default: `3000:3000`

For different port:
```yaml
ports:
  - "8080:3000"  # Access at http://localhost:8080
```

### Database Persistence
Databases are automatically persisted:
- `arthainvest-enterprise.db`
- `arthainvest.db`
- `arthainvest-10-10.db`

### Uploads & Exports
Directories persist automatically:
- `uploads/` - Document uploads
- `exports/` - Data exports

---

## 🌍 Production Deployment (Cloud)

### AWS EC2 Deployment

1. **Launch EC2 Instance**
   - AMI: Ubuntu 20.04 LTS
   - Instance Type: t2.medium
   - Security Group: Allow port 3000

2. **Install Docker**
   ```bash
   sudo apt-get update
   sudo apt-get install docker.io docker-compose -y
   sudo usermod -aG docker $USER
   ```

3. **Clone & Deploy**
   ```bash
   git clone https://github.com/arthainvest/arthainvest-crm.git
   cd arthainvest-crm
   docker-compose up -d
   ```

4. **Access**
   - URL: `http://[EC2-IP]:3000`

### DigitalOcean/Linode Deployment

1. **Create Ubuntu Droplet**
2. **SSH into server**
3. **Run automated setup**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```
4. **Clone & Deploy**
   ```bash
   git clone https://github.com/arthainvest/arthainvest-crm.git
   cd arthainvest-crm
   docker-compose up -d
   ```

### Docker Hub Registry (Optional)

1. **Tag Image**
   ```bash
   docker build -t yourusername/arthainvest-crm:latest .
   ```

2. **Login to Docker Hub**
   ```bash
   docker login
   ```

3. **Push Image**
   ```bash
   docker push yourusername/arthainvest-crm:latest
   ```

4. **Pull on Server**
   ```bash
   docker pull yourusername/arthainvest-crm:latest
   docker run -d -p 3000:3000 yourusername/arthainvest-crm:latest
   ```

---

## 🔍 Health Checks

### Check Container Status
```bash
docker ps | grep arthainvest
```

### Check Health
```bash
docker inspect arthainvest-crm-enterprise | grep -A 10 Health
```

### View Logs
```bash
docker-compose logs
```

### Test API
```bash
curl http://localhost:3000
```

---

## 🔐 Security Best Practices

### 1. Change Default Passwords
After first login:
1. Go to Settings
2. Click "Change Password"
3. Update all admin accounts

### 2. Enable SSL/TLS
Use nginx reverse proxy:
```yaml
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - arthainvest-crm
```

### 3. Network Security
- Restrict port 3000 to internal network only
- Use firewall rules
- Enable container restart policies

### 4. Data Backups
```bash
# Backup databases
docker cp arthainvest-crm-enterprise:/app/arthainvest-enterprise.db ./backup/

# Restore from backup
docker cp ./backup/arthainvest-enterprise.db arthainvest-crm-enterprise:/app/
```

---

## 📊 Monitoring

### CPU & Memory Usage
```bash
docker stats arthainvest-crm-enterprise
```

### Container Logs
```bash
docker-compose logs --tail=100 -f
```

### Network Usage
```bash
docker stats --no-stream
```

---

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs

# Check image built correctly
docker images | grep arthainvest

# Rebuild
docker-compose build --no-cache
docker-compose up
```

### Port Already In Use
```bash
# Find process using port 3000
lsof -i :3000

# Kill process
kill -9 [PID]

# Or use different port in docker-compose.yml
```

### Database Connection Error
```bash
# Ensure database volumes exist
docker-compose down -v
docker-compose up -d

# Check database file permissions
docker exec arthainvest-crm-enterprise ls -la arthainvest-enterprise.db
```

### Memory Issues
```bash
# Increase memory limit in docker-compose.yml
services:
  arthainvest-crm:
    mem_limit: 1g
    memswap_limit: 2g
```

---

## 📈 Scaling

### Horizontal Scaling (Multiple Containers)
```yaml
version: '3.8'
services:
  arthainvest-crm-1:
    build: .
    ports:
      - "3001:3000"
  arthainvest-crm-2:
    build: .
    ports:
      - "3002:3000"
  arthainvest-crm-3:
    build: .
    ports:
      - "3003:3000"

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    # Configure load balancing
```

### Kubernetes (Advanced)
```bash
# Convert docker-compose to Kubernetes manifests
kompose convert -f docker-compose.yml -o k8s/

# Deploy to Kubernetes
kubectl apply -f k8s/
```

---

## ✅ Deployment Checklist

Before going live:

- [ ] Docker installed on target machine
- [ ] Port 3000 is accessible
- [ ] Database files backed up
- [ ] All passwords changed
- [ ] Firewall configured
- [ ] Health checks passing
- [ ] Logs reviewed
- [ ] Backups tested
- [ ] Team trained on login
- [ ] Monitoring configured

---

## 📞 Support

For issues:
1. Check logs: `docker-compose logs`
2. Review this guide
3. Check GitHub issues: https://github.com/arthainvest/arthainvest-crm/issues
4. Contact: support@arthainvest.com

---

## 🎊 Docker Deployment Ready!

Your ArthaInvest Enterprise CRM is now ready for containerized deployment!

**Quick Commands:**
```bash
# Build
docker-compose build

# Deploy
docker-compose up -d

# Monitor
docker-compose logs -f

# Stop
docker-compose down
```

**Access:** http://localhost:3000
**Repository:** https://github.com/arthainvest/arthainvest-crm

---

**Version:** 1.0.0-enterprise
**Last Updated:** August 13, 2026
**Status:** Production Ready ✅
