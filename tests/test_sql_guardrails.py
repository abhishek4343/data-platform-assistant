"""Checks that the SQL tool rejects anything that is not a single SELECT.

Run:  python tests/test_sql_guardrails.py
These cases are rejected before any database connection is made.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tools import run_sql  # noqa: E402

REJECTED = [
    "DELETE FROM pipeline_runs WHERE status = 'failed'",
    "DROP TABLE pipeline_runs",
    "UPDATE pipeline_runs SET status = 'success'",
    "SELECT 1; DROP TABLE pipeline_runs",
    "INSERT INTO pipeline_runs (pipeline) VALUES ('x')",
    "  truncate pipeline_runs",
]

failures = 0
for sql in REJECTED:
    result = run_sql(sql)
    ok = result.startswith("Rejected")
    failures += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {sql}\n      -> {result}")

print(f"\n{len(REJECTED) - failures}/{len(REJECTED)} passed")
sys.exit(1 if failures else 0)
