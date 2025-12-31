# AIFolio Chatbot - Production Deployment Guide

## Pre-Deployment Checklist

### 1. Environment Variables
Add these to your production `.env`:
```bash
# Required for chatbot
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key

# Redis (for Celery and Channels)
REDIS_HOST=your_redis_host
REDIS_PORT=6379
```

### 2. Database Migration
```bash
python manage.py migrate chat
```

### 3. PostgreSQL Extension
Ensure pgvector is enabled (run as superuser):
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Deployment Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Migrations
```bash
python manage.py migrate
```

### Step 3: Initialize RAG for Existing Users
This will create chatbot documents for all users with portfolios:
```bash
# Synchronous (wait for completion)
python manage.py rebuild_all_rag

# Or async via Celery (faster for many users)
python manage.py rebuild_all_rag --async
```

### Step 4: Start Services

**Option A: Daphne (ASGI Server) - Recommended**
```bash
# Production with multiple workers
daphne -b 0.0.0.0 -p 8001 config.asgi:application
```

**Option B: Supervisor Config**
```ini
[program:daphne]
command=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8001 config.asgi:application
directory=/path/to/atlas_backend
autostart=true
autorestart=true
```

**Start Celery Worker**
```bash
celery -A config worker --loglevel=info
```

---

## Nginx Configuration

```nginx
# WebSocket support
location /ws/ {
    proxy_pass http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 86400;
}

# REST API (regular Django)
location /api/chat/ {
    proxy_pass http://127.0.0.1:8000;
    # ... usual proxy settings
}
```

---

## Post-Deployment Verification

### 1. Test REST API
```bash
curl -X POST https://api.aifolio.in/api/chat/session/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 2. Test WebSocket
```bash
# Install websocat: cargo install websocat
websocat "wss://api.aifolio.in/ws/chat/SESSION_ID/?token=YOUR_TOKEN"
```

### 3. Check RAG Status
```bash
curl https://api.aifolio.in/api/chat/rag/status/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Monitoring

### Check Active Sessions
```python
from chat.models import ChatSession
ChatSession.objects.filter(is_active=True).count()
```

### Check RAG Documents per User
```python
from chat.models import RAGDocument
RAGDocument.objects.values('user_id').annotate(count=Count('id'))
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "GOOGLE_API_KEY not set" | Check `.env` is loaded in production |
| WebSocket 403 | Check CORS/ALLOWED_HOSTS settings |
| No documents found | Run `rebuild_all_rag` command |
| Slow responses | Check Redis connection, consider more workers |
