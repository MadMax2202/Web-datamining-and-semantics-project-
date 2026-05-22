# KGE Analysis Report

## Embedding File Used

- `TransE_full_embeddings.npz`

## Model Metrics

|    MRR |   Hits@1 |   Hits@3 |   Hits@10 |   evaluated_queries | model    | subset   |   train_triples |   valid_triples |   test_triples |   entities |   relations |
|-------:|---------:|---------:|----------:|--------------------:|:---------|:---------|----------------:|----------------:|---------------:|-----------:|------------:|
| 0.0342 |   0      |   0      |    0.0909 |                  22 | TransE   | full     |              87 |              11 |             11 |        151 |          68 |
| 0.1051 |   0.0909 |   0.0909 |    0.0909 |                  22 | DistMult | full     |              87 |              11 |             11 |        151 |          68 |

## Size Sensitivity Results

|    MRR |   Hits@1 |   Hits@3 |   Hits@10 |   evaluated_queries | model    | subset   |   train_triples |   valid_triples |   test_triples |   entities |   relations |
|-------:|---------:|---------:|----------:|--------------------:|:---------|:---------|----------------:|----------------:|---------------:|-----------:|------------:|
| 0.0128 |   0      |   0      |    0      |                  22 | TransE   | 20k_cap  |              87 |              11 |             11 |        151 |          68 |
| 0.066  |   0.0455 |   0.0455 |    0.0455 |                  22 | DistMult | 20k_cap  |              87 |              11 |             11 |        151 |          68 |
| 0.0236 |   0      |   0      |    0      |                  22 | TransE   | 50k_cap  |              87 |              11 |             11 |        151 |          68 |
| 0.0162 |   0      |   0      |    0      |                  22 | DistMult | 50k_cap  |              87 |              11 |             11 |        151 |          68 |
| 0.0578 |   0      |   0.0455 |    0.1364 |                  22 | TransE   | full     |              87 |              11 |             11 |        151 |          68 |
| 0.0283 |   0      |   0      |    0.0455 |                  22 | DistMult | full     |              87 |              11 |             11 |        151 |          68 |

## Nearest Neighbor Examples

Nearest neighbors were computed using cosine similarity between entity embeddings.

| entity           |   neighbor_rank | neighbor                            |   cosine_similarity |
|:-----------------|----------------:|:------------------------------------|--------------------:|
| about_45         |               1 | upper_arms                          |              0.6597 |
| about_45         |               2 | excessive_lumbar_extension          |              0.2947 |
| about_45         |               3 | elbow                               |              0.2718 |
| about_45         |               4 | pectoralis_majors_upper_portion     |              0.2672 |
| about_45         |               5 | back                                |              0.2623 |
| aid              |               1 | more_weight                         |              0.3262 |
| aid              |               2 | eccentric_phase                     |              0.3098 |
| aid              |               3 | four_basic_ways                     |              0.2467 |
| aid              |               4 | about_45                            |              0.2346 |
| aid              |               5 | assists                             |              0.2189 |
| angle            |               1 | muscle                              |              0.3517 |
| angle            |               2 | similar_shoulder                    |              0.3264 |
| angle            |               3 | lateral_triceps                     |              0.3143 |
| angle            |               4 | triceps                             |              0.2763 |
| angle            |               5 | greater_horizontal_shoulder_moments |              0.2439 |
| anterior_deltoid |               1 | incline_press                       |              0.3723 |
| anterior_deltoid |               2 | technique                           |              0.2807 |
| anterior_deltoid |               3 | retraction                          |              0.2665 |
| anterior_deltoid |               4 | shoulder_flexion_demands            |              0.2637 |
| anterior_deltoid |               5 | floor                               |              0.2291 |
| anything         |               1 | stronger_triceps                    |              0.3088 |
| anything         |               2 | triceps                             |              0.2923 |
| anything         |               3 | mainly_vertical_resultant_forces    |              0.2868 |
| anything         |               4 | medium_grip_width                   |              0.2677 |
| anything         |               5 | entity_45_pounds                    |              0.2647 |

## t-SNE Visualization

- t-SNE plot saved to: `C:\Users\Maxim\Documents\02_ESILV\A4\S8\Web_datamining_and_semantics\Web_Datamining_and_Semantics_Project_Maxim_Grossmann_Geoffroy_Gankoue\05_Knowledge_Graph_Embeddings\outputs\tsne_embeddings.png`

## Reflection

The KGE results should be interpreted carefully because the project knowledge graph is relatively small. Knowledge graph embedding models generally perform better on larger, denser graphs. However, this experiment demonstrates the full KGE pipeline: RDF cleaning, train/validation/test split, training of two models, link prediction evaluation, size sensitivity, nearest neighbors, and t-SNE visualization.