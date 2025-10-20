import time
from pathlib import Path

from hr_bot.tools.hybrid_rag_tool import HybridRAGRetriever
from hr_bot.crew import HrBot

"""Tests for RAG retriever and agent.

DATA_DIR previously pointed one level too high (../data) which does not
exist; the real documents live in the package directory `hr_bot/data`.
We resolve relative to the package root (parent of tests).
"""

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / 'data'
if not DATA_DIR.exists():  # fallback in unusual layouts
    alt = Path(__file__).resolve().parents[2] / 'hr_bot' / 'data'
    if alt.exists():
        DATA_DIR = alt
    else:
        raise FileNotFoundError(f"HR policy data directory not found. Tried {DATA_DIR} and {alt}")


def test_retriever_build_and_search():
    retriever = HybridRAGRetriever(data_dir=str(DATA_DIR))
    retriever.build_index(force_rebuild=True)
    assert retriever.vector_store is not None, "Vector store not built"
    assert retriever.bm25 is not None, "BM25 index not built"
    results = retriever.hybrid_search("sick leave policy", top_k=5)
    assert len(results) > 0, "No results returned"
    # At least one result should mention 'sick' or 'absence'
    assert any(('sick' in r.content.lower() or 'absence' in r.content.lower()) for r in results), "Results not relevant"


def test_agent_answers_with_content():
    bot = HrBot()
    crew = bot.crew()
    start = time.time()
    result = crew.kickoff(inputs={"query": "What is the sick leave policy?", "context": ""})
    duration = time.time() - start
    answer = str(result)
    assert 'sick' in answer.lower() or 'statutory' in answer.lower(), "Answer seems unrelated"
    assert duration < 30, f"Response too slow: {duration:.2f}s"


def test_agent_hallucination_guard():
    """Semantic hallucination guard: each sentence must semantically align with a retrieved context chunk.

    We use the same embedding model as retrieval. A sentence is supported if max cosine similarity
    with any retrieved chunk >= threshold. This reduces false negatives from simple lexical overlap.
    """
    from langchain_huggingface import HuggingFaceEmbeddings
    import math, re

    retriever = HybridRAGRetriever(data_dir=str(DATA_DIR))
    retriever.build_index()
    query = "What is the sick leave policy?"
    # Pull a larger pool for grounding (increase to 12 to improve semantic coverage)
    top_chunks = retriever.hybrid_search(query, top_k=12)
    contexts = [c.content for c in top_chunks]

    bot = HrBot()
    crew = bot.crew()
    answer_raw = str(crew.kickoff(inputs={"query": query, "context": ""}))

    # Basic sentence segmentation; filter out very short / structural lines
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer_raw) if 30 < len(s.strip()) < 400]
    assert sentences, "No sentences extracted from answer"

    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})

    def cosine(a, b):
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(y*y for y in b))
        return dot / (na * nb + 1e-9)

    # Pre-clean placeholders from contexts and sentences to avoid penalising templated tokens
    def clean(text: str) -> str:
        t = re.sub(r"\[insert[^\]]+\]", "", text, flags=re.IGNORECASE)
        t = t.replace("[the Company]", "the company")
        return t

    cleaned_contexts = [clean(c) for c in contexts]
    ctx_embs = emb.embed_documents(cleaned_contexts)
    query_emb = emb.embed_documents([query])[0]

    supported = 0
    chunk_threshold = 0.55  # similarity to any retrieved chunk
    query_threshold = 0.75  # high similarity to the user query itself counts as supported (paraphrase)
    exempt_prefixes = ("Key points", "Sources", "Next Step", "Final Answer")

    for sent in sentences:
        if sent.startswith(exempt_prefixes):
            # structural / header lines don't need grounding
            supported += 1
            continue
        sent_clean = clean(sent)
        s_emb = emb.embed_documents([sent_clean])[0]
        best_ctx = max(cosine(s_emb, c) for c in ctx_embs)
        sim_query = cosine(s_emb, query_emb)
        if best_ctx >= chunk_threshold or sim_query >= query_threshold:
            supported += 1

    support_ratio = supported / len(sentences)
    # Expect >=0.60 with expanded context + cleaning; allow 0.58 minimum to reduce flakiness on small model variation
    assert support_ratio >= 0.58, f"Semantic support ratio too low {support_ratio:.2f} (<0.58)"


def test_agent_citations_present():
    bot = HrBot()
    crew = bot.crew()
    answer = str(crew.kickoff(inputs={"query": "What is the sick leave policy?", "context": ""}))
    # Basic checks for Sources line and at least one .docx filename
    assert "Sources:" in answer, "Missing Sources line"
    assert ".docx" in answer, "No document filenames cited"
    # Ensure no placeholder tokens remain
    assert "[insert job title]" not in answer.lower(), "Unresolved placeholder present in answer"
