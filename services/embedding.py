from sentence_transformers import SentenceTransformer

# Load the model at the module level to avoid reloading it multiple times
model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str) -> list:
    """
    Generate an embedding vector for a single text.
    
    Args:
        text (str): The input text to generate the embedding for.
    
    Returns:
        list: The embedding vector as a list of floats.
    """
    embedding = model.encode(text)
    return embedding.tolist()

def generate_embeddings_batch(texts: list) -> list:
    """
    Generate embedding vectors for a batch of texts.
    
    Args:
        texts (list): A list of input texts to generate embeddings for.
    
    Returns:
        list: A list of embedding vectors, each as a list of floats.
    """
    embeddings = model.encode(texts)
    return [embedding.tolist() for embedding in embeddings]