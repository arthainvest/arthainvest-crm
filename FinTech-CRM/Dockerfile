FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application
COPY . .

# Build Next.js
RUN npm run build

# Expose ports
EXPOSE 3000 3001

# Start both backend and frontend
CMD ["sh", "-c", "node server/index.js & npm start"]
