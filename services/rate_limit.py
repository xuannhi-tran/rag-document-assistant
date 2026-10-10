import time
from collections import defaultdict, deque
from threading import Lock
from fastapi import HTTPException


class SlidingWindowLimiter:
    """In-memory limiter. Single-process only (matches the single uvicorn worker
    in the Dockerfile); use Redis if you ever scale out."""

    def __init__(self):
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int, label: str = "requests"):
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= now - window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                retry = int(window_seconds - (now - hits[0])) + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many {label}. Please try again in {retry} seconds.",
                    headers={"Retry-After": str(retry)},
                )
            hits.append(now)
            if len(self._hits) > 10000:  # drop idle keys
                for k in [k for k, v in self._hits.items() if not v]:
                    del self._hits[k]

    def reset(self):
        with self._lock:
            self._hits.clear()


limiter = SlidingWindowLimiter()
