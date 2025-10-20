import json
from pathlib import Path
from typing import List, Dict
from statistics import mean

from hr_bot.crew import HrBot
from hr_bot.tools.hybrid_rag_tool import HybridRAGRetriever

# Simple similarity: token overlap Jaccard

def jaccard(a: str, b: str) -> float:
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def load_dataset(path: str) -> List[Dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items

def evaluate_retriever(dataset: List[Dict], retriever: HybridRAGRetriever, k: int = 5) -> Dict:
    retrieved_scores = []
    recall_hits = 0
    for ex in dataset:
        q = ex["question"]
        results = retriever.hybrid_search(q, top_k=k)
        # Check if source doc present in top-k
        if any(r.source == ex["source"] for r in results):
            recall_hits += 1
        # Best content similarity vs gold snippet
        best_sim = 0.0
        for r in results:
            sim = jaccard(r.content, ex["gold_snippet"])
            if sim > best_sim:
                best_sim = sim
        retrieved_scores.append(best_sim)
    return {
        "retriever_doc_recall@k": recall_hits / len(dataset) if dataset else 0.0,
        "retriever_avg_snippet_sim": mean(retrieved_scores) if retrieved_scores else 0.0,
    }

def evaluate_agent(dataset: List[Dict]) -> Dict:
    bot = HrBot()
    crew = bot.crew()
    sims = []
    for ex in dataset:
        result = crew.kickoff(inputs={"query": ex["question"], "context": ""})
        answer = str(result)
        sims.append(jaccard(answer, ex["gold_snippet"]))
    return {"agent_avg_answer_snippet_sim": mean(sims) if sims else 0.0}

def main(dataset_path: str = "data/eval/eval_dataset.jsonl"):
    dataset = load_dataset(dataset_path)
    if not dataset:
        print("Dataset empty. Run: uv run generate_eval")
        return
    # Prepare retriever directly
    r = HybridRAGRetriever(data_dir="data")
    r.build_index(force_rebuild=True)
    retriever_metrics = evaluate_retriever(dataset, r)
    agent_metrics = evaluate_agent(dataset)

    metrics = {**retriever_metrics, **agent_metrics, "num_examples": len(dataset)}
    out_path = Path("data/eval/metrics.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("Metrics:\n" + json.dumps(metrics, indent=2))

if __name__ == "__main__":  # pragma: no cover
    main()
