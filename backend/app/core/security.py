import os
import uuid
import warnings
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
import jwt
import structlog
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Module-level cache for auto-generated local dev keys
_cached_private_key_pem: Optional[str] = None
_cached_public_key_pem: Optional[str] = None


def generate_rsa_key_pair() -> Tuple[str, str]:
    """Generate a temporary 2048-bit RSA key pair in PEM format."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


def get_rsa_keys() -> Tuple[str, str]:
    """Retrieve RSA private and public keys from settings/env or generate dynamic local dev keys."""
    global _cached_private_key_pem, _cached_public_key_pem

    priv_key = settings.JWT_PRIVATE_KEY
    pub_key = settings.JWT_PUBLIC_KEY

    # Check path settings if raw strings are empty
    if not priv_key and settings.JWT_PRIVATE_KEY_PATH and os.path.exists(settings.JWT_PRIVATE_KEY_PATH):
        try:
            with open(settings.JWT_PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
                priv_key = f.read()
        except Exception:
            pass

    if not pub_key and settings.JWT_PUBLIC_KEY_PATH and os.path.exists(settings.JWT_PUBLIC_KEY_PATH):
        try:
            with open(settings.JWT_PUBLIC_KEY_PATH, "r", encoding="utf-8") as f:
                pub_key = f.read()
        except Exception:
            pass

    if priv_key and pub_key:
        if "\\n" in priv_key:
            priv_key = priv_key.replace("\\n", "\n")
        if "\\n" in pub_key:
            pub_key = pub_key.replace("\\n", "\n")
        return priv_key, pub_key

    # Fallback to generated cached keys for local development
    if _cached_private_key_pem is None or _cached_public_key_pem is None:
        warning_msg = (
            "SECURITY WARNING: JWT_PRIVATE_KEY and JWT_PUBLIC_KEY are not configured. "
            "Dynamically generating a temporary RS256 key pair for local development."
        )
        warnings.warn(warning_msg, UserWarning)
        logger.warning("rsa_keys_generated_dynamically", detail=warning_msg)
        _cached_private_key_pem, _cached_public_key_pem = generate_rsa_key_pair()

    return _cached_private_key_pem, _cached_public_key_pem


def hash_password(password: str) -> str:
    """Hash password using PBKDF2 with SHA256 and a random salt."""
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}${hashed.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored PBKDF2 hash."""
    try:
        salt_hex, hash_hex = hashed_password.split("$")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt, 100000
        )
        return hmac.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False


def create_access_token(
    user_id: Union[uuid.UUID, str],
    email: str,
    roles: List[str],
    token_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, str]:
    """Create RS256 signed access token. Returns (jwt_token, token_id/jti)."""
    priv_key, _ = get_rsa_keys()
    jti = token_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    duration = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    exp = now + duration

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "user_id": str(user_id),
        "email": email,
        "roles": roles,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "type": "access",
    }

    token = jwt.encode(payload, priv_key, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def create_refresh_token(
    user_id: Union[uuid.UUID, str],
    token_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, str]:
    """Create RS256 signed refresh token. Returns (jwt_token, token_id/jti)."""
    priv_key, _ = get_rsa_keys()
    jti = token_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    duration = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    exp = now + duration

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "user_id": str(user_id),
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "type": "refresh",
    }

    token = jwt.encode(payload, priv_key, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and verify RS256 token payload."""
    _, pub_key = get_rsa_keys()
    try:
        payload = jwt.decode(token, pub_key, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")
