from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from rag_engine import VulnCopilotRAG

rag_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_app
    print("🚀 Memulai VulnCopilot FastAPI Server & Loading RAG Engine...")
    rag_app = VulnCopilotRAG()
    print("✅ RAG Engine Siap Melayani HTTP Request!")
    yield
    print("🛑 Server dimatikan...")

app = FastAPI(
    title="VulnCopilot DevSecOps RAG API",
    description="Backend API yang membungkus Llama Index RAG Engine dengan Google Gemini & ChromaDB",
    version="1.0.0",
    lifespan=lifespan
)

#konfig Cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mengizinkan semua origin (termasuk localhost React di port 5173/3000)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
class ChatResponse(BaseModel):
    response: str
    status: str = "success"

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "VulnCopilot DevSecOps RAG API",
        "version": "1.0.0"
    }
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong.")
    
    try:
        reply = rag_app.query(request.message)
        return ChatResponse(response=reply, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses query RAG: {str(e)}")
@app.post("/reset-session")
def reset_session():
    if rag_app and rag_app.reset_memory():
        return {"status": "success", "message": "Memori percakapan berhasil di-reset."}
    return {"status": "error", "message": "Gagal mereset percakapan."}