"""
05B_train_kge_models.py

This script trains two Knowledge Graph Embedding models from scratch using PyTorch:

1. TransE
2. DistMult

It evaluates each model using link prediction metrics:
- MRR
- Hits@1
- Hits@3
- Hits@10

It also performs size-sensitivity experiments using the capped subsets created by:

    05A_prepare_kge_dataset.py

Outputs:
- kge_metrics.csv
- size_sensitivity.csv
- model embedding files for the full dataset:
    - TransE_full_embeddings.npz
    - DistMult_full_embeddings.npz
"""

from pathlib import Path
import random
import json

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


# =============================
# PATHS
# =============================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "05_Knowledge_Graph_Embeddings" / "outputs"

TRAIN_FILE = OUTPUT_DIR / "train.txt"
VALID_FILE = OUTPUT_DIR / "valid.txt"
TEST_FILE = OUTPUT_DIR / "test.txt"

ENTITY_TO_ID_FILE = OUTPUT_DIR / "entity_to_id.tsv"
RELATION_TO_ID_FILE = OUTPUT_DIR / "relation_to_id.tsv"

METRICS_FILE = OUTPUT_DIR / "kge_metrics.csv"
SIZE_SENSITIVITY_FILE = OUTPUT_DIR / "size_sensitivity.csv"
TRAINING_CONFIG_FILE = OUTPUT_DIR / "kge_training_config.json"


# =============================
# TRAINING CONFIG
# =============================

SEED = 42
EMBEDDING_DIM = 64
EPOCHS = 250
BATCH_SIZE = 64
LEARNING_RATE = 0.01
MARGIN = 1.0
NEGATIVE_SAMPLES_PER_POSITIVE = 1

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# =============================
# REPRODUCIBILITY
# =============================

def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# =============================
# DATA LOADING
# =============================

def load_triples(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing triples file: {path}")

    df = pd.read_csv(
        path,
        sep="\t",
        header=None,
        names=["head", "relation", "tail"],
        dtype=str
    )

    return df.dropna().drop_duplicates().reset_index(drop=True)


def load_mappings():
    entity_df = pd.read_csv(ENTITY_TO_ID_FILE, sep="\t")
    relation_df = pd.read_csv(RELATION_TO_ID_FILE, sep="\t")

    entity_to_id = dict(zip(entity_df["entity"], entity_df["id"]))
    relation_to_id = dict(zip(relation_df["relation"], relation_df["id"]))

    id_to_entity = {v: k for k, v in entity_to_id.items()}
    id_to_relation = {v: k for k, v in relation_to_id.items()}

    return entity_to_id, relation_to_id, id_to_entity, id_to_relation


def triples_to_ids(df: pd.DataFrame, entity_to_id: dict, relation_to_id: dict) -> np.ndarray:
    rows = []

    for _, row in df.iterrows():
        h = row["head"]
        r = row["relation"]
        t = row["tail"]

        if h not in entity_to_id or t not in entity_to_id or r not in relation_to_id:
            continue

        rows.append([
            entity_to_id[h],
            relation_to_id[r],
            entity_to_id[t],
        ])

    return np.array(rows, dtype=np.int64)


def create_split_from_subset(df: pd.DataFrame, seed=42):
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    n = len(df)

    if n < 5:
        return df, pd.DataFrame(columns=df.columns), pd.DataFrame(columns=df.columns)

    train_end = max(1, int(n * 0.8))
    valid_end = max(train_end + 1, int(n * 0.9))

    if valid_end >= n:
        valid_end = n - 1

    return (
        df.iloc[:train_end].copy(),
        df.iloc[train_end:valid_end].copy(),
        df.iloc[valid_end:].copy(),
    )


# =============================
# MODELS
# =============================

class TransE(nn.Module):
    def __init__(self, num_entities: int, num_relations: int, dim: int):
        super().__init__()

        self.entity_embeddings = nn.Embedding(num_entities, dim)
        self.relation_embeddings = nn.Embedding(num_relations, dim)

        nn.init.xavier_uniform_(self.entity_embeddings.weight.data)
        nn.init.xavier_uniform_(self.relation_embeddings.weight.data)

    def score(self, triples: torch.Tensor) -> torch.Tensor:
        h = self.entity_embeddings(triples[:, 0])
        r = self.relation_embeddings(triples[:, 1])
        t = self.entity_embeddings(triples[:, 2])

        return -torch.linalg.norm(h + r - t, ord=1, dim=1)


class DistMult(nn.Module):
    def __init__(self, num_entities: int, num_relations: int, dim: int):
        super().__init__()

        self.entity_embeddings = nn.Embedding(num_entities, dim)
        self.relation_embeddings = nn.Embedding(num_relations, dim)

        nn.init.xavier_uniform_(self.entity_embeddings.weight.data)
        nn.init.xavier_uniform_(self.relation_embeddings.weight.data)

    def score(self, triples: torch.Tensor) -> torch.Tensor:
        h = self.entity_embeddings(triples[:, 0])
        r = self.relation_embeddings(triples[:, 1])
        t = self.entity_embeddings(triples[:, 2])

        return torch.sum(h * r * t, dim=1)


# =============================
# TRAINING
# =============================

def corrupt_batch(batch: torch.Tensor, num_entities: int) -> torch.Tensor:
    corrupted = batch.clone()

    mask = torch.rand(len(batch), device=batch.device) < 0.5
    random_entities = torch.randint(
        low=0,
        high=num_entities,
        size=(len(batch),),
        device=batch.device
    )

    corrupted[mask, 0] = random_entities[mask]
    corrupted[~mask, 2] = random_entities[~mask]

    return corrupted


def train_model(model, train_ids: np.ndarray, num_entities: int) -> None:
    if len(train_ids) == 0:
        return

    model.to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    train_tensor = torch.tensor(train_ids, dtype=torch.long)
    dataset = TensorDataset(train_tensor)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    model.train()

    for epoch in range(1, EPOCHS + 1):
        epoch_loss = 0.0

        for (batch,) in loader:
            batch = batch.to(DEVICE)

            negative_batch = corrupt_batch(batch, num_entities)

            positive_scores = model.score(batch)
            negative_scores = model.score(negative_batch)

            loss = torch.relu(MARGIN - positive_scores + negative_scores).mean()

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += float(loss.item())

        if epoch % 50 == 0 or epoch == 1:
            avg_loss = epoch_loss / max(1, len(loader))
            print(f"Epoch {epoch:03d}/{EPOCHS} | loss={avg_loss:.4f}")


# =============================
# EVALUATION
# =============================

def evaluate_link_prediction(model, test_ids: np.ndarray, all_true_triples: set, num_entities: int) -> dict:
    """
    Raw/filtered link prediction evaluation.

    For each test triple, evaluate:
    - head prediction: (?, r, t)
    - tail prediction: (h, r, ?)

    Known true triples are filtered out except the target triple.
    """
    if len(test_ids) == 0:
        return {
            "MRR": 0.0,
            "Hits@1": 0.0,
            "Hits@3": 0.0,
            "Hits@10": 0.0,
            "evaluated_queries": 0,
        }

    model.eval()
    ranks = []

    with torch.no_grad():
        for h, r, t in test_ids:
            # Tail prediction
            candidates = torch.tensor(
                [[h, r, candidate_t] for candidate_t in range(num_entities)],
                dtype=torch.long,
                device=DEVICE
            )

            scores = model.score(candidates).detach().cpu().numpy()

            for candidate_t in range(num_entities):
                if candidate_t != t and (h, r, candidate_t) in all_true_triples:
                    scores[candidate_t] = -np.inf

            true_score = scores[t]
            rank = 1 + int(np.sum(scores > true_score))
            ranks.append(rank)

            # Head prediction
            candidates = torch.tensor(
                [[candidate_h, r, t] for candidate_h in range(num_entities)],
                dtype=torch.long,
                device=DEVICE
            )

            scores = model.score(candidates).detach().cpu().numpy()

            for candidate_h in range(num_entities):
                if candidate_h != h and (candidate_h, r, t) in all_true_triples:
                    scores[candidate_h] = -np.inf

            true_score = scores[h]
            rank = 1 + int(np.sum(scores > true_score))
            ranks.append(rank)

    ranks = np.array(ranks, dtype=np.float64)

    return {
        "MRR": round(float(np.mean(1.0 / ranks)), 4),
        "Hits@1": round(float(np.mean(ranks <= 1)), 4),
        "Hits@3": round(float(np.mean(ranks <= 3)), 4),
        "Hits@10": round(float(np.mean(ranks <= 10)), 4),
        "evaluated_queries": int(len(ranks)),
    }


def save_embeddings(model, model_name: str, subset_name: str, id_to_entity: dict, id_to_relation: dict) -> None:
    entity_embeddings = model.entity_embeddings.weight.detach().cpu().numpy()
    relation_embeddings = model.relation_embeddings.weight.detach().cpu().numpy()

    entity_labels = np.array([id_to_entity[i] for i in range(len(id_to_entity))])
    relation_labels = np.array([id_to_relation[i] for i in range(len(id_to_relation))])

    path = OUTPUT_DIR / f"{model_name}_{subset_name}_embeddings.npz"

    np.savez(
        path,
        entity_embeddings=entity_embeddings,
        relation_embeddings=relation_embeddings,
        entity_labels=entity_labels,
        relation_labels=relation_labels,
    )

    print(f"Saved embeddings: {path}")


# =============================
# EXPERIMENT RUNNER
# =============================

def run_experiment(model_name: str, train_df: pd.DataFrame, valid_df: pd.DataFrame, test_df: pd.DataFrame, subset_name: str):
    entity_to_id, relation_to_id, id_to_entity, id_to_relation = load_mappings()

    train_ids = triples_to_ids(train_df, entity_to_id, relation_to_id)
    valid_ids = triples_to_ids(valid_df, entity_to_id, relation_to_id)
    test_ids = triples_to_ids(test_df, entity_to_id, relation_to_id)

    all_ids = np.vstack([
        arr for arr in [train_ids, valid_ids, test_ids]
        if len(arr) > 0
    ])

    all_true_triples = set(map(tuple, all_ids.tolist()))

    num_entities = len(entity_to_id)
    num_relations = len(relation_to_id)

    if model_name == "TransE":
        model = TransE(num_entities, num_relations, EMBEDDING_DIM)
    elif model_name == "DistMult":
        model = DistMult(num_entities, num_relations, EMBEDDING_DIM)
    else:
        raise ValueError(f"Unknown model: {model_name}")

    print()
    print("=" * 60)
    print(f"Training {model_name} on subset: {subset_name}")
    print(f"Train / valid / test triples: {len(train_df)} / {len(valid_df)} / {len(test_df)}")
    print("=" * 60)

    train_model(model, train_ids, num_entities)

    metrics = evaluate_link_prediction(
        model=model,
        test_ids=test_ids,
        all_true_triples=all_true_triples,
        num_entities=num_entities,
    )

    metrics.update({
        "model": model_name,
        "subset": subset_name,
        "train_triples": len(train_df),
        "valid_triples": len(valid_df),
        "test_triples": len(test_df),
        "entities": num_entities,
        "relations": num_relations,
    })

    if subset_name == "full":
        save_embeddings(model, model_name, subset_name, id_to_entity, id_to_relation)

    return metrics


# =============================
# MAIN
# =============================

def main() -> None:
    set_seed(SEED)

    if not TRAIN_FILE.exists() or not VALID_FILE.exists() or not TEST_FILE.exists():
        raise FileNotFoundError(
            "Missing train/valid/test files. Run 05A_prepare_kge_dataset.py first."
        )

    config = {
        "seed": SEED,
        "embedding_dim": EMBEDDING_DIM,
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "margin": MARGIN,
        "device": DEVICE,
        "models": ["TransE", "DistMult"],
    }

    TRAINING_CONFIG_FILE.write_text(json.dumps(config, indent=4), encoding="utf-8")

    full_train = load_triples(TRAIN_FILE)
    full_valid = load_triples(VALID_FILE)
    full_test = load_triples(TEST_FILE)

    all_metrics = []

    # Main full-dataset training
    for model_name in ["TransE", "DistMult"]:
        metrics = run_experiment(
            model_name=model_name,
            train_df=full_train,
            valid_df=full_valid,
            test_df=full_test,
            subset_name="full",
        )
        all_metrics.append(metrics)

    metrics_df = pd.DataFrame(all_metrics)
    metrics_df.to_csv(METRICS_FILE, index=False, encoding="utf-8")

    # Size sensitivity
    size_metrics = []

    subset_files = [
        ("20k_cap", OUTPUT_DIR / "size_20k_cap.tsv"),
        ("50k_cap", OUTPUT_DIR / "size_50k_cap.tsv"),
        ("full", OUTPUT_DIR / "size_full.tsv"),
    ]

    for subset_name, subset_file in subset_files:
        if not subset_file.exists():
            continue

        subset_df = load_triples(subset_file)
        train_df, valid_df, test_df = create_split_from_subset(subset_df, seed=SEED)

        for model_name in ["TransE", "DistMult"]:
            metrics = run_experiment(
                model_name=model_name,
                train_df=train_df,
                valid_df=valid_df,
                test_df=test_df,
                subset_name=subset_name,
            )
            size_metrics.append(metrics)

    size_df = pd.DataFrame(size_metrics)
    size_df.to_csv(SIZE_SENSITIVITY_FILE, index=False, encoding="utf-8")

    print()
    print("KGE training complete.")
    print(f"Metrics saved to: {METRICS_FILE}")
    print(f"Size sensitivity saved to: {SIZE_SENSITIVITY_FILE}")
    print(f"Device used: {DEVICE}")


if __name__ == "__main__":
    main()