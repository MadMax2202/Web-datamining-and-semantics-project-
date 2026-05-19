from pathlib import Path
from rdflib import Graph

ROOT = Path(__file__).resolve().parents[2]
g = Graph()
g.parse(ROOT / "kg_artifacts" / "initial_graph.ttl", format="turtle")
g.parse(ROOT / "kg_artifacts" / "alignment.ttl", format="turtle")
g.serialize(ROOT / "kg_artifacts" / "expanded_with_alignment.ttl", format="turtle")
print(f"Expanded KG written with {len(g)} triples.")
