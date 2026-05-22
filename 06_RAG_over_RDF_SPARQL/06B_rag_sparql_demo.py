"""
06B_rag_sparql_demo.py

Interactive RAG over RDF/SPARQL demo.

This script loads the expanded RDF knowledge base and allows the user to ask
natural-language questions. The system maps the question to a SPARQL query,
runs it on the RDF graph, and repairs/falls back if the first query fails or
returns no result.

Input:
    01_Data/kb_outputs/expanded_kb.ttl

Output:
    Terminal demo for screenshot.
"""

from pathlib import Path
from typing import Tuple, List

from rdflib import Graph, Namespace, RDFS


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_KB = PROJECT_ROOT / "01_Data" / "kb_outputs" / "expanded_kb.ttl"

OUTPUT_DIR = PROJECT_ROOT / "06_RAG_over_RDF_SPARQL" / "outputs"


# =============================
# NAMESPACES
# =============================

EX = Namespace("http://example.org/benchpress-kg/")


PREFIXES = """
PREFIX ex: <http://example.org/benchpress-kg/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""


# =============================
# PROMPT TEMPLATE
# =============================

NL_TO_SPARQL_PROMPT_TEMPLATE = """
You are an RDF/SPARQL assistant for a bench press biomechanics knowledge graph.

Task:
Convert the user question into a SPARQL query.

Rules:
1. Use only the namespace ex: <http://example.org/benchpress-kg/>.
2. Use only known ontology classes and predicates.
3. Return only a valid SPARQL SELECT query.
4. Prefer specific predicates such as:
   - ex:targetsMuscle
   - ex:actsOnJoint
   - ex:affectsBiomechanics
   - ex:appliesForce
   - ex:extends
   - ex:flexes
   - ex:requires
   - ex:influences
   - ex:relatedTo
5. If the question is broad, return a query that searches connected triples.

User question:
{question}
"""


# =============================
# QUERY GENERATION
# =============================

def generate_sparql(question: str) -> Tuple[str, str]:
    """
    Lightweight rule-based NL to SPARQL mapping.

    This replaces an external LLM to keep the project reproducible.
    Returns:
        query_type, sparql_query
    """
    q = question.lower().strip()

    if "technique" in q and ("biomechanic" in q or "affect" in q):
        return "technique_affects_biomechanics", PREFIXES + """
SELECT ?cueLabel ?conceptLabel WHERE {
    ?cue a ex:TechniqueCue .
    ?concept a ex:BiomechanicalConcept .
    ?cue ex:affectsBiomechanics ?concept .
    OPTIONAL { ?cue rdfs:label ?cueLabel . }
    OPTIONAL { ?concept rdfs:label ?conceptLabel . }
}
"""

    if "important technique" in q or "important cue" in q:
        return "important_technique_cues", PREFIXES + """
SELECT ?cueLabel WHERE {
    ?cue a ex:ImportantTechniqueCue .
    OPTIONAL { ?cue rdfs:label ?cueLabel . }
}
"""

    if "muscle" in q and ("joint" in q or "act" in q):
        return "muscle_acts_on_joint", PREFIXES + """
SELECT ?muscleLabel ?jointLabel WHERE {
    ?muscle a ex:Muscle .
    ?joint a ex:Joint .
    ?muscle ex:actsOnJoint ?joint .
    OPTIONAL { ?muscle rdfs:label ?muscleLabel . }
    OPTIONAL { ?joint rdfs:label ?jointLabel . }
}
"""

    if "triceps" in q:
        return "triceps_facts", PREFIXES + """
SELECT ?predicate ?objectLabel WHERE {
    ex:triceps ?predicate ?object .
    OPTIONAL { ?object rdfs:label ?objectLabel . }
}
LIMIT 20
"""

    if "pectoralis" in q or "pec" in q or "chest" in q:
        return "pectoralis_facts", PREFIXES + """
SELECT ?predicate ?objectLabel WHERE {
    ex:pectoralis_major ?predicate ?object .
    OPTIONAL { ?object rdfs:label ?objectLabel . }
}
LIMIT 20
"""

    if "bar" in q and ("apply" in q or "force" in q):
        return "bar_force", PREFIXES + """
SELECT ?objectLabel WHERE {
    ex:bar ex:appliesForce ?object .
    OPTIONAL { ?object rdfs:label ?objectLabel . }
}
"""

    if "grip" in q:
        return "grip_width_facts", PREFIXES + """
SELECT ?predicate ?objectLabel WHERE {
    ex:grip_width ?predicate ?object .
    OPTIONAL { ?object rdfs:label ?objectLabel . }
}
LIMIT 20
"""

    if "extend" in q:
        return "extends_facts", PREFIXES + """
SELECT ?subjectLabel ?objectLabel WHERE {
    ?subject ex:extends ?object .
    OPTIONAL { ?subject rdfs:label ?subjectLabel . }
    OPTIONAL { ?object rdfs:label ?objectLabel . }
}
"""

    if "flex" in q:
        return "flexes_facts", PREFIXES + """
SELECT ?subjectLabel ?objectLabel WHERE {
    ?subject ex:flexes ?object .
    OPTIONAL { ?subject rdfs:label ?subjectLabel . }
    OPTIONAL { ?object rdfs:label ?objectLabel . }
}
"""

    return "broad_search", PREFIXES + """
SELECT ?subjectLabel ?predicate ?objectLabel WHERE {
    ?subject ?predicate ?object .
    FILTER(STRSTARTS(STR(?subject), "http://example.org/benchpress-kg/"))
    FILTER(STRSTARTS(STR(?predicate), "http://example.org/benchpress-kg/"))
    FILTER(STRSTARTS(STR(?object), "http://example.org/benchpress-kg/"))
    OPTIONAL { ?subject rdfs:label ?subjectLabel . }
    OPTIONAL { ?object rdfs:label ?objectLabel . }
}
LIMIT 20
"""


# =============================
# SELF-REPAIR
# =============================

def repair_query(query: str) -> str:
    """
    Basic self-repair mechanism.

    Repairs:
    - missing prefixes
    - lower-case predicate variants
    - unknown/case-inconsistent predicates
    """
    repaired = query

    if "PREFIX ex:" not in repaired:
        repaired = PREFIXES + "\n" + repaired

    predicate_repairs = {
        "ex:appliesforce": "ex:appliesForce",
        "ex:targetsmuscle": "ex:targetsMuscle",
        "ex:affectsbiomechanics": "ex:affectsBiomechanics",
        "ex:actsonjoint": "ex:actsOnJoint",
    }

    for wrong, correct in predicate_repairs.items():
        repaired = repaired.replace(wrong, correct)

    return repaired


def fallback_query(question: str) -> str:
    """
    Broader fallback query if the first query returns no answers.
    """
    keywords = []

    q = question.lower()

    for keyword in [
        "triceps",
        "pectoralis",
        "bar",
        "grip",
        "shoulder",
        "elbow",
        "bench",
        "force",
        "muscle",
        "joint",
    ]:
        if keyword in q:
            keywords.append(keyword)

    if not keywords:
        return PREFIXES + """
SELECT ?subjectLabel ?predicate ?objectLabel WHERE {
    ?subject ?predicate ?object .
    FILTER(STRSTARTS(STR(?subject), "http://example.org/benchpress-kg/"))
    FILTER(STRSTARTS(STR(?predicate), "http://example.org/benchpress-kg/"))
    FILTER(STRSTARTS(STR(?object), "http://example.org/benchpress-kg/"))
    OPTIONAL { ?subject rdfs:label ?subjectLabel . }
    OPTIONAL { ?object rdfs:label ?objectLabel . }
}
LIMIT 10
"""

    filters = " || ".join([
        f'CONTAINS(LCASE(STR(?subjectLabel)), "{kw}") || CONTAINS(LCASE(STR(?objectLabel)), "{kw}")'
        for kw in keywords
    ])

    return PREFIXES + f"""
SELECT ?subjectLabel ?predicate ?objectLabel WHERE {{
    ?subject ?predicate ?object .
    FILTER(STRSTARTS(STR(?subject), "http://example.org/benchpress-kg/"))
    FILTER(STRSTARTS(STR(?predicate), "http://example.org/benchpress-kg/"))
    FILTER(STRSTARTS(STR(?object), "http://example.org/benchpress-kg/"))
    OPTIONAL {{ ?subject rdfs:label ?subjectLabel . }}
    OPTIONAL {{ ?object rdfs:label ?objectLabel . }}
    FILTER({filters})
}}
LIMIT 10
"""


# =============================
# EXECUTION + ANSWER FORMAT
# =============================

def value_to_text(value) -> str:
    if value is None:
        return ""

    value = str(value)

    if value.startswith(str(EX)):
        return value.split("/")[-1]

    return value


def run_query(graph: Graph, query: str) -> Tuple[bool, List[dict], str]:
    try:
        results = graph.query(query)

        rows = []

        for row in results:
            row_dict = {}

            for var, value in zip(results.vars, row):
                row_dict[str(var)] = value_to_text(value)

            rows.append(row_dict)

        return True, rows, ""

    except Exception as e:
        return False, [], str(e)


def format_answer(query_type: str, rows: List[dict]) -> str:
    if not rows:
        return "No answer found in the RDF knowledge base."

    lines = []

    if query_type == "technique_affects_biomechanics":
        lines.append("Technique cues affecting biomechanical concepts:")
        for row in rows:
            lines.append(f"- {row.get('cueLabel', '')} affects {row.get('conceptLabel', '')}")

    elif query_type == "muscle_acts_on_joint":
        lines.append("Muscles acting on joints:")
        for row in rows:
            lines.append(f"- {row.get('muscleLabel', '')} acts on {row.get('jointLabel', '')}")

    elif query_type == "bar_force":
        lines.append("The bar applies:")
        for row in rows:
            lines.append(f"- {row.get('objectLabel', '')}")

    elif query_type in {"triceps_facts", "pectoralis_facts", "grip_width_facts"}:
        lines.append("Facts found in the RDF KB:")
        for row in rows:
            pred = row.get("predicate", "").split("/")[-1]
            obj = row.get("objectLabel", "")
            lines.append(f"- {pred} → {obj}")

    elif query_type == "extends_facts":
        lines.append("Extension facts:")
        for row in rows:
            lines.append(f"- {row.get('subjectLabel', '')} extends {row.get('objectLabel', '')}")

    elif query_type == "flexes_facts":
        lines.append("Flexion facts:")
        for row in rows:
            lines.append(f"- {row.get('subjectLabel', '')} flexes {row.get('objectLabel', '')}")

    elif query_type == "important_technique_cues":
        lines.append("Important technique cues:")
        for row in rows:
            lines.append(f"- {row.get('cueLabel', '')}")

    else:
        lines.append("RDF triples found:")
        for row in rows:
            pred = row.get("predicate", "").split("/")[-1]
            lines.append(
                f"- {row.get('subjectLabel', '')} — {pred} — {row.get('objectLabel', '')}"
            )

    return "\n".join(lines)


def answer_question(graph: Graph, question: str, verbose: bool = True) -> dict:
    query_type, sparql = generate_sparql(question)

    success, rows, error = run_query(graph, sparql)

    repair_used = False
    fallback_used = False

    if not success:
        repair_used = True
        repaired = repair_query(sparql)
        success, rows, error = run_query(graph, repaired)
        sparql = repaired

    if success and not rows:
        fallback_used = True
        fallback = fallback_query(question)
        success, rows, error = run_query(graph, fallback)
        sparql = fallback
        query_type = "fallback_search"

    answer = format_answer(query_type, rows)

    result = {
        "question": question,
        "query_type": query_type,
        "sparql": sparql,
        "success": success,
        "rows": rows,
        "error": error,
        "repair_used": repair_used,
        "fallback_used": fallback_used,
        "answer": answer,
    }

    if verbose:
        print("\n" + "=" * 80)
        print(f"Question: {question}")
        print("=" * 80)
        print("\nGenerated SPARQL:")
        print(sparql)
        print("\nAnswer:")
        print(answer)
        print(f"\nSelf-repair used: {repair_used}")
        print(f"Fallback used: {fallback_used}")

    return result


# =============================
# MAIN DEMO
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

    print("RAG over RDF/SPARQL Demo")
    print("=" * 80)
    print("Ask questions about the bench press knowledge base.")
    print("Type 'exit' to quit.")
    print()
    print("Example questions:")
    print("- Which technique cues affect biomechanical concepts?")
    print("- Which muscles act on joints?")
    print("- What force does the bar apply?")
    print("- What does grip width influence?")
    print("- Which muscles extend joints?")
    print("=" * 80)

    while True:
        question = input("\nQuestion: ").strip()

        if question.lower() in {"exit", "quit", "q"}:
            print("Exiting demo.")
            break

        if not question:
            continue

        answer_question(graph, question, verbose=True)


if __name__ == "__main__":
    main()