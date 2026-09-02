from sentence_transformers import SentenceTransformer

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _model

def generate_embedding(text: str) -> list:
    """
    Generate an embedding vector for a single text.
    """
    model = get_model()
    embedding = model.encode(text)
    return embedding.tolist()

def generate_embeddings_batch(texts: list) -> list:
    """
    Generate embedding vectors for a batch of texts.
    """
    model = get_model()
    embeddings = model.encode(texts)
    return [embedding.tolist() for embedding in embeddings]