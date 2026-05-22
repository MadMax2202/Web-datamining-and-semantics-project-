# Web Datamining and Semantics Project

**Knowledge Graph Construction · Alignment · Reasoning · Knowledge Graph Embeddings · RAG over RDF/SPARQL**

Project members:

- **Maxim Grossmann**
- **Geoffroy Gankoue**

This repository contains the full pipeline for a Web Datamining and Semantics project focused on the **bench press / strength training / biomechanics** domain.

The goal of the project is to start from web data, extract domain knowledge, build an RDF knowledge base, align entities and predicates, apply reasoning, train knowledge graph embedding models, and finally query the graph through a small RAG-style RDF/SPARQL demo.

---

## 1. Project Overview

The project is organized as an end-to-end semantic web pipeline:

```text
Web pages
   ↓
Crawler + cleaning
   ↓
Information extraction / NER
   ↓
RDF knowledge base construction
   ↓
Entity and predicate alignment
   ↓
KB expansion
   ↓
SWRL reasoning
   ↓
Knowledge graph embeddings
   ↓
RAG over RDF/SPARQL demo
```

The domain is intentionally narrow: **bench press biomechanics**. This lets us focus on domain-specific concepts such as muscles, joints, equipment, technique cues, and biomechanical variables.

Examples of extracted entities include:

```text
pectoralis major
triceps
shoulder
elbow
bar
grip width
bar path
horizontal flexion demands
```

Examples of extracted triples include:

```text
triceps → extends → elbow
pectoralis major → flexes → shoulder
bar → appliesForce → downward force
grip width → affectsBiomechanics → horizontal flexion demands
```

---

## 2. Repository Structure

```text
project-root/
│
├── 01_Data/
│   ├── html_files/
│   ├── crawler_outputs/
│   └── kb_outputs/
│
├── 02_Data_acquisition_and_IE/
│   ├── 02A_crawl_and_clean.py
│   ├── 02B_extract_entities.py
│   └── 02C_NER_examples_and_ambiguity_cases.md
│
├── 03_KB_Construction_and_Alignment/
│   ├── 03A_build_initial_rdf.py
│   ├── 03B_alignment_rules.py
│   ├── 03C_expand_kb.py
│   ├── 03D_kb_statistics.py
│   └── 03E_KB_construction_and_alignment.md
│
├── 04_Reasoning_SWRL/
│   ├── 04A_family_swrl_reasoning.py
│   ├── 04B_kb_swrl_reasoning.py
│   ├── 04C_reasoning_explanation.md
│   └── outputs/
│
├── 05_Knowledge_Graph_Embeddings/
│   ├── 05A_prepare_kge_dataset.py
│   ├── 05B_train_kge_models.py
│   ├── 05C_analyze_kge_results.py
│   ├── 05D_visualize_kge_artifacts.py
│   ├── 05E_KGE_explanation.md
│   └── outputs/
│
├── 06_RAG_over_RDF_SPARQL/
│   ├── 06A_schema_summary.py
│   ├── 06B_rag_sparql_demo.py
│   ├── 06C_evaluate_rag.py
│   ├── 06D_RAG_over_RDF_SPARQL.md
│   └── outputs/
│
├── reports/
│   └── final_report.pdf
│
├── requirements.txt
├── README.md
└── .gitignore
```

Some folder names or report filenames may vary slightly depending on the final local organization, but the pipeline logic remains the same.

---

## 3. Installation

### 3.1 Create a virtual environment

From the project root:

```powershell
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then activate again:

```powershell
.\venv\Scripts\Activate.ps1
```

---

### 3.2 Install Python dependencies

```powershell
pip install -r requirements.txt
```

If the `requirements.txt` file is not available yet, install the main packages manually:

```powershell
pip install trafilatura httpx pandas spacy rdflib owlready2 numpy torch scikit-learn matplotlib tabulate networkx
python -m spacy download en_core_web_md
```

Important: install **`scikit-learn`**, not `sklearn`.

---

### 3.3 Java requirement for SWRL reasoning

The SWRL reasoning scripts use Owlready2 with Pellet. Pellet requires Java.

Check Java with:

```powershell
java -version
```

If Java is missing or too old, install a recent JDK, for example Temurin JDK 25:

```powershell
winget install -e --id EclipseAdoptium.Temurin.25.JDK
```

Then close and reopen PowerShell and check again:

```powershell
java -version
```

---

## 4. How to Run the Pipeline

Run all commands from the **project root** unless stated otherwise.

---

## 4.1 Data Acquisition and Information Extraction

### Step 1 — Crawl and clean web pages

```powershell
python .\02_Data_acquisition_and_IE\02A_crawl_and_clean.py
```

The script offers two modes:

```text
1 - Fetch all seed pages from the web
2 - Use local saved HTML files
```

Recommended workflow:

1. Run option `1` once to download and cache the HTML pages.
2. Use option `2` afterwards for reproducible local experiments.

Outputs:

```text
01_Data/html_files/
01_Data/crawler_outputs/crawler_output_live.jsonl
01_Data/crawler_outputs/crawler_output_local.jsonl
```

One of the seed URLs may return a `403 Forbidden` response. The crawler safely skips it instead of trying to bypass restrictions. This is part of the ethical crawling design.

---

### Step 2 — Extract entities and triples

```powershell
python .\02_Data_acquisition_and_IE\02B_extract_entities.py
```

This script reads the cleaned JSONL files and extracts domain-specific triples using spaCy.

Outputs:

```text
01_Data/crawler_outputs/extracted_knowledge_live.csv
01_Data/crawler_outputs/extracted_knowledge_local.csv
```

The extraction focuses on bench press technique and biomechanics.

Example extracted triples:

```text
triceps → extend → elbow
bar → apply → downward force
grip width → determine → horizontal flexion demands
```

The file `02C_NER_examples_and_ambiguity_cases.md` documents NER examples and ambiguity cases such as:

- `pecs`, `chest`, and `pectoralis major`
- `bar` vs `barbell`
- `press` as an exercise, action, or generic word

---

## 4.2 Knowledge Base Construction and Alignment

### Step 3 — Build the initial RDF knowledge base

```powershell
python .\03_KB_Construction_and_Alignment\03A_build_initial_rdf.py
```

This script:

- loads the extracted CSV triples
- normalizes entity names
- aligns predicates
- assigns ontology classes
- creates RDF triples
- stores confidence scores and evidence sentences

`03B_alignment_rules.py` is a helper file. It contains alignment dictionaries and is imported by `03A_build_initial_rdf.py`. It is **not** run directly.

Outputs:

```text
01_Data/kb_outputs/ontology.ttl
01_Data/kb_outputs/initial_kb.ttl
01_Data/kb_outputs/alignment_report.csv
```

---

### Step 4 — Expand the KB

```powershell
python .\03_KB_Construction_and_Alignment\03C_expand_kb.py
```

This applies rule-based/SPARQL-style expansion rules.

Examples:

```text
triceps extends elbow
→ triceps actsOnJoint elbow

grip width influences horizontal flexion demands
→ grip width affectsBiomechanics horizontal flexion demands
```

Outputs:

```text
01_Data/kb_outputs/expanded_kb.ttl
01_Data/kb_outputs/expansion_report.md
```

---

### Step 5 — Generate KB statistics

```powershell
python .\03_KB_Construction_and_Alignment\03D_kb_statistics.py
```

Outputs:

```text
01_Data/kb_outputs/kb_statistics.json
01_Data/kb_outputs/kb_statistics.md
```

Example final statistics from the project:

```text
Initial KB: 2180 RDF triples
Expanded KB: 2188 RDF triples
Entities: 344 → 347
Predicates: 83 → 86
Classes: 8
Knowledge statement nodes: 104
Average confidence: 0.4361
```

---

## 4.3 SWRL Reasoning

### Step 6 — Family ontology SWRL reasoning

```powershell
python .\04_Reasoning_SWRL\04A_family_swrl_reasoning.py
```

This creates a small family ontology and applies the SWRL rule:

```text
parentOf(?x, ?y) ^ parentOf(?y, ?z) → grandparentOf(?x, ?z)
```

Expected inference:

```text
John grandparentOf Alice
```

Outputs:

```text
04_Reasoning_SWRL/outputs/family.owl
04_Reasoning_SWRL/outputs/family_reasoned.owl
04_Reasoning_SWRL/outputs/family_reasoning_output.txt
```

---

### Step 7 — Project KB SWRL reasoning

```powershell
python .\04_Reasoning_SWRL\04B_kb_swrl_reasoning.py
```

This uses the expanded bench press KB and applies the rule:

```text
TechniqueCue(?cue) ^ BiomechanicalConcept(?concept) ^ affectsBiomechanics(?cue, ?concept)
→ ImportantTechniqueCue(?cue)
```

Example inference:

```text
grip width is an ImportantTechniqueCue
```

Outputs:

```text
04_Reasoning_SWRL/outputs/kb_swrl_input.owl
04_Reasoning_SWRL/outputs/kb_swrl_reasoned.owl
04_Reasoning_SWRL/outputs/kb_reasoning_output.txt
```

---

## 4.4 Knowledge Graph Embeddings

### Step 8 — Prepare KGE dataset

```powershell
python .\05_Knowledge_Graph_Embeddings\05A_prepare_kge_dataset.py
```

This script cleans the RDF graph for KGE training by removing metadata triples such as:

```text
rdf:type
rdfs:label
confidence
evidenceSentence
sourceDocument
```

It keeps only semantic triples useful for link prediction.

Outputs:

```text
05_Knowledge_Graph_Embeddings/outputs/semantic_triples.tsv
05_Knowledge_Graph_Embeddings/outputs/train.txt
05_Knowledge_Graph_Embeddings/outputs/valid.txt
05_Knowledge_Graph_Embeddings/outputs/test.txt
05_Knowledge_Graph_Embeddings/outputs/entity_to_id.tsv
05_Knowledge_Graph_Embeddings/outputs/relation_to_id.tsv
```

Final cleaned KGE dataset:

```text
Semantic triples: 109
Training triples: 87
Validation triples: 11
Test triples: 11
Entities: 151
Relations: 68
```

---

### Step 9 — Train KGE models

```powershell
python .\05_Knowledge_Graph_Embeddings\05B_train_kge_models.py
```

This trains two models:

- **TransE**
- **DistMult**

Metrics:

- MRR
- Hits@1
- Hits@3
- Hits@10

Outputs:

```text
05_Knowledge_Graph_Embeddings/outputs/kge_metrics.csv
05_Knowledge_Graph_Embeddings/outputs/size_sensitivity.csv
05_Knowledge_Graph_Embeddings/outputs/TransE_full_embeddings.npz
05_Knowledge_Graph_Embeddings/outputs/DistMult_full_embeddings.npz
```

Example results:

```text
TransE:   MRR = 0.0342, Hits@10 = 0.0909
DistMult: MRR = 0.1051, Hits@1 = 0.0909, Hits@10 = 0.0909
```

The metrics are modest because the graph is small and sparse, but the full KGE pipeline is implemented.

---

### Step 10 — Analyze embeddings

```powershell
python .\05_Knowledge_Graph_Embeddings\05C_analyze_kge_results.py
```

Outputs:

```text
05_Knowledge_Graph_Embeddings/outputs/nearest_neighbors.csv
05_Knowledge_Graph_Embeddings/outputs/tsne_embeddings.png
05_Knowledge_Graph_Embeddings/outputs/kge_analysis_report.md
```

---

### Step 11 — Optional extra visualizations

```powershell
python .\05_Knowledge_Graph_Embeddings\05D_visualize_kge_artifacts.py
```

Outputs:

```text
05_Knowledge_Graph_Embeddings/outputs/tsne_embeddings_dark.png
05_Knowledge_Graph_Embeddings/outputs/kge_metrics_chart.png
05_Knowledge_Graph_Embeddings/outputs/size_sensitivity_chart.png
05_Knowledge_Graph_Embeddings/outputs/kg_graph_network.png
```

These visualizations are useful for the report and final presentation.

---

## 4.5 RAG over RDF/SPARQL

### Step 12 — Generate schema summary

```powershell
python .\06_RAG_over_RDF_SPARQL\06A_schema_summary.py
```

Outputs:

```text
06_RAG_over_RDF_SPARQL/outputs/schema_summary.md
06_RAG_over_RDF_SPARQL/outputs/schema_summary.json
```

The schema summary lists ontology classes, predicates, and example triples. It is used to guide the NL→SPARQL system.

---

### Step 13 — Run interactive RAG/SPARQL demo

```powershell
python .\06_RAG_over_RDF_SPARQL\06B_rag_sparql_demo.py
```

Example question:

```text
Which technique cues affect biomechanical concepts?
```

Example generated SPARQL:

```sparql
PREFIX ex: <http://example.org/benchpress-kg/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?cueLabel ?conceptLabel WHERE {
    ?cue a ex:TechniqueCue .
    ?concept a ex:BiomechanicalConcept .
    ?cue ex:affectsBiomechanics ?concept .
    OPTIONAL { ?cue rdfs:label ?cueLabel . }
    OPTIONAL { ?concept rdfs:label ?conceptLabel . }
}
```

Example answer:

```text
grip width affects horizontal flexion demands
```

Save a screenshot of the terminal demo as:

```text
06_RAG_over_RDF_SPARQL/outputs/demo_screenshot.png
```

---

### Step 14 — Evaluate RAG against baseline

```powershell
python .\06_RAG_over_RDF_SPARQL\06C_evaluate_rag.py
```

Outputs:

```text
06_RAG_over_RDF_SPARQL/outputs/rag_evaluation.csv
06_RAG_over_RDF_SPARQL/outputs/rag_evaluation.md
```

The evaluation compares a simple baseline answer with the RDF/SPARQL answer for at least five questions.

Example evaluation questions:

```text
Which technique cues affect biomechanical concepts?
Which muscles act on joints?
What force does the bar apply?
What does grip width influence?
Which muscles extend joints?
What facts are known about the triceps?
```

---

## 5. Main Results

### Data Acquisition and IE

- Controlled seed-URL crawler
- Local HTML caching for reproducibility
- Trafilatura-based text extraction
- spaCy-based entity and relation extraction
- Domain-specific NER for bench press biomechanics

### KB Construction and Alignment

- RDF ontology with 8 classes
- Entity linking with confidence metadata
- Predicate alignment to controlled vocabulary
- Expanded KB with rule-based graph enrichment

### Reasoning

- Family SWRL rule successfully inferred `John grandparentOf Alice`
- Project SWRL rule successfully inferred `grip width` as an `ImportantTechniqueCue`

### KGE

- Cleaned semantic KGE dataset
- Two models trained: TransE and DistMult
- Metrics computed: MRR, Hits@1, Hits@3, Hits@10
- t-SNE and nearest-neighbor examples generated

### RAG over RDF/SPARQL

- Schema summary generated from RDF graph
- Natural language questions mapped to SPARQL
- Self-repair mechanism included
- Baseline vs RAG evaluation performed
- CLI demo screenshot produced

---

## 6. Reproducibility Notes

The project is designed to be reproducible:

- Raw HTML is cached locally after the first fetch.
- Cleaned text is stored in JSONL format.
- Extracted triples are stored in CSV format.
- RDF artifacts are stored in Turtle format.
- KGE splits are saved as `train.txt`, `valid.txt`, and `test.txt`.
- Model metrics and visualizations are exported to files.
- RAG evaluation outputs are saved as CSV and Markdown.

---

## 7. Known Limitations

The main limitation is graph size. The final semantic KGE dataset contains only 109 triples after metadata cleaning.

This means KGE metrics are not expected to be very high. Knowledge graph embedding models usually perform better on larger and denser graphs.

The extraction pipeline also contains some noise, for example entities such as:

```text
about_45
anything
entity_45_pounds
```

These are useful to mention because they show the realistic impact of noisy information extraction on downstream KB and embedding quality.

The RAG system uses rule-based NL→SPARQL mapping instead of a full LLM. This makes the system reproducible and transparent, but less flexible than a production-level natural language interface.

---

## 8. Hardware Requirements

The project can run on a normal laptop.

The experiments were run using CPU.

Recommended minimum:

```text
Python 3.11+
8 GB RAM
Java JDK for SWRL reasoning
```

GPU is not required.

---

## 9. Final Report

The final report is available in:

```text
reports/final_report.pdf
```

It summarizes:

- Data Acquisition & IE
- KB Construction & Alignment
- SWRL Reasoning
- Knowledge Graph Embeddings
- RAG over RDF/SPARQL
- Critical reflection

---

## 10. Quick Start

To run the full project from scratch:

```powershell
.\venv\Scripts\Activate.ps1

python .\02_Data_acquisition_and_IE\02A_crawl_and_clean.py
python .\02_Data_acquisition_and_IE\02B_extract_entities.py

python .\03_KB_Construction_and_Alignment\03A_build_initial_rdf.py
python .\03_KB_Construction_and_Alignment\03C_expand_kb.py
python .\03_KB_Construction_and_Alignment\03D_kb_statistics.py

python .\04_Reasoning_SWRL\04A_family_swrl_reasoning.py
python .\04_Reasoning_SWRL\04B_kb_swrl_reasoning.py

python .\05_Knowledge_Graph_Embeddings\05A_prepare_kge_dataset.py
python .\05_Knowledge_Graph_Embeddings\05B_train_kge_models.py
python .\05_Knowledge_Graph_Embeddings\05C_analyze_kge_results.py
python .\05_Knowledge_Graph_Embeddings\05D_visualize_kge_artifacts.py

python .\06_RAG_over_RDF_SPARQL\06A_schema_summary.py
python .\06_RAG_over_RDF_SPARQL\06C_evaluate_rag.py
python .\06_RAG_over_RDF_SPARQL\06B_rag_sparql_demo.py
```

For the crawler, run live mode only once, then use local mode afterwards.

---

## 11. Authors

**Maxim Grossmann**  
**Geoffroy Gankoue**

Web Datamining and Semantics Project  
2026
