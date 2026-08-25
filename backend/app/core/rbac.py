import json
import uuid
from typing import Dict, List, Optional, Set, Union
from fastapi import Depends, HTTPException, status
import redis.asyncio as aioredis
import structlog

from app.core.redis import get_redis_client
from app.core.tenant_middleware import TenantContext, get_tenant_context

logger = structlog.get_logger(__name__)

RBAC_CACHE_TTL_SECONDS = 15 * 60  # 15 minutes (900s)

# System RBAC Role to Permission Mapping Matrix
DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "OWNER": ["*"],
    "TENANT_OWNER": ["*", "settings:write", "tenant:billing"],
    "ADMIN": [
        "crm:read",
        "crm:write",
        "crm:delete",
        "settings:read",
        "settings:write",
        "users:read",
        "users:write",
        "users:delete",
        "user:manage",
        "reports:read",
        "reports:export",
    ],
    "TENANT_ADMIN": [
        "crm:read",
        "crm:write",
        "crm:delete",
        "settings:read",
        "settings:write",
        "users:read",
        "users:write",
        "users:delete",
        "user:manage",
        "reports:read",
        "reports:export",
    ],
    "MEMBER": [
        "crm:read",
        "crm:write",
        "reports:read",
    ],
    "DOMAIN_MEMBER": [
        "crm:read",
        "crm:write",
        "reports:read",
    ],
    "VIEWER": [
        "crm:read",
        "reports:read",
    ],
}


class RBACError(HTTPException):
    def __init__(self, detail: str = "Permission denied", code: str = "ERR_RBAC_001"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": code, "detail": detail},
        )


def get_rbac_cache_key(org_id: Union[str, uuid.UUID], user_id: Union[str, uuid.UUID]) -> str:
    """Generate RBAC permission cache key following system contract pattern: org:{org_id}:usr:{user_id}:perms."""
    return f"org:{str(org_id)}:usr:{str(user_id)}:perms"


async def get_user_permissions(
    redis: aioredis.Redis,
    org_id: Union[str, uuid.UUID],
    user_id: Union[str, uuid.UUID],
    role: str,
) -> Set[str]:
    """
    Retrieve user permission set for an organization.
    Uses Redis cache with pattern org:{org_id}:usr:{user_id}:perms and 15-minute TTL.
    """
    cache_key = get_rbac_cache_key(org_id, user_id)
    cached_perms = await redis.smembers(cache_key)

    if cached_perms:
        return set(cached_perms)

    # Cache miss: load permissions from matrix based on role
    role_perms = DEFAULT_ROLE_PERMISSIONS.get(role.upper(), [])
    perm_set = set(role_perms)

    if perm_set:
        await redis.sadd(cache_key, *list(perm_set))
        await redis.expire(cache_key, RBAC_CACHE_TTL_SECONDS)
        logger.info("rbac_permissions_cached", cache_key=cache_key, role=role, count=len(perm_set))

    return perm_set


async def evict_user_permissions_cache(
    redis: aioredis.Redis,
    org_id: Union[str, uuid.UUID],
    user_id: Union[str, uuid.UUID],
) -> bool:
    """Evict cached permissions key in Redis when user role is updated or deactivated."""
    cache_key = get_rbac_cache_key(org_id, user_id)
    deleted = await redis.delete(cache_key)
    logger.info("rbac_permissions_cache_evicted", cache_key=cache_key, deleted=bool(deleted))
    return bool(deleted)


class RequiresPermission:
    """Declarative dependency wrapper to enforce RBAC permission requirements."""

    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(
        self,
        context: TenantContext = Depends(get_tenant_context),
        redis: aioredis.Redis = Depends(get_redis_client),
    ) -> TenantContext:
        perms = await get_user_permissions(
            redis=redis,
            org_id=context.organization_id,
            user_id=context.user_id,
            role=context.role,
        )

        has_perm = (
            "*" in perms
            or self.required_permission in perms
            or self._check_wildcard(perms, self.required_permission)
        )

        if not has_perm:
            raise RBACError(
                f"Operation requires permission '{self.required_permission}'",
                code="ERR_RBAC_001",
            )

        return context

    def _check_wildcard(self, perms: Set[str], required: str) -> bool:
        for p in perms:
            if p.endswith(":*") and required.startswith(p[:-2] + ":"):
                return True
        return False
