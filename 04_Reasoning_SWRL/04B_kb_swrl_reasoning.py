"""
04B_kb_swrl_reasoning.py

This script demonstrates SWRL reasoning on the project's bench press knowledge base.

It reads the expanded RDF KB from:

    01_Data/kb_outputs/expanded_kb.ttl

Then it extracts relevant facts from the RDF graph and rebuilds a small OWLReady2
ontology for SWRL reasoning.

The SWRL rule used is:

TechniqueCue(?cue) ^ BiomechanicalConcept(?concept) ^
affectsBiomechanics(?cue, ?concept) -> ImportantTechniqueCue(?cue)

Meaning:
If a technique cue affects a biomechanical concept, then it is an important
technique cue.

Outputs:
- outputs/kb_swrl_input.owl
- outputs/kb_swrl_reasoned.owl
- outputs/kb_reasoning_output.txt
"""

from pathlib import Path
import re

from rdflib import Graph, Namespace, RDF, RDFS, URIRef
from owlready2 import (
    get_ontology,
    Thing,
    ObjectProperty,
    Imp,
    sync_reasoner_pellet,
)


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPANDED_KB_FILE = PROJECT_ROOT / "01_Data" / "kb_outputs" / "expanded_kb.ttl"

OUTPUT_DIR = PROJECT_ROOT / "04_Reasoning_SWRL" / "outputs"
KB_INPUT_OWL_FILE = OUTPUT_DIR / "kb_swrl_input.owl"
KB_REASONED_OWL_FILE = OUTPUT_DIR / "kb_swrl_reasoned.owl"
KB_OUTPUT_FILE = OUTPUT_DIR / "kb_reasoning_output.txt"


# =============================
# NAMESPACE
# =============================

EX = Namespace("http://example.org/benchpress-kg/")


# =============================
# HELPERS
# =============================

def slugify_uri(uri: URIRef) -> str:
    """
    Convert a URI into a safe Owlready2 individual name.
    """
    text = str(uri).split("/")[-1].split("#")[-1]
    text = text.strip().lower()
    text = re.sub(r"[^a-zA-Z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")

    if not text:
        text = "unknown_entity"

    if text[0].isdigit():
        text = f"entity_{text}"

    return text


def get_label(graph: Graph, uri: URIRef) -> str:
    """
    Get rdfs:label if available, otherwise URI fragment.
    """
    label = next(graph.objects(uri, RDFS.label), None)

    if label:
        return str(label)

    return slugify_uri(uri).replace("_", " ")


def load_kb_facts() -> list[tuple[str, str, str]]:
    """
    Load TechniqueCue -> affectsBiomechanics -> BiomechanicalConcept facts
    from the expanded RDF KB.
    """
    if not EXPANDED_KB_FILE.exists():
        raise FileNotFoundError(
            f"Expanded KB not found: {EXPANDED_KB_FILE}\n"
            "Run 03C_expand_kb.py first."
        )

    graph = Graph()
    graph.parse(EXPANDED_KB_FILE, format="turtle")

    facts = []

    for cue, _, concept in graph.triples((None, EX.affectsBiomechanics, None)):
        if (cue, RDF.type, EX.TechniqueCue) not in graph:
            continue

        if (concept, RDF.type, EX.BiomechanicalConcept) not in graph:
            continue

        cue_label = get_label(graph, cue)
        concept_label = get_label(graph, concept)

        cue_name = slugify_uri(cue)
        concept_name = slugify_uri(concept)

        facts.append((cue_name, cue_label, concept_name, concept_label))

    return facts


# =============================
# MAIN
# =============================

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    facts = load_kb_facts()

    output_lines = []
    output_lines.append("Bench Press KB SWRL Reasoning Demo")
    output_lines.append("=" * 40)
    output_lines.append("")
    output_lines.append("SWRL rule:")
    output_lines.append(
        "TechniqueCue(?cue) ^ BiomechanicalConcept(?concept) ^ "
        "affectsBiomechanics(?cue, ?concept) -> ImportantTechniqueCue(?cue)"
    )
    output_lines.append("")

    if not facts:
        output_lines.append("No affectsBiomechanics facts were found in the expanded KB.")
        output_lines.append("")
        output_lines.append(
            "Suggestion: Check that 03C_expand_kb.py produced at least one "
            "TechniqueCue -> affectsBiomechanics -> BiomechanicalConcept triple."
        )
        KB_OUTPUT_FILE.write_text("\n".join(output_lines), encoding="utf-8")
        print("No KB facts found for reasoning.")
        print(f"Output saved to: {KB_OUTPUT_FILE}")
        return

    onto = get_ontology("http://example.org/benchpress-swrl.owl")

    with onto:
        class DomainEntity(Thing):
            pass

        class TechniqueCue(DomainEntity):
            pass

        class BiomechanicalConcept(DomainEntity):
            pass

        class ImportantTechniqueCue(TechniqueCue):
            pass

        class affectsBiomechanics(ObjectProperty):
            domain = [TechniqueCue]
            range = [BiomechanicalConcept]

        created_cues = {}
        created_concepts = {}

        for cue_name, cue_label, concept_name, concept_label in facts:
            if cue_name not in created_cues:
                created_cues[cue_name] = TechniqueCue(cue_name)
                created_cues[cue_name].label = [cue_label]

            if concept_name not in created_concepts:
                created_concepts[concept_name] = BiomechanicalConcept(concept_name)
                created_concepts[concept_name].label = [concept_label]

            created_cues[cue_name].affectsBiomechanics.append(
                created_concepts[concept_name]
            )

        rule = Imp()
        rule.set_as_rule(
            "TechniqueCue(?cue), BiomechanicalConcept(?concept), "
            "affectsBiomechanics(?cue, ?concept) -> ImportantTechniqueCue(?cue)"
        )

    onto.save(file=str(KB_INPUT_OWL_FILE), format="rdfxml")

    output_lines.append("Initial facts loaded from expanded KB:")
    for cue_name, cue_label, concept_name, concept_label in facts:
        output_lines.append(f"- {cue_label} affectsBiomechanics {concept_label}")

    output_lines.append("")

    try:
        print("Running Pellet reasoner for bench press KB ontology...")
        with onto:
            sync_reasoner_pellet(
                infer_property_values=True,
                infer_data_property_values=True
            )

        output_lines.append("Reasoner status: SUCCESS")
        output_lines.append("")
        output_lines.append("Inferred ImportantTechniqueCue individuals:")

        inferred = list(onto.ImportantTechniqueCue.instances())

        if inferred:
            for individual in inferred:
                label = individual.label[0] if individual.label else individual.name
                output_lines.append(f"- {label}")
        else:
            output_lines.append("- No ImportantTechniqueCue individuals inferred.")

    except Exception as e:
        output_lines.append("Reasoner status: FAILED")
        output_lines.append(f"Reasoner error: {e}")
        output_lines.append("")
        output_lines.append("Manual SWRL-equivalent fallback output:")
        for cue_name, cue_label, _, _ in facts:
            output_lines.append(f"- {cue_label} is an ImportantTechniqueCue")
        output_lines.append("")
        output_lines.append(
            "Note: The SWRL rule was created, but Pellet could not run. "
            "This often happens when Java is not installed or not available in PATH."
        )

    onto.save(file=str(KB_REASONED_OWL_FILE), format="rdfxml")

    KB_OUTPUT_FILE.write_text("\n".join(output_lines), encoding="utf-8")

    print()
    print("KB reasoning complete.")
    print(f"Input OWL ontology saved to: {KB_INPUT_OWL_FILE}")
    print(f"Reasoned OWL ontology saved to: {KB_REASONED_OWL_FILE}")
    print(f"Output saved to: {KB_OUTPUT_FILE}")


if __name__ == "__main__":
    main()