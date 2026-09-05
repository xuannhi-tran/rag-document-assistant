from sqlalchemy import text

from app.database import Base, engine
from app.models import Chunk, Document

with engine.begin() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

Base.metadata.create_all(bind=engine)

# Backwards-compatible migration for existing deployments.
with engine.begin() as connection:
    connection.execute(
        text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS summary TEXT;")
    )
