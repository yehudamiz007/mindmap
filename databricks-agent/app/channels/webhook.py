"""
app/channels/webhook.py

Generic webhook channel handler.
Accepts {user_id, message} and returns the agent response.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

logger = logging.getLogger("agent.channels.webhook")


async def handle_webhook(
    user_id:    str,
    message:    str,
    session_id: Optional[str] = None,
    channel:    str = "generic",
) -> dict:
    """
    Process an inbound webhook message through the AgentRuntime.

    Returns a dict with:
      - session_id: str
      - response:   str
      - user_id:    str
    """
    from agent.runtime import AgentRuntime

    if not session_id:
        session_id = str(uuid.uuid4())

    logger.info("Webhook message: user=%s channel=%s session=%s", user_id, channel, session_id)

    rt = AgentRuntime()
    try:
        response = rt.process_message(
            user_id    = user_id,
            message    = message,
            session_id = session_id,
            channel    = channel,
        )
        return {
            "status":     "ok",
            "user_id":    user_id,
            "session_id": session_id,
            "response":   response,
        }
    except Exception as exc:
        logger.exception("Webhook handler error for user=%s", user_id)
        return {
            "status":     "error",
            "user_id":    user_id,
            "session_id": session_id,
            "error":      str(exc),
        }
