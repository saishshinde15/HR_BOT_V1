"""Production-scale RAGAS style evaluation.

Generates or loads an evaluation dataset, runs retrieval + answer generation,
computes semantic grounding and basic retrieval metrics across many questions.
Outputs JSON and CSV summaries.
"""
from __future__ import annotations
import json, math, csv, time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple
import concurrent.futures

from hr_bot.tools.hybrid_rag_tool import HybridRAGRetriever
from hr_bot.crew import HrBot
from langchain_huggingface import HuggingFaceEmbeddings

# Lightweight local embedding-based metrics (no external APIs)
emb_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})

def embed(texts: List[str]):
    return emb_model.embed_documents(texts)

def cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return dot / (na * nb + 1e-9)

@dataclass
class ExampleResult:
    question: str
    answer: str
    sources: List[str]
    retrieval_contexts: List[str]
    support_ratio: float
    avg_ctx_similarity: float
    latency_s: float


def sentence_split(text: str) -> List[str]:
    import re
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if len(s.strip()) > 25]


def extract_sources(answer: str) -> List[str]:
    lower = answer.lower()
    if "sources:" not in lower:
        return []
    tail = answer[lower.rfind("sources:"):]
    parts = tail.split(":",1)[-1]
    sources = [s.strip().strip('* ,') for s in parts.split(',') if s.strip()]
    # basic normalization: keep .docx only
    return [s for s in sources if s.endswith('.docx')]


def support_score(answer: str, contexts: List[str], sent_sim_threshold: float = 0.60) -> float:
    sentences = sentence_split(answer)
    if not sentences:
        return 0.0
    if not contexts:
        return 0.0
    ctx_embs = embed(contexts)
    supported = 0
    for s in sentences:
        s_emb = embed([s])[0]
        best = max(cosine(s_emb, c) for c in ctx_embs)
        if best >= sent_sim_threshold:
            supported += 1
    return supported / len(sentences)


def avg_context_similarity(answer: str, contexts: List[str]) -> float:
    sentences = sentence_split(answer)
    if not sentences or not contexts:
        return 0.0
    ctx_embs = embed(contexts)
    sims = []
    for s in sentences:
        s_emb = embed([s])[0]
        best = max(cosine(s_emb, c) for c in ctx_embs)
        sims.append(best)
    return sum(sims)/len(sims)


def jaccard(a: str, b: str) -> float:
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def compute_retrieval_metrics(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute retrieval-only metrics when dataset contains gold labels.

    Metrics:
      - doc_recall@k: fraction where gold `source` appears in results
      - avg_best_snippet_sim: average best Jaccard similarity between any retrieved context and gold_snippet
      - avg_best_snippet_cosine: same but using embedding cosine similarity
    """
    if not dataset:
        return {
            'doc_recall_at_k': 0.0,
            'avg_best_snippet_sim': 0.0,
            'avg_best_snippet_cosine': 0.0,
        }

    has_gold = all(('source' in r and 'gold_snippet' in r) for r in dataset)
    if not has_gold:
        return {
            'doc_recall_at_k': 0.0,
            'avg_best_snippet_sim': 0.0,
            'avg_best_snippet_cosine': 0.0,
        }

    # Build per-row stats
    recalls = 0
    best_jaccards: List[float] = []
    best_cosines: List[float] = []
    for row in dataset:
        gold_src = row['source']
        gold_snip = row['gold_snippet']
        raw = row.get('raw', {})
        results = raw.get('results', [])
        if any(r.get('source') == gold_src for r in results):
            recalls += 1
        contexts = [r.get('preview', '') for r in results]
        if contexts:
            # Jaccard
            best_j = max((jaccard(gold_snip, c) for c in contexts), default=0.0)
            best_jaccards.append(best_j)
            # Cosine on embeddings
            gold_emb = embed([gold_snip])[0]
            ctx_embs = embed(contexts)
            best_c = max((cosine(gold_emb, c) for c in ctx_embs), default=0.0)
            best_cosines.append(best_c)
        else:
            best_jaccards.append(0.0)
            best_cosines.append(0.0)

    n = len(dataset)
    return {
        'doc_recall_at_k': recalls / n,
        'avg_best_snippet_sim': sum(best_jaccards) / n if best_jaccards else 0.0,
        'avg_best_snippet_cosine': sum(best_cosines) / n if best_cosines else 0.0,
    }


def load_dataset(path: str) -> List[Dict[str, Any]]:
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def evaluate_question(q: str, retriever: HybridRAGRetriever, top_k: int = 5) -> Dict[str, Any]:
    meta = retriever.hybrid_search_with_metadata(q, top_k=top_k)
    contexts = [r['preview'] for r in meta['results']]
    return {"question": q, "contexts": contexts, "raw": meta}


def run_retrieval(dataset: List[Dict[str, Any]], retriever: HybridRAGRetriever, top_k: int | None = None, max_workers: int = 6):
    if top_k is None:
        top_k = retriever.top_k_results
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(evaluate_question, row['question'], retriever, top_k): row for row in dataset}
        for fut in concurrent.futures.as_completed(futs):
            results.append(fut.result())
    # merge back
    question_map = {r['question']: r for r in results}
    for row in dataset:
        row.update(question_map[row['question']])


def generate_answers(dataset: List[Dict[str, Any]], max_retries: int = 3, backoff: float = 8.0):
    bot = HrBot()
    crew = bot.crew()
    for row in dataset:
        attempt = 0
        while attempt <= max_retries:
            try:
                start = time.time()
                result = crew.kickoff(inputs={"query": row['question'], "context": ""})
                latency = time.time() - start
                answer = str(result)
                row['answer'] = answer
                row['latency_s'] = latency
                row['sources_extracted'] = extract_sources(answer)
                break
            except Exception as e:
                attempt += 1
                if attempt > max_retries:
                    row['answer'] = f"<ERROR: {e.__class__.__name__}>"
                    row['latency_s'] = 0.0
                    row['sources_extracted'] = []
                else:
                    # crude rate limit/backoff handling
                    time.sleep(backoff * attempt)


def compute_metrics(dataset: List[Dict[str, Any]], sent_threshold: float = 0.60) -> Dict[str, Any]:
    support_scores = []
    avg_ctx_sims = []
    latencies = []
    per_example: List[ExampleResult] = []
    for row in dataset:
        answer = row.get('answer', '')
        contexts = row.get('contexts', [])
        sr = support_score(answer, contexts, sent_sim_threshold=sent_threshold)
        acs = avg_context_similarity(answer, contexts)
        support_scores.append(sr)
        avg_ctx_sims.append(acs)
        latencies.append(row.get('latency_s', 0.0))
        per_example.append(ExampleResult(
            question=row['question'],
            answer=answer[:4000],
            sources=row.get('sources_extracted', []),
            retrieval_contexts=contexts,
            support_ratio=sr,
            avg_ctx_similarity=acs,
            latency_s=row.get('latency_s', 0.0)
        ))
    metrics = {
        'num_examples': len(dataset),
        'avg_support_ratio': sum(support_scores)/len(support_scores) if support_scores else 0.0,
        'avg_context_similarity': sum(avg_ctx_sims)/len(avg_ctx_sims) if avg_ctx_sims else 0.0,
        'p95_latency_s': sorted(latencies)[int(0.95*len(latencies))-1] if latencies else 0.0,
        'median_latency_s': sorted(latencies)[len(latencies)//2] if latencies else 0.0,
    }
    return metrics, per_example


def save_outputs(metrics: Dict[str, Any], per_example: List[ExampleResult] | None, out_dir: str = 'data/eval/production'):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    # CSV
    if per_example:
        with (out / 'examples.csv').open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=list(asdict(per_example[0]).keys()))
            w.writeheader()
            for ex in per_example:
                w.writerow(asdict(ex))
    print('Saved metrics and examples to', out)


def main(dataset_path: str = 'data/eval/eval_dataset.jsonl', limit: int | None = None, answer: bool = True, retrieval_only: bool = False, top_k: int | None = None):
    dataset = load_dataset(dataset_path)
    if limit:
        dataset = dataset[:limit]
    if not dataset:
        print('Dataset empty. Run generate_eval first.')
        return
    retriever = HybridRAGRetriever(data_dir='data')
    retriever.build_index()
    print(f"Running retrieval for {len(dataset)} questions ...")
    run_retrieval(dataset, retriever, top_k=top_k)
    if answer and not retrieval_only:
        print("Generating answers ...")
        generate_answers(dataset)
    print("Computing metrics ...")
    metrics: Dict[str, Any] = {}
    per_example: List[ExampleResult] | None = None
    # Retrieval metrics if gold labels available
    retrieval_m = compute_retrieval_metrics(dataset)
    metrics.update(retrieval_m)
    # Answer grounding metrics if answers present
    if answer and not retrieval_only:
        ans_metrics, per_example = compute_metrics(dataset)
        metrics.update(ans_metrics)
    # Always include dataset size
    metrics['num_examples'] = len(dataset)
    save_outputs(metrics, per_example)
    print(json.dumps(metrics, indent=2))

if __name__ == '__main__':  # pragma: no cover
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', type=str, default='data/eval/eval_dataset.jsonl')
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--no-answer', action='store_true')
    p.add_argument('--retrieval-only', action='store_true', help='Skip answer generation and only evaluate retrieval contexts')
    p.add_argument('--top-k', type=int, default=None, help='Override top_k for retrieval evaluation')
    args = p.parse_args()
    main(args.dataset, args.limit, answer=not args.no_answer, retrieval_only=args.retrieval_only, top_k=args.top_k)
