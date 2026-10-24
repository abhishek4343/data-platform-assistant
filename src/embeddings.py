"""Local embeddings with fastembed (no API key, runs on CPU)."""
from functools import lru_cache

import numpy as np
from fastembed import TextEmbedding

from config import EMBED_MODEL, ROOT


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    # First call downloads the model (~100 MB) and caches it locally.
    return TextEmbedding(model_name=EMBED_MODEL, cache_dir=str(ROOT / ".fastembed_cache"))


def embed_documents(texts: list[str]) -> list[np.ndarray]:
    return list(_model().embed(texts))


def embed_query(text: str) -> np.ndarray:
    # bge models work best when queries get this instruction prefix.
    return next(iter(_model().query_embed(text)))
