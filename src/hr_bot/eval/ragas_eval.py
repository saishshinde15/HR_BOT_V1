import json
from pathlib import Path
from typing import List, Dict

from hr_bot.tools.hybrid_rag_tool import HybridRAGRetriever
from langchain_huggingface import HuggingFaceEmbeddings
import math
from hr_bot.crew import HrBot

# We'll construct a minimal dataset for ragas-like scoring manually (no external API calls here).
# If ragas API objects are available they could be plugged in; fallback is custom precision & support checks.


def build_dataset(questions: List[str], retriever: HybridRAGRetriever, top_k: int = 5, log_path: Path | None = None) -> List[Dict]:
    rows = []
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    for q in questions:
        meta = retriever.hybrid_search_with_metadata(q, top_k=top_k)
        contexts = [r["preview"] for r in meta["results"]]
        row = {"question": q, "contexts": contexts, "raw": meta}
        rows.append(row)
        if log_path:
            with log_path.open("a", encoding="utf-8") as lf:
                lf.write(json.dumps(meta) + "\n")
    return rows


def agent_answers(rows: List[Dict]) -> None:
    bot = HrBot()
    crew = bot.crew()
    for row in rows:
        result = crew.kickoff(inputs={"query": row["question"], "context": ""})
        row["answer"] = str(result)


def sentence_split(text: str) -> List[str]:
    import re
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


emb_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})

def embed(texts: List[str]):
    return emb_model.embed_documents(texts)

def cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    return dot / (na * nb + 1e-9)

def support_score(answer: str, contexts: List[str], sent_sim_threshold: float = 0.60) -> float:
    sentences = sentence_split(answer)
    if not sentences:
        return 0.0
    ctx_embs = embed(contexts) if contexts else []
    supported = 0
    for s in sentences:
        s_emb = embed([s])[0]
        best = max((cosine(s_emb, c) for c in ctx_embs), default=0.0)
        if best >= sent_sim_threshold:
            supported += 1
    return supported / len(sentences)


def main():
    questions = [
        "What is the sick leave policy?",
        "What are the notice period requirements?",
        "What is the redundancy process?",
        "What is acceptable use of company email and social media?",
        "What are the home working rules?",
    ]

    retriever = HybridRAGRetriever(data_dir="data")
    retriever.build_index()

    log_path = Path("data/eval/retrieval_logs.jsonl")
    if log_path.exists():
        log_path.unlink()
    rows = build_dataset(questions, retriever, top_k=5, log_path=log_path)
    agent_answers(rows)

    # Compute naive support score per answer
    for row in rows:
        row["support_score"] = support_score(row.get("answer", ""), row["contexts"], sent_sim_threshold=0.60)

    # Aggregate metrics
    avg_support = sum(r["support_score"] for r in rows) / len(rows)

    out_dir = Path("data/eval")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ragas_like_results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (out_dir / "ragas_like_metrics.json").write_text(json.dumps({"avg_support_score": avg_support}, indent=2), encoding="utf-8")

    print("RAGAS-like metrics:\n" + json.dumps({"avg_support_score": avg_support}, indent=2))

if __name__ == "__main__":  # pragma: no cover
    main()
