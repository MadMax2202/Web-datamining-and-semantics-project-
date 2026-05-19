"""
SWRL reasoning on family.owl with OWLReady2.
Rule 1: hasParent(?x,?y) ^ hasParent(?y,?z)  -> hasGrandparent(?x,?z)
Rule 2: hasParent(?x,?y) ^ hasSibling(?y,?z) -> hasUncleOrAunt(?x,?z)
"""
from pathlib import Path
from owlready2 import get_ontology, Imp, sync_reasoner_pellet

ROOT     = Path(__file__).resolve().parents[2]
OWL_PATH = ROOT / "family.owl"
OUT_PATH = ROOT / "kg_artifacts" / "family_reasoned.owl"

def run():
    print("=" * 55)
    print("Family OWL Reasoning — OWLReady2 + SWRL")
    print("=" * 55)

    onto = get_ontology(str(OWL_PATH)).load()
    FAM  = onto.get_namespace("http://example.org/family#")

    print("\nIndividuals:", [i.name for i in onto.individuals()])

    print("\n--- Before reasoning ---")
    for ind in onto.individuals():
        parents  = list(FAM.hasParent[ind])
        siblings = list(FAM.hasSibling[ind])
        if parents:
            print(f"  {ind.name}.hasParent   = {[p.name for p in parents]}")
        if siblings:
            print(f"  {ind.name}.hasSibling  = {[s.name for s in siblings]}")

    with onto:
        rule1 = Imp()
        rule1.set_as_rule(
            "hasParent(?x,?y), hasParent(?y,?z) -> hasGrandparent(?x,?z)"
        )
        rule2 = Imp()
        rule2.set_as_rule(
            "hasParent(?x,?y), hasSibling(?y,?z) -> hasUncleOrAunt(?x,?z)"
        )
    print("\nSWRL rules added:")
    print("  Rule 1: hasParent(?x,?y) ^ hasParent(?y,?z)  -> hasGrandparent(?x,?z)")
    print("  Rule 2: hasParent(?x,?y) ^ hasSibling(?y,?z) -> hasUncleOrAunt(?x,?z)")

    print("\nRunning reasoner...")
    try:
        with onto:
            sync_reasoner_pellet(infer_property_values=True)
        print("Pellet reasoner finished.")
    except Exception as e:
        print(f"Pellet unavailable ({e}), applying rules manually...")
        _manual(onto, FAM)

    print("\n--- After reasoning (inferred) ---")
    count = 0
    for ind in onto.individuals():
        gp  = list(FAM.hasGrandparent[ind])
        ua  = list(FAM.hasUncleOrAunt[ind])
        if gp:
            print(f"  {ind.name}.hasGrandparent  = {[x.name for x in gp]}")
            count += len(gp)
        if ua:
            print(f"  {ind.name}.hasUncleOrAunt = {[x.name for x in ua]}")
            count += len(ua)
    print(f"\nTotal inferred triples: {count}")

    onto.save(file=str(OUT_PATH), format="rdfxml")
    print(f"Saved -> {OUT_PATH}")

def _manual(onto, FAM):
    for x in onto.individuals():
        for y in list(FAM.hasParent[x]):
            for z in list(FAM.hasParent[y]):
                if z not in FAM.hasGrandparent[x]:
                    FAM.hasGrandparent[x].append(z)
                    print(f"  [R1] {x.name} hasGrandparent {z.name}")
            for z in list(FAM.hasSibling[y]):
                if z not in FAM.hasUncleOrAunt[x]:
                    FAM.hasUncleOrAunt[x].append(z)
                    print(f"  [R2] {x.name} hasUncleOrAunt {z.name}")

if __name__ == "__main__":
    run()