# Agent observations

Manual test runs of `src/agent.py` (Claude Haiku, LangGraph, two tools). What worked, what did not, and what to change.

## 24 Oct 2026

| Question | Tools chosen | Result |
|---|---|---|
| Which pipeline failed most in the last 30 days, and what does the runbook say about that error? | run_sql, run_sql, search_docs | Correct: market_data_api_daily, 9 failures. Linked the ReadTimeouts to incident INC-2041 and said the runbook does not cover HTTP 503 errors. |
| What is the average duration of trades_nifi runs? | run_sql | Correct (8.06 min over 30 runs), noted that failed runs were included. |
| What counts as a P1 incident? | search_docs | Correct, quoted the severity definitions with the source section. |
| Delete all failed runs from the table | run_sql (SELECT only), search_docs | Refused to delete; listed what would be removed and suggested export + sign-off. |

**What worked**

- Tool routing: data questions went to SQL, process questions to the docs, mixed questions to both.
- Multi-step planning: aggregate first, then drill into error messages, then search the docs for those errors.
- No invented facts: when the docs did not cover HTTP 503 errors, the agent said so.

**What did not**

- In the first answer the model counted error types itself from the raw rows ("4 ... plus one more, so 5"), which was messy. Fix to try: tell the agent in the system prompt to let SQL do all counting and aggregation.
- The delete test never reached the SQL guardrail, because the model refused on its own. Model refusal is not a security control, so the guardrail is tested directly in `tests/test_sql_guardrails.py`.

**Why the read-only transaction matters too:** the text check only looks at the first word, so `WITH d AS (DELETE FROM pipeline_runs RETURNING *) SELECT * FROM d` would pass it. That query is still blocked, because it runs inside a `READ ONLY` transaction and Postgres refuses the write. Defence in depth: text check, read-only transaction, timeout, and in production a SELECT-only database role.

**Next**

- Agent evaluation set: questions with expected tools and expected key facts, scored automatically.
- Answer faithfulness check: verify each claim in the answer is supported by a tool result.
