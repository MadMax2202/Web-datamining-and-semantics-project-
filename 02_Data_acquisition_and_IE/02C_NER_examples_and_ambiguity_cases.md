02C — NER Examples and Ambiguity Cases

1. Purpose of This File

This file documents the Named Entity Recognition (NER) examples and the three ambiguity cases identified during the Information Extraction step of the project.

The project domain is:

Bench press, strength training, and biomechanics

The goal of this step is to show how the system extracts useful domain-specific entities from cleaned web pages and how ambiguous terms are handled before constructing the knowledge base.

2. What NER Means in This Project

In standard Natural Language Processing, Named Entity Recognition usually detects entities such as:

people
organizations
locations
dates

However, in this project, the domain is not general news or Wikipedia-style text. The domain is bench press biomechanics and strength training.

Therefore, NER is adapted to extract domain-specific entities, such as:

exercises
muscles
joints
body parts
equipment
technique cues
biomechanical concepts

The extracted information is represented as knowledge triples in the form:

subject → relation → object

For example:

triceps → extend → elbow
pectoralis major → flex → shoulder
bar → apply → downward force
grip width → determine → horizontal flexion demands
3. Entity Types

The extracted entities can be grouped into the following categories:

Entity Type	Examples
Exercise / movement	bench press, eccentric phase, concentric phase, movement pattern
Muscle	pectoralis major, triceps, anterior deltoid, pectoralis muscles
Joint / body part	shoulder, elbow, wrist, scapula, torso
Equipment	bar, barbell, bench
Technique cue	grip width, bar path, scapular retraction, lumbar extension
Biomechanical concept	force, moment, moment arm, activation, horizontal flexion, range of motion

These entity types are useful because they later become nodes in the knowledge base.

4. NER and Triple Extraction Examples

The following examples show how the Information Extraction pipeline transforms cleaned text into structured triples.

Text Evidence / Context	Extracted Entities	Extracted Triple
The triceps help extend the elbow.	triceps, elbow	triceps → extend → elbow
The pectoralis major contributes to shoulder flexion.	pectoralis major, shoulder	pectoralis major → flex → shoulder
The bar applies a downward force.	bar, downward force	bar → apply → downward force
Grip width affects the movement pattern.	grip width, horizontal flexion demands	grip width → determine → horizontal flexion demands
Scapular retraction limits scapular movement.	scapular retraction, scapula	scapular retraction → limit_of → scapula
The eccentric phase changes joint demands.	eccentric phase, shoulder horizontal abduction	eccentric phase → require → shoulder horizontal abduction

These examples show that the system does not only extract isolated keywords. It also extracts relations between entities, which is necessary for building a knowledge graph.

5. Explanation of the NER Pipeline

The NER and Information Extraction pipeline works as follows:

The cleaned text produced by 02A_crawl_and_clean.py is loaded from JSONL files.
Each document is split into sentences using spaCy.
Sentences are filtered to keep only those related to bench press technique or biomechanics.
Noun phrases are extracted as candidate entities.
Dependency parsing is used to identify subject-relation-object structures.
Extracted entities are normalized using canonicalization rules.
Extracted triples are saved to CSV with confidence scores, source documents, and example evidence sentences.

The final output is a CSV file containing structured knowledge edges.

Example output format:

subject, relation, object, confidence, source, example_sentence
6. Entity Normalization

One important part of the NER step is entity normalization.

Different sources may use different words to describe the same concept. For example, casual fitness websites often use informal terms, while scientific articles use anatomical terms.

Examples of normalization rules:

pecs → pectoralis major
pectorals → pectoralis major
chest → pectoralis major
barbell → bar
scapulae → scapula
front delts → anterior deltoid

This prevents the knowledge base from creating duplicate nodes for the same concept.

For example, without normalization, the system could create separate entities:

chest
pecs
pectorals
pectoralis major

After normalization, these mentions can be aligned to:

pectoralis major

This improves the consistency and quality of the knowledge base.

7. Ambiguity Cases
7.1 Ambiguity Case 1 — “Pecs”, “Chest”, and “Pectoralis Major”
Problem

In bench press texts, several words can refer to the same anatomical concept.

Examples:

pecs
chest
pectorals
pectoralis major

In casual fitness articles, “pecs” and “chest” are often used to describe the main muscle involved in the bench press. However, in anatomical terms, the more precise entity is usually pectoralis major.

The ambiguity is that chest can refer either to:

a broad body region
the pectoral muscles
the pectoralis major specifically
Example

Possible extracted mentions:

bench press → targets → chest
bench press → targets → pecs
bench press → targets → pectoralis major

Without normalization, these would become separate nodes in the knowledge base, even though they often refer to the same muscle group in this domain.

Resolution

The pipeline uses canonicalization rules to map informal mentions to a standard entity:

pecs → pectoralis major
pectorals → pectoralis major
chest → pectoralis major
Reflection

This ambiguity is important because the corpus contains both scientific and non-scientific sources. Scientific sources tend to use precise anatomical terms, while fitness websites often use informal language.

Normalizing these terms avoids duplicate nodes and makes the knowledge base more coherent.

7.2 Ambiguity Case 2 — “Bar” vs “Barbell” vs General Meaning
Problem

The word bar is ambiguous in general English.

It can mean:

a drinking place
a metal object
a graphical bar
a legal barrier
a gym barbell

In the bench press domain, however, bar usually refers to the barbell used during the exercise.

Example

Extracted triple:

bar → apply → downward force

In this context, the word bar is interpreted as gym equipment because it appears in a bench press biomechanics context.

Relevant context words include:

bench press
force
shoulder
elbow
moment
bar path
grip
Resolution

The system keeps bar as a useful entity only when the sentence is close to the bench press / biomechanics domain.

This is done using domain filtering based on context terms such as:

bench press
bar path
grip width
force
moment
shoulder
elbow
pectoralis major
triceps
Reflection

This ambiguity shows why context filtering is necessary. The entity bar should only be included in the knowledge base when it refers to bench press equipment, not when it appears in an unrelated context.

The system does not try to resolve ambiguity using the word alone. Instead, it uses the surrounding sentence context.

7.3 Ambiguity Case 3 — “Press” as Exercise, Action, or Generic Word
Problem

The word press has several possible meanings.

It can refer to:

bench press
overhead press
leg press
the action of pressing something
the press/media

In this project, press is only relevant when it refers to the bench press exercise or to the pressing action inside the bench press movement.

Example

Relevant bench press contexts include:

press the bar upward
bench press technique
barbell bench press
pressing phase

A possible extracted triple is:

bench press → reduce → workload

However, extracting every occurrence of press would create noise, because the word can appear in many unrelated contexts.

Resolution

The pipeline only keeps sentences where press appears with bench press domain signals, such as:

bar
bench
grip width
pectoralis major
triceps
shoulder
elbow
force
range of motion

If the sentence is not related to strength training or biomechanics, it is filtered out.

Reflection

This ambiguity demonstrates the importance of domain-specific filtering. The system does not treat every occurrence of press as a useful entity. It only keeps it when the surrounding sentence clearly belongs to the strength training or biomechanics domain.

8. Summary

The NER step extracts domain-specific entities from bench press texts, including:

muscles
joints
equipment
exercise variations
technique cues
biomechanical concepts

The extracted knowledge is represented as triples:

subject → relation → object

Examples include:

triceps → extend → elbow
pectoralis major → flex → shoulder
bar → apply → downward force
grip width → determine → horizontal flexion demands

The three main ambiguity cases are:

pecs, chest, and pectoralis major can refer to the same muscle concept.
bar usually means barbell in this domain, but has other meanings in general English.
press can mean an exercise, an action, or an unrelated concept such as media/press.

These ambiguity cases show why the project needs:

entity normalization
context filtering
confidence scoring
domain-specific extraction rules

This improves the quality of the final knowledge base by reducing duplicate entities and filtering noisy triples.