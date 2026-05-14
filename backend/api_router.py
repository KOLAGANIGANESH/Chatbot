from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
from groq import Groq
from config import Config
import asyncio

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    status: str
    response: str
    model_used: str

async def get_gemini_response(message: str) -> str:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    response = await asyncio.to_thread(model.generate_content, message)
    return response.text

async def get_groq_response(message: str) -> str:
    client = Groq(api_key=Config.GROQ_API_KEY)

    def sync_completion():
        return client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[{"role": "user", "content": message}],
        )

    response = await asyncio.to_thread(sync_completion)
    if hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content
    raise ValueError("Groq response did not contain a valid message")

async def generate_text_stream(message: str):
    response_text = None
    model_used = None

    try:
        response_text = await get_gemini_response(message)
        model_used = "Google Gemini"
    except Exception as e:
        print(f"Gemini failed: {e}")

    if not response_text:
        try:
            response_text = await get_groq_response(message)
            model_used = "Groq"
        except Exception as e:
            print(f"Groq failed: {e}")
            yield "ERROR: All AI services failed."
            return

    if not response_text:
        yield "ERROR: Empty response from AI service."
        return

    yield f"[model: {model_used}] "

    chunk_size = 40
    for idx in range(0, len(response_text), chunk_size):
        chunk = response_text[idx: idx + chunk_size]
        yield chunk
        await asyncio.sleep(0)

    yield ""

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    message = request.message
    response = None
    model_used = None

    try:
        response = await get_gemini_response(message)
        model_used = "Google Gemini"
    except Exception as e:
        print(f"Gemini failed: {e}")

    if not response:
        try:
            response = await get_groq_response(message)
            model_used = "Groq"
        except Exception as e:
            print(f"Groq failed: {e}")
            raise HTTPException(status_code=500, detail="All AI services failed")

    return ChatResponse(status="success", response=response, model_used=model_used)

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(generate_text_stream(request.message), media_type="text/plain; charset=utf-8")
