# 05D — Knowledge Graph Embeddings

## 1. Purpose

This section documents the Knowledge Graph Embedding part of the project.

The goal is to transform the RDF knowledge base into vector representations and evaluate whether embedding models can learn useful relational patterns from the graph.

The assignment requires:

- data cleaning and train/validation/test splits
- at least two KGE models
- metrics: MRR, Hits@1, Hits@3, Hits@10
- size-sensitivity analysis
- t-SNE or nearest-neighbor examples

---

## 2. Input Data

The input graph is:

```text
01_Data/kb_outputs/expanded_kb.ttl

This graph was produced in the KB Construction and Alignment step.

It contains RDF triples, ontology classes, evidence nodes, confidence scores, labels, and expanded semantic relations.

However, not all RDF triples are useful for Knowledge Graph Embedding training.

3. Data Cleaning

The KGE dataset is created by 05A_prepare_kge_dataset.py.

The script removes metadata triples such as:

rdf:type
rdfs:label
rdfs:subClassOf
confidence
domainSimilarity
evidenceSentence
sourceDocument
originalSubject
originalPredicate
originalObject
alignedSubject
alignedPredicate
alignedObject

The script keeps only semantic object-property triples where the subject, predicate, and object are project KB URIs.

For example, triples like these are kept:

triceps    extends                 elbow
grip_width affectsBiomechanics     horizontal_flexion_demands
bar        appliesForce            downward_force

Triples like these are removed:

triceps    rdfs:label              "triceps"
statement1 confidence              0.82
statement1 evidenceSentence        "..."

This cleaning step is important because KGE models are designed for relational facts, not metadata.

4. Train / Validation / Test Splits

The cleaned semantic triples are split into:

train.txt
valid.txt
test.txt

The split strategy is:

80% training
10% validation
10% testing

The output files are saved in:

05_Knowledge_Graph_Embeddings/outputs/

The KGE format is:

head<TAB>relation<TAB>tail

Example:

triceps    extends    elbow
5. Models Used

Two KGE models are trained:

5.1 TransE

TransE represents relations as translations in the embedding space.

It tries to learn:

head + relation ≈ tail

For example:

triceps + extends ≈ elbow

TransE is simple and effective for many one-to-one relational patterns.

5.2 DistMult

DistMult uses a bilinear scoring function.

It scores triples using an element-wise interaction between:

head embedding
relation embedding
tail embedding

DistMult is useful as a second baseline because it learns relational similarity differently from TransE.

6. Evaluation Metrics

The models are evaluated using link prediction.

For a test triple:

triceps → extends → elbow

the model is asked to rank the correct missing entity among all possible entities.

For example:

triceps → extends → ?

The model should rank elbow as high as possible.

The metrics used are:

Metric	Meaning
MRR	Mean Reciprocal Rank. Higher is better.
Hits@1	Percentage of cases where the correct answer is ranked first.
Hits@3	Percentage of cases where the correct answer is in the top 3.
Hits@10	Percentage of cases where the correct answer is in the top 10.

The results are saved in:

05_Knowledge_Graph_Embeddings/outputs/kge_metrics.csv
7. Size Sensitivity

The assignment asks for size-sensitivity experiments at:

20k / 50k / full

However, the current project KB is much smaller than 20k semantic triples.

To handle this honestly, the pipeline creates capped subsets:

size_20k_cap.tsv
size_50k_cap.tsv
size_full.tsv

Each capped file contains:

min(requested size, available triples)

This means the same code would scale to 20k and 50k triples if the KB were larger, while still remaining valid for the current smaller project graph.

The results are saved in:

05_Knowledge_Graph_Embeddings/outputs/size_sensitivity.csv
8. Nearest Neighbors

After training, entity embeddings are analyzed using cosine similarity.

For each entity, the nearest neighbors are computed in embedding space.

This helps inspect whether related concepts are close together.

Example expected patterns:

triceps close to elbow
grip_width close to range_of_motion
bar close to downward_force
pectoralis_major close to shoulder

The nearest-neighbor output is saved in:

05_Knowledge_Graph_Embeddings/outputs/nearest_neighbors.csv
9. t-SNE Visualization

A t-SNE plot is created from the entity embeddings.

The plot is saved as:

05_Knowledge_Graph_Embeddings/outputs/tsne_embeddings.png

The purpose of the visualization is to inspect the embedding space and see whether related entities form meaningful local neighborhoods.

10. Reflection

The KGE experiment demonstrates the full embedding pipeline:

RDF graph cleaning
conversion to KGE triples
train/validation/test split
training two models
evaluation with MRR and Hits@k
size-sensitivity analysis
nearest-neighbor inspection
t-SNE visualization

The main limitation is the small graph size.

Knowledge Graph Embedding models usually perform better on larger and denser graphs. Since this project focuses on a narrow bench press domain, the number of semantic triples is limited.

Therefore, the results should be interpreted as a proof of pipeline and methodology rather than as a high-performance large-scale KGE benchmark.