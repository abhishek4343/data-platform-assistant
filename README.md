# Data Platform Assistant

An AI assistant that answers questions about a data platform's runbooks and incident reports, using **Retrieval-Augmented Generation (RAG)** on **Postgres + pgvector** and **Claude**.

> All documents in `docs/` are synthetic and describe a fictional company.

## How it works

1. **Ingest**: markdown documents are split into chunks by section, embedded locally with `BAAI/bge-small-en-v1.5` (fastembed, CPU), and stored in Postgres with pgvector.
2. **Hybrid search + reranking**: each question is matched two ways, by vector similarity (cosine, HNSW index) and by keyword search (Postgres full-text, GIN index). The two rankings are combined with Reciprocal Rank Fusion, then the top 20 candidates are re-scored by a cross-encoder.
3. **Answer**: the top chunks are sent to Claude, which answers only from those sources and cites them as [1], [2].
4. **Agent** (LangGraph): for each question Claude decides whether to search the docs, run read-only SQL on a `pipeline_runs` table, or both, loops until it has enough evidence, then answers. SQL guardrails: single SELECT only, read-only transaction, 5-second timeout, 50-row cap.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # then fill in DATABASE_URL and ANTHROPIC_API_KEY
```

You need a Postgres database with the `vector` extension (for example a free Neon project).

## Usage

```bash
python src/ingest.py                                     # load and embed docs/
python src/search.py "how do I force a full reload?"     # retrieval only, no API key needed
python src/ask.py "why did the market data job fail?"    # answer with citations
python eval/retrieval_eval.py                            # hit@1, hit@5 and MRR on 12 test questions
python src/seed_runs.py                                  # create synthetic pipeline_runs data (30 days)
python src/agent.py "Which pipeline failed most last month and what does the runbook say?"
```

What was tried and what changed is logged in [notes/retrieval-experiments.md](notes/retrieval-experiments.md).

## Roadmap

- [x] Chunking, local embeddings, pgvector storage
- [x] Hybrid search (vector + full-text, RRF)
- [x] Claude answers with citations
- [x] LangGraph agent that chooses between document search and SQL over pipeline-run tables
- [x] Retrieval evaluation set (hit@1, hit@5, MRR)
- [x] Reranking with a cross-encoder
- [ ] Answer faithfulness evaluation
