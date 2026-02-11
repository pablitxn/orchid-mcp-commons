"""End-to-end integration tests for the RabbitMQ broker provider."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from orchid_commons.db import create_rabbitmq_broker

pytestmark = pytest.mark.integration


async def _wait_for_queue_message(
    queue: Any,
    *,
    timeout_seconds: float = 15.0,
    poll_timeout_seconds: float = 1.0,
) -> Any:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while asyncio.get_running_loop().time() < deadline:
        try:
            message = await queue.get(timeout=poll_timeout_seconds)
        except TimeoutError:
            continue
        except Exception as exc:
            if exc.__class__.__name__ == "QueueEmpty":
                continue
            raise
        if message is not None:
            return message
    raise AssertionError(f"No message received from queue within {timeout_seconds:.1f}s")


async def test_rabbitmq_publish_and_health(rabbitmq_settings) -> None:
    broker = await create_rabbitmq_broker(rabbitmq_settings)
    try:
        queue = await broker.declare_queue("integration_test_queue", durable=False)

        await broker.publish(
            {"event": "test", "data": "hello"},
            queue_name="integration_test_queue",
        )

        # Consume one message to verify it arrived, tolerating startup jitter.
        message = await _wait_for_queue_message(queue)
        assert message is not None
        await message.ack()

        assert (await broker.health_check()).healthy is True
    finally:
        await broker.close()
