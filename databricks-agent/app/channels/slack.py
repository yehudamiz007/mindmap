"""
app/channels/slack.py

Slack Events API channel handler.

Handles:
  - url_verification challenge (Slack's initial handshake)
  - message events (new messages in channels/DMs the bot is in)

Environment variables required:
  SLACK_BOT_TOKEN  - Bot OAuth token (xoxb-...)
  SLACK_BOT_USER_ID (optional) - Bot's own user ID to avoid self-replies
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

import httpx

logger = logging.getLogger("agent.channels.slack")

SLACK_BOT_TOKEN   = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_BOT_USER_ID = os.getenv("SLACK_BOT_USER_ID", "")
SLACK_POST_URL    = "https://slack.com/api/chat.postMessage"


async def handle_slack_event(body: dict) -> Any:
    """
    Entry point for all Slack Events API payloads.

    Slack sends:
      1. A url_verification challenge when the endpoint is first registered.
      2. Event payloads wrapped in an "event" key for actual messages.

    Returns:
      - For challenge: {"challenge": "<token>"}
      - For message:   {"ok": True}
      - For ignored:   {"ok": True, "ignored": True}
    """
    # Handle verification challenge
    if body.get("type") == "url_verification":
        challenge = body.get("challenge", "")
        logger.info("Slack url_verification challenge received.")
        return {"challenge": challenge}

    event_wrapper = body.get("event", {})
    event_type    = event_wrapper.get("type", "")

    # Only handle regular messages
    if event_type != "message":
        logger.debug("Ignoring Slack event type: %s", event_type)
        return {"ok": True, "ignored": True}

    # Ignore bot messages (including our own) to avoid infinite loops
    subtype  = event_wrapper.get("subtype", "")
    bot_id   = event_wrapper.get("bot_id", "")
    user_id  = event_wrapper.get("user", "")

    if subtype in ("bot_message", "message_changed", "message_deleted"):
        logger.debug("Ignoring Slack subtype: %s", subtype)
        return {"ok": True, "ignored": True}

    if bot_id:
        logger.debug("Ignoring bot message from bot_id=%s", bot_id)
        return {"ok": True, "ignored": True}

    if SLACK_BOT_USER_ID and user_id == SLACK_BOT_USER_ID:
        logger.debug("Ignoring our own message.")
        return {"ok": True, "ignored": True}

    text       = event_wrapper.get("text", "").strip()
    channel_id = event_wrapper.get("channel", "")
    thread_ts  = event_wrapper.get("thread_ts") or event_wrapper.get("ts", "")

    if not text or not user_id:
        return {"ok": True, "ignored": True}

    # Use Slack user ID as agent user_id, channel+user as session
    agent_user_id  = f"slack:{user_id}"
    session_id     = f"slack:{channel_id}:{user_id}"

    logger.info(
        "Slack message: user=%s channel=%s text=%.60s",
        agent_user_id, channel_id, text,
    )

    # Process through agent
    try:
        from agent.runtime import AgentRuntime
        rt       = AgentRuntime()
        response = rt.process_message(
            user_id    = agent_user_id,
            message    = text,
            session_id = session_id,
            channel    = "slack",
        )
    except Exception as exc:
        logger.exception("Agent error for Slack message from %s", agent_user_id)
        response = f"Sorry, I encountered an error: {exc}"

    # Post reply to Slack
    if SLACK_BOT_TOKEN and channel_id:
        await _post_slack_reply(
            channel   = channel_id,
            text      = response,
            thread_ts = thread_ts,
        )
    else:
        logger.warning("SLACK_BOT_TOKEN not set or no channel_id - response not sent.")

    return {"ok": True}


async def _post_slack_reply(channel: str, text: str, thread_ts: str) -> None:
    """Post a reply to a Slack channel (optionally in a thread)."""
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type":  "application/json; charset=utf-8",
    }
    payload = {
        "channel":   channel,
        "text":      text,
        "thread_ts": thread_ts,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(SLACK_POST_URL, headers=headers, json=payload)
            data = resp.json()
            if not data.get("ok"):
                logger.error("Slack API error: %s", data.get("error", "unknown"))
            else:
                logger.debug("Slack reply sent to channel=%s", channel)
    except Exception as exc:
        logger.error("Failed to post Slack reply: %s", exc)
