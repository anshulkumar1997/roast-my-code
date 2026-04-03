import os
import time

import redis.asyncio as aioredis
from fastapi import HTTPException, status

# ── Redis connection ──────────────────────────────────────────────
# In dev, Redis runs in Docker alongside the app
# In prod, point this to your Redis instance (e.g. Redis Cloud free tier)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# One shared async Redis client for the whole app
_redis: aioredis.Redis = None


async def connect_redis():
    global _redis
    _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    print("Connected to Redis")


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        print("Redis connection closed")


async def check_rate_limit(key: str, limit: int, window_seconds: int):
    """
    Sliding window rate limiter using Redis.

    key            — unique identifier (e.g. "user:anshul@example.com:roast")
    limit          — max requests allowed in the window
    window_seconds — how long the window lasts

    Raises HTTP 429 if the limit is exceeded, with retry_after in seconds.
    """
    now = time.time()
    window_start = now - window_seconds

    pipe = _redis.pipeline()
    # Remove requests older than the window
    pipe.zremrangebyscore(key, 0, window_start)
    # Count remaining requests in window
    pipe.zcard(key)
    # Add this request with current timestamp as score
    pipe.zadd(key, {str(now): now})
    # Set expiry so Redis auto-cleans old keys
    pipe.expire(key, window_seconds)
    results = await pipe.execute()

    count = results[1]  # count BEFORE adding this request

    if count >= limit:
        # Find when the oldest request in window expires
        oldest = await _redis.zrange(key, 0, 0, withscores=True)
        if oldest:
            retry_after = int(window_seconds - (now - oldest[0][1])) + 1
        else:
            retry_after = window_seconds

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            },
        )

    return limit - count - 1  # remaining requests


def get_user_email_from_request(request) -> str:
    """
    Rate limit key function — always by logged-in user's email.
    If somehow called without a valid token, reject immediately.
    """
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer ") :]
        from app.services.auth import decode_access_token

        email = decode_access_token(token)
        if email:
            return f"user:{email}"

    # Should never reach here since routes are protected by get_current_user
    # but just in case, raise 401 rather than silently falling back to IP
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )
