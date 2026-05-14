from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    username: Optional[str] = Field(default="guest", description="Optional username for the message sender")
    user_id: Optional[int] = Field(default=None, description="Optional existing user ID")
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation UUID")
    message: str = Field(..., description="User chat message")


class MessageItem(BaseModel):
    id: int
    user_id: int
    conversation_id: str
    role: str
    message: str
    timestamp: str


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    messages: List[MessageItem]


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


class HistoryResponse(BaseModel):
    conversation_id: str
    messages: List[MessageItem]
    total_messages: int
    has_more: bool


class DeleteResponse(BaseModel):
    success: bool
    message: str
