"""Database helpers: connection and schema for Postgres + pgvector."""
import psycopg
from pgvector.psycopg import register_vector

from config import DATABASE_URL, EMBED_DIM, require

SCHEMA_SQL = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS doc_chunks (
    id          BIGSERIAL PRIMARY KEY,
    doc_name    TEXT NOT NULL,
    section     TEXT NOT NULL,
    chunk_index INT  NOT NULL,
    content     TEXT NOT NULL,
    embedding   VECTOR({EMBED_DIM}) NOT NULL,
    tsv         TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', section || ' ' || content)) STORED,
    UNIQUE (doc_name, chunk_index)
);

-- HNSW index for fast approximate cosine-similarity search
CREATE INDEX IF NOT EXISTS doc_chunks_embedding_hnsw
    ON doc_chunks USING hnsw (embedding vector_cosine_ops);

-- GIN index for keyword (full-text) search
CREATE INDEX IF NOT EXISTS doc_chunks_tsv_gin
    ON doc_chunks USING gin (tsv);
"""


def connect() -> psycopg.Connection:
    # prepare_threshold=None: safe with connection poolers such as Neon's PgBouncer endpoint
    conn = psycopg.connect(require(DATABASE_URL, "DATABASE_URL"), autocommit=True, prepare_threshold=None)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def create_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA_SQL)
