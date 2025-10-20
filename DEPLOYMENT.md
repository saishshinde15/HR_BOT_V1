# 🚀 Production Deployment Guide

## Overview

This guide covers deploying the HR Bot to production environments with considerations for:
- Performance optimization
- Security best practices
- Scalability
- Monitoring and maintenance

## Architecture Options

### Option 1: Single Server Deployment

**Best for**: Small to medium organizations (< 500 employees)

```
┌─────────────────────────────────────┐
│     Production Server (VM/EC2)     │
│                                     │
│  ┌──────────────────────────────┐  │
│  │      HR Bot Application       │  │
│  │  - CrewAI + Gemini LLM       │  │
│  │  - Hybrid RAG Engine         │  │
│  │  - API Deck Integration      │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │     Local Storage            │  │
│  │  - Document indexes (.rag)   │  │
│  │  - Cache files               │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Requirements:**
- 4GB RAM minimum, 8GB recommended
- 2 CPU cores minimum, 4 recommended
- 20GB disk space for indexes and cache
- Ubuntu 22.04 LTS or similar

### Option 2: Containerized Deployment

**Best for**: Scalable, cloud-native deployments

```
┌───────────────────────────────────────┐
│         Container Platform            │
│       (Docker/Kubernetes)             │
│                                       │
│  ┌─────────────┐  ┌─────────────┐   │
│  │ HR Bot Pod  │  │ HR Bot Pod  │   │
│  │  (Replica)  │  │  (Replica)  │   │
│  └─────────────┘  └─────────────┘   │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │   Shared Volume (Indexes)       │ │
│  └─────────────────────────────────┘ │
│                                       │
│  ┌─────────────────────────────────┐ │
│  │   Redis Cache (Optional)        │ │
│  └─────────────────────────────────┘ │
└───────────────────────────────────────┘
```

## Deployment Steps

### 1. Server Setup (Ubuntu Example)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install system dependencies
sudo apt install build-essential libssl-dev libffi-dev -y

# Create application user
sudo useradd -m -s /bin/bash hrbot
sudo su - hrbot
```

### 2. Application Setup

```bash
# Clone/upload your project
cd /home/hrbot
# (Transfer your hr_bot directory here)

cd hr_bot

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install UV
pip install uv

# Install dependencies
uv pip install -e .

# Or use crewai
pip install crewai
crewai install
```

### 3. Environment Configuration

```bash
# Create production .env file
nano .env
```

**Production .env template:**
```bash
# Gemini Configuration
GOOGLE_API_KEY=your_production_api_key
GEMINI_MODEL=gemini/gemini-1.5-flash

# API Deck (if using)
APIDECK_API_KEY=your_production_key
APIDECK_APP_ID=your_app_id
APIDECK_SERVICE_ID=your_service_id

# Performance tuning
ENABLE_CACHE=true
CACHE_TTL=7200

# RAG Configuration
CHUNK_SIZE=800
CHUNK_OVERLAP=200
TOP_K_RESULTS=5
BM25_WEIGHT=0.5
VECTOR_WEIGHT=0.5

# Security
LOG_LEVEL=INFO
```

**Set proper permissions:**
```bash
chmod 600 .env
```

### 4. Document Setup

```bash
# Create data directory
mkdir -p data

# Upload HR documents
# (Transfer your .docx files here)

# Set permissions
chmod 755 data
chmod 644 data/*.docx
```

### 5. Pre-build Indexes

```bash
# Build indexes before starting service
python -m hr_bot.main <<EOF
What is the leave policy?
EOF

# Verify indexes created
ls -lh .rag_index/
```

### 6. Create Systemd Service

```bash
sudo nano /etc/systemd/system/hrbot.service
```

**Service file:**
```ini
[Unit]
Description=HR Bot Assistant
After=network.target

[Service]
Type=simple
User=hrbot
Group=hrbot
WorkingDirectory=/home/hrbot/hr_bot
Environment="PATH=/home/hrbot/hr_bot/venv/bin"
ExecStart=/home/hrbot/hr_bot/venv/bin/python -m hr_bot.main interactive
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/home/hrbot/hr_bot

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable hrbot
sudo systemctl start hrbot
sudo systemctl status hrbot
```

### 7. Web Interface (Optional)

For web access, create a simple FastAPI wrapper:

```python
# web_server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from hr_bot.crew import HrBot
import uvicorn

app = FastAPI(title="HR Bot API")
bot = HrBot()

class Query(BaseModel):
    query: str
    context: str = ""

@app.post("/ask")
async def ask_question(query: Query):
    try:
        result = bot.crew().kickoff(inputs={
            'query': query.query,
            'context': query.context
        })
        return {"response": str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Install FastAPI:**
```bash
pip install fastapi uvicorn
```

**Update systemd service:**
```ini
ExecStart=/home/hrbot/hr_bot/venv/bin/python web_server.py
```

### 8. Nginx Reverse Proxy

```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/hrbot
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name hrbot.company.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Increase timeout for long queries
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/hrbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. SSL/TLS (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d hrbot.company.com
```

## Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./
COPY src/ ./src/
COPY data/ ./data/

# Install Python dependencies
RUN pip install uv && \
    uv pip install --system -e .

# Create directories for indexes and cache
RUN mkdir -p .rag_index .rag_cache .apideck_cache

# Set environment
ENV PYTHONUNBUFFERED=1

# Expose port (if using web server)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run application
CMD ["python", "-m", "hr_bot.main", "interactive"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  hrbot:
    build: .
    container_name: hrbot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./data:/app/data:ro
      - hrbot-indexes:/app/.rag_index
      - hrbot-cache:/app/.rag_cache
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  hrbot-indexes:
  hrbot-cache:
```

**Deploy:**
```bash
docker-compose up -d
docker-compose logs -f hrbot
```

## Kubernetes Deployment

### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hrbot
  labels:
    app: hrbot
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hrbot
  template:
    metadata:
      labels:
        app: hrbot
    spec:
      containers:
      - name: hrbot
        image: your-registry/hrbot:latest
        ports:
        - containerPort: 8000
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: hrbot-secrets
              key: google-api-key
        volumeMounts:
        - name: data
          mountPath: /app/data
          readOnly: true
        - name: indexes
          mountPath: /app/.rag_index
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: hrbot-data-pvc
      - name: indexes
        persistentVolumeClaim:
          claimName: hrbot-indexes-pvc
```

### service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: hrbot-service
spec:
  selector:
    app: hrbot
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Security Best Practices

### 1. API Key Management

**Never commit API keys to version control**

```bash
# Use environment variables
export GOOGLE_API_KEY="your-key"

# Or use secrets management
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id hrbot/google-api-key

# HashiCorp Vault
vault kv get secret/hrbot/google-api-key
```

### 2. Network Security

```bash
# Firewall rules (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

### 3. Rate Limiting

**Nginx rate limiting:**
```nginx
limit_req_zone $binary_remote_addr zone=hrbot:10m rate=10r/s;

server {
    location / {
        limit_req zone=hrbot burst=20;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### 4. Authentication

Add authentication layer (example with FastAPI):

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != os.getenv("API_TOKEN"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return credentials.credentials

@app.post("/ask")
async def ask_question(query: Query, token: str = Depends(verify_token)):
    # ... existing code
```

## Monitoring

### 1. Logging

```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger("hrbot")
    logger.setLevel(logging.INFO)
    
    # File handler
    handler = RotatingFileHandler(
        "hrbot.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

### 2. Metrics

Track key metrics:
- Query response time
- Cache hit rate
- Error rate
- Document retrieval count
- API calls to external services

```python
import time
from collections import defaultdict

class Metrics:
    def __init__(self):
        self.query_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.response_times = []
    
    def record_query(self, response_time, cache_hit):
        self.query_count += 1
        self.response_times.append(response_time)
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
    
    def get_stats(self):
        avg_response = sum(self.response_times) / len(self.response_times)
        cache_hit_rate = self.cache_hits / self.query_count * 100
        return {
            "total_queries": self.query_count,
            "avg_response_time": avg_response,
            "cache_hit_rate": cache_hit_rate
        }
```

### 3. Health Checks

```python
@app.get("/health")
async def health_check():
    checks = {
        "service": "hrbot",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "rag_index": os.path.exists(".rag_index"),
            "cache": os.path.exists(".rag_cache"),
            "data": os.path.exists("data") and len(os.listdir("data")) > 0
        }
    }
    
    if all(checks["checks"].values()):
        return checks
    else:
        raise HTTPException(status_code=503, detail=checks)
```

## Maintenance

### 1. Update Documents

```bash
# Add new documents
cp new-policy.docx /home/hrbot/hr_bot/data/

# Rebuild indexes
rm -rf /home/hrbot/hr_bot/.rag_index/
sudo systemctl restart hrbot
```

### 2. Clear Cache

```bash
# Clear cache periodically
rm -rf /home/hrbot/hr_bot/.rag_cache/*
rm -rf /home/hrbot/hr_bot/.apideck_cache/*
```

### 3. Backup

```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backups/hrbot"
DATE=$(date +%Y%m%d)

# Backup data
tar -czf $BACKUP_DIR/data-$DATE.tar.gz /home/hrbot/hr_bot/data/

# Backup indexes
tar -czf $BACKUP_DIR/indexes-$DATE.tar.gz /home/hrbot/hr_bot/.rag_index/

# Keep last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### 4. Log Rotation

```bash
# /etc/logrotate.d/hrbot
/home/hrbot/hr_bot/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## Scaling Considerations

### Horizontal Scaling

**Load Balancer + Multiple Instances:**

```
                    ┌──────────────┐
                    │ Load Balancer│
                    └──────┬───────┘
                           │
        ┏━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┓
        ▼                                    ▼
┌───────────────┐                   ┌───────────────┐
│  HR Bot #1    │                   │  HR Bot #2    │
└───────────────┘                   └───────────────┘
        │                                    │
        └────────────────┬───────────────────┘
                         ▼
                ┌─────────────────┐
                │ Shared Storage  │
                │  (NFS/EFS)      │
                └─────────────────┘
```

### Vertical Scaling

**Increase resources based on load:**

| Users | RAM | CPU | Storage |
|-------|-----|-----|---------|
| <100 | 4GB | 2 cores | 20GB |
| 100-500 | 8GB | 4 cores | 50GB |
| 500-1000 | 16GB | 8 cores | 100GB |
| 1000+ | 32GB+ | 16+ cores | 200GB+ |

## Cost Optimization

### 1. Gemini API Usage

```python
# Monitor API usage
import functools

def track_api_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Log API call
        logger.info(f"Gemini API call: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper
```

**Cost estimation:**
- Gemini 1.5 Flash: $0.00001875/1K characters input, $0.000075/1K output
- Embeddings: Free (as of 2025)
- Average query: ~$0.0001

### 2. Caching Strategy

- Enable aggressive caching for static policies
- Set appropriate TTL based on content change frequency
- Use Redis for distributed caching in multi-instance setup

### 3. API Deck Optimization

- Batch requests when possible
- Cache API responses
- Use webhooks instead of polling

## Troubleshooting Production Issues

### Issue: High Memory Usage

**Solution:**
```bash
# Reduce index size
CHUNK_SIZE=600
TOP_K_RESULTS=3

# Clear unused cache
rm -rf .rag_cache/*
```

### Issue: Slow Responses

**Solution:**
```bash
# Enable caching
ENABLE_CACHE=true

# Reduce results
TOP_K_RESULTS=3

# Pre-warm cache for common queries
```

### Issue: Index Corruption

**Solution:**
```bash
# Rebuild indexes
rm -rf .rag_index/
sudo systemctl restart hrbot
```

## Production Checklist

- [ ] Environment variables configured securely
- [ ] API keys stored in secrets manager
- [ ] Documents uploaded and verified
- [ ] Indexes pre-built
- [ ] Systemd service configured
- [ ] Firewall rules applied
- [ ] SSL/TLS certificates installed
- [ ] Logging configured
- [ ] Monitoring setup
- [ ] Backup system in place
- [ ] Health checks operational
- [ ] Rate limiting enabled
- [ ] Authentication implemented
- [ ] Documentation updated
- [ ] Team trained on usage

---

**Production deployment complete! 🚀**
