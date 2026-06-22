import os
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from agent import run_agent

app = FastAPI()

# ✅ CORS (important for browser)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# ✅ API
@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        return {"response": run_agent(req.message)}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}

# ✅ Serve UI
@app.get("/")
def home():
    return FileResponse("index.html")


# ✅ Render entry point
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)