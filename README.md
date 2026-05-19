# Bench Press Knowledge Graph, KGE, and RAG Project

This repository implements a semantic pipeline for a **bench press training knowledge graph**. It uses a custom crawler, cleaning pipeline, entity/relation extraction, RDF graph construction, lightweight alignment, reasoning, KGE dataset preparation, and a natural-language-to-SPARQL RAG demo.

## Domain

The domain is strength training knowledge focused on the bench press: muscles, equipment, technique cues, joints, biomechanics, and evidence sentences.

## Repository structure

```text
src/
  crawl/      crawler + text extraction
  ie/         information extraction / NER / relation extraction
  kg/         RDF construction + SPARQL expansion
  reason/     rule-based reasoning
  kge/        KGE split prep + model scripts
  rag/        NL-to-SPARQL CLI demo
data/
  samples/    extracted source CSV
kg_artifacts/ ontology, alignment, generated graphs, statistics
reports/      final report + evaluation notes
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m spacy download en_core_web_md
```

## Run the pipeline

```bash
python src/kg/build_rdf_graph.py
python src/kg/sparql_expand.py
python src/reason/run_reasoning.py
python src/kge/prepare_kge_data.py
python src/kge/train_kge.py --model TransE
python src/kge/train_kge.py --model DistMult
python src/rag/rag_cli.py
```

## Crawler

The crawler supports live web fetching and local HTML replay. For grading, prefer local replay to avoid repeatedly hitting websites.

```bash
python src/crawl/crawl_and_clean.py
```

## Information extraction

```bash
python src/ie/extract_entities.py
```

The current sample file contains **107 extracted KG edges**.

## Ollama instructions

Install Ollama, pull a local model, then adapt `src/rag/rag_cli.py` to call the model for NL-to-SPARQL generation:

```bash
ollama pull llama3.1
ollama run llama3.1
```

The submitted CLI includes a deterministic template-based NL-to-SPARQL fallback so the project remains runnable without an API key.

## Hardware requirements

The RDF/RAG demo runs on a normal laptop. KGE training with PyKEEN is recommended on CPU for small graphs and GPU for larger graphs.

## Screenshot

Add a screenshot of the terminal running:

```bash
python src/rag/rag_cli.py
```

and place it in `screenshots/rag_demo.png`.

## Reproducibility

All generated KG artifacts can be recreated from `data/samples/extracted_knowledge_local.csv` using the scripts above.
