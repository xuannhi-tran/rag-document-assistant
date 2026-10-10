"""Manual cleanup of legacy rows (uploaded before per-session isolation existed).

    python -m app.purge             # dry run: list what would be deleted (no text printed)
    python -m app.purge --yes       # actually delete legacy rows (session_id IS NULL)
    python -m app.purge --expired --yes   # also delete session rows past retention
"""
import argparse
from sqlalchemy import func
from app.database import SessionLocal
from app.models import Chunk, Document
from app.services.cleanup import delete_documents, purge_expired

parser = argparse.ArgumentParser()
parser.add_argument("--yes", action="store_true", help="perform the deletion")
parser.add_argument("--expired", action="store_true", help="also purge expired session documents")
args = parser.parse_args()

db = SessionLocal()
rows = (
    db.query(Document.id, Document.filename, Document.upload_date, func.count(Chunk.id))
    .outerjoin(Chunk, Chunk.document_id == Document.id)
    .filter(Document.session_id.is_(None))
    .group_by(Document.id)
    .order_by(Document.id)
    .all()
)
print(f"Legacy documents (no session): {len(rows)}")
for r in rows:
    print(f"  id={r[0]} file={r[1]!r} uploaded={r[2]} chunks={r[3]}")

if not args.yes:
    print("Dry run only. Re-run with --yes to delete these rows.")
else:
    n = delete_documents(db, [r[0] for r in rows])
    print(f"Deleted {n} legacy documents (and their chunks).")
    if args.expired:
        print(f"Deleted {purge_expired(db)} expired session documents.")
