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
├── Chatapplication/
├── frontend/            
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

<img width="1421" height="685" alt="Screenshot 2026-05-14 184304" src="https://github.com/user-attachments/assets/e4d09a68-cc0f-4570-a04b-2fa4b69026be" />
<img width="1423" height="676" alt="Screenshot 2026-05-14 184329" src="https://github.com/user-attachments/assets/df8ad631-25b2-4703-a3cb-1b22922a4d62" />
