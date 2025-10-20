# Production Guide — HR Bot

This guide captures how to run, evaluate, and tune the HR Bot for production.

## Quickstart (uv)

```bash
cd hr_bot
# Retrieval-only production evaluation (no LLM cost)
export TOP_K=12 RERANK_ENABLED=1 RERANK_TOP_N=50
uv run -- python -m hr_bot.eval.ragas_production_eval --dataset data/eval/eval_dataset.jsonl --retrieval-only --top-k 12

# Run the agent (CrewAI)
uv run -- crewai run
```

## Retrieval Metrics (Oct 2025)
- doc_recall@k (k=12): 0.8261
- avg_best_snippet_jaccard: 0.2556
- avg_best_snippet_cosine: 0.6399
- num_examples: 46

Configuration behind these numbers:
- EnsembleRetriever + CrossEncoder reranker enabled
- CHUNK_SIZE=700, CHUNK_OVERLAP=200
- RRF_CANDIDATE_MULTIPLIER=8
- TOP_K=12

## Tuning Knobs
- Retrieval: `TOP_K` (12–15), `RRF_CANDIDATE_MULTIPLIER` (8–10)
- Weights: `BM25_WEIGHT`, `VECTOR_WEIGHT`
- Reranker: `RERANK_ENABLED` (1/0), `RERANK_TOP_N` (30–50), `RERANK_BATCH_SIZE` (16), `RERANK_TIME_BUDGET_MS` (e.g., 150),
  `RERANK_BIENCODER_PRUNE` (1), `RERANK_BIENCODER_N` (24)
- Chunking: `CHUNK_SIZE` (700), `CHUNK_OVERLAP` (200)

## SLO Guidance
- Retrieval quality: recall@k ≥ 0.85 (k=12–15), cosine ≥ 0.70
- Latency: p50 < 800ms retrieval, p95 < 1.5s; end-to-end < 2.5s
- CI: Fail if recall drops > 5% from last green; keep hallucination guard tests

## Troubleshooting
- “Index not built” after restart: indexes load and retrievers are rebuilt automatically
- Slow rerank: lower `RERANK_TOP_N` or enable pruning; increase batch size if CPU allows
- Table-heavy precision: consider row-aware chunking (python-docx) for matrix policies
