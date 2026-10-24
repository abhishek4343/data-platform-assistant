"""Shared settings, loaded from the .env file in the project root."""
import os
from pathlib import Path

from dotenv import load_dotenv

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")  # harmless Windows cache warning

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")

DOCS_DIR = ROOT / "docs"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # small local model, 384 dimensions, runs on CPU
EMBED_DIM = 384
RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"  # small cross-encoder (~80 MB), CPU
RERANK_CANDIDATES = 20  # hybrid search returns this many, the reranker picks the best k

# Chunking: split by markdown section, then cap each chunk at about this many characters.
CHUNK_MAX_CHARS = 900
CHUNK_OVERLAP_CHARS = 150


def require(value: str, name: str) -> str:
    if not value:
        raise SystemExit(f"Missing {name}. Add it to the .env file (see .env.example).")
    return value
