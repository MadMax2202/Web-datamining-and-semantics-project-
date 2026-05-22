# KGE Dataset Summary

## Source

- Input RDF graph: `C:\Users\Maxim\Documents\02_ESILV\A4\S8\Web_datamining_and_semantics\Web_Datamining_and_Semantics_Project_Maxim_Grossmann_Geoffroy_Gankoue\01_Data\kb_outputs\expanded_kb.ttl`

## Cleaning Strategy

- Removed RDF metadata triples such as `rdf:type`, `rdfs:label`, confidence scores, evidence sentences, and source document metadata.
- Kept only semantic object-property triples where subject, predicate, and object are project KB URIs.
- Removed statement/evidence nodes from the KGE training dataset.

## Final Dataset

- Semantic triples: `109`
- Training triples: `87`
- Validation triples: `11`
- Test triples: `11`
- Entities: `151`
- Relations: `68`

## Size Sensitivity

The assignment requests 20k / 50k / full size-sensitivity tests.
Because this domain-specific KB is smaller than 20k semantic triples, capped subsets were created:

- `size_20k_cap.tsv`: min(20k, available triples)
- `size_50k_cap.tsv`: min(50k, available triples)
- `size_full.tsv`: all available triples

This keeps the experiment reproducible and honest while preserving the same evaluation logic.