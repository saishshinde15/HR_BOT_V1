import json
import re
from pathlib import Path
from typing import List, Dict
from docx import Document as DocxDocument

# Simple heuristic Q generation templates
TEMPLATES = [
    (re.compile(r"sick(ness)?|absence", re.I), "What is the sick leave policy?"),
    (re.compile(r"matern|patern|parental", re.I), "What are the parental leave entitlements?"),
    (re.compile(r"redundancy", re.I), "How does the redundancy process work?"),
    (re.compile(r"retire", re.I), "What is the retirement policy?"),
    (re.compile(r"internet|email|social", re.I), "What is acceptable use of company email and social media?"),
    (re.compile(r"alcohol|drug", re.I), "What is the substance (alcohol/drugs) policy?"),
    (re.compile(r"home\s*working|remote", re.I), "What are the home working rules?"),
    (re.compile(r"notice", re.I), "What are the notice period requirements?"),
]

def extract_text(doc_path: Path) -> str:
    d = DocxDocument(str(doc_path))
    parts = []
    for p in d.paragraphs:
        t = p.text.strip()
        if t:
            parts.append(t)
    return "\n".join(parts)

def pick_questions(text: str) -> List[str]:
    qs = []
    for pattern, q in TEMPLATES:
        if pattern.search(text):
            qs.append(q)
    return list(dict.fromkeys(qs))  # dedupe preserve order

def main(out_path: str = "data/eval/eval_dataset.jsonl", data_dir: str = "data"):
    data_root = Path(data_dir)
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    records: List[Dict] = []
    for docx in sorted(data_root.glob("*.docx")):
        raw = extract_text(docx)
        questions = pick_questions(raw)
        # For now gold answer is a trimmed snippet (first 40 words) around first keyword match
        for q in questions:
            # naive snippet: first 80 words of document containing keyword(s)
            words = raw.split()
            snippet = " ".join(words[:80])
            records.append({
                "source": docx.name,
                "question": q,
                "gold_snippet": snippet,
            })

    with out_file.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} examples to {out_file}")

if __name__ == "__main__":  # pragma: no cover
    main()
