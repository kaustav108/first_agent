import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# 🔥 import your existing agent functions
from agent import (
    extract_cities,
    choose_tool,
    call_mcp,
    clean_data,
    build_prompt,
    generate_llm_response
)

app = FastAPI(title="MCP AI Agent 🌍")

# ==============================
# ✅ CORS (allow frontend calls)
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# 🏠 HOME (NO JINJA → NO ERROR)
# ==============================
@app.get("/")
def home():
    return FileResponse("templates/index.html")


# ==============================
# 💬 CHAT API
# ==============================
@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        user_input = body.get("message", "").strip()

        if not user_input:
            return {"response": "❌ Empty message"}

        # run blocking agent in thread
        result = await asyncio.to_thread(process_query, user_input)

        return {"response": result}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"response": f"❌ {str(e)}"}
        )


# ==============================
# 🧠 CORE LOGIC (UNCHANGED)
# ==============================
def process_query(user_input: str) -> str:
    try:
        cities = extract_cities(user_input)

        if not cities:
            return "❌ No city found"

        # ======================
        # MULTI-CITY
        # ======================
        if len(cities) > 1:
            results = []

            for city in cities:
                data = call_mcp("getFullInsights", city)

                if isinstance(data, dict) and "error" in data:
                    continue

                results.append({city: clean_data(data)})

            if not results:
                return "❌ No valid data found"

            prompt = build_prompt(user_input, results)

        # ======================
        # SINGLE CITY
        # ======================
        else:
            city = cities[0]
            tool = choose_tool(user_input)

            data = call_mcp(tool, city)

            if isinstance(data, dict) and "error" in data:
                return data["error"]

            prompt = build_prompt(user_input, clean_data(data))

        # ======================
        # LLM RESPONSE
        # ======================
        return generate_llm_response(prompt)

    except Exception as e:
        return f"❌ Processing error: {str(e)}"


# ==============================
# ❤️ HEALTH CHECK
# ==============================
@app.get("/health")
def health():
    return {"status": "ok"}


# ==============================
# ▶️ RUN SERVER
# ==============================
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )