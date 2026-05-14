from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api_router import router

app = FastAPI(title="Chatbot Backend", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Chatbot Backend is running"}