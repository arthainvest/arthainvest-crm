#!/bin/bash
# Quick Start Script for Local Testing
# Run this to get the full stack up and running quickly

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ArthaInvest CRM - Quick Start (Local)                    ║"
echo "║  $(date '+%Y-%m-%d %H:%M:%S')                                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Build
echo "📦 Building Docker images..."
docker-compose build

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready (30 seconds)..."
sleep 30

# Step 2: Verify
echo ""
echo "🔍 Verifying stack..."

echo -n "  Database: "
if docker-compose exec -T postgres pg_isready -U arthainvest > /dev/null 2>&1; then
    echo "✓ Connected"
else
    echo "✗ Failed"
fi

echo -n "  Application: "
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✓ Running"
else
    echo "✗ Not responding"
fi

echo -n "  Nginx: "
if docker-compose ps nginx | grep -q "Up"; then
    echo "✓ Running"
else
    echo "✗ Failed"
fi

echo ""
echo "✅ Stack is running!"
echo ""
echo "📝 Next steps:"
echo "   1. Review LOCAL-TESTING-GUIDE.md for full test procedures"
echo "   2. Follow the 10-phase testing checklist"
echo "   3. Monitor logs: docker-compose logs -f app"
echo ""
echo "🌐 Access points:"
echo "   App: http://localhost:3000"
echo "   Health: http://localhost:3000/health"
echo "   API: http://localhost:3000/api"
echo ""
echo "🛑 To stop: docker-compose down"
echo "🔄 To restart: docker-compose restart"
echo ""
