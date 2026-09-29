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
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline

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


# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
def load_data(path: Path, sample_n: int | None = None) -> pd.DataFrame:
    """
    Load the CSV and keep only rows that have a narrative.

    Why sample_n?  The full dataset is 5.5M rows. During development we use a
    small sample (e.g. 50_000) so the feedback loop is fast. Set sample_n=None
    to train on everything.
    """
    log.info("Loading data from %s", path)
    df = pd.read_csv(
        path,
        usecols=[DATE_COL, TEXT_COL, LABEL_COL],  # only load what we need
        parse_dates=[DATE_COL],
        low_memory=False,
    )
    # Drop rows with no narrative text
    df = df.dropna(subset=[TEXT_COL]).reset_index(drop=True)
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
    df = df.sort_values(DATE_COL)
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
      n_jobs=-1: use all CPU cores.
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
                    n_jobs=-1,
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
    }


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

        # -- Data --
        df = load_data(DATA_PATH, sample_n=sample_n)
        df = preprocess(df)
        train_df, test_df = time_split(df, test_months=test_months)

        X_train, y_train = train_df[TEXT_COL], train_df[LABEL_COL]
        X_test, y_test = test_df[TEXT_COL], test_df[LABEL_COL]

        # -- Train --
        log.info("Training pipeline...")
        pipeline = build_pipeline(max_features=max_features, C=C)
        pipeline.fit(X_train, y_train)

        # -- Evaluate --
        metrics = evaluate(pipeline, X_test, y_test)
        mlflow.log_metrics(metrics)
        log.info("Metrics: %s", metrics)

        # -- Log model --
        mlflow.sklearn.log_model(
            sk_model=pipeline,
            artifact_path="model",
            registered_model_name="cfpb-complaint-classifier"
            if register_model
            else None,
        )
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
