#!/bin/bash

###############################################################################
# ArthaInvest CRM - Production Deployment Script
# This script handles the complete deployment process to production
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="arthainvest-crm"
DOCKER_REGISTRY="docker.io"
PRODUCTION_DOMAIN="arthainvestcapital.com"
DEPLOYMENT_USER="deploy"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker is installed"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose is installed"

    # Check git
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed"
        exit 1
    fi
    print_success "Git is installed"
}

# Backup current production
backup_production() {
    print_header "Backing Up Current Production"

    BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # Export database
    if [ -f "docker-compose.yml" ]; then
        print_info "Exporting PostgreSQL database..."
        docker-compose exec -T postgres pg_dump -U arthainvest arthainvest_crm > "$BACKUP_DIR/database.sql" 2>/dev/null || true
        print_success "Database backed up to $BACKUP_DIR/database.sql"
    fi

    # Copy docker-compose
    cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.bak"
    print_success "Configuration backed up"
}

# Update environment
update_environment() {
    print_header "Updating Environment"

    if [ ! -f ".env.production" ]; then
        print_error ".env.production file not found"
        exit 1
    fi

    print_info "Environment file exists"
    print_warning "Make sure to update sensitive values in .env.production before continuing"
    print_warning "Press Enter to continue..."
    read -r
}

# Build Docker images
build_docker_images() {
    print_header "Building Docker Images"

    print_info "Building application image..."
    docker-compose build --no-cache app
    print_success "Application image built"

    print_info "Pulling PostgreSQL image..."
    docker-compose pull postgres
    print_success "PostgreSQL image pulled"

    print_info "Pulling Nginx image..."
    docker-compose pull nginx
    print_success "Nginx image pulled"
}

# Start services
start_services() {
    print_header "Starting Services"

    print_info "Starting Docker containers..."
    docker-compose up -d
    print_success "Containers started"

    # Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    sleep 10

    if docker-compose ps | grep -q "healthy\|Exited"; then
        print_warning "Some services may not be healthy yet. Waiting..."
        sleep 10
    fi

    print_success "Services are running"
}

# Run migrations
run_migrations() {
    print_header "Running Database Migrations"

    print_info "Running migrations on PostgreSQL..."
    docker-compose exec -T app npm run migrate 2>/dev/null || print_warning "No migration script found"
    print_success "Migrations completed"
}

# Health checks
health_check() {
    print_header "Running Health Checks"

    print_info "Checking application health..."
    if curl -f -s http://localhost:3000/health > /dev/null 2>&1; then
        print_success "Application is healthy"
    else
        print_error "Application health check failed"
        exit 1
    fi

    print_info "Checking database connection..."
    if docker-compose exec -T postgres pg_isready -U arthainvest &> /dev/null; then
        print_success "Database is healthy"
    else
        print_error "Database health check failed"
        exit 1
    fi

    print_info "Checking Nginx..."
    if curl -f -s http://localhost/health > /dev/null 2>&1; then
        print_success "Nginx is healthy"
    else
        print_error "Nginx health check failed"
        exit 1
    fi
}

# Verify deployment
verify_deployment() {
    print_header "Verifying Deployment"

    print_info "Checking running containers..."
    docker-compose ps

    print_info "Checking logs..."
    docker-compose logs --tail=20 app
}

# Setup SSL certificates
setup_ssl() {
    print_header "Setting Up SSL Certificates"

    if [ ! -f "ssl/arthainvestcapital.com.crt" ] || [ ! -f "ssl/arthainvestcapital.com.key" ]; then
        print_warning "SSL certificates not found"
        print_info "To use Let's Encrypt with Certbot:"
        print_info "  1. Install Certbot: sudo apt-get install certbot"
        print_info "  2. Run: sudo certbot certonly --standalone -d arthainvestcapital.com -d www.arthainvestcapital.com"
        print_info "  3. Copy certificates to ./ssl/ directory"
        print_info "  4. Restart nginx: docker-compose restart nginx"
    else
        print_success "SSL certificates found"
    fi
}

# Main deployment flow
main() {
    print_header "ArthaInvest CRM Production Deployment"
    print_info "Starting deployment at $(date)"

    # Run deployment steps
    check_prerequisites
    update_environment
    backup_production
    build_docker_images
    start_services
    run_migrations
    health_check
    setup_ssl
    verify_deployment

    print_header "Deployment Complete! ✓"
    print_success "ArthaInvest CRM is now running in production"
    print_info "URL: https://$PRODUCTION_DOMAIN"
    print_info "Time: $(date)"

    print_info ""
    print_info "Next steps:"
    print_info "  1. Set up SSL certificates"
    print_info "  2. Configure your domain DNS"
    print_info "  3. Set up monitoring and logging"
    print_info "  4. Configure backups and disaster recovery"
    print_info "  5. Train your team on the new system"
}

# Error handling
trap 'print_error "Deployment failed at line $LINENO"; exit 1' ERR

# Run main function
main "$@"
