"""
03A_build_initial_rdf.py

This script builds the initial RDF knowledge base from the extracted CSV triples.

Input:
    01_Data/crawler_outputs/extracted_knowledge_live.csv
    or
    01_Data/crawler_outputs/extracted_knowledge_local.csv

Output:
    01_Data/kb_outputs/ontology.ttl
    01_Data/kb_outputs/initial_kb.ttl
    01_Data/kb_outputs/alignment_report.csv

The script:
1. Loads extracted subject-relation-object triples.
2. Canonicalizes entity names.
3. Aligns noisy predicates to a controlled predicate vocabulary.
4. Assigns entity types such as Muscle, Joint, Equipment, etc.
5. Creates RDF triples using rdflib.
6. Stores confidence scores and evidence sentences using statement nodes.
"""

from pathlib import Path
import hashlib
import pandas as pd

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD
from rdflib.namespace import OWL

from importlib.machinery import SourceFileLoader


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_LIVE = PROJECT_ROOT / "01_Data" / "crawler_outputs" / "extracted_knowledge_live.csv"
INPUT_LOCAL = PROJECT_ROOT / "01_Data" / "crawler_outputs" / "extracted_knowledge_local.csv"

OUTPUT_DIR = PROJECT_ROOT / "01_Data" / "kb_outputs"
ONTOLOGY_FILE = OUTPUT_DIR / "ontology.ttl"
INITIAL_KB_FILE = OUTPUT_DIR / "initial_kb.ttl"
ALIGNMENT_REPORT_FILE = OUTPUT_DIR / "alignment_report.csv"


# =============================
# LOAD ALIGNMENT RULES
# =============================

RULES_PATH = PROJECT_ROOT / "03_KB_Construction_and_Alignment" / "03B_alignment_rules.py"
rules = SourceFileLoader("alignment_rules", str(RULES_PATH)).load_module()

canonical_entity = rules.canonical_entity
canonical_predicate = rules.canonical_predicate
guess_entity_type = rules.guess_entity_type


# =============================
# NAMESPACES
# =============================

EX = Namespace("http://example.org/benchpress-kg/")
SCHEMA = Namespace("http://schema.org/")


# =============================
# HELPER FUNCTIONS
# =============================

def slugify(text: str) -> str:
    """
    Convert a label into a safe URI fragment.
    """
    text = str(text).strip().lower()
    text = text.replace("→", " ")
    text = text.replace("/", " ")
    text = text.replace("\\", " ")
    text = text.replace("-", " ")
    text = "_".join(text.split())
    text = "".join(ch for ch in text if ch.isalnum() or ch == "_")

    if not text:
        text = "unknown"

    if text[0].isdigit():
        text = f"entity_{text}"

    return text


def entity_uri(label: str) -> URIRef:
    return EX[slugify(label)]


def predicate_uri(label: str) -> URIRef:
    return EX[slugify(label)]


def statement_uri(subject: str, predicate: str, obj: str, source: str) -> URIRef:
    key = f"{subject}|{predicate}|{obj}|{source}"
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    return EX[f"statement_{digest}"]


def choose_input_file() -> Path:
    """
    Prefer live extracted knowledge if available, otherwise local.
    """
    if INPUT_LIVE.exists():
        return INPUT_LIVE

    if INPUT_LOCAL.exists():
        return INPUT_LOCAL

    raise FileNotFoundError(
        "No extracted knowledge CSV found. Expected one of:\n"
        f"- {INPUT_LIVE}\n"
        f"- {INPUT_LOCAL}"
    )


def safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


# =============================
# ONTOLOGY CREATION
# =============================

def add_ontology(graph: Graph) -> None:
    """
    Add simple ontology classes and properties.
    """
    graph.add((EX.KnowledgeStatement, RDF.type, OWL.Class))
    graph.add((EX.DomainEntity, RDF.type, OWL.Class))
    graph.add((EX.Exercise, RDF.type, OWL.Class))
    graph.add((EX.Muscle, RDF.type, OWL.Class))
    graph.add((EX.Joint, RDF.type, OWL.Class))
    graph.add((EX.Equipment, RDF.type, OWL.Class))
    graph.add((EX.TechniqueCue, RDF.type, OWL.Class))
    graph.add((EX.BiomechanicalConcept, RDF.type, OWL.Class))

    for cls in [
        EX.Exercise,
        EX.Muscle,
        EX.Joint,
        EX.Equipment,
        EX.TechniqueCue,
        EX.BiomechanicalConcept,
    ]:
        graph.add((cls, RDFS.subClassOf, EX.DomainEntity))

    object_properties = [
        "targetsMuscle",
        "influences",
        "increases",
        "decreases",
        "reduces",
        "appliesForce",
        "produces",
        "requires",
        "involves",
        "allows",
        "extends",
        "flexes",
        "abducts",
        "adducts",
        "relatedTo",
    ]

    for prop in object_properties:
        graph.add((EX[prop], RDF.type, OWL.ObjectProperty))

    datatype_properties = [
        "confidence",
        "domainSimilarity",
        "evidenceSentence",
        "sourceDocument",
        "originalSubject",
        "originalPredicate",
        "originalObject",
        "alignedSubject",
        "alignedPredicate",
        "alignedObject",
        "category",
    ]

    for prop in datatype_properties:
        graph.add((EX[prop], RDF.type, OWL.DatatypeProperty))

    graph.add((EX.hasSubject, RDF.type, OWL.ObjectProperty))
    graph.add((EX.hasPredicate, RDF.type, OWL.ObjectProperty))
    graph.add((EX.hasObject, RDF.type, OWL.ObjectProperty))


# =============================
# MAIN RDF BUILDING
# =============================

def build_initial_kb() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_file = choose_input_file()
    print(f"Reading extracted knowledge from: {input_file}")

    df = pd.read_csv(input_file)

    required_cols = ["subject", "relation", "object"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in CSV: {col}")

    graph = Graph()
    graph.bind("ex", EX)
    graph.bind("schema", SCHEMA)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    graph.bind("xsd", XSD)

    add_ontology(graph)

    alignment_rows = []

    for idx, row in df.iterrows():
        original_subject = str(row.get("subject", "")).strip()
        original_predicate = str(row.get("relation", "")).strip()
        original_object = str(row.get("object", "")).strip()

        if not original_subject or not original_predicate or not original_object:
            continue

        aligned_subject = canonical_entity(original_subject)
        aligned_object = canonical_entity(original_object)
        aligned_predicate = canonical_predicate(original_predicate)

        subj_uri = entity_uri(aligned_subject)
        obj_uri = entity_uri(aligned_object)
        pred_uri = predicate_uri(aligned_predicate)

        subj_type = guess_entity_type(aligned_subject)
        obj_type = guess_entity_type(aligned_object)

        confidence = safe_float(row.get("max_confidence", row.get("confidence", 0.0)))
        domain_similarity = safe_float(row.get("max_domain_similarity", row.get("domain_similarity", 0.0)))
        evidence_count = int(row.get("evidence_count", 1)) if str(row.get("evidence_count", "1")).isdigit() else 1

        source = str(row.get("sources", row.get("source", "unknown")))
        example_sentence = str(row.get("example_sentence", row.get("sentence", "")))
        category = str(row.get("category", "unknown"))

        # Main RDF triple
        graph.add((subj_uri, pred_uri, obj_uri))

        # Entity labels and types
        graph.add((subj_uri, RDF.type, EX[subj_type]))
        graph.add((obj_uri, RDF.type, EX[obj_type]))
        graph.add((subj_uri, RDFS.label, Literal(aligned_subject)))
        graph.add((obj_uri, RDFS.label, Literal(aligned_object)))

        # Predicate label
        graph.add((pred_uri, RDFS.label, Literal(aligned_predicate)))

        # Statement node for confidence and evidence
        stmt_uri = statement_uri(aligned_subject, aligned_predicate, aligned_object, source)
        graph.add((stmt_uri, RDF.type, EX.KnowledgeStatement))
        graph.add((stmt_uri, EX.hasSubject, subj_uri))
        graph.add((stmt_uri, EX.hasPredicate, pred_uri))
        graph.add((stmt_uri, EX.hasObject, obj_uri))

        graph.add((stmt_uri, EX.confidence, Literal(confidence, datatype=XSD.float)))
        graph.add((stmt_uri, EX.domainSimilarity, Literal(domain_similarity, datatype=XSD.float)))
        graph.add((stmt_uri, EX.evidenceCount, Literal(evidence_count, datatype=XSD.integer)))
        graph.add((stmt_uri, EX.sourceDocument, Literal(source)))
        graph.add((stmt_uri, EX.evidenceSentence, Literal(example_sentence)))
        graph.add((stmt_uri, EX.category, Literal(category)))

        graph.add((stmt_uri, EX.originalSubject, Literal(original_subject)))
        graph.add((stmt_uri, EX.originalPredicate, Literal(original_predicate)))
        graph.add((stmt_uri, EX.originalObject, Literal(original_object)))
        graph.add((stmt_uri, EX.alignedSubject, Literal(aligned_subject)))
        graph.add((stmt_uri, EX.alignedPredicate, Literal(aligned_predicate)))
        graph.add((stmt_uri, EX.alignedObject, Literal(aligned_object)))

        alignment_rows.append({
            "original_subject": original_subject,
            "aligned_subject": aligned_subject,
            "subject_type": subj_type,
            "original_predicate": original_predicate,
            "aligned_predicate": aligned_predicate,
            "original_object": original_object,
            "aligned_object": aligned_object,
            "object_type": obj_type,
            "confidence": confidence,
            "domain_similarity": domain_similarity,
            "source": source,
            "example_sentence": example_sentence,
        })

    # Save ontology-only graph
    ontology_graph = Graph()
    ontology_graph.bind("ex", EX)
    ontology_graph.bind("owl", OWL)
    ontology_graph.bind("rdfs", RDFS)
    ontology_graph.bind("xsd", XSD)
    add_ontology(ontology_graph)
    ontology_graph.serialize(destination=ONTOLOGY_FILE, format="turtle")

    # Save full initial KB
    graph.serialize(destination=INITIAL_KB_FILE, format="turtle")

    # Save alignment report
    alignment_df = pd.DataFrame(alignment_rows)
    alignment_df.to_csv(ALIGNMENT_REPORT_FILE, index=False, encoding="utf-8")

    print("Initial KB construction complete.")
    print(f"Ontology saved to: {ONTOLOGY_FILE}")
    print(f"Initial KB saved to: {INITIAL_KB_FILE}")
    print(f"Alignment report saved to: {ALIGNMENT_REPORT_FILE}")
    print(f"Total RDF triples: {len(graph)}")
    print(f"Aligned rows: {len(alignment_df)}")


if __name__ == "__main__":
    build_initial_kb()