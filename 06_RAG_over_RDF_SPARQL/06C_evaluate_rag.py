"""
06C_evaluate_rag.py

This script evaluates the RDF/SPARQL RAG system on at least five questions.

It compares:
1. A simple baseline answer.
2. The RDF/SPARQL RAG answer.

Outputs:
    06_RAG_over_RDF_SPARQL/outputs/rag_evaluation.csv
    06_RAG_over_RDF_SPARQL/outputs/rag_evaluation.md
"""

from pathlib import Path
import sys
import importlib.util

import pandas as pd
from rdflib import Graph


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_KB = PROJECT_ROOT / "01_Data" / "kb_outputs" / "expanded_kb.ttl"

OUTPUT_DIR = PROJECT_ROOT / "06_RAG_over_RDF_SPARQL" / "outputs"
EVAL_CSV_FILE = OUTPUT_DIR / "rag_evaluation.csv"
EVAL_MD_FILE = OUTPUT_DIR / "rag_evaluation.md"

DEMO_SCRIPT = PROJECT_ROOT / "06_RAG_over_RDF_SPARQL" / "06B_rag_sparql_demo.py"


# =============================
# IMPORT DEMO FUNCTIONS
# =============================

spec = importlib.util.spec_from_file_location("rag_demo", DEMO_SCRIPT)
rag_demo = importlib.util.module_from_spec(spec)
sys.modules["rag_demo"] = rag_demo
spec.loader.exec_module(rag_demo)


# =============================
# EVALUATION QUESTIONS
# =============================

EVALUATION_SET = [
    {
        "question": "Which technique cues affect biomechanical concepts?",
        "baseline_answer": "Technique cues such as grip and bar path may affect biomechanics, but the baseline does not query the KB.",
        "expected_signal": "grip width affects horizontal flexion demands",
    },
    {
        "question": "Which muscles act on joints?",
        "baseline_answer": "Muscles such as triceps and pectoralis major act on joints during bench press.",
        "expected_signal": "triceps acts on elbow; pectoralis major acts on shoulder",
    },
    {
        "question": "What force does the bar apply?",
        "baseline_answer": "The bar applies force during the bench press.",
        "expected_signal": "bar applies downward force",
    },
    {
        "question": "What does grip width influence?",
        "baseline_answer": "Grip width can influence bench press mechanics.",
        "expected_signal": "grip width influences horizontal flexion demands",
    },
    {
        "question": "Which muscles extend joints?",
        "baseline_answer": "The triceps usually extend the elbow.",
        "expected_signal": "triceps extends elbow",
    },
    {
        "question": "What facts are known about the triceps?",
        "baseline_answer": "The triceps are involved in pressing movements.",
        "expected_signal": "triceps extends elbow or targets muscle facts",
    },
]


# =============================
# SCORING
# =============================

def score_answer(answer: str, expected_signal: str) -> int:
    """
    Simple qualitative score:
    1 = answer contains at least one important expected keyword
    0 = answer does not
    """
    answer_low = answer.lower()
    expected_words = [
        word.strip().lower()
        for word in expected_signal.replace(";", " ").split()
        if len(word.strip()) > 3
    ]

    hits = sum(1 for word in expected_words if word in answer_low)

    return 1 if hits >= 2 else 0


def escape_md(text: str) -> str:
    text = str(text).replace("\n", "<br>")
    return text


# =============================
# MAIN
# =============================

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_KB.exists():
        raise FileNotFoundError(
            f"Expanded KB not found: {INPUT_KB}\n"
            "Run 03C_expand_kb.py first."
        )

    graph = Graph()
    graph.parse(INPUT_KB, format="turtle")

    rows = []

    for item in EVALUATION_SET:
        question = item["question"]
        baseline = item["baseline_answer"]
        expected = item["expected_signal"]

        rag_result = rag_demo.answer_question(graph, question, verbose=False)
        rag_answer = rag_result["answer"]

        baseline_score = score_answer(baseline, expected)
        rag_score = score_answer(rag_answer, expected)

        rows.append({
            "question": question,
            "baseline_answer": baseline,
            "rag_answer": rag_answer,
            "expected_signal": expected,
            "baseline_score": baseline_score,
            "rag_score": rag_score,
            "rag_better_or_equal": rag_score >= baseline_score,
            "sparql_success": rag_result["success"],
            "self_repair_used": rag_result["repair_used"],
            "fallback_used": rag_result["fallback_used"],
            "query_type": rag_result["query_type"],
            "generated_sparql": rag_result["sparql"],
        })

    df = pd.DataFrame(rows)
    df.to_csv(EVAL_CSV_FILE, index=False, encoding="utf-8")

    baseline_total = int(df["baseline_score"].sum())
    rag_total = int(df["rag_score"].sum())

    md = []
    md.append("# RAG over RDF/SPARQL Evaluation\n")
    md.append("## Evaluation Setup\n")
    md.append("The system was evaluated on natural-language questions about the bench press RDF knowledge base.")
    md.append("")
    md.append("For each question, we compared:")
    md.append("")
    md.append("- **Baseline answer**: generic keyword-style answer without querying RDF.")
    md.append("- **RAG/SPARQL answer**: answer generated by translating the question into SPARQL and querying the RDF KB.")
    md.append("")
    md.append("## Summary\n")
    md.append(f"- Number of questions: `{len(df)}`")
    md.append(f"- Baseline score: `{baseline_total}/{len(df)}`")
    md.append(f"- RAG/SPARQL score: `{rag_total}/{len(df)}`")
    md.append("")
    md.append("## Results\n")
    md.append("| Question | Baseline answer | RAG/SPARQL answer | Baseline score | RAG score | Repair used | Fallback used |")
    md.append("|---|---|---|---:|---:|---|---|")

    for _, row in df.iterrows():
        md.append(
            f"| {escape_md(row['question'])} "
            f"| {escape_md(row['baseline_answer'])} "
            f"| {escape_md(row['rag_answer'])} "
            f"| {row['baseline_score']} "
            f"| {row['rag_score']} "
            f"| {row['self_repair_used']} "
            f"| {row['fallback_used']} |"
        )

    md.append("")
    md.append("## NL→SPARQL Prompt Template\n")
    md.append("```text")
    md.append(rag_demo.NL_TO_SPARQL_PROMPT_TEMPLATE.strip())
    md.append("```")
    md.append("")
    md.append("## Self-Repair Mechanism\n")
    md.append("The self-repair mechanism handles:")
    md.append("")
    md.append("- missing prefixes")
    md.append("- predicate casing errors such as `appliesforce` → `appliesForce`")
    md.append("- empty results by retrying with broader fallback queries")
    md.append("- broad keyword search over project KB triples")
    md.append("")
    md.append("## Reflection\n")
    md.append("The RDF/SPARQL RAG system provides grounded answers from the structured KB.")
    md.append("Compared with the baseline, the RAG answers are more explicit because they return exact KB triples.")
    md.append("The main limitation is that the NL→SPARQL component is rule-based rather than a full LLM.")
    md.append("However, it is reproducible, transparent, and includes a self-repair fallback mechanism.")

    EVAL_MD_FILE.write_text("\n".join(md), encoding="utf-8")

    print("RAG evaluation complete.")
    print(f"CSV saved to: {EVAL_CSV_FILE}")
    print(f"Markdown saved to: {EVAL_MD_FILE}")
    print(f"Baseline score: {baseline_total}/{len(df)}")
    print(f"RAG score: {rag_total}/{len(df)}")


if __name__ == "__main__":
    main()