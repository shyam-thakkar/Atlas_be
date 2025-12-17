# WebSocket API Documentation - Portfolio RAG Chatbot

Complete guide for the WebSocket-based chat API with session management.

## 🔌 WebSocket Connection

### Connection URL
```
ws://localhost:8000/ws/chat/
```

### With Existing Session
```
ws://localhost:8000/ws/chat/?session_id=<uuid>
```

---

## 📡 Connection Flow

### 1. New Session (No session_id)

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/');
```

**Server Response:**
```json
{
  "type": "session_info",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_new_session": true,
  "message": "Connected successfully"
}
```

### 2. Continue Existing Session

**Connect:**
```javascript
const sessionId = '550e8400-e29b-41d4-a716-446655440000';
const ws = new WebSocket(`ws://localhost:8000/ws/chat/?session_id=${sessionId}`);
```

**Server Response:**
```json
{
  "type": "session_info",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_new_session": false,
  "message": "Connected successfully"
}
```

---

## 💬 Message Types

### 1. Query Message (Client → Server)

Send a question to the chatbot:

```json
{
  "type": "query",
  "query": "What are your technical skills?",
  "top_k": 5,
  "category": "skills"
}
```

**Fields:**
- `type` (string, required): Must be "query"
- `query` (string, required): The user's question
- `top_k` (integer, optional): Number of documents to retrieve (default: 5)
- `category` (string, optional): Filter by category

### 2. Typing Indicator (Server → Client)

Server sends this while processing:

```json
{
  "type": "typing",
  "message": "Thinking..."
}
```

### 3. Response Message (Server → Client)

AI-generated response:

```json
{
  "type": "response",
  "query": "What are your technical skills?",
  "response": "I am proficient in Python, JavaScript, TypeScript...",
  "sources": [
    {
      "id": 2,
      "category": "skills",
      "title": "Programming Languages",
      "snippet": "I am proficient in Python, JavaScript..."
    }
  ],
  "success": true,
  "timestamp": "2025-12-12T11:52:20+05:30"
}
```

### 4. Ping/Pong (Keep-Alive)

**Client → Server:**
```json
{
  "type": "ping"
}
```

**Server → Client:**
```json
{
  "type": "pong"
}
```

### 5. Error Message (Server → Client)

```json
{
  "type": "error",
  "error": "Error description",
  "details": "Detailed error message"
}
```

---

## 🌐 REST API Endpoints

### Get Chat History (Paginated)

**GET** `/chat/history/<session_id>/?page=1&page_size=20`

Retrieve chat messages for a session with pagination support.

**Query Parameters:**
- `page` (integer, optional): Page number, default: 1
- `page_size` (integer, optional): Messages per page, default: 20, max: 100

**Examples:**

```bash
# Get first page (20 messages)
curl http://localhost:8000/chat/history/550e8400-e29b-41d4-a716-446655440000/

# Get second page with 50 messages per page
curl "http://localhost:8000/chat/history/550e8400-e29b-41d4-a716-446655440000/?page=2&page_size=50"

# Get all messages (up to 100 per page)
curl "http://localhost:8000/chat/history/550e8400-e29b-41d4-a716-446655440000/?page_size=100"
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-12-12T06:00:00Z",
  "last_activity": "2025-12-12T06:15:00Z",
  "messages": [
    {
      "query": "What are your skills?",
      "response": "I am proficient in...",
      "timestamp": "2025-12-12T06:05:00Z",
      "retrieved_documents": [1, 2, 3]
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_messages": 45,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  },
  "success": true
}
```

**Pagination Metadata:**
- `page`: Current page number
- `page_size`: Number of messages per page
- `total_messages`: Total number of messages in this session
- `total_pages`: Total number of pages
- `has_next`: Boolean indicating if there's a next page
- `has_previous`: Boolean indicating if there's a previous page

### Delete Chat Session

**DELETE** `/chat/session/<session_id>/`

Delete a chat session and all its associated messages.

**Example:**

```bash
curl -X DELETE http://localhost:8000/chat/session/550e8400-e29b-41d4-a716-446655440000/
```

**Response:**
```json
{
  "message": "Session deleted successfully",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "deleted_messages": 12,
  "success": true
}
```

**Error Response (Session not found):**
```json
{
  "error": "Session not found",
  "success": false
}
```

### Health Check

**GET** `/health/`

```bash
curl http://localhost:8000/health/
```

**Response:**
```json
{
  "status": "healthy",
  "documents_count": 15,
  "success": true
}
```

---

## 💻 Client Implementation Examples

### JavaScript (Browser)

```javascript
class ChatClient {
  constructor() {
    this.ws = null;
    this.sessionId = null;
  }

  connect(existingSessionId = null) {
    const url = existingSessionId 
      ? `ws://localhost:8000/ws/chat/?session_id=${existingSessionId}`
      : 'ws://localhost:8000/ws/chat/';
    
    this.ws = new WebSocket(url);
    
    this.ws.onopen = () => {
      console.log('Connected to chatbot');
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('Disconnected from chatbot');
    };
  }

  handleMessage(data) {
    switch(data.type) {
      case 'session_info':
        this.sessionId = data.session_id;
        localStorage.setItem('chatSessionId', this.sessionId);
        console.log('Session ID:', this.sessionId);
        break;
      
      case 'typing':
        console.log('Bot is typing...');
        break;
      
      case 'response':
        console.log('Bot:', data.response);
        console.log('Sources:', data.sources);
        break;
      
      case 'error':
        console.error('Error:', data.error);
        break;
    }
  }

  sendQuery(query, options = {}) {
    const message = {
      type: 'query',
      query: query,
      ...options
    };
    this.ws.send(JSON.stringify(message));
  }

  async getHistory() {
    if (!this.sessionId) return null;
    
    const response = await fetch(
      `http://localhost:8000/chat/history/${this.sessionId}/`
    );
    return await response.json();
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const chat = new ChatClient();

// New session
chat.connect();

// Or continue existing session
const savedSessionId = localStorage.getItem('chatSessionId');
if (savedSessionId) {
  chat.connect(savedSessionId);
}

// Send a query
chat.sendQuery('What are your skills?', { top_k: 5 });

// Get chat history
chat.getHistory().then(history => {
  console.log('Chat history:', history);
});
```

### React Component

```jsx
import { useState, useEffect, useRef } from 'react';

function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    // Try to get existing session
    const savedSession = localStorage.getItem('chatSessionId');
    
    // Connect to WebSocket
    const url = savedSession 
      ? `ws://localhost:8000/ws/chat/?session_id=${savedSession}`
      : 'ws://localhost:8000/ws/chat/';
    
    ws.current = new WebSocket(url);
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'session_info') {
        setSessionId(data.session_id);
        localStorage.setItem('chatSessionId', data.session_id);
        
        // Load history if continuing session
        if (!data.is_new_session) {
          loadHistory(data.session_id);
        }
      } else if (data.type === 'typing') {
        setIsTyping(true);
      } else if (data.type === 'response') {
        setIsTyping(false);
        setMessages(prev => [...prev, {
          query: data.query,
          response: data.response,
          timestamp: data.timestamp
        }]);
      }
    };
    
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const loadHistory = async (sessionId, page = 1, pageSize = 20) => {
    const response = await fetch(
      `http://localhost:8000/chat/history/${sessionId}/?page=${page}&page_size=${pageSize}`
    );
    const data = await response.json();
    if (data.success) {
      setMessages(data.messages);
      // You can use data.pagination to implement pagination controls
      console.log('Pagination:', data.pagination);
    }
  };

  const sendMessage = () => {
    if (!input.trim()) return;
    
    ws.current.send(JSON.stringify({
      type: 'query',
      query: input
    }));
    
    setInput('');
  };

  return (
    <div className="chatbot">
      <div className="messages">
        {messages.map((msg, idx) => (
          <div key={idx}>
            <div className="user-message">{msg.query}</div>
            <div className="bot-message">{msg.response}</div>
          </div>
        ))}
        {isTyping && <div className="typing">Bot is typing...</div>}
      </div>
      
      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask me anything..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
      
      <div className="session-info">
        Session: {sessionId ? sessionId.substring(0, 8) + '...' : 'Connecting...'}
      </div>
    </div>
  );
}
```

### Python Client

```python
import asyncio
import websockets
import json

class ChatClient:
    def __init__(self, session_id=None):
        self.session_id = session_id
        self.ws = None
        
    async def connect(self):
        url = "ws://localhost:8000/ws/chat/"
        if self.session_id:
            url += f"?session_id={self.session_id}"
        
        self.ws = await websockets.connect(url)
        
        # Receive session info
        response = await self.ws.recv()
        data = json.loads(response)
        
        if data['type'] == 'session_info':
            self.session_id = data['session_id']
            print(f"Connected! Session: {self.session_id}")
    
    async def send_query(self, query, top_k=5, category=None):
        message = {
            "type": "query",
            "query": query,
            "top_k": top_k
        }
        if category:
            message["category"] = category
        
        await self.ws.send(json.dumps(message))
        
        # Wait for response
        while True:
            response = await self.ws.recv()
            data = json.loads(response)
            
            if data['type'] == 'typing':
                print("Bot is thinking...")
            elif data['type'] == 'response':
                return data
            elif data['type'] == 'error':
                print(f"Error: {data['error']}")
                return None
    
    async def close(self):
        if self.ws:
            await self.ws.close()

# Usage
async def main():
    client = ChatClient()
    await client.connect()
    
    # Send a query
    response = await client.send_query("What are your skills?")
    print(f"Bot: {response['response']}")
    
    # Send another query in same session
    response = await client.send_query("Tell me about your projects")
    print(f"Bot: {response['response']}")
    
    await client.close()

asyncio.run(main())
```

---

## 🔄 Session Management

### Session Lifecycle

1. **New Connection** → Server creates new session → Returns session_id
2. **Client Saves** → Store session_id in localStorage/cookies
3. **Reconnect** → Pass session_id in query params → Continue conversation
4. **Session Expires** → Inactive sessions can be cleaned up (implement TTL)

### Best Practices

1. **Save Session ID**: Store in localStorage or cookies
2. **Reconnect Logic**: Always try to reconnect with saved session_id
3. **Handle Expiry**: If session not found, start new session
4. **Load History**: Fetch history when continuing session

---

## 🛠️ Error Handling

### Connection Errors

```javascript
ws.onerror = (error) => {
  console.error('Connection error:', error);
  // Implement retry logic
};

ws.onclose = (event) => {
  if (event.code !== 1000) {
    // Abnormal closure, try to reconnect
    setTimeout(() => reconnect(), 3000);
  }
};
```

### Message Errors

```javascript
if (data.type === 'error') {
  // Show user-friendly error
  showError(data.error);
}
```

---

## 📊 Message Flow Diagram

```
Client                          Server
  |                               |
  |--- Connect (ws://...)-------->|
  |<-- session_info --------------|
  |    (session_id)               |
  |                               |
  |--- query ------------------>  |
  |<-- typing -------------------|
  |                              |
  |                    [Processing RAG]
  |                              |
  |<-- response -----------------|
  |    (answer + sources)        |
  |                               |
  |--- query ------------------->|
  |<-- typing -------------------|
  |<-- response -----------------|
  |                               |
```

---

## 🚀 Running the Server

```bash
# Install Redis
sudo apt-get install redis-server
sudo systemctl start redis

# Run Django with Daphne (ASGI server)
daphne -b 0.0.0.0 -p 8000 backend.asgi:application

# Or use Django's development server (supports ASGI)
python manage.py runserver
```

---

## 📝 Testing

### Test WebSocket Connection

```bash
# Using websocat
websocat ws://localhost:8000/ws/chat/

# Send a message
{"type": "query", "query": "What are your skills?"}
```

### Test Chat History API

```bash
curl http://localhost:8000/chat/history/550e8400-e29b-41d4-a716-446655440000/
```

---

**For more details, see README.md and IMPLEMENTATION.md**
