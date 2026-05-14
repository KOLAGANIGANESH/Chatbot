import sqlite3
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional
import uuid
from dotenv import load_dotenv
import os
import google.genai as genai

# Load environment variables
load_dotenv(Path(__file__).resolve().parent / ".env")

api_key = os.getenv('Gemini_API_Key')
if api_key:
    os.environ['GOOGLE_API_KEY'] = api_key
    client = genai.Client()
else:
    client = None

DATABASE_PATH = Path(__file__).resolve().parent / "chat_history.db"

CREATE_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_timestamp ON messages(conversation_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_text ON messages(message);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
"""


class Database:
    _instance: Optional["Database"] = None
    _singleton_lock = Lock()

    def __init__(self, database_path: Path = DATABASE_PATH):
        self.database_path = database_path
        self.connection = sqlite3.connect(
            str(self.database_path), check_same_thread=False, isolation_level=None
        )
        self.connection.row_factory = sqlite3.Row
        self.lock = Lock()
        self.cache_lock = Lock()
        self._recent_messages_cache: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict()
        self._initialize_database()

    @classmethod
    def get_instance(cls) -> "Database":
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = Database()
            return cls._instance

    def _initialize_database(self) -> None:
        with self.lock:
            cursor = self.connection.cursor()
            cursor.executescript(CREATE_SCHEMA)
            cursor.close()

    def _execute(self, query: str, parameters: tuple = (), commit: bool = False):
        with self.lock:
            cursor = self.connection.cursor()
            cursor.execute(query, parameters)
            if commit:
                self.connection.commit()
            return cursor

    def _fetchall(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        cursor = self._execute(query, parameters)
        rows = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return rows

    def _fetchone(self, query: str, parameters: tuple = ()) -> Optional[Dict[str, Any]]:
        cursor = self._execute(query, parameters)
        row = cursor.fetchone()
        cursor.close()
        return dict(row) if row else None

    def get_or_create_user(self, username: str) -> int:
        user = self._fetchone("SELECT id FROM users WHERE username = ?", (username,))
        if user:
            return user["id"]
        insert = self._execute(
            "INSERT INTO users (username) VALUES (?)", (username,), commit=True
        )
        return insert.lastrowid

    def create_conversation(self, user_id: int, title: Optional[str] = None) -> str:
        conversation_id = str(uuid.uuid4())
        title_value = title.strip()[:120] if title else f"Conversation {datetime.utcnow().isoformat()}"
        self._execute(
            "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
            (conversation_id, user_id, title_value),
            commit=True,
        )
        self.clear_conversation_cache(conversation_id)
        return conversation_id

    def conversation_exists(self, conversation_id: str) -> bool:
        result = self._fetchone(
            "SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)
        )
        return bool(result)

    def user_exists(self, user_id: int) -> bool:
        result = self._fetchone("SELECT 1 FROM users WHERE id = ?", (user_id,))
        return bool(result)

    def save_message(
        self, user_id: int, conversation_id: str, role: str, message: str
    ) -> int:
        timestamp = datetime.utcnow().isoformat()
        insert = self._execute(
            "INSERT INTO messages (user_id, conversation_id, role, message, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, conversation_id, role, message, timestamp),
            commit=True,
        )
        self._execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?", (timestamp, conversation_id), commit=True
        )
        self.clear_conversation_cache(conversation_id)
        return insert.lastrowid

    def fetch_recent_messages(
        self, conversation_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        with self.cache_lock:
            cache_key = f"recent:{conversation_id}:{limit}"
            if cache_key in self._recent_messages_cache:
                self._recent_messages_cache.move_to_end(cache_key)
                return self._recent_messages_cache[cache_key][:]

        rows = self._fetchall(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp DESC LIMIT ?",
            (conversation_id, limit),
        )
        messages = list(reversed(rows))
        with self.cache_lock:
            self._recent_messages_cache[cache_key] = messages
            if len(self._recent_messages_cache) > 50:
                self._recent_messages_cache.popitem(last=False)
        return messages

    def fetch_full_conversation(
        self, conversation_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        return self._fetchall(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC LIMIT ? OFFSET ?",
            (conversation_id, limit, offset),
        )

    def count_conversation_messages(self, conversation_id: str) -> int:
        row = self._fetchone(
            "SELECT COUNT(1) AS total FROM messages WHERE conversation_id = ?",
            (conversation_id,),
        )
        return row["total"] if row else 0

    def delete_conversation(self, conversation_id: str) -> bool:
        if not self.conversation_exists(conversation_id):
            return False
        self._execute(
            "DELETE FROM conversations WHERE id = ?", (conversation_id,), commit=True
        )
        self.clear_conversation_cache(conversation_id)
        return True

    def search_messages(
        self,
        query: str,
        user_id: Optional[int] = None,
        conversation_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        sql = ["SELECT * FROM messages WHERE message LIKE ?"]
        parameters: List[Any] = [f"%{query}%"]
        if user_id is not None:
            sql.append("AND user_id = ?")
            parameters.append(user_id)
        if conversation_id is not None:
            sql.append("AND conversation_id = ?")
            parameters.append(conversation_id)
        sql.append("ORDER BY timestamp DESC LIMIT ?")
        parameters.append(limit)
        return self._fetchall(" ".join(sql), tuple(parameters))

    def list_conversations(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        return self._fetchall(
            "SELECT c.id, c.title, c.created_at, c.updated_at, COUNT(m.id) AS message_count"
            " FROM conversations c"
            " LEFT JOIN messages m ON c.id = m.conversation_id"
            " WHERE c.user_id = ?"
            " GROUP BY c.id"
            " ORDER BY c.updated_at DESC"
            " LIMIT ?",
            (user_id, limit),
        )

    def clear_conversation_cache(self, conversation_id: str) -> None:
        with self.cache_lock:
            keys = [key for key in self._recent_messages_cache if key.startswith(f"recent:{conversation_id}:")]
            for key in keys:
                self._recent_messages_cache.pop(key, None)

    def get_ai_context(self, conversation_id: str, limit: int = 15) -> List[Dict[str, Any]]:
        return self.fetch_recent_messages(conversation_id, limit=limit)

    def build_ai_prompt(self, context: List[Dict[str, Any]]) -> str:
        prompt_parts = []
        for message in context:
            role = message["role"]
            text = message["message"]
            prompt_parts.append(f"[{role}] {text}")
        return "\n".join(prompt_parts)

    def generate_assistant_response(self, user_text: str, context: List[Dict[str, Any]]) -> str:
        if client is None:
            return f"[Assistant] API key not configured. Latest user input: {user_text[:180]}"

        try:
            prompt = self.build_ai_prompt(context[-10:]) if context else user_text
            chat = client.chats.create(model="gemini-2.5-flash")
            response = chat.send_message(prompt)
            return response.text
        except Exception as e:
            return f"[Assistant] Error generating response: {str(e)}. Latest user input: {user_text[:180]}"
