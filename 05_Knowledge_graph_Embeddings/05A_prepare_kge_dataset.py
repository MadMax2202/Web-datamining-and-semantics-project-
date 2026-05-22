"""
05A_prepare_kge_dataset.py

This script prepares the Knowledge Graph Embedding dataset.

It loads the expanded RDF knowledge base produced in the KB construction step:

    01_Data/kb_outputs/expanded_kb.ttl

Then it:
1. Removes metadata triples such as labels, confidence scores, evidence sentences, and RDF types.
2. Keeps only semantic object-property triples useful for link prediction.
3. Converts RDF URIs into clean string identifiers.
4. Creates train / validation / test splits.
5. Creates entity and relation ID mappings.
6. Creates size-sensitivity subsets.

Output folder:

    05_Knowledge_Graph_Embeddings/outputs/

Main outputs:
- semantic_triples.tsv
- train.txt
- valid.txt
- test.txt
- entity_to_id.tsv
- relation_to_id.tsv
- kge_dataset_summary.md
"""

from pathlib import Path
import random
import re
import pandas as pd

from rdflib import Graph, Namespace, URIRef, RDF, RDFS, OWL


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_KB = PROJECT_ROOT / "01_Data" / "kb_outputs" / "expanded_kb.ttl"

OUTPUT_DIR = PROJECT_ROOT / "05_Knowledge_Graph_Embeddings" / "outputs"

SEMANTIC_TRIPLES_FILE = OUTPUT_DIR / "semantic_triples.tsv"

TRAIN_FILE = OUTPUT_DIR / "train.txt"
VALID_FILE = OUTPUT_DIR / "valid.txt"
TEST_FILE = OUTPUT_DIR / "test.txt"

ENTITY_TO_ID_FILE = OUTPUT_DIR / "entity_to_id.tsv"
RELATION_TO_ID_FILE = OUTPUT_DIR / "relation_to_id.tsv"

SUMMARY_FILE = OUTPUT_DIR / "kge_dataset_summary.md"


# =============================
# NAMESPACES
# =============================

EX = Namespace("http://example.org/benchpress-kg/")


# =============================
# FILTERING SETTINGS
# =============================

EXCLUDED_PREDICATES = {
    RDF.type,
    RDFS.label,
    RDFS.subClassOf,
    OWL.sameAs,
    EX.confidence,
    EX.domainSimilarity,
    EX.evidenceSentence,
    EX.sourceDocument,
    EX.originalSubject,
    EX.originalPredicate,
    EX.originalObject,
    EX.alignedSubject,
    EX.alignedPredicate,
    EX.alignedObject,
    EX.category,
    EX.evidenceCount,
    EX.hasSubject,
    EX.hasPredicate,
    EX.hasObject,
}

EXCLUDED_PREFIX_FRAGMENTS = {
    "statement_",
    "KnowledgeStatement",
}


# =============================
# HELPERS
# =============================

def clean_name(uri) -> str:
    """
    Convert a URI into a readable machine-learning identifier.
    """
    text = str(uri).split("/")[-1].split("#")[-1]
    text = text.strip()

    text = re.sub(r"[^a-zA-Z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text)
    text = text.strip("_")

    if not text:
        text = "unknown"

    if text[0].isdigit():
        text = f"entity_{text}"

    return text


def is_ex_namespace(uri) -> bool:
    return str(uri).startswith(str(EX))


def is_statement_node(uri) -> bool:
    text = str(uri)
    return any(fragment in text for fragment in EXCLUDED_PREFIX_FRAGMENTS)


def is_semantic_triple(s, p, o) -> bool:
    """
    Keep only useful semantic triples for KGE link prediction.
    """
    if not isinstance(s, URIRef):
        return False

    if not isinstance(p, URIRef):
        return False

    if not isinstance(o, URIRef):
        return False

    if p in EXCLUDED_PREDICATES:
        return False

    if not is_ex_namespace(s):
        return False

    if not is_ex_namespace(p):
        return False

    if not is_ex_namespace(o):
        return False

    if is_statement_node(s):
        return False

    if is_statement_node(o):
        return False

    return True


def split_triples(df: pd.DataFrame, train_ratio=0.8, valid_ratio=0.1, seed=42):
    """
    Split triples into train / valid / test.
    """
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    n = len(df)

    if n < 5:
        return df, pd.DataFrame(columns=df.columns), pd.DataFrame(columns=df.columns)

    train_end = max(1, int(n * train_ratio))
    valid_end = max(train_end + 1, int(n * (train_ratio + valid_ratio)))

    if valid_end >= n:
        valid_end = n - 1

    train_df = df.iloc[:train_end].copy()
    valid_df = df.iloc[train_end:valid_end].copy()
    test_df = df.iloc[valid_end:].copy()

    return train_df, valid_df, test_df


def save_triples(df: pd.DataFrame, path: Path) -> None:
    """
    Save triples in KGE format: head TAB relation TAB tail.
    """
    df[["head", "relation", "tail"]].to_csv(
        path,
        sep="\t",
        index=False,
        header=False,
        encoding="utf-8"
    )


def create_id_mappings(df: pd.DataFrame):
    entities = sorted(set(df["head"]).union(set(df["tail"])))
    relations = sorted(set(df["relation"]))

    entity_to_id = pd.DataFrame({
        "entity": entities,
        "id": range(len(entities))
    })

    relation_to_id = pd.DataFrame({
        "relation": relations,
        "id": range(len(relations))
    })

    return entity_to_id, relation_to_id


def save_size_subsets(df: pd.DataFrame, seed=42):
    """
    Create size-sensitivity subsets.

    The assignment mentions 20k / 50k / full. Since this project KB is much
    smaller, the script creates capped versions:
    - size_20k_cap.tsv = min(20k, available triples)
    - size_50k_cap.tsv = min(50k, available triples)
    - size_full.tsv = all available triples

    This keeps the pipeline honest and scalable.
    """
    n = len(df)

    subset_specs = [
        ("size_20k_cap.tsv", min(20000, n)),
        ("size_50k_cap.tsv", min(50000, n)),
        ("size_full.tsv", n),
    ]

    subset_rows = []

    for filename, size in subset_specs:
        subset = df.sample(n=size, random_state=seed).reset_index(drop=True)
        path = OUTPUT_DIR / filename
        save_triples(subset, path)

        subset_rows.append({
            "subset_file": filename,
            "requested_size": filename.replace("size_", "").replace(".tsv", ""),
            "actual_triples": size,
        })

    subset_df = pd.DataFrame(subset_rows)
    subset_df.to_csv(OUTPUT_DIR / "size_subsets_summary.csv", index=False)


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

    print(f"Loading RDF graph from: {INPUT_KB}")

    graph = Graph()
    graph.parse(INPUT_KB, format="turtle")

    triples = []

    for s, p, o in graph:
        if not is_semantic_triple(s, p, o):
            continue

        triples.append({
            "head": clean_name(s),
            "relation": clean_name(p),
            "tail": clean_name(o),
            "raw_subject": str(s),
            "raw_predicate": str(p),
            "raw_object": str(o),
        })

    df = pd.DataFrame(triples)

    if df.empty:
        raise ValueError("No semantic triples found for KGE training.")

    df = df.drop_duplicates(subset=["head", "relation", "tail"])
    df = df.sort_values(["head", "relation", "tail"]).reset_index(drop=True)

    df.to_csv(SEMANTIC_TRIPLES_FILE, sep="\t", index=False, encoding="utf-8")

    train_df, valid_df, test_df = split_triples(df)

    save_triples(train_df, TRAIN_FILE)
    save_triples(valid_df, VALID_FILE)
    save_triples(test_df, TEST_FILE)

    entity_to_id, relation_to_id = create_id_mappings(df)

    entity_to_id.to_csv(ENTITY_TO_ID_FILE, sep="\t", index=False, encoding="utf-8")
    relation_to_id.to_csv(RELATION_TO_ID_FILE, sep="\t", index=False, encoding="utf-8")

    save_size_subsets(df)

    summary = []
    summary.append("# KGE Dataset Summary\n")
    summary.append("## Source\n")
    summary.append(f"- Input RDF graph: `{INPUT_KB}`\n")
    summary.append("## Cleaning Strategy\n")
    summary.append("- Removed RDF metadata triples such as `rdf:type`, `rdfs:label`, confidence scores, evidence sentences, and source document metadata.")
    summary.append("- Kept only semantic object-property triples where subject, predicate, and object are project KB URIs.")
    summary.append("- Removed statement/evidence nodes from the KGE training dataset.")
    summary.append("")
    summary.append("## Final Dataset\n")
    summary.append(f"- Semantic triples: `{len(df)}`")
    summary.append(f"- Training triples: `{len(train_df)}`")
    summary.append(f"- Validation triples: `{len(valid_df)}`")
    summary.append(f"- Test triples: `{len(test_df)}`")
    summary.append(f"- Entities: `{len(entity_to_id)}`")
    summary.append(f"- Relations: `{len(relation_to_id)}`")
    summary.append("")
    summary.append("## Size Sensitivity\n")
    summary.append("The assignment requests 20k / 50k / full size-sensitivity tests.")
    summary.append("Because this domain-specific KB is smaller than 20k semantic triples, capped subsets were created:")
    summary.append("")
    summary.append("- `size_20k_cap.tsv`: min(20k, available triples)")
    summary.append("- `size_50k_cap.tsv`: min(50k, available triples)")
    summary.append("- `size_full.tsv`: all available triples")
    summary.append("")
    summary.append("This keeps the experiment reproducible and honest while preserving the same evaluation logic.")

    SUMMARY_FILE.write_text("\n".join(summary), encoding="utf-8")

    print("KGE dataset preparation complete.")
    print(f"Semantic triples: {len(df)}")
    print(f"Train / valid / test: {len(train_df)} / {len(valid_df)} / {len(test_df)}")
    print(f"Entities: {len(entity_to_id)}")
    print(f"Relations: {len(relation_to_id)}")
    print(f"Outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    random.seed(42)
    main()