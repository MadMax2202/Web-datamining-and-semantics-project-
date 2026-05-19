from pathlib import Path
import re
import pandas as pd
from rdflib import Graph, Namespace, RDF, RDFS, Literal, URIRef
from rdflib.namespace import XSD, OWL

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data" / "samples" / "extracted_knowledge_local.csv"
OUT_DIR = ROOT / "kg_artifacts"
OUT_DIR.mkdir(exist_ok=True)

EX = Namespace("http://example.org/benchpress/kg/")

MUSCLES = {"pectoralis major","triceps","deltoids","anterior deltoid","pectoralis","pecs","lats","rotator cuff"}
JOINTS = {"shoulder","elbow","wrist","scapula","scapulae"}
EQUIPMENT = {"bar","barbell","bench"}
VARS = {"force","torque","moment","moment arm","activation","emg","range of motion","velocity","power","eccentric phase","concentric phase"}

def slug(text: str) -> str:
    text = str(text).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "node"

def node_uri(text: str) -> URIRef:
    return EX[slug(text)]

def classify_entity(text: str):
    t = str(text).lower()
    if any(m in t for m in MUSCLES): return EX.Muscle
    if any(j in t for j in JOINTS): return EX.Joint
    if any(e in t for e in EQUIPMENT): return EX.Equipment
    if any(v in t for v in VARS): return EX.BiomechanicalVariable
    if "risk" in t or "pain" in t or "injury" in t: return EX.RiskFactor
    return EX.TechniqueCue

def pred_uri(relation: str) -> URIRef:
    clean = slug(relation)
    mapping = {
        "activate": EX.targetsMuscle,
        "increase": EX.affects,
        "decrease": EX.affects,
        "reduce": EX.affects,
        "affect": EX.affects,
        "produce": EX.affects,
        "require": EX.hasTechniqueCue,
        "touch": EX.hasTechniqueCue,
        "grip": EX.hasTechniqueCue,
        "lower": EX.hasTechniqueCue,
        "press": EX.hasTechniqueCue,
    }
    for key, val in mapping.items():
        if key in clean:
            return val
    return EX[clean]

def main():
    df = pd.read_csv(INPUT)
    g = Graph()
    g.bind("ex", EX)
    g.bind("owl", OWL)
    g.bind("rdfs", RDFS)

    bench = EX.BenchPress
    g.add((bench, RDF.type, EX.Exercise))
    g.add((bench, RDFS.label, Literal("bench press")))

    for _, row in df.iterrows():
        s_txt = str(row["subject"]).strip()
        o_txt = str(row["object"]).strip()
        rel = str(row["relation"]).strip()
        s = node_uri(s_txt)
        o = node_uri(o_txt)
        p = pred_uri(rel)

        g.add((s, RDF.type, classify_entity(s_txt)))
        g.add((s, RDFS.label, Literal(s_txt)))
        g.add((o, RDF.type, classify_entity(o_txt)))
        g.add((o, RDFS.label, Literal(o_txt)))
        g.add((s, p, o))

        # Link extracted domain nodes back to the central exercise.
        if classify_entity(s_txt) == EX.Muscle:
            g.add((bench, EX.targetsMuscle, s))
        if classify_entity(o_txt) == EX.Muscle:
            g.add((bench, EX.targetsMuscle, o))
        if classify_entity(s_txt) == EX.Equipment:
            g.add((bench, EX.usesEquipment, s))
        if classify_entity(o_txt) == EX.Equipment:
            g.add((bench, EX.usesEquipment, o))

        ev = EX["evidence_" + str(abs(hash(str(row.get("example_sentence","")))))]
        g.add((ev, RDF.type, EX.EvidenceSentence))
        g.add((ev, RDFS.comment, Literal(str(row.get("example_sentence","")))))
        g.add((ev, EX.sourceFile, Literal(str(row.get("sources","")))))
        g.add((ev, EX.confidence, Literal(float(row.get("max_confidence", 0.0)), datatype=XSD.float)))
        g.add((ev, EX.category, Literal(str(row.get("category","")))))
        g.add((s, EX.hasEvidence, ev))

    g.serialize(OUT_DIR / "initial_graph.ttl", format="turtle")
    g.serialize(OUT_DIR / "expanded.nt", format="nt")

    stats = {
        "triples": len(g),
        "unique_subjects": len(set(g.subjects())),
        "unique_predicates": len(set(g.predicates())),
        "unique_objects": len(set(g.objects())),
        "source_rows": len(df),
    }
    (OUT_DIR / "kb_statistics.json").write_text(__import__("json").dumps(stats, indent=2), encoding="utf-8")
    print("Wrote KG artifacts:", stats)

if __name__ == "__main__":
    main()
