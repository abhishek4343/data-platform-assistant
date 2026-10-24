"""Cross-encoder reranking: re-score candidate chunks by reading question and chunk together.

Embeddings compare question and chunk separately, so they miss answers that use different
words (for example a "why did it fail?" question whose answer talks about a proxy port).
A cross-encoder reads both texts at once and scores how well the chunk answers the question.
It is slower, so it only re-scores the top candidates from hybrid search.
"""
from functools import lru_cache

from fastembed.rerank.cross_encoder import TextCrossEncoder

from config import RERANK_MODEL, ROOT


@lru_cache(maxsize=1)
def _model() -> TextCrossEncoder:
    return TextCrossEncoder(model_name=RERANK_MODEL, cache_dir=str(ROOT / ".fastembed_cache"))


def rerank_scores(question: str, passages: list[str]) -> list[float]:
    return [float(s) for s in _model().rerank(question, passages)]
