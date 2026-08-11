import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger(__name__)

DEFAULT_SESSION_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def get_session_key(user_id: Union[str, Any], token_id: str) -> str:
    """Generate session key strictly following system contract pattern: sess:{user_id}:{token_id}."""
    return f"sess:{str(user_id)}:{token_id}"


async def create_session(
    redis: aioredis.Redis,
    user_id: Union[str, Any],
    token_id: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    ttl_seconds: int = DEFAULT_SESSION_TTL_SECONDS,
) -> str:
    """Write session record to Redis with specified TTL (default 7 days)."""
    key = get_session_key(user_id, token_id)
    session_data: Dict[str, Any] = {
        "user_id": str(user_id),
        "token_id": token_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ip_address": ip_address,
        "user_agent": user_agent,
        "status": "active",
    }
    await redis.set(key, json.dumps(session_data), ex=ttl_seconds)
    logger.info("redis_session_created", session_key=key, user_id=str(user_id))
    return key


async def get_session(
    redis: aioredis.Redis, user_id: Union[str, Any], token_id: str
) -> Optional[Dict[str, Any]]:
    """Retrieve session record from Redis if active."""
    key = get_session_key(user_id, token_id)
    raw = await redis.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


async def is_session_active(
    redis: aioredis.Redis, user_id: Union[str, Any], token_id: str
) -> bool:
    """Check if session is present and valid in Redis."""
    key = get_session_key(user_id, token_id)
    return await redis.exists(key) > 0


async def revoke_session(
    redis: aioredis.Redis, user_id: Union[str, Any], token_id: str
) -> bool:
    """Revoke (delete) specific session record from Redis."""
    key = get_session_key(user_id, token_id)
    result = await redis.delete(key)
    logger.info("redis_session_revoked", session_key=key, deleted=bool(result))
    return bool(result)


async def revoke_all_user_sessions(
    redis: aioredis.Redis, user_id: Union[str, Any]
) -> int:
    """Revoke all active sessions for a given user in Redis (e.g. on password change)."""
    pattern = f"sess:{str(user_id)}:*"
    keys = []
    async for k in redis.scan_iter(match=pattern):
        keys.append(k)

    if keys:
        deleted = await redis.delete(*keys)
        logger.info("redis_all_user_sessions_revoked", user_id=str(user_id), count=deleted)
        return deleted
    return 0
