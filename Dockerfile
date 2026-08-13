# ArthaInvest Enterprise CRM - Docker Image
# Production-ready Node.js application

FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    sqlite3 \
    python3 \
    make \
    g++

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm install --production

# Copy application files
COPY . .

# Create uploads and exports directories
RUN mkdir -p uploads exports

# Expose port
EXPOSE 3000

# Environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start application
CMD ["node", "arthainvest-crm-enterprise-server.js"]
