# Kolagani AI

A high-performance GenAI chat backend built with FastAPI, SQLite, and a vanilla JavaScript frontend.

## Project Structure

```
chatapplication/
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── models.py
│   ├── requirements.txt
│   ├── __init__.py
│   └── chat_history.db  # created automatically after first run
├── frontend/
│   └── index.html
├── .env
├── .gitignore
└── README.md
```

## Backend Features

- SQLite database with tables for `users`, `conversations`, and `messages`
- Auto-initializing schema and indices
- Caching for recent messages
- Thread-safe database access with `sqlite3`
- Async FastAPI endpoints for better concurrency
- Conversation history loading with lazy messages
- Search and delete conversation APIs
- UUID conversation IDs
- Example GenAI prompt builder for memory-aware context

## API Endpoints

- `POST /chat`
- `GET /history/{conversation_id}`
- `DELETE /conversation/{conversation_id}`
- `GET /conversations/{user_id}`
- `GET /search?query=...` 
- `GET /health`

## Setup Instructions

### 1. Install dependencies

From the project root:

```powershell
pip install -r backend/requirements.txt
```

### 2. Run the backend

```powershell
uvicorn backend.app:app --reload
```

The backend runs by default at `http://127.0.0.1:8000`.

### 3. Open the frontend

Open `frontend/index.html` in your browser or visit `http://127.0.0.1:8000/` if you want the backend to serve the UI directly.

## Example Frontend Integration

The frontend uses `fetch` to call the chat API:

```js
const response = await fetch("http://127.0.0.1:8000/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message, conversation_id }),
});
const data = await response.json();
```

## Notes

- The database file `backend/chat_history.db` is created automatically.
- The backend is optimized for conversation memory by limiting AI context to the last 10-20 messages.
- Use `DELETE /conversation/{conversation_id}` to remove full history.
- Use `GET /history/{conversation_id}?limit=20&offset=0` to lazily load older messages.
