# Environment Setup Guide

## Required API Keys

Your RAG chatbot now uses:
- **Google Gemini** for embeddings (text-embedding-004)
- **Groq** for LLM chat (llama-3.3-70b-versatile)

## Setup Instructions

### 1. Get API Keys

**Google API Key:**
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the key (starts with `AIzaSy...`)

**Groq API Key:**
1. Go to [Groq Console](https://console.groq.com/keys)
2. Create a new API key
3. Copy the key (starts with `gsk_...`)

### 2. Update .env File

Add both keys to your `.env` file:

```env
# Google API for embeddings
GOOGLE_API_KEY=AIzaSy...your-key-here

# Groq API for LLM chat
GROQ_API_KEY=gsk_...your-key-here

# Database settings
DB_NAME=portfolio_rag
DB_USER=rag_user
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379

# CORS settings
CORS_ALLOWED_ORIGINS=https://shyam-thakkar.github.io,http://localhost:3000
```

### 3. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the Server

```bash
python manage.py runserver 0.0.0.0:8000
```

## Why This Combination?

- **Google Embeddings**: High-quality 768-dimensional embeddings for semantic search
- **Groq LLM**: Ultra-fast inference with llama-3.3-70b-versatile model
- **Best of both**: Quality embeddings + blazing fast responses

## Model Details

### Embeddings: text-embedding-004
- Provider: Google
- Dimensions: 768
- Use case: Document similarity search

### LLM: llama-3.3-70b-versatile
- Provider: Groq
- Model: Llama 3.3 70B
- Speed: ~500 tokens/second
- Use case: Chat responses

## Troubleshooting

**Error: "GOOGLE_API_KEY not set"**
- Add your Google API key to `.env`

**Error: "GROQ_API_KEY not set"**
- Add your Groq API key to `.env`

**Rate limits:**
- Google: Free tier limits apply
- Groq: Very generous free tier (14,400 requests/day)

## Testing

```bash
# Test the chatbot
python test_boundaries.py
```

Your chatbot is now optimized for speed with Groq! 🚀
