"""Hybrid search: vector similarity (pgvector) + keyword search (Postgres full-text),
combined with Reciprocal Rank Fusion (RRF).

Run:  python src/search.py "why did the market data job fail?"
"""
import sys
from dataclasses import dataclass

from config import RERANK_CANDIDATES
from db import connect
from embeddings import embed_query

HYBRID_SQL = """
WITH vec AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> %(qvec)s) AS rnk
    FROM doc_chunks
    ORDER BY embedding <=> %(qvec)s
    LIMIT 20
),
kw AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv, q) DESC) AS rnk
    -- OR the keywords: requiring ALL words (AND) misses chunks that answer the question in other words
    FROM doc_chunks, to_tsquery('english', replace(plainto_tsquery('english', %(qtext)s)::text, '&', '|')) AS q
    WHERE tsv @@ q
    ORDER BY ts_rank_cd(tsv, q) DESC
    LIMIT 20
)
SELECT c.id, c.doc_name, c.section, c.content,
       COALESCE(1.0 / (60 + vec.rnk), 0) + COALESCE(1.0 / (60 + kw.rnk), 0) AS score
FROM doc_chunks c
LEFT JOIN vec ON vec.id = c.id
LEFT JOIN kw  ON kw.id  = c.id
WHERE vec.id IS NOT NULL OR kw.id IS NOT NULL
ORDER BY score DESC
LIMIT %(k)s
"""


@dataclass
class Hit:
    id: int
    doc_name: str
    section: str
    content: str
    score: float


def hybrid_search(question: str, k: int, conn) -> list[Hit]:
    params = {"qvec": embed_query(question), "qtext": question, "k": k}
    return [Hit(*row) for row in conn.execute(HYBRID_SQL, params).fetchall()]


def search(question: str, k: int = 5, conn=None, rerank: bool = True) -> list[Hit]:
    """Hybrid search; with rerank=True, re-score the top candidates with a cross-encoder."""
    if conn is None:
        with connect() as c:
            return search(question, k, c, rerank)
    if not rerank:
        return hybrid_search(question, k, conn)
    from rerank import rerank_scores  # imported lazily: only loads the model when used

    candidates = hybrid_search(question, RERANK_CANDIDATES, conn)
    scores = rerank_scores(question, [f"{h.section}\n{h.content}" for h in candidates])
    for h, s in zip(candidates, scores):
        h.score = s
    return sorted(candidates, key=lambda h: h.score, reverse=True)[:k]


if __name__ == "__main__":
    q = " ".join(a for a in sys.argv[1:] if not a.startswith("--")) or "How do I force a full reload of a NiFi flow?"
    print(f"Question: {q}\n")
    for i, h in enumerate(search(q, rerank="--no-rerank" not in sys.argv), 1):
        print(f"[{i}] score={h.score:.4f}  {h.doc_name}  |  {h.section}")
        print("    " + h.content[:200].replace("\n", " ") + "...\n")
