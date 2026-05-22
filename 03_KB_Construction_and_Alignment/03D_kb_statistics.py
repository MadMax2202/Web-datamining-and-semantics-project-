"""
03D_kb_statistics.py

This script computes final statistics for the RDF knowledge base.

Input:
    01_Data/kb_outputs/initial_kb.ttl
    01_Data/kb_outputs/expanded_kb.ttl

Output:
    01_Data/kb_outputs/kb_statistics.json
    01_Data/kb_outputs/kb_statistics.md

The statistics include:
- number of triples
- number of entities
- number of predicates
- number of classes
- number of statement/evidence nodes
- average confidence
- number of expanded triples
"""

from pathlib import Path
import json

from rdflib import Graph, Namespace, RDF, RDFS, OWL


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

KB_DIR = PROJECT_ROOT / "01_Data" / "kb_outputs"

INITIAL_KB_FILE = KB_DIR / "initial_kb.ttl"
EXPANDED_KB_FILE = KB_DIR / "expanded_kb.ttl"

STATS_JSON_FILE = KB_DIR / "kb_statistics.json"
STATS_MD_FILE = KB_DIR / "kb_statistics.md"


# =============================
# NAMESPACE
# =============================

EX = Namespace("http://example.org/benchpress-kg/")


# =============================
# HELPERS
# =============================

def load_graph(path: Path) -> Graph:
    if not path.exists():
        raise FileNotFoundError(f"Missing RDF file: {path}")

    graph = Graph()
    graph.parse(path, format="turtle")
    return graph


def count_instances(graph: Graph, class_uri) -> int:
    return len(set(graph.subjects(RDF.type, class_uri)))


def get_confidence_values(graph: Graph) -> list[float]:
    values = []

    for value in graph.objects(None, EX.confidence):
        try:
            values.append(float(value))
        except Exception:
            continue

    return values


def graph_stats(graph: Graph) -> dict:
    entities = set()
    predicates = set()
    classes = set()

    for s, p, o in graph:
        predicates.add(p)

        if str(s).startswith(str(EX)):
            entities.add(s)

        if str(o).startswith(str(EX)):
            entities.add(o)

    for cls in graph.subjects(RDF.type, OWL.Class):
        classes.add(cls)

    confidence_values = get_confidence_values(graph)

    avg_confidence = (
        sum(confidence_values) / len(confidence_values)
        if confidence_values
        else 0.0
    )

    return {
        "triples": len(graph),
        "entities": len(entities),
        "predicates": len(predicates),
        "classes": len(classes),
        "knowledge_statements": count_instances(graph, EX.KnowledgeStatement),
        "exercises": count_instances(graph, EX.Exercise),
        "muscles": count_instances(graph, EX.Muscle),
        "joints": count_instances(graph, EX.Joint),
        "equipment": count_instances(graph, EX.Equipment),
        "technique_cues": count_instances(graph, EX.TechniqueCue),
        "biomechanical_concepts": count_instances(graph, EX.BiomechanicalConcept),
        "domain_entities": count_instances(graph, EX.DomainEntity),
        "confidence_values": len(confidence_values),
        "average_confidence": round(avg_confidence, 4),
    }


# =============================
# MAIN
# =============================

def compute_statistics() -> None:
    initial_graph = load_graph(INITIAL_KB_FILE)
    expanded_graph = load_graph(EXPANDED_KB_FILE)

    initial_stats = graph_stats(initial_graph)
    expanded_stats = graph_stats(expanded_graph)

    stats = {
        "initial_kb": initial_stats,
        "expanded_kb": expanded_stats,
        "expansion": {
            "new_triples_added": expanded_stats["triples"] - initial_stats["triples"],
            "new_entities_added": expanded_stats["entities"] - initial_stats["entities"],
            "new_predicates_added": expanded_stats["predicates"] - initial_stats["predicates"],
        }
    }

    STATS_JSON_FILE.write_text(
        json.dumps(stats, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    md = []
    md.append("# Final KB Statistics\n")
    md.append("## Initial KB\n")
    md.append(f"- RDF triples: `{initial_stats['triples']}`")
    md.append(f"- Entities: `{initial_stats['entities']}`")
    md.append(f"- Predicates: `{initial_stats['predicates']}`")
    md.append(f"- Classes: `{initial_stats['classes']}`")
    md.append(f"- Knowledge statement nodes: `{initial_stats['knowledge_statements']}`")
    md.append(f"- Average confidence: `{initial_stats['average_confidence']}`")
    md.append("")
    md.append("### Entity Type Counts")
    md.append(f"- Exercises: `{initial_stats['exercises']}`")
    md.append(f"- Muscles: `{initial_stats['muscles']}`")
    md.append(f"- Joints: `{initial_stats['joints']}`")
    md.append(f"- Equipment: `{initial_stats['equipment']}`")
    md.append(f"- Technique cues: `{initial_stats['technique_cues']}`")
    md.append(f"- Biomechanical concepts: `{initial_stats['biomechanical_concepts']}`")
    md.append("")
    md.append("## Expanded KB\n")
    md.append(f"- RDF triples: `{expanded_stats['triples']}`")
    md.append(f"- Entities: `{expanded_stats['entities']}`")
    md.append(f"- Predicates: `{expanded_stats['predicates']}`")
    md.append(f"- Classes: `{expanded_stats['classes']}`")
    md.append(f"- Knowledge statement nodes: `{expanded_stats['knowledge_statements']}`")
    md.append(f"- Average confidence: `{expanded_stats['average_confidence']}`")
    md.append("")
    md.append("## Expansion Summary\n")
    md.append(f"- New triples added: `{stats['expansion']['new_triples_added']}`")
    md.append(f"- New entities added: `{stats['expansion']['new_entities_added']}`")
    md.append(f"- New predicates added: `{stats['expansion']['new_predicates_added']}`")

    STATS_MD_FILE.write_text("\n".join(md), encoding="utf-8")

    print("KB statistics generated.")
    print(f"JSON statistics saved to: {STATS_JSON_FILE}")
    print(f"Markdown statistics saved to: {STATS_MD_FILE}")

    print()
    print("Summary:")
    print(json.dumps(stats, indent=4))


if __name__ == "__main__":
    compute_statistics()