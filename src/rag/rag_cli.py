from pathlib import Path
import re
from rdflib import Graph, Namespace, RDFS

ROOT = Path(__file__).resolve().parents[2]
EX = Namespace("http://example.org/benchpress/kg/")

SCHEMA_SUMMARY = """
Classes: Exercise, Muscle, Joint, Equipment, TechniqueCue, BiomechanicalVariable, RiskFactor.
Main properties: targetsMuscle, usesEquipment, hasTechniqueCue, affects, increasesRiskOf, hasEvidence.
Central entity: ex:BenchPress.
"""

def load_graph():
    g = Graph()
    path = ROOT / "kg_artifacts" / "reasoned_graph.ttl"
    if not path.exists():
        path = ROOT / "kg_artifacts" / "initial_graph.ttl"
    g.parse(path, format="turtle")
    return g

def safe_query(g, sparql):
    try:
        return list(g.query(sparql))
    except Exception as e:
        repaired = sparql.replace("benchpress:", "ex:")
        try:
            return list(g.query(repaired))
        except Exception:
            raise e

def nl_to_sparql(question):
    q = question.lower()
    prefixes = """
PREFIX ex: <http://example.org/benchpress/kg/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""
    if "muscle" in q or "target" in q:
        return prefixes + """
SELECT DISTINCT ?label WHERE {
  ex:BenchPress ex:targetsMuscle ?m .
  ?m rdfs:label ?label .
}
LIMIT 20
"""
    if "equipment" in q or "bar" in q:
        return prefixes + """
SELECT DISTINCT ?label WHERE {
  ex:BenchPress ex:usesEquipment ?e .
  ?e rdfs:label ?label .
}
LIMIT 20
"""
    if "evidence" in q or "source" in q:
        return prefixes + """
SELECT DISTINCT ?entityLabel ?sentence WHERE {
  ?entity ex:hasEvidence ?ev .
  ?entity rdfs:label ?entityLabel .
  ?ev rdfs:comment ?sentence .
}
LIMIT 10
"""
    return prefixes + """
SELECT DISTINCT ?sLabel ?p ?oLabel WHERE {
  ?s ?p ?o .
  ?s rdfs:label ?sLabel .
  ?o rdfs:label ?oLabel .
}
LIMIT 15
"""

def main():
    g = load_graph()
    print("Bench Press KG RAG CLI")
    print(SCHEMA_SUMMARY)
    print("Ask a question, or type 'exit'.")
    while True:
        question = input("> ").strip()
        if question.lower() in {"exit", "quit"}:
            break
        sparql = nl_to_sparql(question)
        print("\nGenerated SPARQL:\n", sparql)
        rows = safe_query(g, sparql)
        print("Answer:")
        for row in rows:
            print(" - " + " | ".join(str(x) for x in row))
        print()

if __name__ == "__main__":
    main()
