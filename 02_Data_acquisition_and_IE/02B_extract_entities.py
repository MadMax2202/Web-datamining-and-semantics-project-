"""
extract_entities.py

This script performs the Information Extraction step of the project.

It reads the cleaned JSONL files created by crawl_and_clean.py and extracts
domain-relevant knowledge triples from the bench press / strength training corpus.

The script uses spaCy for sentence segmentation, dependency parsing, noun phrase
detection, and semantic similarity. It focuses on useful sentences related to:
1. Technique instructions, for example grip, bar path, scapula retraction, elbow tuck.
2. Biomechanics, for example force, torque, moment arm, EMG activation, range of motion.

For each useful sentence, the script tries to extract triples of the form:

    subject ; relation ; object

Example:
    bench press ; activate ; pectoralis major
    grip width ; influence ; range of motion
    bar ; touch ; chest

The output is a CSV file containing normalized subjects, relations, objects,
confidence scores, source documents, and example evidence sentences. This CSV is
used later for RDF/knowledge-base construction.
"""

import json
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import pandas as pd
import spacy
from spacy.matcher import DependencyMatcher
from spacy.tokens import Span, Token


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_LOCAL = PROJECT_ROOT / "01_Data" / "crawler_outputs" / "crawler_output_local.jsonl"
INPUT_LIVE = PROJECT_ROOT / "01_Data" / "crawler_outputs" / "crawler_output_live.jsonl"

OUTPUT_LOCAL = PROJECT_ROOT / "01_Data" / "crawler_outputs" / "extracted_knowledge_local.csv"
OUTPUT_LIVE = PROJECT_ROOT / "01_Data" / "crawler_outputs" / "extracted_knowledge_live.csv"


# =============================
# LOAD SPACY MODEL
# =============================

try:
    nlp = spacy.load("en_core_web_md")
except OSError:
    raise OSError(
        "spaCy model 'en_core_web_md' is not installed.\n"
        "Install it with:\n"
        "python -m spacy download en_core_web_md"
    )

if "sentencizer" not in nlp.pipe_names:
    nlp.add_pipe("sentencizer", first=True)


# =============================
# DOMAIN ANCHOR
# =============================

DOMAIN_ANCHOR = nlp(
    "bench press biomechanics muscle activation EMG joint mechanics force torque moment arm "
    "grip width bar path scapula shoulder elbow wrist triceps pectoralis deltoid sticking point "
    "range of motion technique cues retract tuck arch touch chest"
)

SIM_THRESHOLD = 0.50


# =============================
# TEXT CLEANUP
# =============================

_ws = re.compile(r"\s+")
_bullets = re.compile(r"[•·▪●]+")


def normalize_ws(text: str) -> str:
    """
    Normalize whitespace and remove bullet-like characters.
    """
    text = text.replace("\n", " ")
    text = _bullets.sub(" ", text)
    text = re.sub(r":\s*-\s*", ". ", text)
    text = re.sub(r":\s*•\s*", ". ", text)
    text = re.sub(r":\s*\*\s*", ". ", text)
    text = _ws.sub(" ", text)
    return text.strip()


def sentence_hash(text: str) -> str:
    """
    Hash a sentence so repeated evidence can be identified.
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# =============================
# FILTER CONSTANTS
# =============================

MAX_ENTITY_CHARS = 80
MAX_ENTITY_COMMAS = 1
MIN_ENTITY_ALPHA = 3
MAX_ENTITY_TOKENS = 12

PRONOUN_LIKE = {
    "that", "this", "these", "those", "it", "they", "them", "we", "you", "i",
    "what", "who", "which", "one", "ones", "someone", "anyone", "most", "many",
    "none", "all", "some", "both", "your", "my", "our", "their"
}

RESEARCH_META_PATTERNS = [
    r"\bthis study\b", r"\bthe present study\b", r"\bwe (found|show|demonstrate)\b",
    r"\bhypothesis\b", r"\bmethodolog(y|ies)\b", r"\babstract\b", r"\bconclusion\b",
    r"\bfindings\b", r"\bresults\b", r"\bto the best of (our|authors') knowledge\b",
    r"\bfuture research\b", r"\bstatistical\b", r"\bsignificant\b", r"\bstandard deviation\b",
    r"\bparticipants?\b", r"\bexperiment\b", r"\bprotocol\b", r"\binclusion criteria\b",
    r"\bdata (were|was) (collected|recorded)\b",
]

META_SENTENCE_PATTERNS = [
    r"\btable\s+\d+\b", r"\bfigure\s+\d+\b", r"\bsection\s+\d+\b",
    r"\breferences?\b", r"\bcitation\b", r"\bgoogle scholar\b",
]

BULLETISH = re.compile(r":\s*[-•*]")

BAD_RELATIONS = {
    "be", "have", "do", "say", "tell", "go", "get", "make", "use", "include",
    "show", "find", "reveal", "provide", "discuss", "offer", "receive",
    "know", "feel", "explain", "represent", "describe", "introduce", "confirm",
    "suggest", "highlight", "consider", "establish", "aim", "conclude", "fill"
}

GENERIC_NODES = {
    "people", "person", "individual", "most people", "some people",
    "exercises", "events", "approach", "work", "study", "results", "findings",
    "conclusion", "abstract", "instruments", "participants", "research", "methods",
    "influence", "level", "degree"
}

TECHNIQUE_PATTERNS = [
    r"\bstart with\b", r"\blie (with|on)\b", r"\bset (your|the)\b",
    r"\bgrip\b", r"\b(retract|depress) (your )?scapula\b",
    r"\btuck (your )?elbows\b", r"\barch\b", r"\bbrace\b",
    r"\blower the bar\b", r"\bpress\b", r"\btouch (the )?chest\b",
    r"\bbar (grazes|touches)\b", r"\bkeep (your )?wrists\b",
    r"\brack\b"
]

BIOMECH_PATTERNS = [
    r"\b(moment arm|moment|torque)\b",
    r"\b(force|newton|n\b)\b",
    r"\b(velocity|acceleration|power|work)\b",
    r"\b(emg|activation)\b",
    r"\b(horizontal flexion|abduction|adduction|internal rotation|external rotation)\b",
    r"\b(eccentric|concentric)\b",
    r"\b(sticking region|sticking point)\b",
    r"\b(range of motion|rom)\b",
    r"\b(\d+(\.\d+)?\s*(%|°|deg|n|kg|m/s|m s))\b",
]

KG_KEYWORDS = [
    "bench press", "barbell", "bar", "grip", "grip width", "bar path",
    "scapula", "scapulae", "scapular", "retraction", "protraction", "tilting",
    "shoulder", "elbow", "wrist", "torso", "spine",
    "pectoralis", "pecs", "triceps", "deltoid", "lats", "rotator cuff",
    "serratus", "clavicular", "sternocostal",
    "moment", "moment arm", "force", "activation", "emg", "torque",
    "eccentric", "concentric", "range of motion"
]


# =============================
# SENTENCE FILTERING
# =============================

def has_pattern(patterns: List[str], sent_text: str) -> bool:
    """
    Return True if at least one regex pattern matches the sentence.
    """
    s = sent_text.lower()
    return any(re.search(pattern, s) for pattern in patterns)


def is_domain_sentence(sent: Span) -> bool:
    """
    Compare a sentence with the domain anchor using spaCy vector similarity.
    """
    try:
        return sent.similarity(DOMAIN_ANCHOR) >= SIM_THRESHOLD
    except Exception:
        return False


def sentence_is_useful(sent_text: str) -> Tuple[bool, str]:
    """
    Keep only sentences that are useful for the project domain.

    Categories:
    - technique
    - biomechanics
    - domain
    - drop
    """
    s = sent_text.lower()

    if BULLETISH.search(sent_text):
        return False, "drop"

    if has_pattern(RESEARCH_META_PATTERNS, sent_text):
        return False, "drop"

    if has_pattern(META_SENTENCE_PATTERNS, sent_text):
        return False, "drop"

    is_technique = any(re.search(pattern, s) for pattern in TECHNIQUE_PATTERNS)
    is_biomechanics = any(re.search(pattern, s) for pattern in BIOMECH_PATTERNS)

    if is_technique:
        return True, "technique"

    if is_biomechanics:
        return True, "biomechanics"

    if any(keyword in s for keyword in KG_KEYWORDS):
        return True, "domain"

    return False, "drop"


# =============================
# ENTITY CLEANUP
# =============================

CANON = {
    "pecs": "pectoralis major",
    "your pecs": "pectoralis major",
    "pectorals": "pectoralis major",
    "chest": "pectoralis major",
    "delts": "deltoids",
    "front delts": "anterior deltoid",
    "scapulae": "scapula",
    "barbell": "bar",
}


def strip_determiners(span: Span) -> Span:
    """
    Remove determiners such as 'the' or 'a' from the beginning of a span.
    """
    start = span.start

    while start < span.end and span.doc[start].dep_ == "det":
        start += 1

    if start >= span.end:
        return span

    return span.doc[start:span.end]


def span_token_count(span: Span) -> int:
    """
    Count non-space tokens in a span.
    """
    return len([token for token in span if not token.is_space])


def entity_is_valid(text: str) -> bool:
    """
    Validate an entity mention after cleaning.
    """
    t = text.strip()

    if not t or len(t) > MAX_ENTITY_CHARS:
        return False

    if t.count(",") > MAX_ENTITY_COMMAS:
        return False

    if sum(ch.isalpha() for ch in t) < MIN_ENTITY_ALPHA:
        return False

    low = t.lower()

    if low in PRONOUN_LIKE:
        return False

    if low in GENERIC_NODES:
        return False

    return True


def clean_entity(span: Span) -> Optional[str]:
    """
    Normalize and canonicalize an entity span.
    """
    span = strip_determiners(span)

    if span_token_count(span) > MAX_ENTITY_TOKENS:
        return None

    text = normalize_ws(span.text)
    text = text.strip(" ,;:.-–—()[]{}\"“”'")

    if not entity_is_valid(text):
        return None

    low = text.lower()
    low = re.sub(r"\s+", " ", low).strip()

    low = CANON.get(low, low)

    low = re.sub(r"\b(your|their|our|my)\b\s+", "", low).strip()

    if not entity_is_valid(low):
        return None

    return low


# =============================
# DEPENDENCY UTILITIES
# =============================

def best_np_containing(token: Token, noun_chunks: List[Span]) -> Span:
    """
    Return the shortest noun chunk containing the token.
    If none exists, return the token itself as a span.
    """
    candidates = [
        noun_chunk
        for noun_chunk in noun_chunks
        if noun_chunk.start <= token.i < noun_chunk.end
    ]

    if not candidates:
        return token.doc[token.i:token.i + 1]

    candidates.sort(key=lambda span: span.end - span.start)
    return candidates[0]


def expand_with_compounds(span: Span) -> Span:
    """
    Expand noun spans with compound or adjective modifiers.
    """
    doc = span.doc
    start = span.start
    end = span.end

    i = start - 1

    while i >= 0:
        token = doc[i]

        if (
            token.dep_ in {"compound", "amod", "nummod", "poss"}
            and start <= token.head.i < end
        ):
            start = i
            i -= 1
            continue

        break

    return doc[start:end]


# =============================
# OBJECT REFINEMENT
# =============================

GOOD_PREPS = {
    "of", "on", "in", "at", "to", "for", "from", "with", "into", "over", "under"
}


def refine_object(
    rel: Token,
    obj_span: Span,
    noun_chunks: List[Span]
) -> Tuple[Span, str]:
    """
    If the object contains a useful prepositional phrase, refine the object.

    Example:
    relation = "activation"
    object = "activation of pectoralis major"

    becomes:
    relation = "activation_of"
    object = "pectoralis major"
    """
    obj_root = obj_span.root
    base_rel = rel.lemma_.lower().strip()

    preps = [
        child
        for child in obj_root.children
        if child.dep_ == "prep" and child.lemma_.lower() in GOOD_PREPS
    ]

    if not preps:
        return obj_span, base_rel

    for prep in preps:
        pobj = next((child for child in prep.children if child.dep_ == "pobj"), None)

        if pobj is None:
            continue

        pobj_span = expand_with_compounds(best_np_containing(pobj, noun_chunks))
        enriched_relation = f"{base_rel}_{prep.lemma_.lower()}"

        return pobj_span, enriched_relation

    return obj_span, base_rel


# =============================
# RELATION VALIDATION
# =============================

def predicate_is_valid(rel: Token) -> bool:
    """
    Validate the extracted relation predicate.
    """
    lemma = rel.lemma_.lower().strip()

    if not lemma.isalpha():
        return False

    if lemma in BAD_RELATIONS:
        return False

    if len(lemma) < 3:
        return False

    return True


# =============================
# DEPENDENCY MATCHER
# =============================

matcher = DependencyMatcher(nlp.vocab)

RELATION_PATTERN = [
    {
        "RIGHT_ID": "rel",
        "RIGHT_ATTRS": {
            "POS": {"IN": ["VERB", "NOUN"]}
        }
    },
    {
        "LEFT_ID": "rel",
        "REL_OP": ">",
        "RIGHT_ID": "subj",
        "RIGHT_ATTRS": {
            "DEP": {"IN": ["nsubj", "nsubjpass"]}
        }
    },
    {
        "LEFT_ID": "rel",
        "REL_OP": ">",
        "RIGHT_ID": "obj",
        "RIGHT_ATTRS": {
            "DEP": {"IN": ["dobj", "pobj", "obl", "attr", "nmod"]}
        }
    }
]

matcher.add("RELATION", [RELATION_PATTERN])


# =============================
# TRIPLE EXTRACTION
# =============================

def confidence_score(similarity: float, category: str) -> float:
    """
    Compute a simple confidence score from domain similarity and sentence category.
    """
    normalized_similarity = min(
        max((similarity - SIM_THRESHOLD) / (1.0 - SIM_THRESHOLD), 0.0),
        1.0
    )

    confidence = normalized_similarity * 0.7

    if category == "biomechanics":
        confidence += 0.2
    elif category == "technique":
        confidence += 0.15
    elif category == "domain":
        confidence += 0.1

    return round(min(confidence, 1.0), 3)


def extract_triplets(text: str, source: str) -> List[Dict]:
    """
    Extract subject-relation-object triples from one cleaned document.
    """
    doc = nlp(normalize_ws(text))
    triplets: List[Dict] = []

    sentence_info = {}

    for sent in doc.sents:
        sent_text = normalize_ws(sent.text)

        if not sent_text:
            continue

        keep, category = sentence_is_useful(sent_text)

        if not keep:
            continue

        if not is_domain_sentence(sent):
            continue

        sim = float(sent.similarity(DOMAIN_ANCHOR))

        sentence_info[(sent.start, sent.end)] = {
            "span": sent,
            "text": sent_text,
            "category": category,
            "similarity": sim
        }

    if not sentence_info:
        return triplets

    noun_chunks = list(doc.noun_chunks)
    matches = matcher(doc)

    for _, token_ids in matches:
        rel_id, subj_id, obj_id = token_ids

        rel = doc[rel_id]
        subj_tok = doc[subj_id]
        obj_tok = doc[obj_id]

        matching_sentence = None

        for (start, end), info in sentence_info.items():
            if start <= rel.i < end and start <= subj_tok.i < end and start <= obj_tok.i < end:
                matching_sentence = info
                break

        if matching_sentence is None:
            continue

        if not predicate_is_valid(rel):
            continue

        sent_text = matching_sentence["text"]
        category = matching_sentence["category"]
        sim = matching_sentence["similarity"]

        sent_start = matching_sentence["span"].start
        sent_end = matching_sentence["span"].end

        sent_noun_chunks = [
            noun_chunk
            for noun_chunk in noun_chunks
            if sent_start <= noun_chunk.start and noun_chunk.end <= sent_end
        ]

        subj_span = expand_with_compounds(best_np_containing(subj_tok, sent_noun_chunks))
        obj_span = expand_with_compounds(best_np_containing(obj_tok, sent_noun_chunks))

        obj_span_refined, relation = refine_object(rel, obj_span, sent_noun_chunks)

        subj_clean = clean_entity(subj_span)
        obj_clean = clean_entity(obj_span_refined)

        if not subj_clean or not obj_clean:
            continue

        if subj_clean == obj_clean:
            continue

        side_text = f"{subj_clean} {obj_clean}"

        if not any(keyword in side_text for keyword in KG_KEYWORDS):
            if category != "technique":
                continue

        confidence = confidence_score(sim, category)

        triplets.append({
            "subject": subj_clean,
            "relation": relation,
            "object": obj_clean,
            "source": source,
            "sentence": sent_text,
            "sentence_hash": sentence_hash(sent_text),
            "domain_similarity": round(sim, 3),
            "confidence": confidence,
            "category": category
        })

    return triplets


# =============================
# POST-PROCESSING
# =============================

def postprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate extracted triples and aggregate evidence.
    """
    if df.empty:
        return df

    df["triple_key"] = (
        df["subject"]
        + "|"
        + df["relation"]
        + "|"
        + df["object"]
    )

    df = (
        df.sort_values(["confidence", "domain_similarity"], ascending=False)
          .drop_duplicates(subset=["triple_key", "source"], keep="first")
    )

    aggregated = (
        df.groupby("triple_key")
          .agg(
              subject=("subject", "first"),
              relation=("relation", "first"),
              object=("object", "first"),
              category=("category", "first"),
              max_confidence=("confidence", "max"),
              max_domain_similarity=("domain_similarity", "max"),
              evidence_count=("sentence_hash", "count"),
              sources=("source", lambda s: "; ".join(sorted(set(s)))),
              example_sentence=("sentence", "first"),
          )
          .reset_index(drop=True)
    )

    return aggregated.sort_values(
        [
            "category",
            "max_confidence",
            "max_domain_similarity",
            "evidence_count"
        ],
        ascending=[True, False, False, False]
    )


# =============================
# FILE PROCESSING
# =============================

def process_file(input_path: Path, output_path: Path) -> None:
    """
    Read one JSONL crawler output file and write extracted triples to CSV.
    """
    all_triplets: List[Dict] = []

    if not input_path.exists():
        print(f"Missing input file: {input_path}")
        return

    print(f"Reading: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line {line_number} in {input_path.name}")
                continue

            text = record.get("text", "") or ""
            source = record.get("file") or record.get("url") or "unknown"

            if not text.strip():
                continue

            extracted = extract_triplets(text, source)
            all_triplets.extend(extracted)

    raw_df = pd.DataFrame(all_triplets)

    if raw_df.empty:
        print(f"No useful triples extracted from {input_path.name}")
        return

    kg_df = postprocess_df(raw_df)

    output_path.parent.mkdir(exist_ok=True)
    kg_df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"Saved {len(kg_df)} useful KG edges to: {output_path}")


# =============================
# MAIN
# =============================

def main() -> None:
    print("Starting Information Extraction")
    print()

    print("Processing LOCAL crawler output...")
    process_file(INPUT_LOCAL, OUTPUT_LOCAL)

    print()

    print("Processing LIVE crawler output...")
    process_file(INPUT_LIVE, OUTPUT_LIVE)

    print()
    print("Information Extraction complete.")


if __name__ == "__main__":
    main()