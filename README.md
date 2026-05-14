# Amigo Chatbot Project

A full-stack chatbot application with AI failover using Gemini and Groq.

## Project Structure

```
Amigo/
├── venv/                ← Virtual environment
├── backend/             ← FastAPI backend
│   ├── app.py
│   ├── api_router.py
│   ├── config.py
│   └── requirements.txt
├── frontend/            ← ChatGPT-style UI
│   ├── index.html
│   ├── style.css
│   └── script.js
├── .env                 ← Environment variables
└── README.md
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend folder:
   ```bash
   cd backend
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv ..\venv
   ..\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the backend server:
   ```bash
   uvicorn app:app --reload
   ```

### Frontend Setup

1. Open `frontend/index.html` in your browser, or serve it with a local server.

2. Make sure the backend is running on `http://localhost:8000`.

## Features

- **AI Failover**: Google Gemini → Groq
- **Frontend**: Clean ChatGPT-style interface
- **Backend**: FastAPI with CORS enabled

## API Endpoints

- `GET /` - Health check
- `POST /chat` - Send message and get AI response

## Environment Variables

Fill in your `.env` file with actual Gemini and Groq API keys.