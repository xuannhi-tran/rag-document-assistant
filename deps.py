import re
from fastapi import Header, HTTPException, Request
from app import config

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


def get_session_id(x_session_id: str | None = Header(default=None)) -> str:
    """The browser-generated random session id. It is the only credential: every
    document/chunk query is filtered by it, so it must look like a UUID."""
    if not x_session_id or not _UUID_RE.match(x_session_id):
        raise HTTPException(status_code=400, detail="Missing or invalid X-Session-Id header")
    return x_session_id.lower()


def get_client_ip(request: Request) -> str:
    if config.TRUST_PROXY:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
