from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from backend.agent import chat_with_agent

app = FastAPI()

# Optional: Allow frontend to access backend (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model for /chat endpoint
class ChatRequest(BaseModel):
    prompt: str

# Health check
@app.get("/")
def read_root():
    return {"message": "AI Media Planner backend is running."}

# Main chat route
@app.post("/chat")
def chat(request: ChatRequest):
    response = chat_with_agent(request.prompt)
    return {"response": str(response["output"])}
