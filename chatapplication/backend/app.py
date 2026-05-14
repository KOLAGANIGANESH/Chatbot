import asyncio
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.database import Database
from backend.models import (
    ChatRequest,
    ChatResponse,
    ConversationSummary,
    DeleteResponse,
    HistoryResponse,
    MessageItem,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title="Kolagani Chat Backend",
    description="FastAPI backend with SQLite chat history, caching, and lazy message loading.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

db = Database.get_instance()


@app.on_event("startup")
async def startup_event() -> None:
    await asyncio.to_thread(db._initialize_database)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "database": str(db.database_path)}


@app.get("/", response_class=FileResponse)
def serve_frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/chat", response_model=ChatResponse)
async def create_chat(request: ChatRequest):
    if request.user_id is not None and not await asyncio.to_thread(db.user_exists, request.user_id):
        raise HTTPException(status_code=404, detail="User not found")

    user_id = request.user_id or await asyncio.to_thread(db.get_or_create_user, request.username or "guest")
    conversation_id = request.conversation_id

    if conversation_id and not await asyncio.to_thread(db.conversation_exists, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not conversation_id:
        conversation_id = await asyncio.to_thread(db.create_conversation, user_id, request.message[:80])

    await asyncio.to_thread(db.save_message, user_id, conversation_id, "user", request.message)
    context = await asyncio.to_thread(db.get_ai_context, conversation_id, 15)
    assistant_response = await asyncio.to_thread(db.generate_assistant_response, request.message, context)
    await asyncio.to_thread(db.save_message, user_id, conversation_id, "assistant", assistant_response)

    recent_messages = await asyncio.to_thread(db.fetch_recent_messages, conversation_id, 20)
    return ChatResponse(
        conversation_id=conversation_id,
        reply=assistant_response,
        messages=[MessageItem(**message) for message in recent_messages],
    )


@app.get("/history/{conversation_id}", response_model=HistoryResponse)
async def history(
    conversation_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    if not await asyncio.to_thread(db.conversation_exists, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await asyncio.to_thread(db.fetch_full_conversation, conversation_id, limit, offset)
    total = await asyncio.to_thread(db.count_conversation_messages, conversation_id)
    return HistoryResponse(
        conversation_id=conversation_id,
        messages=[MessageItem(**row) for row in messages],
        total_messages=total,
        has_more=offset + len(messages) < total,
    )


@app.delete("/conversation/{conversation_id}", response_model=DeleteResponse)
async def delete_conversation(conversation_id: str):
    success = await asyncio.to_thread(db.delete_conversation, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return DeleteResponse(success=True, message="Conversation deleted")


@app.get("/conversations/{user_id}", response_model=List[ConversationSummary])
async def list_conversations(user_id: int, limit: int = Query(20, ge=1, le=50)):
    rows = await asyncio.to_thread(db.list_conversations, user_id, limit)
    return [ConversationSummary(**row) for row in rows]


@app.get("/search", response_model=List[MessageItem])
async def search_messages(
    query: str,
    user_id: Optional[int] = None,
    conversation_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
):
    rows = await asyncio.to_thread(db.search_messages, query, user_id, conversation_id, limit)
    return [MessageItem(**row) for row in rows]
