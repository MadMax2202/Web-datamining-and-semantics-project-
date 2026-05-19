"""
SPARQL Expansion:
1. Fusion locale : initial_graph + alignment.ttl
2. Expansion distante : federation SPARQL vers Wikidata
"""
from pathlib import Path
import json, time, urllib.request, urllib.parse
from rdflib import Graph, Namespace, RDFS, Literal
from rdflib.namespace import OWL

ROOT = Path(__file__).resolve().parents[2]
EX   = Namespace("http://example.org/benchpress/kg/")

def local_merge():
    g = Graph()
    g.bind("ex", EX); g.bind("owl", OWL)
    g.parse(ROOT/"kg_artifacts"/"initial_graph.ttl", format="turtle")
    print(f"[1] Initial graph : {len(g)} triples")
    g.parse(ROOT/"kg_artifacts"/"alignment.ttl", format="turtle")
    print(f"[2] Après merge alignment : {len(g)} triples")
    return g

def remote_expansion(g):
    print("[3] Federation SPARQL -> Wikidata...")
    wd_prefix = "http://www.wikidata.org/entity/"
    qid_map = {}
    for s, _, o in g.triples((None, OWL.sameAs, None)):
        uri = str(o)
        if uri.startswith(wd_prefix):
            qid_map[uri[len(wd_prefix):]] = s

    if not qid_map:
        print("  Aucun lien Wikidata trouvé."); return 0

    print(f"  {len(qid_map)} entités Wikidata : {list(qid_map.keys())}")
    values = " ".join(f"wd:{q}" for q in qid_map)
    query  = f"""
SELECT ?entity ?label ?description WHERE {{
  VALUES ?entity {{ {values} }}
  SERVICE wikibase:label {{
    bd:serviceParam wikibase:language "en" .
    ?entity rdfs:label ?label .
    ?entity schema:description ?description .
  }}
}}"""
    params = urllib.parse.urlencode({"query": query, "format": "json"})
    req    = urllib.request.Request(
        f"https://query.wikidata.org/sparql?{params}",
        headers={"User-Agent": "BenchPressKG/1.0 (student project)",
                 "Accept": "application/json"}
    )
    try:
        time.sleep(1)
        with urllib.request.urlopen(req, timeout=15) as resp:
            bindings = json.loads(resp.read())["results"]["bindings"]
    except Exception as e:
        print(f"  Wikidata inaccessible ({e}), skip remote expansion."); return 0

    added = 0
    for b in bindings:
        uri   = b.get("entity",{}).get("value","")
        qid   = uri[len(wd_prefix):]
        local = qid_map.get(qid)
        if not local: continue
        if label := b.get("label",{}).get("value",""):
            g.add((local, RDFS.label, Literal(label, lang="en"))); added += 1
        if desc := b.get("description",{}).get("value",""):
            g.add((local, RDFS.comment, Literal(f"[Wikidata] {desc}", lang="en"))); added += 1
    print(f"  +{added} triples depuis Wikidata.")
    return added

def main():
    g = local_merge()
    remote_expansion(g)
    g.serialize(ROOT/"kg_artifacts"/"expanded_with_alignment.ttl", format="turtle")
    g.serialize(ROOT/"kg_artifacts"/"expanded.nt", format="nt")
    print(f"[4] KG étendu écrit : {len(g)} triples")
    stats = {
        "triples": len(g),
        "unique_subjects": len(set(g.subjects())),
        "unique_predicates": len(set(g.predicates())),
        "unique_objects": len(set(g.objects())),
        "expansion_strategy": "Local: merge alignment.ttl. Remote: SPARQL federation Wikidata."
    }
    (ROOT/"kg_artifacts"/"kb_statistics.json").write_text(
        json.dumps(stats, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()