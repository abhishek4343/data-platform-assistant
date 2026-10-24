# Retrieval experiments log

A record of what was tried, what failed, and what changed. Each entry: the problem, the evidence, the fix, the result.

## Experiment 1: Keyword search used AND matching (24 Oct 2026)

**Setup:** hybrid search = pgvector cosine similarity + Postgres full-text search, fused with Reciprocal Rank Fusion (RRF, k = 60). Keyword query built with `websearch_to_tsquery`, which requires **all** terms to match.

**Problem observed**

| Question | Chunk that answers it | Rank before |
|---|---|---|
| how do I force a full reload of a NiFi flow? | NiFi runbook > How incremental loading works | 5 |
| what happens to rows that fail validation? | Data quality standards > Quarantine | 2 (behind the on-call triage checklist) |

**Root cause:** with AND matching, a chunk had to contain every word of the question. For the reload question no chunk contained all terms, so the keyword side returned nothing and ranking relied on vector similarity alone. For the validation question, the only chunk containing every term was the triage checklist, matched by chance on the word "happened".

**Fix:** build an OR query from the normalised terms (`plainto_tsquery` with `&` replaced by `|`) and let `ts_rank_cd` rank chunks by how well they match.

**Result**

| Question | Rank before | Rank after |
|---|---|---|
| how do I force a full reload of a NiFi flow? | 5 | 3 |
| what happens to rows that fail validation? | 2 | 2 (top 2 are now both correct quarantine rules) |

**Still open:** for the reload question, the answer is one paragraph inside a section titled "How incremental loading works". The keyword side now ranks it first, but the small embedding model ranks it lower, so the fused score lands at 3. It is inside the top 5 that is sent to the LLM, so the final answer is still correct.

## Experiment 2: Baseline evaluation (24 Oct 2026)

12 labelled questions (`eval/questions.json`), hybrid search with OR keyword matching:

**hit@1 = 58% | hit@5 = 83% | MRR = 0.67**

| Question | Rank | Why |
|---|---|---|
| why did the market data job fail? | MISS | The answer chunk talks about a "ReadTimeout" and a "proxy port", not "fail" or "market data". Every chunk of the incident report shares the same title words, so keyword ranking cannot tell them apart, and the embedding model prefers the Summary chunk. |
| what counts as a P1 incident? | MISS | Postgres `ts_rank_cd` has no IDF: the common word "incident" (in every incident report) counts as much as the rare and decisive "P1", so chunks about incidents in general outrank the severity definitions. |
| why did postcodes end up containing city names? | 5 | Same vocabulary gap: the root cause talks about unquoted text fields, while the Detection chunk repeats the question's words. |

**Pattern:** "why" questions whose answer uses different words, and keyword ranking without IDF. Both point to reranking (a model that reads question and answer together) and, later, BM25-style keyword scoring.

## Experiment 3: Cross-encoder reranking

Re-score the top 20 hybrid candidates with `Xenova/ms-marco-MiniLM-L-6-v2` and keep the best 5. Results: run `python eval/retrieval_eval.py`, which prints both set-ups side by side.

## Ideas to try next

1. **Measure first:** an evaluation set (`eval/questions.json`) with hit@1, hit@5 and MRR, so every change is compared on the same questions.
2. **BM25 keyword scoring:** replace `ts_rank_cd` with a ranking that down-weights common words.
3. **Smaller chunks:** split long sections by paragraph so each chunk covers one idea.
4. **Query rewriting:** let the LLM rewrite vague questions into search-friendly terms before retrieval.
