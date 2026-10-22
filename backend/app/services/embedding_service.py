from threading import Lock


MODEL_NAME = "BAAI/bge-base-en-v1.5"

_embedding_model = None
_embedding_lock = Lock()


def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        # Prevent concurrent cold requests from loading duplicate model instances.
        with _embedding_lock:
            if _embedding_model is None:
                from sentence_transformers import SentenceTransformer
                _embedding_model = SentenceTransformer(MODEL_NAME)

    return _embedding_model


def generate_embedding(text: str) -> list[float]:
    model = get_embedding_model()

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()