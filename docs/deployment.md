# Production Deployment

This guide covers everything you need to know about deploying Xaibo agents to production environments, including Docker deployment, environment configuration, scaling strategies, and security best practices.

---

## Production Setup

### Environment Configuration

Create a production-ready environment configuration:

```bash title=".env.production"
# Core Configuration
XAIBO_ENV=production
XAIBO_LOG_LEVEL=INFO
XAIBO_DEBUG=false

# Server Configuration
XAIBO_HOST=0.0.0.0
XAIBO_PORT=9001
XAIBO_WORKERS=4

# API Keys (use secure secret management in production)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/xaibo_prod
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your_very_secure_secret_key_here
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

### Production Agent Configuration

Create production-optimized agent configurations:

```yaml title="agents/production/main-agent.yml"
id: main-agent
description: Production-ready agent with optimized settings
modules:
  - module: xaibo.primitives.modules.llm.OpenAILLM
    id: llm
    config:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}
      timeout: 60.0
      max_retries: 3
      retry_delay: 1.0
  
  - module: xaibo.primitives.modules.memory.VectorMemory
    id: memory
    config:
      memory_file_path: /data/memory/agent_memory.pkl
      max_memory_size: 10000
  
  - module: xaibo.primitives.modules.memory.TokenChunker
    id: chunker
    config:
      window_size: 1024
      window_overlap: 100
  
  - module: xaibo.primitives.modules.memory.OpenAIEmbedder
    id: embedder
    config:
      model: text-embedding-ada-002
      api_key: ${OPENAI_API_KEY}
      timeout: 30.0
  
  - module: xaibo.primitives.modules.memory.NumpyVectorIndex
    id: vector_index
    config:
      storage_dir: /data/vectors
  
  - module: xaibo.primitives.modules.tools.PythonToolProvider
    id: tools
    config:
      tool_packages: [tools.production_tools]
  
  - module: xaibo.primitives.modules.orchestrator.StressingToolUser
    id: orchestrator
    config:
      max_thoughts: 10
      timeout: 300.0
      system_prompt: |
        You are a production AI assistant. Be helpful, accurate, and efficient.
        Always validate inputs and handle errors gracefully.
```

---

## Docker Deployment

### Basic Dockerfile

```dockerfile title="Dockerfile"
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user
RUN groupadd -r xaibo && useradd -r -g xaibo xaibo

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data/memory /data/vectors /data/logs && \
    chown -R xaibo:xaibo /data /app

# Switch to non-root user
USER xaibo

# Expose port
EXPOSE 9001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1

# Start command
CMD ["python", "-m", "xaibo.server.web", "--host", "0.0.0.0", "--port", "9001"]
```

### Multi-stage Dockerfile (Optimized)

```dockerfile title="Dockerfile.optimized"
# Build stage
FROM python:3.11-slim as builder

ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/home/xaibo/.local/bin:$PATH

# Create app user
RUN groupadd -r xaibo && useradd -r -g xaibo xaibo

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/xaibo/.local

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=xaibo:xaibo . .

# Create necessary directories
RUN mkdir -p /data/memory /data/vectors /data/logs && \
    chown -R xaibo:xaibo /data

# Switch to non-root user
USER xaibo

# Expose port
EXPOSE 9001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9001/health || exit 1

# Start command
CMD ["python", "-m", "xaibo.server.web", "--host", "0.0.0.0", "--port", "9001"]
### Docker Compose Setup

```yaml title="docker-compose.yml"
version: '3.8'

services:
  xaibo:
    build: .
    ports:
      - "9001:9001"
    environment:
      - XAIBO_ENV=production
      - DATABASE_URL=postgresql://xaibo:password@postgres:5432/xaibo
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    volumes:
      - xaibo_data:/data
      - ./agents:/app/agents:ro
      - ./tools:/app/tools:ro
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: xaibo
      POSTGRES_USER: xaibo
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U xaibo"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - xaibo
    restart: unless-stopped

volumes:
  xaibo_data:
  postgres_data:
  redis_data:
```

---

## Scaling and Performance

### Horizontal Scaling

Configure your deployment for horizontal scaling:

```python title="server/production.py"
import os
from xaibo.core.xaibo import Xaibo
from xaibo.server.web import create_app

def create_production_app():
    """Create a production-ready Xaibo application"""
    
    # Initialize Xaibo with production settings
    xaibo = Xaibo()
    
    # Load agents from configuration directory
    agent_dir = os.getenv('XAIBO_AGENT_DIR', './agents/production')
    xaibo.load_agents_from_directory(agent_dir)
    
    # Create web application
    app = create_app(xaibo)
    
    # Configure for production
    app.config.update({
        'DEBUG': False,
        'TESTING': False,
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max request size
    })
    
    return app
```

### Load Balancing with Nginx

```nginx title="nginx.prod.conf"
upstream xaibo_backend {
    least_conn;
    server xaibo:9001 max_fails=3 fail_timeout=30s;
    server xaibo:9002 max_fails=3 fail_timeout=30s;
    server xaibo:9003 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://xaibo_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }
    
    location /health {
        access_log off;
        proxy_pass http://xaibo_backend;
    }
}
```

---

## Security Best Practices

### Environment Security

```bash title="scripts/secure-env.sh"
#!/bin/bash

# Generate secure secret key
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Set secure file permissions
chmod 600 .env.production
chmod 700 /data/memory
chmod 700 /data/vectors

# Create non-root user for running the application
useradd -r -s /bin/false xaibo
chown -R xaibo:xaibo /app /data

# Configure firewall (example for UFW)
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp  # SSH
ufw allow 80/tcp  # HTTP
ufw allow 443/tcp # HTTPS
ufw --force enable
```

### API Security

```python title="security/middleware.py"
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import hashlib
from collections import defaultdict

class RateLimitMiddleware:
    def __init__(self, app: FastAPI, calls: int = 100, period: int = 60):
        self.app = app
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            client_ip = scope["client"][0]
            now = time.time()
            
            # Clean old requests
            self.clients[client_ip] = [
                req_time for req_time in self.clients[client_ip]
                if now - req_time < self.period
            ]
            
            # Check rate limit
            if len(self.clients[client_ip]) >= self.calls:
                response = {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [[b"content-type", b"application/json"]],
                }
                await send(response)
                await send({
                    "type": "http.response.body",
                    "body": b'{"error": "Rate limit exceeded"}',
                })
                return
            
            # Add current request
            self.clients[client_ip].append(now)
        
        await self.app(scope, receive, send)

def setup_security_middleware(app: FastAPI):
    """Configure security middleware for production"""
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # Trusted hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
    )
    
    # Rate limiting
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)
    
    return app
```

---

## Monitoring and Logging

### Structured Logging

```python title="logging/config.py"
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        if hasattr(record, 'agent_id'):
            log_entry['agent_id'] = record.agent_id
        
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

def setup_logging():
    """Configure structured logging for production"""
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler('/data/logs/xaibo.log')
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
```

### Health Checks

```python title="monitoring/health.py"
from fastapi import APIRouter, HTTPException
import psutil
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check():
    """Readiness check with dependency verification"""
    checks = {}
    
    # Check system resources
    memory_percent = psutil.virtual_memory().percent
    cpu_percent = psutil.cpu_percent(interval=1)
    
    checks["memory"] = f"{memory_percent}%"
    checks["cpu"] = f"{cpu_percent}%"
    
    return {
        "status": "ready",
        "checks": checks,
        "timestamp": time.time()
    }
```

---

## Backup and Recovery

### Data Backup Strategy

```bash title="scripts/backup.sh"
#!/bin/bash

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="xaibo_backup_$DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

# Backup agent configurations
cp -r /app/agents "$BACKUP_DIR/$BACKUP_NAME/"

# Backup memory data
cp -r /data/memory "$BACKUP_DIR/$BACKUP_NAME/"
cp -r /data/vectors "$BACKUP_DIR/$BACKUP_NAME/"

# Create archive
cd "$BACKUP_DIR"
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"

# Clean up old backups (keep last 30 days)
find "$BACKUP_DIR" -name "xaibo_backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_NAME.tar.gz"
```

### Recovery Procedures

```bash title="scripts/restore.sh"
#!/bin/bash

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

BACKUP_FILE=$1
RESTORE_DIR="/tmp/xaibo_restore"

# Extract backup
mkdir -p "$RESTORE_DIR"
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"

# Stop services
docker-compose down

# Restore data
cp -r "$RESTORE_DIR"/*/agents /app/
cp -r "$RESTORE_DIR"/*/memory /data/
cp -r "$RESTORE_DIR"/*/vectors /data/

# Set permissions
chown -R xaibo:xaibo /app/agents /data

# Start services
docker-compose up -d

# Clean up
rm -rf "$RESTORE_DIR"

echo "Restore completed from: $BACKUP_FILE"
```

---

## Deployment Checklist

### Pre-deployment

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrations completed
- [ ] Agent configurations validated
- [ ] Security settings reviewed
- [ ] Backup procedures tested

### Deployment

- [ ] Application deployed
- [ ] Health checks passing
- [ ] Load balancer configured
- [ ] Monitoring enabled
- [ ] Logs configured
- [ ] Performance metrics baseline established

### Post-deployment

- [ ] Smoke tests completed
- [ ] Performance monitoring active
- [ ] Error tracking configured
- [ ] Backup schedule verified
- [ ] Documentation updated
- [ ] Team notified

---

!!! tip "Next Steps"
    - Review the [architecture documentation](architecture.md) to understand system design
    - Set up [monitoring and alerting](troubleshooting.md) for your production environment
    - Explore [examples](examples.md) for advanced deployment patterns