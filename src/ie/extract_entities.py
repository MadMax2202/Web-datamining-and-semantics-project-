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
DATA_DIR = Path("data")

INPUT_LOCAL = DATA_DIR / "crawler_output_local.jsonl"
INPUT_LIVE = DATA_DIR / "crawler_output_live.jsonl"

OUTPUT_LOCAL = DATA_DIR / "extracted_knowledge_local.csv"
OUTPUT_LIVE = DATA_DIR / "extracted_knowledge_live.csv"


# =============================
# LOAD MODEL
# =============================
nlp = spacy.load("en_core_web_md")
if "sentencizer" not in nlp.pipe_names:
    nlp.add_pipe("sentencizer", first=True)


# =============================
# DOMAIN ANCHOR (broad)
# =============================
DOMAIN_ANCHOR = nlp(
    "bench press biomechanics muscle activation EMG joint mechanics force torque moment arm "
    "grip width bar path scapula shoulder elbow wrist triceps pectoralis deltoid sticking point "
    "range of motion technique cues retract tuck arch touch chest"
)
SIM_THRESHOLD = 0.50  # slightly lower, but we will add strict usefulness gating


# =============================
# TEXT CLEANUP
# =============================
_ws = re.compile(r"\s+")
_bullets = re.compile(r"[•·▪●]+")

def normalize_ws(text: str) -> str:
    text = text.replace("\n", " ")
    text = _bullets.sub(" ", text)
    text = re.sub(r":\s*-\s*", ". ", text)
    text = re.sub(r":\s*•\s*", ". ", text)
    text = re.sub(r":\s*\*\s*", ". ", text)
    text = _ws.sub(" ", text)
    return text.strip()

def sentence_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# =============================
# FILTERS
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

# Hard-kill meta/research sentences
RESEARCH_META_PATTERNS = [
    r"\bthis study\b", r"\bthe present study\b", r"\bwe (found|show|demonstrate)\b",
    r"\bhypothesis\b", r"\bmethodolog(y|ies)\b", r"\babstract\b", r"\bconclusion\b",
    r"\bfindings\b", r"\bresults\b", r"\bto the best of (our|authors') knowledge\b",
    r"\bfuture research\b", r"\bstatistical\b", r"\bsignificant\b", r"\bstandard deviation\b",
    r"\bparticipants?\b", r"\bexperiment\b", r"\bprotocol\b", r"\binclusion criteria\b",
    r"\bdata (were|was) (collected|recorded)\b",
]

# Headings/tables/figures
META_SENTENCE_PATTERNS = [
    r"\btable\s+\d+\b", r"\bfigure\s+\d+\b", r"\bsection\s+\d+\b",
    r"\breferences?\b", r"\bcitation\b", r"\bgoogle scholar\b",
]

# If colon + bullets, usually a list block
BULLETISH = re.compile(r":\s*[-•*]")

# Bad relations (discourse/meta)
BAD_RELATIONS = {
    "be", "have", "do", "say", "tell", "go", "get", "make", "use", "include",
    "show", "find", "reveal", "provide", "discuss", "offer", "receive",
    "know", "feel", "explain", "represent", "describe", "introduce", "confirm",
    "suggest", "highlight", "consider", "establish", "aim", "conclude", "fill"
}

# Subjects/objects that are too generic unless strongly biomech-coded
GENERIC_NODES = {
    "people", "person", "individual", "most people", "some people",
    "exercises", "events", "approach", "work", "study", "results", "findings",
    "conclusion", "abstract", "instruments", "participants", "research", "methods",
    "influence", "level", "degree"
}

# Technique cue patterns (sentence-level)
TECHNIQUE_PATTERNS = [
    r"\bstart with\b", r"\blie (with|on)\b", r"\bset (your|the)\b",
    r"\bgrip\b", r"\b(retract|depress) (your )?scapula\b",
    r"\btuck (your )?elbows\b", r"\barch\b", r"\bbrace\b",
    r"\blower the bar\b", r"\bpress\b", r"\btouch (the )?chest\b",
    r"\bbar (grazes|touches)\b", r"\bkeep (your )?wrists\b",
    r"\brack\b"
]

# Biomechanics signal patterns (sentence-level)
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

# Node whitelist hints (entity-level): muscles/joints/implements/variables
KG_KEYWORDS = [
    "bench press", "barbell", "bar", "grip", "grip width", "bar path",
    "scapula", "scapulae", "scapular", "retraction", "protraction", "tilting",
    "shoulder", "elbow", "wrist", "torso", "spine",
    "pectoralis", "pecs", "triceps", "deltoid", "lats", "rotator cuff",
    "serratus", "clavicular", "sternocostal",
    "moment", "moment arm", "force", "activation", "emg", "torque",
    "eccentric", "concentric", "range of motion"
]

def has_pattern(patterns: List[str], sent_text: str) -> bool:
    s = sent_text.lower()
    return any(re.search(p, s) for p in patterns)

def is_domain_sentence(sent: Span) -> bool:
    try:
        return sent.similarity(DOMAIN_ANCHOR) >= SIM_THRESHOLD
    except Exception:
        return False

def sentence_is_useful(sent_text: str) -> Tuple[bool, str]:
    """
    Gatekeeper: keep only technique/instruction or biomechanics/mechanics.
    Returns (keep, category).
    """
    s = sent_text.lower()

    # hard kills
    if BULLETISH.search(sent_text):
        return False, "drop"
    if has_pattern(RESEARCH_META_PATTERNS, sent_text):
        return False, "drop"
    if has_pattern(META_SENTENCE_PATTERNS, sent_text):
        return False, "drop"

    is_tech = any(re.search(p, s) for p in TECHNIQUE_PATTERNS)
    is_biomech = any(re.search(p, s) for p in BIOMECH_PATTERNS)

    if is_tech:
        return True, "technique"
    if is_biomech:
        return True, "biomechanics"

    # fallback: if contains strong KG keywords, allow (rare)
    if any(k in s for k in KG_KEYWORDS):
        return True, "domain"
    return False, "drop"


# =============================
# ENTITY CLEANUP
# =============================
def strip_determiners(span: Span) -> Span:
    start = span.start
    while start < span.end and span.doc[start].dep_ == "det":
        start += 1
    if start >= span.end:
        return span
    return span.doc[start:span.end]

def span_token_count(span: Span) -> int:
    return len([t for t in span if not t.is_space])

def entity_is_valid(text: str) -> bool:
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

# Small canonicalization: merge common synonyms
CANON = {
    "pecs": "pectoralis major",
    "your pecs": "pectoralis major",
    "delts": "deltoids",
    "front delts": "anterior deltoid",
    "scapulae": "scapula",
    "barbell": "bar",
}

def clean_entity(span: Span) -> Optional[str]:
    span = strip_determiners(span)
    text = normalize_ws(span.text).strip(" ,;:.-–—()[]{}\"“”'")
    if span_token_count(span) > MAX_ENTITY_TOKENS:
        return None
    if not entity_is_valid(text):
        return None

    low = text.lower()
    low = re.sub(r"\s+", " ", low).strip()
    low = CANON.get(low, low)

    # remove trailing possessives
    low = re.sub(r"\b(your|their|our|my)\b\s+", "", low).strip()

    if not entity_is_valid(low):
        return None
    return low


# =============================
# DEPENDENCY UTILS
# =============================
def best_np_containing(token: Token, noun_chunks: List[Span]) -> Span:
    cands = [nc for nc in noun_chunks if token.i >= nc.start and token.i < nc.end]
    if not cands:
        return token.doc[token.i:token.i + 1]
    cands.sort(key=lambda s: (s.end - s.start))
    return cands[0]

def expand_with_compounds(span: Span) -> Span:
    doc = span.doc
    start, end = span.start, span.end
    i = start - 1
    while i >= 0:
        t = doc[i]
        if t.dep_ in {"compound", "amod", "nummod", "poss"} and t.head.i >= start and t.head.i < end:
            start = i
            i -= 1
            continue
        break
    return doc[start:end]


# =============================
# OBJECT REFINEMENT
# =============================
GOOD_PREPS = {"of", "on", "in", "at", "to", "for", "from", "with", "into", "over", "under"}

def refine_object(rel: Token, obj_span: Span, noun_chunks: List[Span]) -> Tuple[Span, str]:
    obj_root = obj_span.root
    base_rel = rel.lemma_.lower().strip()

    # If object has prep -> pobj, use pobj as object and enrich relation
    preps = [c for c in obj_root.children if c.dep_ == "prep" and c.lemma_.lower() in GOOD_PREPS]
    if not preps:
        return obj_span, base_rel

    for p in preps:
        pobj = next((c for c in p.children if c.dep_ == "pobj"), None)
        if pobj is None:
            continue
        pobj_span = expand_with_compounds(best_np_containing(pobj, noun_chunks))
        enriched = f"{base_rel}_{obj_root.lemma_.lower()}_{p.lemma_.lower()}"
        return pobj_span, enriched

    return obj_span, base_rel


# =============================
# RELATION VALIDATION
# =============================
def predicate_is_valid(rel: Token) -> bool:
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
    {"RIGHT_ID": "rel", "RIGHT_ATTRS": {"POS": {"IN": ["VERB", "NOUN"]}}},
    {"LEFT_ID": "rel", "REL_OP": ">", "RIGHT_ID": "subj",
     "RIGHT_ATTRS": {"DEP": {"IN": ["nsubj", "nsubjpass"]}}},
    {"LEFT_ID": "rel", "REL_OP": ">", "RIGHT_ID": "obj",
     "RIGHT_ATTRS": {"DEP": {"IN": ["dobj", "pobj", "obl", "attr", "nmod"]}}},
]
matcher.add("RELATION", [RELATION_PATTERN])


# =============================
# TRIPLE EXTRACTION
# =============================
def extract_triplets(text: str, source: str) -> List[Dict]:
    doc = nlp(normalize_ws(text))
    triplets: List[Dict] = []

    for sent in doc.sents:
        sent_text = normalize_ws(sent.text)
        if not sent_text:
            continue

        keep, category = sentence_is_useful(sent_text)
        if not keep:
            continue

        # still require domain similarity (but lower threshold + usefulness gate)
        if not is_domain_sentence(sent):
            continue

        noun_chunks = [nc for nc in doc.noun_chunks if nc.start >= sent.start and nc.end <= sent.end]
        matches = matcher(sent)

        for _, (rel_id, subj_id, obj_id) in matches:
            rel = sent[rel_id]
            if not predicate_is_valid(rel):
                continue

            subj_tok = sent[subj_id]
            obj_tok = sent[obj_id]

            subj_span = expand_with_compounds(best_np_containing(subj_tok, noun_chunks))
            obj_span = expand_with_compounds(best_np_containing(obj_tok, noun_chunks))

            obj_span_refined, relation = refine_object(rel, obj_span, noun_chunks)

            subj_clean = clean_entity(subj_span)
            obj_clean = clean_entity(obj_span_refined)

            if not subj_clean or not obj_clean:
                continue
            if subj_clean == obj_clean:
                continue

            # extra “utility”: require at least one side to be KG-keyword-ish
            side_text = f"{subj_clean} {obj_clean}"
            if not any(k in side_text for k in KG_KEYWORDS):
                # allow if category is technique (since it’s coaching)
                if category != "technique":
                    continue

            sim = float(sent.similarity(DOMAIN_ANCHOR))

            # confidence: domain similarity + category boost
            conf = 0.0
            conf += min(max((sim - SIM_THRESHOLD) / (1.0 - SIM_THRESHOLD), 0.0), 1.0) * 0.7
            conf += 0.2 if category == "biomechanics" else 0.15 if category == "technique" else 0.0
            conf = round(min(conf, 1.0), 3)

            triplets.append({
                "subject": subj_clean,
                "relation": relation,
                "object": obj_clean,
                "source": source,
                "sentence": sent_text,
                "sentence_hash": sentence_hash(sent_text),
                "domain_similarity": round(sim, 3),
                "confidence": conf,
                "category": category,  # NEW: technique / biomechanics / domain
            })

    return triplets


# =============================
# POST-PROCESSING / DEDUPE
# =============================
def postprocess_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df["triple_key"] = df["subject"] + "|" + df["relation"] + "|" + df["object"]

    # keep best evidence per triple per source
    df = (
        df.sort_values(["confidence", "domain_similarity"], ascending=False)
          .drop_duplicates(subset=["triple_key", "source"], keep="first")
    )

    agg = (
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

    return agg.sort_values(
        ["category", "max_confidence", "max_domain_similarity", "evidence_count"],
        ascending=[True, False, False, False]
    )


# =============================
# FILE PROCESSING
# =============================
def process_file(input_path: Path, output_path: Path) -> None:
    all_triplets: List[Dict] = []

    if not input_path.exists():
        print(f"Missing file: {input_path.name}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            text = record.get("text", "") or ""
            source = record.get("file") or record.get("url") or "unknown"
            if not text.strip():
                continue
            all_triplets.extend(extract_triplets(text, source))

    raw_df = pd.DataFrame(all_triplets)
    if raw_df.empty:
        print(f"⚠ No useful triples extracted from {input_path.name}")
        return

    kg_df = postprocess_df(raw_df)
    kg_df.to_csv(output_path, index=False)
    print(f"✅ {len(kg_df)} useful KG edges saved → {output_path.name}")


# =============================
# MAIN
# =============================
def main():
    print("🔍 Extracting LOCAL (useful biomechanics + technique)...")
    process_file(INPUT_LOCAL, OUTPUT_LOCAL)

    print("\n🔍 Extracting LIVE (useful biomechanics + technique)...")
    process_file(INPUT_LIVE, OUTPUT_LIVE)


if __name__ == "__main__":
    main()
