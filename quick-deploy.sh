#!/bin/bash

################################################################################
# ArthaInvest CRM - Quick Production Deployment Script
# Copy this entire script and run on production server
# Usage: bash quick-deploy.sh
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ArthaInvest CRM - Production Deployment v1.0              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Step 1: Clone Repository
echo -e "${YELLOW}[1/7] Cloning repository...${NC}"
if [ -d "arthainvest-crm" ]; then
    echo -e "${YELLOW}Directory exists, pulling latest changes...${NC}"
    cd arthainvest-crm
    git pull origin production
else
    git clone https://github.com/arthainvest/arthainvest-crm.git
    cd arthainvest-crm
    git checkout production
fi
echo -e "${GREEN}✓ Repository ready${NC}"

# Step 2: Create directories
echo -e "${YELLOW}[2/7] Creating directories...${NC}"
mkdir -p ssl logs uploads backups
chmod 755 ssl logs uploads backups
echo -e "${GREEN}✓ Directories created${NC}"

# Step 3: Check .env.production exists
echo -e "${YELLOW}[3/7] Checking environment configuration...${NC}"
if [ ! -f ".env.production" ]; then
    echo -e "${RED}✗ .env.production not found!${NC}"
    echo -e "${YELLOW}Creating template...${NC}"
    cp .env.production.template .env.production 2>/dev/null || echo "Template not found"
    echo -e "${YELLOW}⚠ IMPORTANT: Edit .env.production with your credentials${NC}"
    echo -e "${YELLOW}nano .env.production${NC}"
    exit 1
fi

# Check if passwords are still default
if grep -q "CHANGE_TO_STRONG_PASSWORD" .env.production; then
    echo -e "${RED}✗ WARNING: Passwords not changed in .env.production!${NC}"
    echo -e "${YELLOW}Edit .env.production before continuing${NC}"
    echo -e "${YELLOW}nano .env.production${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Environment configured${NC}"

# Step 4: Check SSL certificates
echo -e "${YELLOW}[4/7] Checking SSL certificates...${NC}"
if [ ! -f "ssl/arthainvestcapital.com.crt" ] || [ ! -f "ssl/arthainvestcapital.com.key" ]; then
    echo -e "${RED}✗ SSL certificates not found in ssl/ directory${NC}"
    echo -e "${YELLOW}Setup SSL certificates using Let's Encrypt:${NC}"
    echo -e "${YELLOW}sudo certbot certonly --standalone -d arthainvestcapital.com -d www.arthainvestcapital.com${NC}"
    echo -e "${YELLOW}Then copy to ssl/ directory${NC}"
    exit 1
fi
chmod 600 ssl/*
echo -e "${GREEN}✓ SSL certificates verified${NC}"

# Step 5: Check Docker
echo -e "${YELLOW}[5/7] Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not installed${NC}"
    exit 1
fi
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker ready${NC}"

# Step 6: Build and start containers
echo -e "${YELLOW}[6/7] Building and starting containers...${NC}"
docker-compose down 2>/dev/null || true
docker-compose build --no-cache
docker-compose up -d
echo -e "${GREEN}✓ Containers started${NC}"

# Step 7: Wait for services and run migrations
echo -e "${YELLOW}[7/7] Waiting for services to be healthy...${NC}"
sleep 10

# Check if services are running
if docker-compose exec -T postgres pg_isready -U arthainvest &> /dev/null; then
    echo -e "${GREEN}✓ Database is healthy${NC}"

    # Run migrations
    echo -e "${YELLOW}Running database migrations...${NC}"
    docker-compose exec -T app npm run migrate 2>/dev/null || echo "No migrations to run"
else
    echo -e "${YELLOW}⚠ Database not ready yet, trying again...${NC}"
    sleep 5
fi

# Final status
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Service Status:${NC}"
docker-compose ps
echo ""
echo -e "${BLUE}Health Checks:${NC}"
echo -n "Application: "
if curl -f -s http://localhost:3000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
fi

echo -n "Database: "
if docker-compose exec -T postgres pg_isready -U arthainvest &> /dev/null; then
    echo -e "${GREEN}✓ Ready${NC}"
else
    echo -e "${RED}✗ Not ready${NC}"
fi

echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Verify application: https://arthainvestcapital.com"
echo "2. Check logs: docker-compose logs -f app"
echo "3. Test login with admin credentials"
echo "4. Monitor: docker-compose logs -f"
echo ""
echo -e "${GREEN}Deployment URL: https://arthainvestcapital.com${NC}"
echo -e "${GREEN}Time: $(date)${NC}"
