from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress
from typing import Optional

import redis.asyncio as aioredis

from ansible_web_ui.core.config import settings
from ansible_web_ui.websocket.manager import get_websocket_manager

logger = logging.getLogger(__name__)


class WebSocketEventListener:
    """Background listener bridging Redis pub/sub events to WebSocket clients."""

    CHANNEL_PATTERN = "ws:tasks:*"

    def __init__(self) -> None:
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._task: Optional[asyncio.Task] = None
        self._stop_event: Optional[asyncio.Event] = None

    async def start(self) -> None:
        """Begin listening for websocket events if not already running."""
        if self._task and not self._task.done():
            return

        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )

        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("WebSocket event listener started")

    async def stop(self) -> None:
        """Stop listening and release Redis resources."""
        if self._stop_event:
            self._stop_event.set()

        if self._task:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        await self._cleanup_pubsub()

        if self._redis:
            await self._redis.close()
            self._redis = None

        logger.info("WebSocket event listener stopped")

    async def _run_loop(self) -> None:
        while self._stop_event and not self._stop_event.is_set():
            try:
                await self._consume_events()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("WebSocket event listener error: %s", exc)
                await asyncio.sleep(1)

    async def _consume_events(self) -> None:
        if not self._redis:
            return

        manager = get_websocket_manager()
        self._pubsub = self._redis.pubsub()
        await self._pubsub.psubscribe(self.CHANNEL_PATTERN)

        try:
            while self._stop_event and not self._stop_event.is_set():
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if not message:
                    continue

                data = message.get("data")
                if not data:
                    continue

                try:
                    payload = json.loads(data)
                except json.JSONDecodeError:
                    logger.warning("Invalid WebSocket event payload: %s", data)
                    continue

                await manager.dispatch_event(payload)
        finally:
            await self._cleanup_pubsub()

    async def _cleanup_pubsub(self) -> None:
        if not self._pubsub:
            return
        with suppress(Exception):
            await self._pubsub.punsubscribe(self.CHANNEL_PATTERN)
            await self._pubsub.close()
        self._pubsub = None


def get_websocket_event_listener() -> WebSocketEventListener:
    """Return the singleton WebSocket event listener."""
    global _listener
    try:
        listener = _listener
    except NameError:
        listener = None

    if listener is None:
        listener = WebSocketEventListener()
        globals()["_listener"] = listener
    return listener
