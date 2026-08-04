import redis.asyncio as redis
import hashlib
import json
from app.core.config import settings
from app.core.logging import logger

redis_client: redis.Redis = None

async def get_redis_client() -> redis.Redis:
    """Get or create Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        logger.info("Redis client initialized.")
    return redis_client

def get_cache_key(problem: str, question: str, answer: str) -> str:
    """Generate a cache key for a Gemini response."""
    content = f"{problem}:{question}:{answer}"
    hash_obj = hashlib.sha256(content.encode())
    return f"gemini:{hash_obj.hexdigest()}"

async def get_cached_response(key: str) -> dict | None:
    """Retrieve cached response from Redis."""
    client = await get_redis_client()
    data = await client.get(key)
    if data:
        return json.loads(data)
    return None

async def set_cached_response(key: str, response: dict, ttl_seconds: int = 604800) -> None:
    """Store response in Redis with TTL (default 7 days)."""
    client = await get_redis_client()
    await client.setex(key, ttl_seconds, json.dumps(response))