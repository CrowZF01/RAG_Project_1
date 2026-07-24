from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="VulnCopilot DevSecOps RAG API")

class ChatRequest(BaseModel):
    message: str
class ChatResponse(BaseModel):
    response: str
    status: str = "success"