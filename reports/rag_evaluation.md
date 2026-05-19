# RAG Evaluation — Baseline vs RAG

| # | Question | Baseline (LLM) | RAG (SPARQL) |
|---|---|---|---|
| 1 | What muscles does the bench press target? | The bench press primarily targets the pectoralis major, with secondary activation of the triceps and | both pecs; chest and triceps development; lateral triceps; lower pectoralis major; medial triceps |
| 2 | What equipment is associated with the bench press? | The bench press uses a barbell and a flat bench. | bar; bar path; barbell bench press; barbell movement; bench |
| 3 | What evidence sentences support the extracted KG? | Research shows proper technique and progressive overload are key for bench press performance. | triceps | Because of that, the pecs and the triceps can work synergistically at both the elbow and s |
| 4 | What biomechanical variables appear in the bench press KG? | The bench press involves horizontal shoulder flexion generating force through the pectoralis major. | concentric phase; eccentric phase; elite powerlifters; horizontal forces; internal moment arm |
| 5 | Which entities are related to technique cues? | Proper bench press technique involves retracting the scapula and tucking the elbows. | 15° decline; 30° inclination; angle; article; assists |

## Observations
- Baseline : réponses génériques non sourcées.
- RAG : entités et phrases extraites directement du graphe RDF.
- Les réponses RAG sont traçables et reproductibles.
- Limitation : template NL->SPARQL limité ; Ollama améliore la couverture.