"""
05D_visualize_kge_artifacts.py

Optional visualization script for the KGE section.

This script reuses the artifacts already produced by the KGE pipeline:

- TransE_full_embeddings.npz
- DistMult_full_embeddings.npz
- kge_metrics.csv
- size_sensitivity.csv
- semantic_triples.tsv

It generates extra visual outputs for the final report / presentation:

- tsne_embeddings_dark.png
- kge_metrics_chart.png
- size_sensitivity_chart.png
- kg_graph_network.png

This script does not retrain models. It only visualizes existing outputs.
"""

from pathlib import Path
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.manifold import TSNE


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "05_Knowledge_Graph_Embeddings" / "outputs"

TRANSE_EMBEDDINGS = OUTPUT_DIR / "TransE_full_embeddings.npz"
DISTMULT_EMBEDDINGS = OUTPUT_DIR / "DistMult_full_embeddings.npz"

METRICS_FILE = OUTPUT_DIR / "kge_metrics.csv"
SIZE_FILE = OUTPUT_DIR / "size_sensitivity.csv"
SEMANTIC_TRIPLES_FILE = OUTPUT_DIR / "semantic_triples.tsv"

TSNE_DARK_FILE = OUTPUT_DIR / "tsne_embeddings_dark.png"
METRICS_CHART_FILE = OUTPUT_DIR / "kge_metrics_chart.png"
SIZE_CHART_FILE = OUTPUT_DIR / "size_sensitivity_chart.png"
KG_GRAPH_FILE = OUTPUT_DIR / "kg_graph_network.png"


# =============================
# ENTITY TYPE HEURISTICS
# =============================

MUSCLES = {
    "pectoralis", "triceps", "deltoid", "anterior_deltoid",
    "lats", "rotator_cuff", "muscle"
}

JOINTS = {
    "shoulder", "elbow", "wrist", "scapula", "joint"
}

EQUIPMENT = {
    "bar", "barbell", "bench", "rack"
}

BIOMECH = {
    "force", "torque", "moment", "activation", "emg",
    "range_of_motion", "velocity", "power", "demands",
    "flexion", "extension", "abduction"
}

TYPE_COLORS = {
    "Muscle": "#E24B4A",
    "Joint": "#378ADD",
    "Equipment": "#EF9F27",
    "BiomechanicalConcept": "#1D9E75",
    "Exercise": "#7F77DD",
    "TechniqueCue": "#AAAAAA",
}


def entity_type(name: str) -> str:
    n = name.lower()

    if any(x in n for x in MUSCLES):
        return "Muscle"

    if any(x in n for x in JOINTS):
        return "Joint"

    if any(x in n for x in EQUIPMENT):
        return "Equipment"

    if any(x in n for x in BIOMECH):
        return "BiomechanicalConcept"

    if "bench_press" in n or "press" in n:
        return "Exercise"

    return "TechniqueCue"


# =============================
# LOAD EMBEDDINGS
# =============================

def choose_embedding_file() -> Path:
    if TRANSE_EMBEDDINGS.exists():
        return TRANSE_EMBEDDINGS

    if DISTMULT_EMBEDDINGS.exists():
        return DISTMULT_EMBEDDINGS

    raise FileNotFoundError(
        "No embedding file found. Run 05B_train_kge_models.py first."
    )


def load_embeddings(path: Path):
    data = np.load(path, allow_pickle=True)
    embeddings = data["entity_embeddings"]
    labels = [str(x) for x in data["entity_labels"]]
    return embeddings, labels


# =============================
# DARK T-SNE
# =============================

def plot_dark_tsne():
    embedding_file = choose_embedding_file()
    embeddings, labels = load_embeddings(embedding_file)

    n = len(labels)

    if n < 3:
        print("Not enough entities for t-SNE.")
        return

    rng = np.random.default_rng(42)
    idx = rng.choice(n, min(200, n), replace=False)

    selected_embeddings = embeddings[idx]
    selected_labels = [labels[i] for i in idx]
    selected_types = [entity_type(label) for label in selected_labels]

    perplexity = min(30, max(2, len(idx) // 3))

    coords = TSNE(
        n_components=2,
        perplexity=perplexity,
        random_state=42,
        init="random",
        learning_rate="auto"
    ).fit_transform(selected_embeddings)

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    for typ, color in TYPE_COLORS.items():
        mask = [i for i, t in enumerate(selected_types) if t == typ]

        if mask:
            ax.scatter(
                coords[mask, 0],
                coords[mask, 1],
                c=color,
                s=35,
                alpha=0.85,
                label=typ,
                edgecolors="none"
            )

    key_entities = {
        "bench_press",
        "pectoralis_major",
        "triceps",
        "bar",
        "shoulder",
        "elbow",
        "force",
        "grip_width",
        "bar_path",
    }

    for i, label in enumerate(selected_labels):
        if label in key_entities:
            ax.annotate(
                label.replace("_", " "),
                (coords[i, 0], coords[i, 1]),
                fontsize=8,
                color="white",
                xytext=(4, 4),
                textcoords="offset points"
            )

    ax.set_title("t-SNE of KGE Entity Embeddings", color="white", fontsize=14)
    ax.set_xlabel("t-SNE dimension 1", color="white")
    ax.set_ylabel("t-SNE dimension 2", color="white")

    ax.tick_params(colors="#8b949e")

    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")

    ax.legend(
        loc="upper right",
        framealpha=0.25,
        labelcolor="white",
        facecolor="#161b22",
        edgecolor="#30363d"
    )

    plt.tight_layout()
    plt.savefig(
        TSNE_DARK_FILE,
        dpi=180,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )
    plt.close()

    print(f"Dark t-SNE saved to: {TSNE_DARK_FILE}")


# =============================
# METRICS CHART
# =============================

def plot_metrics_chart():
    if not METRICS_FILE.exists():
        print(f"Missing metrics file: {METRICS_FILE}")
        return

    df = pd.read_csv(METRICS_FILE)

    if df.empty:
        print("Metrics file is empty.")
        return

    metrics = ["MRR", "Hits@1", "Hits@3", "Hits@10"]
    models = df["model"].tolist()

    x = np.arange(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    colors = ["#378ADD", "#E24B4A", "#1D9E75", "#EF9F27"]

    for i, (_, row) in enumerate(df.iterrows()):
        values = [row[m] for m in metrics]

        bars = ax.bar(
            x + i * width - width / 2,
            values,
            width,
            label=row["model"],
            color=colors[i % len(colors)],
            alpha=0.9
        )

        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.005,
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=8,
                color="white"
            )

    ax.set_xticks(x)
    ax.set_xticklabels(metrics, color="white")
    ax.set_ylabel("Score", color="white")
    ax.set_title("KGE Model Comparison", color="white", fontsize=14)
    ax.tick_params(colors="white")
    ax.yaxis.grid(True, color="#30363d", linewidth=0.5)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")

    ax.legend(
        framealpha=0.25,
        labelcolor="white",
        facecolor="#161b22",
        edgecolor="#30363d"
    )

    plt.tight_layout()
    plt.savefig(
        METRICS_CHART_FILE,
        dpi=180,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )
    plt.close()

    print(f"Metrics chart saved to: {METRICS_CHART_FILE}")


# =============================
# SIZE SENSITIVITY CHART
# =============================

def plot_size_sensitivity():
    if not SIZE_FILE.exists():
        print(f"Missing size sensitivity file: {SIZE_FILE}")
        return

    df = pd.read_csv(SIZE_FILE)

    if df.empty:
        print("Size sensitivity file is empty.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    for model_name, group in df.groupby("model"):
        group = group.sort_values("train_triples")

        ax.plot(
            group["subset"],
            group["MRR"],
            marker="o",
            linewidth=2,
            label=model_name
        )

    ax.set_title("Size Sensitivity — MRR by Subset", color="white", fontsize=14)
    ax.set_xlabel("Subset", color="white")
    ax.set_ylabel("MRR", color="white")
    ax.tick_params(colors="white")
    ax.yaxis.grid(True, color="#30363d", linewidth=0.5)

    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")

    ax.legend(
        framealpha=0.25,
        labelcolor="white",
        facecolor="#161b22",
        edgecolor="#30363d"
    )

    plt.tight_layout()
    plt.savefig(
        SIZE_CHART_FILE,
        dpi=180,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )
    plt.close()

    print(f"Size sensitivity chart saved to: {SIZE_CHART_FILE}")


# =============================
# KG GRAPH NETWORK
# =============================

def plot_kg_graph_network(max_edges: int = 45):
    try:
        import networkx as nx
    except ImportError:
        print("networkx not installed. Run: pip install networkx")
        return

    if not SEMANTIC_TRIPLES_FILE.exists():
        print(f"Missing semantic triples file: {SEMANTIC_TRIPLES_FILE}")
        return

    df = pd.read_csv(SEMANTIC_TRIPLES_FILE, sep="\t")

    if not {"head", "relation", "tail"}.issubset(df.columns):
        # In case the TSV was saved without headers
        df = pd.read_csv(
            SEMANTIC_TRIPLES_FILE,
            sep="\t",
            header=None,
            names=["head", "relation", "tail"]
        )

    priority_terms = [
        "bench_press",
        "triceps",
        "pectoralis_major",
        "bar",
        "shoulder",
        "elbow",
        "grip_width",
        "bar_path",
    ]

    priority_df = df[
        df["head"].isin(priority_terms) | df["tail"].isin(priority_terms)
    ].copy()

    if len(priority_df) < 10:
        priority_df = df.copy()

    priority_df = priority_df.head(max_edges)

    graph = nx.DiGraph()

    for _, row in priority_df.iterrows():
        graph.add_edge(
            row["head"],
            row["tail"],
            label=row["relation"]
        )

    node_colors = []

    for node in graph.nodes():
        typ = entity_type(node)
        node_colors.append(TYPE_COLORS.get(typ, "#AAAAAA"))

    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    pos = nx.spring_layout(graph, seed=42, k=1.8)

    nx.draw_networkx_nodes(
        graph,
        pos,
        node_color=node_colors,
        node_size=800,
        alpha=0.9,
        ax=ax
    )

    nx.draw_networkx_labels(
        graph,
        pos,
        labels={n: n.replace("_", " ")[:25] for n in graph.nodes()},
        font_size=7,
        font_color="white",
        ax=ax
    )

    nx.draw_networkx_edges(
        graph,
        pos,
        edge_color="#444c56",
        arrows=True,
        arrowsize=15,
        connectionstyle="arc3,rad=0.08",
        ax=ax
    )

    edge_labels = {
        (u, v): d["label"]
        for u, v, d in graph.edges(data=True)
    }

    nx.draw_networkx_edge_labels(
        graph,
        pos,
        edge_labels=edge_labels,
        font_size=6,
        font_color="#8b949e",
        ax=ax
    )

    ax.set_title("Semantic Knowledge Graph Subgraph", color="white", fontsize=14)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(
        KG_GRAPH_FILE,
        dpi=180,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )
    plt.close()

    print(f"KG network graph saved to: {KG_GRAPH_FILE}")


# =============================
# MAIN
# =============================

def main():
    plot_dark_tsne()
    plot_metrics_chart()
    plot_size_sensitivity()
    plot_kg_graph_network()

    print()
    print("Extra KGE visualizations complete.")


if __name__ == "__main__":
    main()