# RAG Evaluation Questions

Use these five questions for the baseline vs RAG comparison:

| # | Question | Expected KG/RAG behavior |
|---|---|---|
| 1 | What muscles does the bench press target? | Uses `ex:targetsMuscle` and returns extracted muscle entities. |
| 2 | What equipment is associated with the bench press? | Uses `ex:usesEquipment`. |
| 3 | What evidence sentences support the extracted KG? | Uses `ex:hasEvidence`. |
| 4 | What biomechanical variables appear in the bench press KG? | Searches labels and classes. |
| 5 | Which extracted relations are related to technique cues? | Returns triples from extracted technique category. |

Baseline: ask the LLM without the KG and record whether answers are unsupported or generic.
RAG: use the generated SPARQL + graph results and record exact entities/evidence.
