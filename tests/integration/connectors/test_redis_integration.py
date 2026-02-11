"""End-to-end integration tests for the Redis cache provider."""

from __future__ import annotations

import asyncio

import pytest

from orchid_commons.db import create_redis_cache

pytestmark = pytest.mark.integration


async def _wait_until_key_absent(
    cache: object,
    key: str,
    *,
    timeout_seconds: float = 5.0,
    poll_interval_seconds: float = 0.1,
) -> None:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while asyncio.get_running_loop().time() < deadline:
        if await cache.get(key) is None:
            return
        await asyncio.sleep(poll_interval_seconds)
    raise AssertionError(f"Key '{key}' did not expire within {timeout_seconds:.1f}s")


async def test_redis_roundtrip(redis_settings) -> None:
    cache = await create_redis_cache(redis_settings)
    try:
        await cache.set("test_key", "hello")
        value = await cache.get("test_key")
        assert value == "hello"

        exists = await cache.exists("test_key")
        assert exists is True

        deleted = await cache.delete("test_key")
        assert deleted == 1

        exists_after = await cache.exists("test_key")
        assert exists_after is False

        assert (await cache.health_check()).healthy is True
    finally:
        await cache.close()


async def test_redis_ttl(redis_settings) -> None:
    cache = await create_redis_cache(redis_settings)
    try:
        await cache.set("ttl_key", "expires", ttl_seconds=1)
        value = await cache.get("ttl_key")
        assert value == "expires"

        await _wait_until_key_absent(cache, "ttl_key", timeout_seconds=5.0)
    finally:
        await cache.close()
