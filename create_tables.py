from sqlalchemy import text
from app.database import Base, engine
from app.models import Document, Chunk

Base.metadata.create_all(bind=engine)

# Ensure summary column exists in existing database deployments
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS summary TEXT;"))
        conn.commit()
except Exception as e:
    print(f"Note: Could not run migration alter table: {e}")