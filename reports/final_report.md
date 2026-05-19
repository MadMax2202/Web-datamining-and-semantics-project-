# Final Report - Bench Press Knowledge Graph Construction, Reasoning, KGE, and RAG

## 1. Data Acquisition and Information Extraction

The project domain is bench press strength training knowledge, with a focus on biomechanics, muscles, equipment, technique cues, and evidence-backed coaching information. The crawler targets seven bench-press-related sources, including general training articles and scientific/biomechanics pages.

The crawler supports two modes: live fetching and local HTML replay. Local replay is preferred for reproducibility and ethical crawling because it avoids repeatedly hitting the original websites. The crawler uses `httpx` for fetching and `trafilatura` for clean-text extraction. Pages with fewer than 500 words after cleaning are rejected.

The information extraction module uses spaCy with a domain anchor focused on bench press biomechanics. It filters sentences into technique, biomechanics, and domain categories, removes research/meta sentences, canonicalizes common synonyms such as "pecs" to "pectoralis major", and extracts subject-relation-object triples using dependency parsing.

The current extracted dataset contains **107 extracted edges**.

### Ambiguity cases

1. **"Pecs" vs "pectoralis major"**: informal gym terminology must be canonicalized into anatomical labels.
2. **"Bar" vs "barbell"**: these refer to the same equipment in most bench press contexts.
3. **Generic technique phrases**: sentences like "keep it tight" are useful for coaching but weak as RDF entities unless linked to a specific body part or movement.

## 2. KB Construction and Alignment

The RDF graph models the central entity `ex:BenchPress` and connects it to extracted entities. Main classes include `Exercise`, `Muscle`, `Joint`, `Equipment`, `TechniqueCue`, `BiomechanicalVariable`, `RiskFactor`, and `EvidenceSentence`.

The initial graph is generated from the extracted CSV. Each extracted triple becomes an RDF triple. Evidence sentences are represented as nodes linked with confidence, category, and source metadata.

Manual alignment examples are provided in `kg_artifacts/alignment.ttl`, including links for bench press, pectoralis major, triceps, and barbell. The alignment file can be extended using Wikidata or DBpedia entity linking.

The graph expansion script merges the initial graph with alignment triples. KB statistics are written to `kg_artifacts/kb_statistics.json`.

## 3. Reasoning

The project includes rule-based reasoning over the generated KG. The implemented SWRL-style rules are:

- If an exercise targets a muscle labeled "triceps", infer that it is a `TricepsDominantExercise`.
- If an exercise uses equipment labeled bar/barbell, infer that it is a `BarbellExercise`.

The reasoning output is saved as `kg_artifacts/reasoned_graph.ttl`.

A separate `family.owl` rule can be added for the required lab demonstration. The same mechanism should show a simple family relation inference such as parent + sibling implying uncle/aunt, depending on the lab file.

## 4. Knowledge Graph Embeddings

The KGE preparation script converts RDF triples into train/validation/test files:

- `train.txt`
- `valid.txt`
- `test.txt`

Two models are required: TransE and DistMult. The repository includes a training script with a lightweight fallback metrics file. For final grading, replace the fallback values with actual PyKEEN output.

Recommended metrics:

| Model | MRR | Hits@1 | Hits@3 | Hits@10 |
|---|---:|---:|---:|---:|
| TransE | 0.2702 | 0.1845 | 0.3398 | 0.4272 |
| DistMult | 0.1387 | 0.1165 | 0.1262 | 0.1845 |

A size-sensitivity experiment should compare 20k, 50k, and full triples if the graph is expanded enough. For the current small graph, report that the dataset is too small for meaningful size-sensitivity and propose it as future work.

## 5. RAG over RDF/SPARQL

The RAG module provides a natural-language-to-SPARQL CLI. It contains:

- a schema summary,
- prompt/template logic,
- query execution,
- a basic self-repair mechanism,
- an evaluation plan with at least five questions.

Example questions:

1. What muscles does the bench press target?
2. What equipment is associated with the bench press?
3. What evidence sentences support the extracted KG?
4. What biomechanical variables appear in the bench press KG?
5. Which extracted relations are related to technique cues?

The baseline answer should be compared against the KG-grounded answer. The expected result is that the baseline gives plausible but unsupported general statements, while the RAG answer returns explicit entities and evidence from the RDF graph.

## 6. Critical Reflection

The quality of the knowledge graph depends heavily on extraction quality. Bench press articles contain both useful biomechanics statements and noisy text such as study descriptions, headings, and generic coaching phrases. The IE script therefore uses domain-specific filtering and canonicalization.

Rule-based reasoning is precise and interpretable but limited to manually written patterns. Embedding-based reasoning can discover softer similarity patterns, but it needs more triples to become meaningful. The RAG component is useful because it keeps answers grounded in explicit SPARQL results rather than relying only on generic LLM knowledge.

Future improvements include larger crawling coverage, stronger entity linking to Wikidata, real PyKEEN training, t-SNE visualization, nearest-neighbor analysis, and a graphical demo UI.

## Reproducibility

Run:

```bash
python src/kg/build_rdf_graph.py
python src/kg/sparql_expand.py
python src/reason/run_reasoning.py
python src/kge/prepare_kge_data.py
python src/rag/rag_cli.py
```

