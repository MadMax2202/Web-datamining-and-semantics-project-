"""
04A_family_swrl_reasoning.py

This script demonstrates SWRL reasoning on a simple family ontology.

It creates a small family ontology with:
- John parentOf Mary
- Mary parentOf Alice

Then it adds the SWRL rule:

parentOf(?x, ?y) ^ parentOf(?y, ?z) -> grandparentOf(?x, ?z)

Expected inference:
- John grandparentOf Alice

Outputs:
- outputs/family.owl
- outputs/family_reasoned.owl
- outputs/family_reasoning_output.txt
"""

from pathlib import Path

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
OUTPUT_DIR = PROJECT_ROOT / "04_Reasoning_SWRL" / "outputs"

FAMILY_OWL_FILE = OUTPUT_DIR / "family.owl"
FAMILY_REASONED_FILE = OUTPUT_DIR / "family_reasoned.owl"
FAMILY_OUTPUT_FILE = OUTPUT_DIR / "family_reasoning_output.txt"


# =============================
# MAIN
# =============================

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    onto = get_ontology("http://example.org/family.owl")

    with onto:
        class Person(Thing):
            pass

        class parentOf(ObjectProperty):
            domain = [Person]
            range = [Person]

        class grandparentOf(ObjectProperty):
            domain = [Person]
            range = [Person]

        # Individuals
        john = Person("John")
        mary = Person("Mary")
        alice = Person("Alice")

        # Initial facts
        john.parentOf.append(mary)
        mary.parentOf.append(alice)

        # SWRL rule:
        # parentOf(?x, ?y) ^ parentOf(?y, ?z) -> grandparentOf(?x, ?z)
        rule = Imp()
        rule.set_as_rule(
            "parentOf(?x, ?y), parentOf(?y, ?z) -> grandparentOf(?x, ?z)"
        )

    onto.save(file=str(FAMILY_OWL_FILE), format="rdfxml")

    output_lines = []
    output_lines.append("Family SWRL Reasoning Demo")
    output_lines.append("=" * 40)
    output_lines.append("")
    output_lines.append("Initial facts:")
    output_lines.append("- John parentOf Mary")
    output_lines.append("- Mary parentOf Alice")
    output_lines.append("")
    output_lines.append("SWRL rule:")
    output_lines.append("parentOf(?x, ?y) ^ parentOf(?y, ?z) -> grandparentOf(?x, ?z)")
    output_lines.append("")

    try:
        print("Running Pellet reasoner for family ontology...")
        with onto:
            sync_reasoner_pellet(
                infer_property_values=True,
                infer_data_property_values=True
            )

        output_lines.append("Reasoner status: SUCCESS")
        output_lines.append("")
        output_lines.append("Inferred grandparentOf relations:")

        inferred_count = 0

        for person in onto.Person.instances():
            for grandchild in person.grandparentOf:
                output_lines.append(f"- {person.name} grandparentOf {grandchild.name}")
                inferred_count += 1

        if inferred_count == 0:
            output_lines.append("- No inferred grandparentOf relations found.")

    except Exception as e:
        output_lines.append("Reasoner status: FAILED")
        output_lines.append(f"Reasoner error: {e}")
        output_lines.append("")
        output_lines.append("Manual SWRL-equivalent fallback output:")
        output_lines.append("- John grandparentOf Alice")
        output_lines.append("")
        output_lines.append(
            "Note: The SWRL rule was created, but Pellet could not run. "
            "This often happens when Java is not installed or not available in PATH."
        )

    onto.save(file=str(FAMILY_REASONED_FILE), format="rdfxml")

    FAMILY_OUTPUT_FILE.write_text("\n".join(output_lines), encoding="utf-8")

    print()
    print("Family reasoning complete.")
    print(f"Family ontology saved to: {FAMILY_OWL_FILE}")
    print(f"Reasoned ontology saved to: {FAMILY_REASONED_FILE}")
    print(f"Output saved to: {FAMILY_OUTPUT_FILE}")


if __name__ == "__main__":
    main()