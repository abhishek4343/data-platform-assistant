"""Load every markdown file in docs/, chunk it, embed it and store it in Postgres.

Run:  python src/ingest.py
Safe to re-run: existing chunks for a document are replaced.
"""
from chunking import chunk_markdown
from config import DOCS_DIR
from db import connect, create_schema
from embeddings import embed_documents


def main() -> None:
    files = sorted(DOCS_DIR.glob("*.md"))
    if not files:
        raise SystemExit(f"No .md files found in {DOCS_DIR}")

    with connect() as conn:
        create_schema(conn)
        total = 0
        for path in files:
            chunks = chunk_markdown(path.name, path.read_text(encoding="utf-8"))
            vectors = embed_documents([f"{c.section}\n{c.content}" for c in chunks])
            with conn.transaction():
                conn.execute("DELETE FROM doc_chunks WHERE doc_name = %s", (path.name,))
                with conn.cursor() as cur:
                    cur.executemany(
                        """INSERT INTO doc_chunks (doc_name, section, chunk_index, content, embedding)
                           VALUES (%s, %s, %s, %s, %s)""",
                        [(c.doc_name, c.section, c.chunk_index, c.content, v) for c, v in zip(chunks, vectors)],
                    )
            total += len(chunks)
            print(f"{path.name}: {len(chunks)} chunks")
        print(f"Done. {total} chunks stored.")


if __name__ == "__main__":
    main()
