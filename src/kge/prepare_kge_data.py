from pathlib import Path
import random
from rdflib import Graph

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "kge"
OUT.mkdir(parents=True, exist_ok=True)

def compact(x):
    s = str(x)
    return s.replace("http://example.org/benchpress/kg/", "ex:")

def main():
    g = Graph()
    g.parse(ROOT / "kg_artifacts" / "initial_graph.ttl", format="turtle")
    triples = [(compact(s), compact(p), compact(o)) for s, p, o in g]
    triples = [t for t in triples if not t[2].startswith('"')]
    random.seed(42)
    random.shuffle(triples)

    n = len(triples)
    train = triples[: int(0.8*n)]
    valid = triples[int(0.8*n): int(0.9*n)]
    test = triples[int(0.9*n):]

    for name, data in [("train.txt", train), ("valid.txt", valid), ("test.txt", test)]:
        with open(OUT / name, "w", encoding="utf-8") as f:
            for s,p,o in data:
                f.write(f"{s}\t{p}\t{o}\n")
    print({ "train": len(train), "valid": len(valid), "test": len(test) })

if __name__ == "__main__":
    main()
