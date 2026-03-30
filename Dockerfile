# Multi-stage build for Pi Monitor
# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json frontend/yarn.lock* ./

# Install dependencies
RUN yarn install --frozen-lockfile || yarn install

# Copy frontend source
COPY frontend/ .

# Build the React app
RUN yarn build

# Stage 2: Final Image with Python Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements-docker.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements-docker.txt

# Copy backend code
COPY backend/server.py ./backend/

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create nginx config
RUN echo 'server { \n\
    listen 80; \n\
    server_name localhost; \n\
    \n\
    location / { \n\
        root /app/frontend/build; \n\
        try_files $uri $uri/ /index.html; \n\
    } \n\
    \n\
    location /api { \n\
        proxy_pass http://127.0.0.1:8001; \n\
        proxy_set_header Host $host; \n\
        proxy_set_header X-Real-IP $remote_addr; \n\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \n\
    } \n\
}' > /etc/nginx/sites-available/default

# Create supervisor config
RUN echo '[supervisord] \n\
nodaemon=true \n\
\n\
[program:nginx] \n\
command=nginx -g "daemon off;" \n\
autostart=true \n\
autorestart=true \n\
\n\
[program:backend] \n\
command=uvicorn server:app --host 0.0.0.0 --port 8001 \n\
directory=/app/backend \n\
autostart=true \n\
autorestart=true \n\
environment=MONGO_URL="%(ENV_MONGO_URL)s",DB_NAME="%(ENV_DB_NAME)s" \n\
' > /etc/supervisor/conf.d/supervisord.conf

# Expose port 80
EXPOSE 80

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
