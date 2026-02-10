# Build stage - Railway deployment
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for environment variables
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build production bundle
RUN npm run build

# Production stage - use Node.js to serve static files
FROM node:20-alpine

WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/dist ./dist

# Expose port (Railway will override with $PORT)
EXPOSE 3000

# Start serve - use shell form for variable expansion
CMD serve -s dist -l tcp://0.0.0.0:${PORT:-3000}
