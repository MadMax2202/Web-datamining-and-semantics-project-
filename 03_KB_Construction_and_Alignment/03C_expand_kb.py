"""
03C_expand_kb.py

This script expands the initial RDF knowledge base using simple rule-based
SPARQL CONSTRUCT queries.

Input:
    01_Data/kb_outputs/initial_kb.ttl

Output:
    01_Data/kb_outputs/expanded_kb.ttl
    01_Data/kb_outputs/expansion_report.md

Expansion strategy:
1. If a muscle flexes, extends, abducts, or adducts a joint,
   add: muscle ex:actsOnJoint joint.
2. If a technique cue influences or reduces a concept,
   add: technique cue ex:affectsBiomechanics concept.
3. If equipment applies force,
   add: equipment ex:involvesBiomechanicalConcept force.
4. If something requires or involves another concept,
   add a generic ex:relatedTo relation.
"""

from pathlib import Path

from rdflib import Graph, Namespace, RDF, OWL


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "01_Data" / "kb_outputs" / "initial_kb.ttl"
OUTPUT_FILE = PROJECT_ROOT / "01_Data" / "kb_outputs" / "expanded_kb.ttl"
EXPANSION_REPORT_FILE = PROJECT_ROOT / "01_Data" / "kb_outputs" / "expansion_report.md"


# =============================
# NAMESPACE
# =============================

EX = Namespace("http://example.org/benchpress-kg/")


# =============================
# EXPANSION QUERIES
# =============================

EXPANSION_QUERIES = {
    "muscle_acts_on_joint": """
        PREFIX ex: <http://example.org/benchpress-kg/>
        CONSTRUCT {
            ?muscle ex:actsOnJoint ?joint .
        }
        WHERE {
            ?muscle a ex:Muscle .
            ?joint a ex:Joint .
            {
                ?muscle ex:flexes ?joint .
            }
            UNION
            {
                ?muscle ex:extends ?joint .
            }
            UNION
            {
                ?muscle ex:abducts ?joint .
            }
            UNION
            {
                ?muscle ex:adducts ?joint .
            }
        }
    """,

    "technique_affects_biomechanics": """
        PREFIX ex: <http://example.org/benchpress-kg/>
        CONSTRUCT {
            ?cue ex:affectsBiomechanics ?concept .
        }
        WHERE {
            ?cue a ex:TechniqueCue .
            ?concept a ex:BiomechanicalConcept .
            {
                ?cue ex:influences ?concept .
            }
            UNION
            {
                ?cue ex:reduces ?concept .
            }
            UNION
            {
                ?cue ex:increases ?concept .
            }
            UNION
            {
                ?cue ex:decreases ?concept .
            }
        }
    """,

    "equipment_involves_biomechanical_concept": """
        PREFIX ex: <http://example.org/benchpress-kg/>
        CONSTRUCT {
            ?equipment ex:involvesBiomechanicalConcept ?concept .
        }
        WHERE {
            ?equipment a ex:Equipment .
            ?concept a ex:BiomechanicalConcept .
            ?equipment ex:appliesForce ?concept .
        }
    """,

    "requires_involves_related_to": """
        PREFIX ex: <http://example.org/benchpress-kg/>
        CONSTRUCT {
            ?s ex:relatedTo ?o .
        }
        WHERE {
            {
                ?s ex:requires ?o .
            }
            UNION
            {
                ?s ex:involves ?o .
            }
        }
    """
}


# =============================
# MAIN
# =============================

def expand_kb() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Initial KB not found: {INPUT_FILE}\n"
            "Run 03A_build_initial_rdf.py first."
        )

    graph = Graph()
    graph.parse(INPUT_FILE, format="turtle")
    graph.bind("ex", EX)
    graph.bind("owl", OWL)

    original_count = len(graph)

    expansion_counts = {}

    # Add expansion predicates to ontology
    expansion_predicates = [
        EX.actsOnJoint,
        EX.affectsBiomechanics,
        EX.involvesBiomechanicalConcept,
        EX.relatedTo,
    ]

    for pred in expansion_predicates:
        graph.add((pred, RDF.type, OWL.ObjectProperty))

    for name, query in EXPANSION_QUERIES.items():
        constructed_graph = graph.query(query)
        added = 0

        for triple in constructed_graph:
            if triple not in graph:
                graph.add(triple)
                added += 1

        expansion_counts[name] = added
        print(f"{name}: added {added} triples")

    final_count = len(graph)
    total_added = final_count - original_count

    graph.serialize(destination=OUTPUT_FILE, format="turtle")

    report = []
    report.append("# KB Expansion Report\n")
    report.append("## Expansion Strategy\n")
    report.append("The KB was expanded using simple SPARQL CONSTRUCT rules.\n")
    report.append("These rules add higher-level semantic relations from existing extracted triples.\n")
    report.append("\n## Expansion Results\n")
    report.append(f"- Initial RDF triples: `{original_count}`\n")
    report.append(f"- Final RDF triples: `{final_count}`\n")
    report.append(f"- New triples added: `{total_added}`\n")
    report.append("\n## Rule-Level Additions\n")

    for name, count in expansion_counts.items():
        report.append(f"- `{name}`: `{count}` triples added\n")

    EXPANSION_REPORT_FILE.write_text("\n".join(report), encoding="utf-8")

    print()
    print("KB expansion complete.")
    print(f"Expanded KB saved to: {OUTPUT_FILE}")
    print(f"Expansion report saved to: {EXPANSION_REPORT_FILE}")


if __name__ == "__main__":
    expand_kb()