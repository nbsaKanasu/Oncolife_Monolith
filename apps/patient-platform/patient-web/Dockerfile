# OncoLife Patient Web - Production Dockerfile
# =============================================
# Multi-stage build: Node.js build → nginx serve
# 
# NOTE: Build context should be the monorepo root to include shared packages
# docker build -f apps/patient-platform/patient-web/Dockerfile -t patient-web .

# Stage 1: Build
FROM node:20-alpine as builder

WORKDIR /app

# Copy shared packages first
COPY packages/ui-components ./packages/ui-components

# Copy package files
COPY apps/patient-platform/patient-web/package*.json ./apps/patient-platform/patient-web/

# Install dependencies for shared package
WORKDIR /app/packages/ui-components
RUN npm install --legacy-peer-deps || true

# Install dependencies for patient-web
WORKDIR /app/apps/patient-platform/patient-web
RUN npm install --legacy-peer-deps

# Copy source code
COPY apps/patient-platform/patient-web/ ./

# Build arguments for API URLs (can be overridden at build time)
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_WS_BASE_URL=ws://localhost:8000

# Set environment variables for build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_WS_BASE_URL=$VITE_WS_BASE_URL

# Build the application
RUN npm run build


# Stage 2: Production with nginx
FROM nginx:alpine as production

# Copy custom nginx config
COPY apps/patient-platform/patient-web/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from builder stage
COPY --from=builder /app/apps/patient-platform/patient-web/dist /usr/share/nginx/html

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
