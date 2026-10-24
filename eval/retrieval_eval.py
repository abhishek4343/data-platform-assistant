"""Retrieval evaluation: does the chunk that answers each question come back, and how high?

Run:  python eval/retrieval_eval.py
Compares two set-ups on the same questions:
  hybrid           vector + keyword search fused with RRF
  hybrid + rerank  the same top 20 candidates re-scored by a cross-encoder
Metrics:
  hit@1  share of questions where the right chunk is ranked first
  hit@5  share where it appears in the top 5 (what the LLM actually sees)
  MRR    mean reciprocal rank (1 = always first, 0.5 = usually second, ...)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from db import connect  # noqa: E402
from search import search  # noqa: E402

QUESTIONS = Path(__file__).with_name("questions.json")


def rank_of_answer(hits, case) -> int | None:
    for i, h in enumerate(hits, 1):
        if h.doc_name == case["doc"] and case["section"].lower() in h.section.lower():
            return i
    return None


def metrics(ranks: list) -> str:
    n = len(ranks)
    hit1 = sum(r == 1 for r in ranks) / n
    hit5 = sum(r is not None for r in ranks) / n
    mrr = sum(1 / r for r in ranks if r) / n
    return f"hit@1 = {hit1:.0%} | hit@5 = {hit5:.0%} | MRR = {mrr:.2f}"


def main() -> None:
    cases = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    results = {"hybrid": [], "hybrid + rerank": []}
    with connect() as conn:
        for case in cases:
            for name, use_rerank in (("hybrid", False), ("hybrid + rerank", True)):
                hits = search(case["question"], k=5, conn=conn, rerank=use_rerank)
                results[name].append(rank_of_answer(hits, case))

    fmt = lambda r: f"rank {r}" if r else "MISS"  # noqa: E731
    print(f"{'hybrid':>8} {'+rerank':>8}  question")
    for case, a, b in zip(cases, results["hybrid"], results["hybrid + rerank"]):
        print(f"{fmt(a):>8} {fmt(b):>8}  {case['question']}")
    print()
    for name, ranks in results.items():
        print(f"{name:<16} {metrics(ranks)}")


if __name__ == "__main__":
    main()
