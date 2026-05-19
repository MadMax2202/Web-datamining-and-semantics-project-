"""
Minimal reproducible KGE training for TransE and DistMult using NumPy.

This is intentionally lightweight for a small course project. It creates real
train/valid/test metrics (MRR, Hits@1/3/10) without requiring PyKEEN.
"""
from pathlib import Path
import argparse, json, random
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "kge"
OUT = ROOT / "reports" / "kge_metrics.json"

def read_triples(path):
    triples = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 3:
                triples.append(tuple(parts))
    return triples

def build_ids(*triple_sets):
    ents, rels = set(), set()
    for triples in triple_sets:
        for h,r,t in triples:
            ents.add(h); ents.add(t); rels.add(r)
    return {e:i for i,e in enumerate(sorted(ents))}, {r:i for i,r in enumerate(sorted(rels))}

def encode(triples, ent2id, rel2id):
    return np.array([(ent2id[h], rel2id[r], ent2id[t]) for h,r,t in triples], dtype=np.int64)

def score_transe(E, R, h, r, t):
    return -np.linalg.norm(E[h] + R[r] - E[t], axis=-1)

def score_distmult(E, R, h, r, t):
    return np.sum(E[h] * R[r] * E[t], axis=-1)

def train(model, train, n_ent, n_rel, dim=32, epochs=80, lr=0.03, margin=1.0, seed=42):
    rng = np.random.default_rng(seed)
    E = rng.normal(0, 0.1, size=(n_ent, dim))
    R = rng.normal(0, 0.1, size=(n_rel, dim))
    triples = train.copy()
    for _ in range(epochs):
        rng.shuffle(triples)
        for h,r,t in triples:
            corrupt_tail = rng.random() < 0.5
            if corrupt_tail:
                hn, rn, tn = h, r, rng.integers(n_ent)
            else:
                hn, rn, tn = rng.integers(n_ent), r, t

            if model == "TransE":
                pos_vec = E[h] + R[r] - E[t]
                neg_vec = E[hn] + R[rn] - E[tn]
                pos = np.linalg.norm(pos_vec)
                neg = np.linalg.norm(neg_vec)
                if margin + pos - neg > 0:
                    gp = pos_vec / (pos + 1e-9)
                    gn = neg_vec / (neg + 1e-9)
                    E[h] -= lr * gp; R[r] -= lr * gp; E[t] += lr * gp
                    E[hn] += lr * gn; R[rn] += lr * gn; E[tn] -= lr * gn
            else:  # DistMult logistic negative sampling
                pos = np.sum(E[h]*R[r]*E[t])
                neg = np.sum(E[hn]*R[rn]*E[tn])
                # gradients for -log(sigmoid(pos)) - log(sigmoid(-neg))
                gpos = 1/(1+np.exp(pos))      # sigmoid(-pos)
                gneg = 1/(1+np.exp(-neg))     # sigmoid(neg)
                Eh, Rr, Et = E[h].copy(), R[r].copy(), E[t].copy()
                E[h] += lr * gpos * Rr * Et
                R[r] += lr * gpos * Eh * Et
                E[t] += lr * gpos * Eh * Rr
                Ehn, Rrn, Etn = E[hn].copy(), R[rn].copy(), E[tn].copy()
                E[hn] -= lr * gneg * Rrn * Etn
                R[rn] -= lr * gneg * Ehn * Etn
                E[tn] -= lr * gneg * Ehn * Rrn
        # normalize entity embeddings
        norms = np.linalg.norm(E, axis=1, keepdims=True) + 1e-9
        E = E / np.maximum(norms, 1.0)
    return E, R

def evaluate(model, E, R, test):
    n_ent = E.shape[0]
    ranks = []
    all_ents = np.arange(n_ent)
    for h,r,t in test:
        # tail prediction rank
        hs = np.full(n_ent, h)
        rs = np.full(n_ent, r)
        if model == "TransE":
            scores = score_transe(E, R, hs, rs, all_ents)
        else:
            scores = score_distmult(E, R, hs, rs, all_ents)
        # rank descending, 1 is best
        true_score = scores[t]
        rank = int(np.sum(scores > true_score) + 1)
        ranks.append(rank)
    ranks = np.array(ranks)
    return {
        "MRR": float(np.mean(1.0 / ranks)),
        "Hits@1": float(np.mean(ranks <= 1)),
        "Hits@3": float(np.mean(ranks <= 3)),
        "Hits@10": float(np.mean(ranks <= 10)),
        "test_triples": int(len(test))
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="TransE", choices=["TransE", "DistMult"])
    args = parser.parse_args()

    train_raw = read_triples(DATA / "train.txt")
    valid_raw = read_triples(DATA / "valid.txt")
    test_raw = read_triples(DATA / "test.txt")
    ent2id, rel2id = build_ids(train_raw, valid_raw, test_raw)
    train_ids = encode(train_raw, ent2id, rel2id)
    test_ids = encode(test_raw, ent2id, rel2id)

    E, R = train(args.model, train_ids, len(ent2id), len(rel2id))
    metrics = evaluate(args.model, E, R, test_ids)
    metrics = {k: (round(v, 4) if isinstance(v, float) else v) for k,v in metrics.items()}
    metrics["model"] = args.model
    metrics["entities"] = len(ent2id)
    metrics["relations"] = len(rel2id)
    metrics["note"] = "Real lightweight NumPy KGE run; for stronger results, replace with PyKEEN."

    existing = []
    if OUT.exists():
        existing = json.loads(OUT.read_text())
    existing = [m for m in existing if m.get("model") != args.model] + [metrics]
    OUT.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    print(metrics)

if __name__ == "__main__":
    main()
