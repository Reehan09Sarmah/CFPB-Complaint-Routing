"""
Training pipeline for CFPB complaint product classifier.

What this script does, step by step:
  1. Load a sample of complaints.csv (only rows that have a narrative)
  2. Clean the text (lowercase, strip whitespace)
  3. Split by date: train on older data, test on newer (time-based split)
  4. Vectorise with TF-IDF: converts text -> numeric vectors
  5. Train a Logistic Regression classifier
  6. Evaluate on the test set
  7. Log everything to MLflow (params, metrics, model artifact)
  8. Optionally register the model if it beats the current champion
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    fbeta_score,
    precision_recall_curve,
)
from sklearn.pipeline import Pipeline
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]  # mlops-platform/
DATA_PATH = REPO_ROOT / "data" / "complaints.csv"

# Columns we care about
TEXT_COL = "Consumer complaint narrative"
LABEL_COL = "Product"
DATE_COL = "Date received"
SUB_COL = "Sub-product"

# ADR-0009: the CFPB renamed its products in 2017 and 2023. Train only on the
# 2017 taxonomy onward and map its names onto the current (2023) classes.
LABEL_START = pd.Timestamp("2017-04-24")
RENAMED = {
    "Credit reporting, credit repair services, or other personal consumer reports": (
        "Credit reporting or other personal consumer reports"
    ),
    "Payday loan, title loan, or personal loan": (
        "Payday loan, title loan, personal loan, or advance loan"
    ),
}
CARD_OLD = "Credit card or prepaid card"
CARD_SPLIT = {  # old combined label -> new label, decided by Sub-product
    "General-purpose credit card or charge card": "Credit card",
    "Store credit card": "Credit card",
    "General-purpose prepaid card": "Prepaid card",
    "Gift card": "Prepaid card",
    "Government benefit card": "Prepaid card",
    "Payroll card": "Prepaid card",
    "Student prepaid card": "Prepaid card",
}
CLASSES = {
    "Credit reporting or other personal consumer reports",
    "Debt collection",
    "Credit card",
    "Checking or savings account",
    "Mortgage",
    "Money transfer, virtual currency, or money service",
    "Student loan",
    "Vehicle loan or lease",
    "Payday loan, title loan, personal loan, or advance loan",
    "Prepaid card",
    "Debt or credit management",
}


def normalize_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply ADR-0009: drop pre-2017-04-24 rows, map renamed labels to the 2023
    taxonomy, and raise if any label outside CLASSES remains (a new CFPB rename
    must stop the run, not train silently on a dead label).
    """
    df = df[df[DATE_COL] >= LABEL_START].copy()
    card = df[LABEL_COL] == CARD_OLD
    df.loc[card, LABEL_COL] = df.loc[card, SUB_COL].map(CARD_SPLIT)
    df[LABEL_COL] = df[LABEL_COL].replace(RENAMED)
    df = df.dropna(subset=[LABEL_COL])  # card rows whose sub-product can't decide
    unknown = set(df[LABEL_COL]) - CLASSES
    if unknown:
        raise ValueError(f"Unknown product labels (extend ADR-0009 mapping): {unknown}")
    return df.drop(columns=SUB_COL)


# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
def load_data(
    path: Path, sample_n: int | None = None, chunksize: int = 200_000
) -> pd.DataFrame:
    """
    Load the CSV and keep only rows that have a narrative.

    Why sample_n?  The full dataset is 5.5M rows. During development we use a
    small sample (e.g. 50_000) so the feedback loop is fast. Set sample_n=None
    to train on everything.

    Why chunksize?  The file is 3.5GB. Reading it in chunks (instead of one
    pd.read_csv call) lets us show a progress bar and drop null-narrative
    rows chunk-by-chunk, instead of holding the full unfiltered file in
    memory before the drop happens.
    """
    log.info("Loading data from %s", path)
    reader = pd.read_csv(
        path,
        usecols=[DATE_COL, TEXT_COL, LABEL_COL, SUB_COL],  # only what we need
        parse_dates=[DATE_COL],
        low_memory=False,
        chunksize=chunksize,
    )
    chunks = [
        normalize_labels(chunk.dropna(subset=[TEXT_COL]))
        for chunk in tqdm(reader, desc="Reading CSV", unit="chunk")
    ]
    df = pd.concat(chunks, ignore_index=True)
    log.info("Rows with narrative: %s", len(df))

    if sample_n is not None and sample_n < len(df):
        # Sample reproducibly by sorting by date first, then taking the most recent N
        df = df.sort_values(DATE_COL).tail(sample_n).reset_index(drop=True)
        log.info("After sampling: %s rows", len(df))

    return df


# ---------------------------------------------------------------------------
# 2. Preprocess
# ---------------------------------------------------------------------------
def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Minimal text cleaning. TF-IDF handles most of the heavy lifting itself.
    We lowercase and strip whitespace. That is all we need at baseline.
    """
    df = df.copy()
    df[TEXT_COL] = df[TEXT_COL].str.lower().str.strip()
    return df


# ---------------------------------------------------------------------------
# 3. Time-based train/test split
# ---------------------------------------------------------------------------
def time_split(
    df: pd.DataFrame, test_months: int = 6
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split by date rather than randomly.

    Why time-based?  In production, the model is always trained on past data
    and predicts future complaints. A random split would leak future information
    into training and give falsely optimistic accuracy numbers.

    test_months: the most recent N months go into the test set.
    """
    cutoff = df[DATE_COL].max() - pd.DateOffset(months=test_months)
    train = df[df[DATE_COL] <= cutoff]
    test = df[df[DATE_COL] > cutoff]
    log.info(
        "Train: %s rows (up to %s) | Test: %s rows (after %s)",
        len(train),
        cutoff.date(),
        len(test),
        cutoff.date(),
    )
    return train, test


# ---------------------------------------------------------------------------
# 4 + 5. Build and train the pipeline
# ---------------------------------------------------------------------------
def build_pipeline(max_features: int, C: float) -> Pipeline:
    """
    A sklearn Pipeline chains steps so they are applied in order.

    Step 1 - TfidfVectorizer:
      Converts raw complaint text into a matrix of TF-IDF numbers.
      max_features: vocabulary size (how many unique words to keep).
      sublinear_tf: applies log(1 + count) to dampen very frequent words.

    Step 2 - LogisticRegression:
      A linear classifier that learns which word patterns map to which product.
      C: regularisation strength. Higher C = less regularisation = fits more
         tightly to training data (risk of overfitting).
      max_iter: how many optimisation steps before giving up.
    """
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=max_features,
                    sublinear_tf=True,
                    ngram_range=(1, 2),  # unigrams and bigrams
                    min_df=5,  # ignore words appearing in fewer than 5 docs
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=C,
                    max_iter=1000,
                    class_weight="balanced",  # handles class imbalance automatically
                ),
            ),
        ]
    )


# ---------------------------------------------------------------------------
# 6. Evaluate
# ---------------------------------------------------------------------------
def evaluate(
    pipeline: Pipeline, X_test: pd.Series, y_test: pd.Series
) -> dict[str, float]:
    """Compute accuracy and macro-F1 on the test set."""
    preds = pipeline.predict(X_test)
    return {
        "accuracy": round(accuracy_score(y_test, preds), 4),
        "f1_macro": round(f1_score(y_test, preds, average="macro"), 4),
        "f2_macro": round(fbeta_score(y_test, preds, beta=2, average="macro"), 4),
    }


def diagnostics(
    pipeline: Pipeline, X_test: pd.Series, y_test: pd.Series, y_train: pd.Series
) -> tuple[dict, pd.DataFrame, float]:
    """
    Per-class report, confusion matrix, and the "always guess the biggest
    class" baseline accuracy. Needed to explain why accuracy and macro-F1
    differ and whether the model beats a trivial guess.
    """
    preds = pipeline.predict(X_test)
    report = classification_report(y_test, preds, output_dict=True, zero_division=0)
    confusion = pd.crosstab(
        y_test.rename("true"), pd.Series(preds, index=y_test.index, name="pred")
    )
    baseline = round(float((y_test == y_train.mode()[0]).mean()), 4)
    return report, confusion, baseline


def pr_curves(
    pipeline: Pipeline, X_test: pd.Series, y_test: pd.Series
) -> dict[str, dict[str, list[float]]]:
    """
    Per class: for each recall level 0.00..1.00, the strictest cutoff that still
    reaches it, with the precision there. Lets a recall floor (ADR-0010) be
    turned into a per-class cutoff and its false-alarm cost, without retraining.
    """
    proba = pipeline.predict_proba(X_test)
    levels = np.linspace(0, 1, 101)
    out: dict[str, dict[str, list[float]]] = {}
    for k, cls in enumerate(pipeline.classes_):
        y = (y_test == cls).to_numpy()
        if not y.any():
            continue
        p, r, t = precision_recall_curve(y, proba[:, k])
        i = np.searchsorted(-r[:-1], -levels, side="right") - 1
        i = np.unique(np.clip(i, 0, len(t) - 1))
        out[str(cls)] = {
            "recall": r[i].round(4).tolist(),
            "precision": p[i].round(4).tolist(),
            "threshold": t[i].round(4).tolist(),
        }
    return out


# ---------------------------------------------------------------------------
# 7 + 8. MLflow run
# ---------------------------------------------------------------------------
def train(
    sample_n: int | None = 50_000,
    max_features: int = 10_000,
    C: float = 1.0,
    test_months: int = 6,
    register_model: bool = False,
) -> None:
    """
    Full training run, wrapped in an MLflow context.

    mlflow.start_run() opens a new "run" in MLflow. Everything logged inside
    this block is saved to that run:
      - mlflow.log_param()   -> the settings you chose (hyperparameters)
      - mlflow.log_metric()  -> the results (accuracy, F1)
      - mlflow.sklearn.log_model() -> the trained model file itself

    After training, you can open the MLflow UI with:
        uv run mlflow ui
    and browse all runs at http://localhost:5000
    """
    mlflow.set_experiment("cfpb-complaint-classifier")

    with mlflow.start_run():
        # -- Log params (the choices we made) --
        mlflow.log_params(
            {
                "sample_n": sample_n,
                "max_features": max_features,
                "C": C,
                "test_months": test_months,
            }
        )

        # -- Stages --
        # Note: the CSV-read stage (inside load_data) has its own granular
        # per-chunk bar. The bar below just shows which of these 6 coarse
        # stages is currently running -- sklearn's TF-IDF fit and Logistic
        # Regression fit are single C/Fortran-level calls with no hook for
        # per-iteration progress, so "Fitting" will sit still and then jump
        # to done, not creep up incrementally.
        stages = tqdm(total=6, desc="Pipeline", unit="stage")

        stages.set_description("Loading data")
        df = load_data(DATA_PATH, sample_n=sample_n)
        stages.update(1)

        stages.set_description("Preprocessing")
        df = preprocess(df)
        stages.update(1)

        stages.set_description("Splitting by date")
        train_df, test_df = time_split(df, test_months=test_months)
        stages.update(1)

        X_train, y_train = train_df[TEXT_COL], train_df[LABEL_COL]
        X_test, y_test = test_df[TEXT_COL], test_df[LABEL_COL]

        stages.set_description("Fitting (TF-IDF + Logistic Regression)")
        pipeline = build_pipeline(max_features=max_features, C=C)
        pipeline.fit(X_train, y_train)
        stages.update(1)

        stages.set_description("Evaluating")
        metrics = evaluate(pipeline, X_test, y_test)
        report, confusion, baseline = diagnostics(pipeline, X_test, y_test, y_train)
        metrics["baseline_accuracy"] = baseline
        mlflow.log_metrics(metrics)
        mlflow.log_params(
            {
                "n_train": len(train_df),
                "n_test": len(test_df),
                "n_classes": y_train.nunique(),
                "train_min_date": train_df[DATE_COL].min().date(),
                "train_max_date": train_df[DATE_COL].max().date(),
                "test_min_date": test_df[DATE_COL].min().date(),
                "test_max_date": test_df[DATE_COL].max().date(),
            }
        )
        mlflow.log_dict(report, "diagnostics/classification_report.json")
        mlflow.log_dict(
            pr_curves(pipeline, X_test, y_test), "diagnostics/pr_curves.json"
        )
        mlflow.log_text(confusion.to_csv(), "diagnostics/confusion_matrix.csv")
        mlflow.log_dict(
            {
                "train": y_train.value_counts().to_dict(),
                "test": y_test.value_counts().to_dict(),
            },
            "diagnostics/class_counts.json",
        )
        stages.update(1)
        log.info("Metrics: %s", metrics)

        stages.set_description("Logging model to MLflow")
        mlflow.sklearn.log_model(
            sk_model=pipeline,
            artifact_path="model",
            registered_model_name="cfpb-complaint-classifier"
            if register_model
            else None,
        )
        stages.update(1)
        stages.close()
        log.info("Run complete. Open MLflow UI: uv run mlflow ui")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train CFPB complaint classifier")
    parser.add_argument(
        "--sample-n", type=int, default=50_000, help="Rows to use (None = all)"
    )
    parser.add_argument(
        "--max-features", type=int, default=10_000, help="TF-IDF vocab size"
    )
    parser.add_argument(
        "--C", type=float, default=1.0, help="Logistic regression regularisation"
    )
    parser.add_argument(
        "--test-months", type=int, default=6, help="Months of data for test set"
    )
    parser.add_argument(
        "--register", action="store_true", help="Register model in MLflow registry"
    )
    args = parser.parse_args()

    train(
        sample_n=args.sample_n,
        max_features=args.max_features,
        C=args.C,
        test_months=args.test_months,
        register_model=args.register,
    )
