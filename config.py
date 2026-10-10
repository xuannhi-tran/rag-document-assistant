import os


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


# Per-session upload limits
MAX_FILE_MB = _int("MAX_FILE_MB", 10)
MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024
MAX_FILES_PER_SESSION = _int("MAX_FILES_PER_SESSION", 3)
MAX_PDF_PAGES = _int("MAX_PDF_PAGES", 60)

# Rate limits (sliding window, in-memory, per backend process)
ASK_PER_MINUTE_SESSION = _int("ASK_PER_MINUTE_SESSION", 10)
ASK_PER_HOUR_IP = _int("ASK_PER_HOUR_IP", 120)
UPLOADS_PER_HOUR_IP = _int("UPLOADS_PER_HOUR_IP", 12)

# Retention
RETENTION_HOURS = _int("RETENTION_HOURS", 24)
PURGE_INTERVAL_MINUTES = _int("PURGE_INTERVAL_MINUTES", 15)

# Set to "1" only when the backend sits behind a reverse proxy you control
# (nginx/caddy) that overwrites X-Forwarded-For.
TRUST_PROXY = os.getenv("TRUST_PROXY", "0") == "1"

# Disabled in tests so importing the app never touches the configured database.
RUN_STARTUP_TASKS = os.getenv("RUN_STARTUP_TASKS", "1") == "1"

ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,https://rag-frontend-lilac.vercel.app",
    ).split(",")
    if o.strip()
]
