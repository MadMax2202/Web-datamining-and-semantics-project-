"""
03B_alignment_rules.py

This file contains the alignment rules used during KB construction.

It defines:
1. Entity aliases: maps noisy extracted entity mentions to canonical entities.
2. Predicate aliases: maps noisy extracted relations to a controlled RDF predicate vocabulary.
3. Entity type rules: assigns entities to ontology classes such as Muscle, Joint, Equipment, etc.

This keeps the RDF construction step clean and makes the alignment process explicit
for the project report and presentation.
"""

import re


# =============================
# ENTITY ALIGNMENT
# =============================

ENTITY_ALIASES = {
    # Muscles
    "pecs": "pectoralis major",
    "your pecs": "pectoralis major",
    "pectorals": "pectoralis major",
    "chest": "pectoralis major",
    "pectoralis muscles": "pectoralis major",
    "front delts": "anterior deltoid",
    "delts": "deltoids",

    # Equipment
    "barbell": "bar",
    "barbells": "bar",
    "the bar": "bar",

    # Body parts / joints
    "scapulae": "scapula",
    "shoulders": "shoulder",
    "elbows": "elbow",
    "wrists": "wrist",

    # Biomechanics
    "rom": "range of motion",
    "emg": "muscle activation",
}


# =============================
# PREDICATE ALIGNMENT
# =============================

PREDICATE_ALIASES = {
    # Muscle activation / targeting
    "activate": "targetsMuscle",
    "activation": "targetsMuscle",
    "activation_of": "targetsMuscle",
    "target": "targetsMuscle",
    "train": "targetsMuscle",
    "work": "targetsMuscle",
    "hit": "targetsMuscle",

    # Influence / causality
    "affect": "influences",
    "influence": "influences",
    "determine": "influences",
    "change": "influences",
    "impact": "influences",
    "increase": "increases",
    "decrease": "decreases",
    "reduce": "reduces",
    "limit": "reduces",
    "limit_of": "reduces",

    # Biomechanical actions
    "apply": "appliesForce",
    "produce": "produces",
    "generate": "produces",
    "require": "requires",
    "involve": "involves",
    "involve_with": "involves",
    "allow": "allows",

    # Joint actions
    "extend": "extends",
    "flex": "flexes",
    "abduct": "abducts",
    "adduct": "adducts",

    # Generic fallback
    "relate": "relatedTo",
    "associate": "relatedTo",
}


# =============================
# ENTITY TYPE KEYWORDS
# =============================

ENTITY_TYPE_KEYWORDS = {
    "Exercise": [
        "bench press",
        "incline bench press",
        "close grip bench press",
        "barbell bench press",
        "pressing movement",
    ],

    "Muscle": [
        "pectoralis",
        "triceps",
        "deltoid",
        "deltoids",
        "anterior deltoid",
        "lats",
        "latissimus",
        "serratus",
        "rotator cuff",
        "muscle",
    ],

    "Joint": [
        "shoulder",
        "elbow",
        "wrist",
        "scapula",
        "scapular",
        "joint",
    ],

    "Equipment": [
        "bar",
        "barbell",
        "bench",
        "rack",
        "equipment",
    ],

    "TechniqueCue": [
        "grip",
        "grip width",
        "bar path",
        "scapular retraction",
        "retraction",
        "arch",
        "elbow tuck",
        "tuck",
        "brace",
        "touch point",
        "setup",
    ],

    "BiomechanicalConcept": [
        "force",
        "downward force",
        "moment",
        "moment arm",
        "torque",
        "activation",
        "range of motion",
        "horizontal flexion",
        "horizontal abduction",
        "eccentric",
        "concentric",
        "velocity",
        "power",
        "workload",
        "demands",
        "sticking point",
    ],
}


# =============================
# HELPER FUNCTIONS
# =============================

def normalize_text(text: str) -> str:
    """
    Normalize a raw string before alignment.
    """
    if text is None:
        return ""

    text = str(text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" ,;:.-–—()[]{}\"“”'")
    return text


def canonical_entity(entity: str) -> str:
    """
    Map an extracted entity mention to a canonical entity label.
    """
    entity = normalize_text(entity)
    return ENTITY_ALIASES.get(entity, entity)


def canonical_predicate(predicate: str) -> str:
    """
    Map an extracted relation to a controlled predicate.
    """
    predicate = normalize_text(predicate)
    predicate = predicate.replace(" ", "_")
    return PREDICATE_ALIASES.get(predicate, predicate)


def guess_entity_type(entity: str) -> str:
    """
    Assign an ontology class to an entity using keyword rules.
    """
    entity_norm = normalize_text(entity)

    for entity_type, keywords in ENTITY_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in entity_norm:
                return entity_type

    return "DomainEntity"