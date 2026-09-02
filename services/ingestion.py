from sqlalchemy.orm import Session
from pathlib import Path
from app.services.pdf_processor import extract_text_from_pdf, chunk_text
from app.services.embedding import generate_embeddings_batch
from app.services.llm import generate_document_summary
from app.models import Document, Chunk

def process_pdf(file_path: str, db_session: Session):
    # Extract text from PDF
    text = extract_text_from_pdf(file_path)
    if not text.strip():
        text = "No readable text extracted from PDF."

    # Generate comprehensive executive summary using LLM
    try:
        summary = generate_document_summary(text)
    except Exception as e:
        print(f"Error generating summary: {e}")
        summary = "Summary generation failed during ingestion."

    # Clean filename (store basename instead of full path)
    filename = Path(file_path).name

    # Create a new Document record with precomputed summary
    new_document = Document(
        filename=filename,
        content_type="application/pdf",
        summary=summary
    )
    db_session.add(new_document)
    db_session.commit()
    document_id = new_document.id

    # Chunk the text
    chunks = chunk_text(text)

    # Hierarchical RAG: Include the summary as a meta-chunk for semantic search
    all_chunks_to_embed = [f"Document Overview / Summary:\n{summary}"] + chunks

    # Generate embeddings in batch
    embeddings = generate_embeddings_batch(all_chunks_to_embed)

    # Create Chunk records and save to DB
    for chunk, embedding in zip(all_chunks_to_embed, embeddings):
        new_chunk = Chunk(document_id=document_id, content=chunk, embedding=embedding)
        db_session.add(new_chunk)
    db_session.commit()

    return new_document

