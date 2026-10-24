"""Tools the agent can call: document search and read-only SQL over pipeline_runs."""
import re

from db import connect
from search import search

TABLE_DESCRIPTION = """Table pipeline_runs (one row per pipeline per day, last 30 days):
  pipeline TEXT, run_date DATE, status TEXT ('success' or 'failed'), started_at TIMESTAMP,
  duration_min NUMERIC, rows_loaded INT, rows_quarantined INT, error_message TEXT (NULL on success).
Pipelines: market_data_api_daily, crm_accounts_sftp, trades_nifi, positions_nifi, risk_reports_mart."""

TOOL_SPECS = [
    {
        "name": "search_docs",
        "description": "Search the data platform runbooks, incident reports and standards. "
                       "Use for how-to, policy, root-cause and process questions.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to look up"}},
            "required": ["query"],
        },
    },
    {
        "name": "run_sql",
        "description": "Run ONE read-only PostgreSQL SELECT query on the pipeline_runs table. "
                       "Use for counts, trends, failures, durations and row volumes.\n" + TABLE_DESCRIPTION,
        "input_schema": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "A single SELECT statement"}},
            "required": ["sql"],
        },
    },
]

MAX_ROWS = 50


def search_docs(query: str) -> str:
    hits = search(query, k=4)
    return "\n\n".join(f"[{h.doc_name} | {h.section}]\n{h.content}" for h in hits) or "No results."


def run_sql(sql: str) -> str:
    """Guardrails: a single SELECT/WITH statement, read-only transaction, 5 s timeout, row cap.
    (In production you would also connect as a database role that only has SELECT rights.)"""
    statement = sql.strip().rstrip(";").strip()
    if ";" in statement:
        return "Rejected: only one statement is allowed."
    if not re.match(r"^(select|with)\b", statement, flags=re.IGNORECASE):
        return "Rejected: only SELECT queries are allowed."
    try:
        with connect() as conn:
            with conn.transaction():
                conn.execute("SET TRANSACTION READ ONLY")
                conn.execute("SET LOCAL statement_timeout = '5s'")
                cur = conn.execute(statement)
                columns = [d.name for d in cur.description]
                rows = cur.fetchmany(MAX_ROWS + 1)
    except Exception as exc:  # return the error to the model so it can fix its query
        return f"SQL error: {exc}"
    lines = [" | ".join(columns)] + [" | ".join(str(v) for v in row) for row in rows[:MAX_ROWS]]
    if len(rows) > MAX_ROWS:
        lines.append(f"... truncated to {MAX_ROWS} rows")
    return "\n".join(lines)


def call_tool(name: str, args: dict) -> str:
    if name == "search_docs":
        return search_docs(args["query"])
    if name == "run_sql":
        return run_sql(args["sql"])
    return f"Unknown tool: {name}"
