from sqlalchemy import text

from app.database import Base, engine
from app.models import Chunk, Document  # noqa: F401 (registers models on Base)


def ensure_schema():
    """Idempotent: creates missing tables and upgrades existing deployments."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS summary TEXT;"))
        conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS size_bytes INTEGER;"))
        conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS session_id VARCHAR(36);"))
        conn.execute(text("ALTER TABLE chunks ADD COLUMN IF NOT EXISTS session_id VARCHAR(36);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_session_id ON documents (session_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chunks_session_id ON chunks (session_id);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chunks_document_id ON chunks (document_id);"))


if __name__ == "__main__":
    ensure_schema()
    print("Schema is up to date.")