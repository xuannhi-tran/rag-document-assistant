from app.models import Chunk
from app.services.embedding import generate_embedding


def retrieve_chunks(question, db_session, top_k=5):
    # Generate embedding for the question
    question_embedding = generate_embedding(question)
    
    # Query the Chunk table, order by cosine distance, and limit results
    chunks = (
        db_session.query(Chunk)
        .order_by(Chunk.embedding.cosine_distance(question_embedding))
        .limit(top_k)
        .all()
    )
    
    # Return the text content of the retrieved chunks
    return [chunk.content for chunk in chunks]