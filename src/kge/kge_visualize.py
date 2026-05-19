"""
KGE Visualizations:
  - t-SNE des embeddings (reports/tsne_embeddings.png)
  - Bar chart métriques (reports/kge_metrics_chart.png)
  - Nearest neighbors  (reports/nearest_neighbors.txt)
  - Size sensitivity   (reports/size_sensitivity.json)
  - KG graph networkx  (reports/kg_graph.png)
"""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "kge"
OUT  = ROOT / "reports"
OUT.mkdir(exist_ok=True)

# ── helpers ────────────────────────────────────────────────────

def read_triples(path):
    triples = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            p = line.strip().split("\t")
            if len(p) == 3:
                triples.append(tuple(p))
    return triples

def build_ids(*sets):
    ents, rels = set(), set()
    for triples in sets:
        for h, r, t in triples:
            ents.add(h); ents.add(t); rels.add(r)
    return ({e: i for i, e in enumerate(sorted(ents))},
            {r: i for i, r in enumerate(sorted(rels))})

def encode(triples, e2i, r2i):
    return np.array([(e2i[h], r2i[r], e2i[t]) for h,r,t in triples], dtype=np.int64)

def train_transe(train, n_ent, n_rel, dim=50, epochs=150, lr=0.02, margin=1.0, seed=42):
    rng = np.random.default_rng(seed)
    E = rng.normal(0, 0.1, (n_ent, dim))
    R = rng.normal(0, 0.1, (n_rel, dim))
    arr = train.copy()
    for _ in range(epochs):
        rng.shuffle(arr)
        for h, r, t in arr:
            tn  = rng.integers(n_ent)
            pos = np.linalg.norm(E[h]+R[r]-E[t])
            neg = np.linalg.norm(E[h]+R[r]-E[tn])
            if margin + pos - neg > 0:
                gp = (E[h]+R[r]-E[t])  / (pos+1e-9)
                gn = (E[h]+R[r]-E[tn]) / (neg+1e-9)
                E[h]-=lr*gp; R[r]-=lr*gp; E[t] +=lr*gp
                E[h]+=lr*gn; R[r]+=lr*gn; E[tn]-=lr*gn
        norms = np.linalg.norm(E, axis=1, keepdims=True)+1e-9
        E = E / np.maximum(norms, 1.0)
    return E, R

# ── entity type ────────────────────────────────────────────────

MUSCLES   = {"pectoralis major","triceps","deltoids","anterior deltoid","lats","rotator cuff"}
JOINTS    = {"shoulder","elbow","wrist","scapula"}
EQUIPMENT = {"bar","barbell","bench"}
BIOMECH   = {"force","torque","moment","activation","emg","range of motion","velocity","power"}

TYPE_COLORS = {
    "Muscle":          "#E24B4A",
    "Joint":           "#378ADD",
    "Equipment":       "#EF9F27",
    "BiomechanicalVar":"#1D9E75",
    "Exercise":        "#7F77DD",
    "TechniqueCue":    "#888780",
}

def etype(name):
    n = name.lower().replace("_"," ")
    if any(m in n for m in MUSCLES):   return "Muscle"
    if any(j in n for j in JOINTS):    return "Joint"
    if any(e in n for e in EQUIPMENT): return "Equipment"
    if any(v in n for v in BIOMECH):   return "BiomechanicalVar"
    if "bench" in n:                   return "Exercise"
    return "TechniqueCue"

# ── t-SNE ──────────────────────────────────────────────────────

def plot_tsne(E, id2ent):
    n   = len(id2ent)
    rng = np.random.default_rng(0)
    idx = rng.choice(n, min(200, n), replace=False)
    emb   = E[idx]
    names = [id2ent[i] for i in idx]
    types = [etype(nm) for nm in names]

    perp   = min(30, len(idx)-1)
    coords = TSNE(n_components=2, perplexity=perp, random_state=0, max_iter=1000).fit_transform(emb)

    fig, ax = plt.subplots(figsize=(11, 8))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    for typ, col in TYPE_COLORS.items():
        mask = [i for i, t in enumerate(types) if t == typ]
        if mask:
            ax.scatter(coords[mask,0], coords[mask,1], c=col, s=28,
                       alpha=0.82, label=typ, edgecolors="none", zorder=3)

    KEY = {"bench press","pectoralis major","triceps","bar","shoulder","elbow","force","torque"}
    for i, nm in enumerate(names):
        if nm.replace("_"," ") in KEY:
            ax.annotate(nm.replace("_"," "), (coords[i,0], coords[i,1]),
                        fontsize=7, color="white", xytext=(4,4),
                        textcoords="offset points")

    ax.legend(loc="upper right", framealpha=0.25, labelcolor="white",
              fontsize=8, facecolor="#161b22", edgecolor="#30363d")
    ax.set_title("t-SNE of TransE Entity Embeddings", color="white", fontsize=13)
    ax.tick_params(colors="#444")
    for sp in ax.spines.values(): sp.set_edgecolor("#30363d")

    out = OUT / "tsne_embeddings.png"
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"t-SNE saved -> {out}")

# ── nearest neighbors ──────────────────────────────────────────

def nearest_neighbors(E, id2ent, k=5):
    ent2id = {v: ki for ki, v in id2ent.items()}
    queries = ["bench_press","pectoralis_major","triceps","bar","shoulder","force"]
    lines   = ["# Nearest Neighbors (TransE embeddings)\n"]
    for q in queries:
        qid = ent2id.get(q)
        if qid is None:
            for nm, i in ent2id.items():
                if q in nm: qid = i; q = nm; break
        if qid is None:
            lines.append(f"[{q}] not found.\n"); continue
        dists = np.linalg.norm(E - E[qid], axis=1)
        dists[qid] = np.inf
        top = np.argsort(dists)[:k]
        lines.append(f"Nearest neighbors of '{id2ent[qid]}':")
        for rank, idx in enumerate(top, 1):
            lines.append(f"  {rank}. {id2ent[idx]:<40} dist={dists[idx]:.4f}")
        lines.append("")
    text = "\n".join(lines)
    out  = OUT / "nearest_neighbors.txt"
    out.write_text(text, encoding="utf-8")
    print(f"Nearest neighbors saved -> {out}")
    print(text)

# ── size sensitivity ───────────────────────────────────────────

def size_sensitivity(train_ids, n_ent, n_rel):
    print("\n--- Size-sensitivity (TransE) ---")
    rng     = np.random.default_rng(0)
    results = []
    for frac in (0.3, 0.6, 1.0):
        n      = max(10, int(len(train_ids)*frac))
        subset = train_ids[rng.choice(len(train_ids), n, replace=False)]
        E, R   = train_transe(subset, n_ent, n_rel, dim=32, epochs=80)
        test   = train_ids[rng.choice(len(train_ids), min(30,len(train_ids)), replace=False)]
        all_e  = np.arange(n_ent)
        ranks  = []
        for h, r, t in test:
            scores = -np.linalg.norm(E[np.full(n_ent,h)] + R[np.full(n_ent,r)] - E[all_e], axis=1)
            ranks.append(int(np.sum(scores > scores[t])+1))
        mrr = float(np.mean(1.0/np.array(ranks)))
        results.append({"fraction": frac, "n_triples": n, "MRR": round(mrr,4)})
        print(f"  {int(frac*100):3d}% ({n:4d} triples) -> MRR={mrr:.4f}")
    (OUT/"size_sensitivity.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

# ── metrics chart ──────────────────────────────────────────────

def plot_metrics_chart():
    path = ROOT / "reports" / "kge_metrics.json"
    if not path.exists(): return
    data    = json.loads(path.read_text())
    models  = [d["model"] for d in data]
    metrics = ["MRR","Hits@1","Hits@3","Hits@10"]
    x       = np.arange(len(metrics))
    width   = 0.35
    colors  = ["#378ADD","#E24B4A"]

    fig, ax = plt.subplots(figsize=(9,5))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    for i, (model, col) in enumerate(zip(models, colors)):
        vals = [data[i][m] for m in metrics]
        bars = ax.bar(x + i*width - width/2, vals, width, label=model, color=col, alpha=0.88)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.008,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=8, color="white")

    ax.set_xticks(x); ax.set_xticklabels(metrics, color="white")
    ax.set_ylim(0, 0.6); ax.set_ylabel("Score", color="white")
    ax.set_title("KGE Model Comparison — TransE vs DistMult", color="white", fontsize=12)
    ax.tick_params(colors="white")
    ax.yaxis.grid(True, color="#30363d", linewidth=0.5); ax.set_axisbelow(True)
    for sp in ax.spines.values(): sp.set_edgecolor("#30363d")
    ax.legend(framealpha=0.25, labelcolor="white", facecolor="#161b22", edgecolor="#30363d")

    out = OUT / "kge_metrics_chart.png"
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"Metrics chart saved -> {out}")

# ── KG graph ───────────────────────────────────────────────────

def plot_kg_graph():
    try:
        import networkx as nx
    except ImportError:
        print("networkx not installed, skipping KG graph.")
        return
    from rdflib import Graph, Namespace, RDFS
    EX = Namespace("http://example.org/benchpress/kg/")
    g  = Graph()
    g.parse(ROOT/"kg_artifacts"/"reasoned_graph.ttl", format="turtle")

    G = nx.DiGraph()
    bench = EX.BenchPress
    edges = []
    for p, o in g.predicate_objects(bench):
        if str(p).startswith(str(EX)):
            pred  = str(p).split("/")[-1]
            label = str(next(g.objects(o, RDFS.label), str(o).split("/")[-1]))[:25]
            edges.append(("BenchPress", label, pred))
        if len(edges) >= 35: break

    for src, tgt, pred in edges:
        G.add_edge(src, tgt, label=pred)

    node_colors = ["#7F77DD" if n == "BenchPress" else "#378ADD" for n in G.nodes()]
    fig, ax = plt.subplots(figsize=(14,10))
    fig.patch.set_facecolor("#0d1117"); ax.set_facecolor("#0d1117")
    pos = nx.spring_layout(G, seed=42, k=2.2)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=800, ax=ax, alpha=0.9)
    nx.draw_networkx_labels(G, pos, font_size=7, font_color="white", ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color="#444c56", arrows=True,
                           arrowsize=15, connectionstyle="arc3,rad=0.1", ax=ax)
    edge_labels = {(u,v): d["label"] for u,v,d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                 font_size=6, font_color="#8b949e", ax=ax)
    ax.set_title("Bench Press Knowledge Graph", color="white", fontsize=12)
    ax.axis("off")
    out = OUT / "kg_graph.png"
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"KG graph saved -> {out}")

# ── main ───────────────────────────────────────────────────────

def main():
    train_raw = read_triples(DATA/"train.txt")
    valid_raw = read_triples(DATA/"valid.txt")
    test_raw  = read_triples(DATA/"test.txt")
    ent2id, rel2id = build_ids(train_raw, valid_raw, test_raw)
    id2ent = {v: k for k,v in ent2id.items()}
    train_ids = encode(train_raw, ent2id, rel2id)

    print("Training TransE (dim=50, epochs=150)...")
    E, _ = train_transe(train_ids, len(ent2id), len(rel2id))

    plot_tsne(E, id2ent)
    nearest_neighbors(E, id2ent)
    size_sensitivity(train_ids, len(ent2id), len(rel2id))
    plot_metrics_chart()
    plot_kg_graph()
    print("\nDone.")

if __name__ == "__main__":
    main()