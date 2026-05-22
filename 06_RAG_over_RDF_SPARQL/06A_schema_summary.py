"""
06A_schema_summary.py

This script generates a schema summary from the expanded RDF knowledge base.

Input:
    01_Data/kb_outputs/expanded_kb.ttl

Output:
    06_RAG_over_RDF_SPARQL/outputs/schema_summary.md
    06_RAG_over_RDF_SPARQL/outputs/schema_summary.json

The schema summary is used by the RAG/SPARQL system to know which classes,
predicates, and example triples exist in the RDF graph.
"""

from pathlib import Path
import json
from collections import Counter, defaultdict

from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_KB = PROJECT_ROOT / "01_Data" / "kb_outputs" / "expanded_kb.ttl"

OUTPUT_DIR = PROJECT_ROOT / "06_RAG_over_RDF_SPARQL" / "outputs"
SCHEMA_MD_FILE = OUTPUT_DIR / "schema_summary.md"
SCHEMA_JSON_FILE = OUTPUT_DIR / "schema_summary.json"


# =============================
# NAMESPACE
# =============================

EX = Namespace("http://example.org/benchpress-kg/")


# =============================
# HELPERS
# =============================

def local_name(uri) -> str:
    text = str(uri)
    if "#" in text:
        return text.split("#")[-1]
    return text.rstrip("/").split("/")[-1]


def is_project_uri(uri) -> bool:
    return isinstance(uri, URIRef) and str(uri).startswith(str(EX))


def get_label(graph: Graph, uri) -> str:
    label = next(graph.objects(uri, RDFS.label), None)
    if label:
        return str(label)
    return local_name(uri)


def collect_schema(graph: Graph) -> dict:
    classes = sorted({
        local_name(cls)
        for cls in graph.subjects(RDF.type, OWL.Class)
        if is_project_uri(cls)
    })

    class_instances = defaultdict(list)

    for entity, _, cls in graph.triples((None, RDF.type, None)):
        if is_project_uri(entity) and is_project_uri(cls):
            cls_name = local_name(cls)
            if cls_name not in {"KnowledgeStatement"}:
                class_instances[cls_name].append(get_label(graph, entity))

    predicate_counter = Counter()

    for s, p, o in graph:
        if is_project_uri(s) and is_project_uri(p) and is_project_uri(o):
            if p not in {RDF.type, RDFS.label, RDFS.subClassOf}:
                predicate_counter[local_name(p)] += 1

    predicate_examples = defaultdict(list)

    for s, p, o in graph:
        if is_project_uri(s) and is_project_uri(p) and is_project_uri(o):
            pred = local_name(p)

            if pred in {
                "hasSubject",
                "hasPredicate",
                "hasObject",
                "originalSubject",
                "originalPredicate",
                "originalObject",
                "alignedSubject",
                "alignedPredicate",
                "alignedObject",
            }:
                continue

            if len(predicate_examples[pred]) < 5:
                predicate_examples[pred].append({
                    "subject": get_label(graph, s),
                    "predicate": pred,
                    "object": get_label(graph, o),
                })

    schema = {
        "namespace": str(EX),
        "classes": classes,
        "class_instance_counts": {
            cls: len(values)
            for cls, values in sorted(class_instances.items())
        },
        "class_examples": {
            cls: sorted(set(values))[:10]
            for cls, values in sorted(class_instances.items())
        },
        "predicates": [
            {"predicate": pred, "count": count}
            for pred, count in predicate_counter.most_common()
        ],
        "predicate_examples": dict(predicate_examples),
    }

    return schema


def write_markdown(schema: dict) -> str:
    lines = []

    lines.append("# RDF/SPARQL Schema Summary\n")
    lines.append("## Namespace\n")
    lines.append(f"```text\n{schema['namespace']}\n```\n")

    lines.append("## Classes\n")
    lines.append("| Class | Instance count | Examples |")
    lines.append("|---|---:|---|")

    for cls in schema["classes"]:
        count = schema["class_instance_counts"].get(cls, 0)
        examples = ", ".join(schema["class_examples"].get(cls, [])[:5])
        lines.append(f"| `{cls}` | {count} | {examples} |")

    lines.append("\n## Predicates\n")
    lines.append("| Predicate | Count |")
    lines.append("|---|---:|")

    for item in schema["predicates"]:
        lines.append(f"| `ex:{item['predicate']}` | {item['count']} |")

    lines.append("\n## Predicate Examples\n")

    for pred, examples in schema["predicate_examples"].items():
        lines.append(f"### `ex:{pred}`\n")
        lines.append("| Subject | Predicate | Object |")
        lines.append("|---|---|---|")

        for ex_row in examples[:5]:
            lines.append(
                f"| `{ex_row['subject']}` | `ex:{ex_row['predicate']}` | `{ex_row['object']}` |"
            )

        lines.append("")

    lines.append("## NL→SPARQL Guidance\n")
    lines.append("Use only the namespace and predicates listed above when generating SPARQL queries.")
    lines.append("Always include:")
    lines.append("")
    lines.append("```sparql")
    lines.append("PREFIX ex: <http://example.org/benchpress-kg/>")
    lines.append("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>")
    lines.append("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>")
    lines.append("```")

    return "\n".join(lines)


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

    schema = collect_schema(graph)

    SCHEMA_JSON_FILE.write_text(
        json.dumps(schema, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    SCHEMA_MD_FILE.write_text(
        write_markdown(schema),
        encoding="utf-8"
    )

    print("Schema summary generated.")
    print(f"Markdown: {SCHEMA_MD_FILE}")
    print(f"JSON: {SCHEMA_JSON_FILE}")


if __name__ == "__main__":
    main()