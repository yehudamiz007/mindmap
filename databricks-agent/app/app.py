"""
app/app.py
FastAPI application for the Databricks AI Agent Platform.

Routes:
  POST /chat                 - Main chat endpoint
  POST /webhook/slack        - Slack Events API
  POST /webhook/generic      - Generic webhook
  GET  /health               - Health check
  GET  /memory/{user_id}     - Memory summary for a user
  POST /memory/{user_id}     - Save a memory entry
  GET  /skills               - List all skills
  POST /admin/sync-skills    - Reload skill index from Volume
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agent.identity import get_current_user

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agent.app")

# ---------------------------------------------------------------------------
# App bootstrap
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Databricks AI Agent",
    description="OpenClaw-style AI agent platform running on Databricks Apps",
    version="1.0.0",
)

# Lazy-initialise the runtime so the app starts fast even if Spark/SDK init
# takes a second.  We initialise on first request.
_runtime = None


def get_runtime():
    global _runtime
    if _runtime is None:
        from agent.runtime import AgentRuntime
        _runtime = AgentRuntime()
        logger.info("AgentRuntime initialised.")
    return _runtime


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    user_id:    str            = Field(..., description="Unique user identifier")
    message:    str            = Field(..., description="User message text")
    session_id: Optional[str]  = Field(None, description="Existing session ID (new one created if omitted)")


class ChatResponse(BaseModel):
    session_id: str
    response:   str
    latency_ms: int


class MemorySaveRequest(BaseModel):
    key:        str            = Field(..., description="Memory key")
    value:      str            = Field(..., description="Memory value")
    category:   str            = Field("fact", description="Category: fact, preference, person, lesson, project")
    importance: int            = Field(5, ge=1, le=10, description="Importance 1-10")


class WebhookRequest(BaseModel):
    user_id: str
    message: str
    session_id: Optional[str] = None
    channel:    str = "generic"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "databricks-ai-agent", "version": "1.0.0"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user_id: str = Depends(get_current_user)):
    """
    user_id comes from the authenticated Databricks identity
    (X-Forwarded-Access-Token in production, fallback for dev).
    The user_id in the request body is ignored in production -
    the real identity is always resolved server-side.
    """
    session_id = req.session_id or str(uuid.uuid4())
    t0 = time.time()
    try:
        rt = get_runtime()
        response = rt.process_message(
            user_id=user_id,   # ← real Databricks identity, not from body
            message=req.message,
            session_id=session_id,
            channel="direct",
        )
        latency_ms = int((time.time() - t0) * 1000)
        return ChatResponse(session_id=session_id, response=response, latency_ms=latency_ms)
    except Exception as exc:
        logger.exception("Error in /chat")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/webhook/slack")
async def slack_webhook(request: Request):
    from channels.slack import handle_slack_event
    body = await request.json()
    return await handle_slack_event(body)


@app.post("/webhook/generic")
async def generic_webhook(req: WebhookRequest):
    from channels.webhook import handle_webhook
    return await handle_webhook(req.user_id, req.message, req.session_id, req.channel)


@app.get("/memory/me")
async def get_my_memory(user_id: str = Depends(get_current_user)):
    """Returns memory for the authenticated user only."""
    try:
        from agent.memory import get_user_context
        context = get_user_context(user_id)
        return {"user_id": user_id, "context": context}
    except Exception as exc:
        logger.exception("Error fetching memory for %s", user_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/memory/me")
async def save_my_memory(req: MemorySaveRequest, user_id: str = Depends(get_current_user)):
    """Saves memory for the authenticated user only."""
    try:
        from agent.memory import save_memory
        save_memory(
            user_id=user_id,
            key=req.key,
            value=req.value,
            category=req.category,
            importance=req.importance,
            source="user",
        )
        return {"status": "saved", "user_id": user_id, "key": req.key}
    except Exception as exc:
        logger.exception("Error saving memory for %s", user_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/skills")
async def list_skills():
    try:
        from agent.skills import SkillIndex
        idx = SkillIndex()
        return {"skills": idx.list_skills()}
    except Exception as exc:
        logger.exception("Error listing skills")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/admin/sync-skills")
async def sync_skills():
    """Reload the skill index from the Volume (hot-reload without restart)."""
    try:
        from agent.skills import SkillIndex
        idx = SkillIndex(force_reload=True)
        skills = idx.list_skills()
        return {"status": "reloaded", "skill_count": len(skills), "skills": [s["name"] for s in skills]}
    except Exception as exc:
        logger.exception("Error syncing skills")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
