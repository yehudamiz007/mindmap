"""
app/agent/identity.py

Resolves the authenticated Databricks user identity from the incoming
HTTP request.  Inside a Databricks App, every request carries an
X-Forwarded-Access-Token header containing a short-lived OAuth token
issued for the end-user by the Databricks platform.

We exchange that token for the user's email / username via the
WorkspaceClient - this becomes the canonical user_id used throughout
the memory and audit layers.

Fallback chain (in order):
  1. X-Forwarded-Access-Token header  → real Databricks identity (prod)
  2. X-Agent-User-Id header           → integration testing / CI
  3. user_id field in request body    → local dev / curl testing
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Optional

from databricks.sdk import WorkspaceClient
from fastapi import Header, HTTPException, Request

logger = logging.getLogger("agent.identity")


# ---------------------------------------------------------------------------
# Token → user resolution (cached per token for the lifetime of the process)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=512)
def _resolve_token(token: str) -> str:
    """
    Given a Databricks OAuth access token, return the user's email address.
    Result is cached so we don't call the API on every request for the same
    token (tokens are typically valid for ~1 hour).
    """
    try:
        w = WorkspaceClient(token=token)
        me = w.current_user.me()
        user_name = me.user_name or me.display_name
        if not user_name:
            raise ValueError("Empty user_name returned by Databricks API")
        logger.debug("Resolved token → %s", user_name)
        return user_name
    except Exception as exc:
        logger.warning("Failed to resolve Databricks token: %s", exc)
        raise


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    request: Request,
    x_forwarded_access_token: Optional[str] = Header(None, alias="X-Forwarded-Access-Token"),
    x_agent_user_id:          Optional[str] = Header(None, alias="X-Agent-User-Id"),
) -> str:
    """
    FastAPI dependency that returns the authenticated user_id.

    Inject with:
        from agent.identity import get_current_user
        from fastapi import Depends

        @app.post("/chat")
        async def chat(req: ChatRequest, user_id: str = Depends(get_current_user)):
            ...
    """

    # 1. Real Databricks App token (production path)
    if x_forwarded_access_token:
        try:
            return _resolve_token(x_forwarded_access_token)
        except Exception:
            raise HTTPException(
                status_code=401,
                detail="Could not authenticate with Databricks identity token",
            )

    # 2. Integration test header
    if x_agent_user_id:
        logger.info("Using X-Agent-User-Id header: %s", x_agent_user_id)
        return x_agent_user_id

    # 3. Local dev fallback from request body
    try:
        body = await request.json()
        if body.get("user_id"):
            logger.info("Using user_id from request body (dev mode): %s", body["user_id"])
            return body["user_id"]
    except Exception:
        pass

    # 4. Env var override (local dev only)
    dev_user = os.getenv("DEV_USER_ID")
    if dev_user:
        logger.info("Using DEV_USER_ID env var: %s", dev_user)
        return dev_user

    raise HTTPException(
        status_code=401,
        detail=(
            "Unable to determine user identity. "
            "In production, deploy as a Databricks App. "
            "For local dev, set DEV_USER_ID env var."
        ),
    )


# ---------------------------------------------------------------------------
# Sync version for use outside FastAPI request context (e.g. jobs)
# ---------------------------------------------------------------------------

def resolve_current_user(token: Optional[str] = None) -> str:
    """
    Resolve the current user synchronously.
    Used in background jobs and notebooks where there is no HTTP request.

    If token is None, uses the ambient WorkspaceClient credentials
    (e.g. the job/notebook's own service principal or user identity).
    """
    try:
        if token:
            return _resolve_token(token)
        w = WorkspaceClient()
        me = w.current_user.me()
        return me.user_name or me.display_name or "unknown"
    except Exception as exc:
        logger.error("Could not resolve current user: %s", exc)
        return "unknown"
