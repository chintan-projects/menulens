"""Dish name embedding generation using sentence-transformers.

Uses all-MiniLM-L6-v2 (384-dim) for fast, local dish name similarity.
"""

import numpy as np
from numpy.typing import NDArray
from sentence_transformers import SentenceTransformer

from src.common.logger import get_logger

logger = get_logger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Get or initialize the sentence-transformer model.

    Returns:
        Loaded SentenceTransformer model (cached after first call).
    """
    global _model  # noqa: PLW0603
    if _model is None:
        logger.info("loading_embedding_model", model=MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_dish_name(dish_name: str) -> NDArray[np.float32]:
    """Generate an embedding for a single dish name.

    Args:
        dish_name: The dish name to embed.

    Returns:
        384-dimensional float32 embedding vector.
    """
    model = get_model()
    embedding: NDArray[np.float32] = model.encode(
        dish_name, convert_to_numpy=True, normalize_embeddings=True
    )
    return embedding


def embed_dish_names(dish_names: list[str]) -> NDArray[np.float32]:
    """Generate embeddings for a batch of dish names.

    Args:
        dish_names: List of dish names to embed.

    Returns:
        Array of shape (N, 384) with normalized embeddings.
    """
    model = get_model()
    embeddings: NDArray[np.float32] = model.encode(
        dish_names, convert_to_numpy=True, normalize_embeddings=True, batch_size=64
    )
    return embeddings
