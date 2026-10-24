"""Retrieval-Augmented Generation: retrieve chunks, then ask Claude to answer with citations.

Run:  python src/ask.py "What should I check when a COPY INTO fails?"
Needs ANTHROPIC_API_KEY in .env.
"""
import sys

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, require
from search import Hit, search

SYSTEM_PROMPT = (
    "You are a data platform assistant. Answer the question using ONLY the numbered sources provided. "
    "Cite sources inline like [1] or [2][3]. If the sources do not contain the answer, say "
    "\"I don't know based on the available documents.\" Be concise and practical."
)


def format_sources(hits: list[Hit]) -> str:
    return "\n\n".join(
        f"[{i}] ({h.doc_name} | {h.section})\n{h.content}" for i, h in enumerate(hits, 1)
    )


def answer(question: str, hits: list[Hit]) -> str:
    client = anthropic.Anthropic(api_key=require(ANTHROPIC_API_KEY, "ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Sources:\n\n{format_sources(hits)}\n\nQuestion: {question}",
        }],
    )
    return "".join(block.text for block in message.content if block.type == "text")


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "What should I check when a COPY INTO fails?"
    hits = search(q)
    print(f"Question: {q}\n")
    print(answer(q, hits))
    print("\nSources:")
    for i, h in enumerate(hits, 1):
        print(f"  [{i}] {h.doc_name} | {h.section}")
