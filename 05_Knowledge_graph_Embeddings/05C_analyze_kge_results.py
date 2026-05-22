"""
05C_analyze_kge_results.py

This script analyzes the trained KGE embeddings.

It creates:
1. Nearest-neighbor examples based on cosine similarity.
2. A t-SNE visualization of entity embeddings.
3. A Markdown report summarizing the KGE results.

Inputs:
- TransE_full_embeddings.npz or DistMult_full_embeddings.npz
- kge_metrics.csv
- size_sensitivity.csv

Outputs:
- nearest_neighbors.csv
- tsne_embeddings.png
- kge_analysis_report.md
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "05_Knowledge_Graph_Embeddings" / "outputs"

METRICS_FILE = OUTPUT_DIR / "kge_metrics.csv"
SIZE_SENSITIVITY_FILE = OUTPUT_DIR / "size_sensitivity.csv"

NEAREST_NEIGHBORS_FILE = OUTPUT_DIR / "nearest_neighbors.csv"
TSNE_PLOT_FILE = OUTPUT_DIR / "tsne_embeddings.png"
ANALYSIS_REPORT_FILE = OUTPUT_DIR / "kge_analysis_report.md"


# =============================
# HELPERS
# =============================

def choose_embedding_file() -> Path:
    """
    Prefer TransE full embeddings, otherwise use DistMult.
    """
    candidates = [
        OUTPUT_DIR / "TransE_full_embeddings.npz",
        OUTPUT_DIR / "DistMult_full_embeddings.npz",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "No full embedding file found. Run 05B_train_kge_models.py first."
    )


def load_embeddings(path: Path):
    data = np.load(path, allow_pickle=True)

    embeddings = data["entity_embeddings"]
    labels = data["entity_labels"]

    labels = [str(label) for label in labels]

    return embeddings, labels


def compute_nearest_neighbors(embeddings, labels, top_k=5):
    sim = cosine_similarity(embeddings)

    rows = []

    for i, label in enumerate(labels):
        scores = sim[i].copy()
        scores[i] = -np.inf

        nearest_ids = np.argsort(scores)[::-1][:top_k]

        for rank, neighbor_id in enumerate(nearest_ids, start=1):
            rows.append({
                "entity": label,
                "neighbor_rank": rank,
                "neighbor": labels[neighbor_id],
                "cosine_similarity": round(float(scores[neighbor_id]), 4),
            })

    return pd.DataFrame(rows)


def create_tsne_plot(embeddings, labels):
    n = len(labels)

    if n < 3:
        print("Not enough entities for t-SNE plot.")
        return False

    perplexity = min(30, max(2, (n - 1) // 3))

    tsne = TSNE(
        n_components=2,
        random_state=42,
        perplexity=perplexity,
        init="random",
        learning_rate="auto"
    )

    coords = tsne.fit_transform(embeddings)

    plt.figure(figsize=(12, 8))
    plt.scatter(coords[:, 0], coords[:, 1], s=25)

    max_labels = min(40, n)

    # Label only the first entities to keep the figure readable
    for i in range(max_labels):
        plt.annotate(labels[i], (coords[i, 0], coords[i, 1]), fontsize=8)

    plt.title("t-SNE Visualization of KGE Entity Embeddings")
    plt.xlabel("t-SNE dimension 1")
    plt.ylabel("t-SNE dimension 2")
    plt.tight_layout()
    plt.savefig(TSNE_PLOT_FILE, dpi=200)
    plt.close()

    return True


def dataframe_to_markdown_table(df: pd.DataFrame, max_rows=20) -> str:
    if df.empty:
        return "_No data available._"

    return df.head(max_rows).to_markdown(index=False)


# =============================
# MAIN
# =============================

def main() -> None:
    embedding_file = choose_embedding_file()

    print(f"Loading embeddings from: {embedding_file}")

    embeddings, labels = load_embeddings(embedding_file)

    nn_df = compute_nearest_neighbors(embeddings, labels, top_k=5)
    nn_df.to_csv(NEAREST_NEIGHBORS_FILE, index=False, encoding="utf-8")

    plot_created = create_tsne_plot(embeddings, labels)

    metrics_df = pd.read_csv(METRICS_FILE) if METRICS_FILE.exists() else pd.DataFrame()
    size_df = pd.read_csv(SIZE_SENSITIVITY_FILE) if SIZE_SENSITIVITY_FILE.exists() else pd.DataFrame()

    report = []
    report.append("# KGE Analysis Report\n")
    report.append("## Embedding File Used\n")
    report.append(f"- `{embedding_file.name}`\n")

    report.append("## Model Metrics\n")
    report.append(dataframe_to_markdown_table(metrics_df))
    report.append("")

    report.append("## Size Sensitivity Results\n")
    report.append(dataframe_to_markdown_table(size_df, max_rows=30))
    report.append("")

    report.append("## Nearest Neighbor Examples\n")
    report.append(
        "Nearest neighbors were computed using cosine similarity between entity embeddings."
    )
    report.append("")
    report.append(dataframe_to_markdown_table(nn_df, max_rows=25))
    report.append("")

    report.append("## t-SNE Visualization\n")
    if plot_created:
        report.append(f"- t-SNE plot saved to: `{TSNE_PLOT_FILE}`")
    else:
        report.append("- t-SNE plot was not created because there were not enough entities.")

    report.append("")
    report.append("## Reflection\n")
    report.append(
        "The KGE results should be interpreted carefully because the project knowledge graph is relatively small. "
        "Knowledge graph embedding models generally perform better on larger, denser graphs. "
        "However, this experiment demonstrates the full KGE pipeline: RDF cleaning, train/validation/test split, "
        "training of two models, link prediction evaluation, size sensitivity, nearest neighbors, and t-SNE visualization."
    )

    ANALYSIS_REPORT_FILE.write_text("\n".join(report), encoding="utf-8")

    print("KGE analysis complete.")
    print(f"Nearest neighbors saved to: {NEAREST_NEIGHBORS_FILE}")
    print(f"t-SNE plot saved to: {TSNE_PLOT_FILE}")
    print(f"Analysis report saved to: {ANALYSIS_REPORT_FILE}")


if __name__ == "__main__":
    main()