from app.database import SessionLocal
from app.models import Chunk
from app.services.embedding import generate_embeddings_batch

db = SessionLocal()
chunks = db.query(Chunk).all()
print(f"Found {len(chunks)} chunks to re-embed.")

batch_size = 30
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i+batch_size]
    texts = [c.content for c in batch]
    embeddings = generate_embeddings_batch(texts)
    for c, emb in zip(batch, embeddings):
        c.embedding = emb
    db.commit()
    print(f"Progress: {min(i+batch_size, len(chunks))}/{len(chunks)}")
print("All chunks successfully re-embedded!")

