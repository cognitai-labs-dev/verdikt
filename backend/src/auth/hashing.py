import hashlib
from datetime import datetime, timezone


def sha256_hex(value: str) -> str:
    """Hex-encoded SHA-256 of a string. Used for client secrets and tokens."""
    return hashlib.sha256(value.encode()).hexdigest()


def utcnow() -> datetime:
    """Naive UTC `now`, matching the timezone-less `DateTime` columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
