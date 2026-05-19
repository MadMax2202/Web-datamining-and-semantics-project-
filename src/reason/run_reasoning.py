from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS

ROOT = Path(__file__).resolve().parents[2]
EX = Namespace("http://example.org/benchpress/kg/")

def main():
    g = Graph()
    g.parse(ROOT / "kg_artifacts" / "initial_graph.ttl", format="turtle")

    # SWRL-style rule implemented deterministically:
    # BenchPress(?e) ^ targetsMuscle(?e, ?m) ^ label(?m, "triceps") -> TricepsDominantExercise(?e)
    inferred = 0
    for e, _, m in g.triples((None, EX.targetsMuscle, None)):
        label = str(next(g.objects(m, RDFS.label), "")).lower()
        if "triceps" in label:
            g.add((EX.TricepsDominantExercise, RDF.type, RDFS.Class))
            g.add((e, RDF.type, EX.TricepsDominantExercise))
            inferred += 1

    # Another rule:
    # Exercise that uses bar/barbell -> BarbellExercise
    for e, _, equip in g.triples((None, EX.usesEquipment, None)):
        label = str(next(g.objects(equip, RDFS.label), "")).lower()
        if "bar" in label:
            g.add((EX.BarbellExercise, RDF.type, RDFS.Class))
            g.add((e, RDF.type, EX.BarbellExercise))
            inferred += 1

    out = ROOT / "kg_artifacts" / "reasoned_graph.ttl"
    g.serialize(out, format="turtle")
    print(f"Reasoning complete. Inferred statements added approximately: {inferred}. Output: {out}")

if __name__ == "__main__":
    main()
