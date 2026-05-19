"""
RAG CLI — NL -> SPARQL avec Ollama + fallback template + self-repair + évaluation.
"""
from pathlib import Path
import re, json, subprocess
from rdflib import Graph, Namespace, RDFS

ROOT = Path(__file__).resolve().parents[2]
EX   = Namespace("http://example.org/benchpress/kg/")

SCHEMA_SUMMARY = """
PREFIX ex:   <http://example.org/benchpress/kg/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

Classes: Exercise, Muscle, Joint, Equipment, TechniqueCue,
         BiomechanicalVariable, RiskFactor, EvidenceSentence

Propriétés:
  ex:targetsMuscle   (Exercise -> Muscle)
  ex:usesEquipment   (Exercise -> Equipment)
  ex:hasTechniqueCue (Exercise -> TechniqueCue)
  ex:affects         (any -> any)
  ex:hasEvidence     (any -> EvidenceSentence)
  ex:confidence      (EvidenceSentence -> float)
  rdfs:label         (any -> string)
  rdfs:comment       (EvidenceSentence -> string, texte de la phrase)

Entité centrale: ex:BenchPress
"""

PROMPT_TEMPLATE = """\
Tu es un expert SPARQL. Voici le schéma du knowledge graph :
{schema}

Question : {question}

Écris une requête SPARQL SELECT qui répond à cette question.
Retourne UNIQUEMENT la requête SPARQL, sans explication ni balises markdown.
"""

PREFIXES = """\
PREFIX ex:   <http://example.org/benchpress/kg/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

# ── graph ──────────────────────────────────────────────────────

def load_graph():
    g = Graph()
    for f in ["reasoned_graph.ttl","expanded_with_alignment.ttl","initial_graph.ttl"]:
        p = ROOT/"kg_artifacts"/f
        if p.exists():
            g.parse(p, format="turtle")
            print(f"[KG] {f} chargé ({len(g)} triples)")
            return g
    raise FileNotFoundError("Aucun artefact KG trouvé.")

# ── ollama ─────────────────────────────────────────────────────

def ollama_ok():
    try:
        r = subprocess.run(["ollama","list"], capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False

def call_ollama(prompt, model="llama3.1"):
    try:
        r = subprocess.run(["ollama","run",model], input=prompt,
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None

# ── NL -> SPARQL ───────────────────────────────────────────────

def nl_to_sparql(question):
    if ollama_ok():
        prompt = PROMPT_TEMPLATE.format(schema=SCHEMA_SUMMARY, question=question)
        resp   = call_ollama(prompt)
        if resp:
            sparql = re.sub(r"```(?:sparql)?", "", resp).replace("```","").strip()
            if "SELECT" in sparql.upper():
                return sparql, "ollama"
    return template(question), "template"

def template(question):
    q = question.lower()
    if any(w in q for w in ["muscle","target"]):
        return PREFIXES+"""
SELECT DISTINCT ?label WHERE {
  ex:BenchPress ex:targetsMuscle ?m .
  ?m rdfs:label ?label .
} LIMIT 20"""
    if any(w in q for w in ["equipment","bar","barbell"]):
        return PREFIXES+"""
SELECT DISTINCT ?label WHERE {
  ex:BenchPress ex:usesEquipment ?e .
  ?e rdfs:label ?label .
} LIMIT 20"""
    if any(w in q for w in ["evidence","sentence","source"]):
        return PREFIXES+"""
SELECT DISTINCT ?entityLabel ?sentence ?confidence WHERE {
  ?entity ex:hasEvidence ?ev .
  ?entity rdfs:label ?entityLabel .
  ?ev rdfs:comment ?sentence .
  OPTIONAL { ?ev ex:confidence ?confidence . }
} ORDER BY DESC(?confidence) LIMIT 10"""
    if any(w in q for w in ["technique","cue","form","how to"]):
        return PREFIXES+"""
SELECT DISTINCT ?label WHERE {
  ?s a ex:TechniqueCue .
  ?s rdfs:label ?label .
} LIMIT 20"""
    if any(w in q for w in ["biomech","force","torque","moment","activation"]):
        return PREFIXES+"""
SELECT DISTINCT ?label WHERE {
  ?s a ex:BiomechanicalVariable .
  ?s rdfs:label ?label .
} LIMIT 20"""
    if any(w in q for w in ["joint","shoulder","elbow","wrist"]):
        return PREFIXES+"""
SELECT DISTINCT ?label WHERE {
  ?s a ex:Joint .
  ?s rdfs:label ?label .
} LIMIT 20"""
    return PREFIXES+"""
SELECT DISTINCT ?sLabel ?p ?oLabel WHERE {
  ?s ?p ?o .
  ?s rdfs:label ?sLabel .
  ?o rdfs:label ?oLabel .
  FILTER(?p != rdf:type)
} LIMIT 15"""

# ── self-repair ────────────────────────────────────────────────

REPAIRS = [
    ("Replace wrong prefix",       lambda q: q.replace("benchpress:","ex:").replace("bp:","ex:")),
    ("Add missing PREFIX block",   lambda q: PREFIXES+q if "PREFIX" not in q else q),
    ("Increase LIMIT",             lambda q: re.sub(r"LIMIT\s+\d+","LIMIT 50",q)),
    ("Fix ex:name -> rdfs:label",  lambda q: re.sub(r"ex:name\b","rdfs:label",q)),
]

def safe_query(g, sparql):
    try:
        return list(g.query(sparql)), None
    except Exception as e:
        err = str(e)
    repaired = sparql
    for desc, fn in REPAIRS:
        repaired = fn(repaired)
        try:
            rows = list(g.query(repaired))
            print(f"  [self-repair] {desc}")
            return rows, None
        except Exception as e:
            err = str(e)
    return [], f"Échec après toutes les réparations : {err}"

# ── baseline ───────────────────────────────────────────────────

STATIC_BASELINE = {
    "muscle":    "The bench press primarily targets the pectoralis major, with secondary activation of the triceps and anterior deltoid.",
    "equipment": "The bench press uses a barbell and a flat bench.",
    "evidence":  "Research shows proper technique and progressive overload are key for bench press performance.",
    "technique": "Proper bench press technique involves retracting the scapula and tucking the elbows.",
    "biomech":   "The bench press involves horizontal shoulder flexion generating force through the pectoralis major.",
    "joint":     "The shoulder, elbow, and wrist joints are involved in the bench press.",
}

def baseline(question):
    if ollama_ok():
        prompt = f"Answer in 2 sentences from general knowledge:\n{question}"
        resp   = call_ollama(prompt)
        if resp: return resp
    q = question.lower()
    for key, ans in STATIC_BASELINE.items():
        if key in q: return ans
    return "The bench press is a compound upper-body exercise."

# ── evaluation ─────────────────────────────────────────────────

EVAL_QUESTIONS = [
    "What muscles does the bench press target?",
    "What equipment is associated with the bench press?",
    "What evidence sentences support the extracted KG?",
    "What biomechanical variables appear in the bench press KG?",
    "Which entities are related to technique cues?",
]

def run_evaluation(g):
    print("\n"+"="*65)
    print("RAG EVALUATION — Baseline vs RAG")
    print("="*65)
    results = []
    for i, q in enumerate(EVAL_QUESTIONS, 1):
        print(f"\nQ{i}: {q}")
        base         = baseline(q)
        sparql, meth = nl_to_sparql(q)
        rows, err    = safe_query(g, sparql)
        rag = (f"[Error] {err}" if err
               else "(no results)" if not rows
               else "; ".join(" | ".join(str(x) for x in r) for r in rows[:5]))
        print(f"  Baseline : {base[:100]}")
        print(f"  RAG ({meth}): {rag[:100]}")
        results.append({"question":q,"baseline":base,"rag_method":meth,
                        "rag_answer":rag,"sparql":sparql.strip()})

    # markdown
    lines = ["# RAG Evaluation — Baseline vs RAG\n",
             "| # | Question | Baseline (LLM) | RAG (SPARQL) |",
             "|---|---|---|---|"]
    for i, r in enumerate(results,1):
        lines.append(f"| {i} | {r['question']} | {r['baseline'][:100]} | {r['rag_answer'][:100]} |")
    lines += ["","## Observations",
              "- Baseline : réponses génériques non sourcées.",
              "- RAG : entités et phrases extraites directement du graphe RDF.",
              "- Les réponses RAG sont traçables et reproductibles.",
              "- Limitation : template NL->SPARQL limité ; Ollama améliore la couverture."]
    (ROOT/"reports"/"rag_evaluation.md").write_text("\n".join(lines), encoding="utf-8")
    (ROOT/"reports"/"rag_evaluation_results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\nEvaluation sauvegardée -> reports/rag_evaluation.md")

# ── main ───────────────────────────────────────────────────────

def main():
    g = load_graph()
    print("[RAG] Ollama :", "OK" if ollama_ok() else "non disponible — fallback template")
    print(SCHEMA_SUMMARY)
    run_evaluation(g)
    print("\n"+"="*65)
    print("Mode interactif — tape ta question ou 'exit'")
    print("="*65)
    while True:
        q = input("\n> ").strip()
        if q.lower() in {"exit","quit","q"}: break
        sparql, meth = nl_to_sparql(q)
        print(f"\n[{meth}] SPARQL:\n{sparql}")
        rows, err = safe_query(g, sparql)
        if err: print(f"[Error] {err}")
        else:
            print(f"Réponse ({len(rows)} résultats):")
            for row in rows: print("  -", " | ".join(str(x) for x in row))

if __name__ == "__main__":
    main()