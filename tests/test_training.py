"""
Smoke test for the training pipeline.

Uses a tiny in-memory dataset so it runs in seconds with no real data needed.
If this passes, the pipeline wiring is correct.
"""

from __future__ import annotations

import pandas as pd
import pytest
from cfpb_mlops.training.train import (
    build_pipeline,
    diagnostics,
    evaluate,
    load_data,
    normalize_labels,
    pr_curves,
    preprocess,
    time_split,
)

# ---------------------------------------------------------------------------
# Minimal fake dataset that mirrors the real CSV schema
# ---------------------------------------------------------------------------
FAKE_NARRATIVES = [
    "my credit card was charged without my authorization",
    "the bank refused to refund my overdraft fee",
    "i was harassed by a debt collector repeatedly",
    "my mortgage payment was applied incorrectly",
    "my student loan servicer lost my payment",
    "fraudulent charges appeared on my credit card statement",
    "the debt collection agency called me at work",
    "my home loan modification was denied without explanation",
    "unauthorized withdrawal from my checking account",
    "my student loan interest rate changed without notice",
]

FAKE_PRODUCTS = [
    "Credit card",
    "Checking or savings account",
    "Debt collection",
    "Mortgage",
    "Student loan",
    "Credit card",
    "Debt collection",
    "Mortgage",
    "Checking or savings account",
    "Student loan",
]


def make_fake_df(n_rows: int = 10) -> pd.DataFrame:
    """Create a tiny fake DataFrame with the same columns as the real data."""
    dates = pd.date_range("2020-01-01", periods=n_rows, freq="ME")
    return pd.DataFrame(
        {
            "Date received": dates,
            "Consumer complaint narrative": FAKE_NARRATIVES[:n_rows],
            "Product": FAKE_PRODUCTS[:n_rows],
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_preprocess_lowercases() -> None:
    """preprocess() should lowercase the narrative text."""
    df = make_fake_df(2)
    df["Consumer complaint narrative"] = ["UPPERCASE TEXT", "Mixed Case"]
    result = preprocess(df)
    assert result["Consumer complaint narrative"].iloc[0] == "uppercase text"
    assert result["Consumer complaint narrative"].iloc[1] == "mixed case"


def test_time_split_respects_cutoff() -> None:
    """Test set should only contain rows after the cutoff date."""
    df = make_fake_df(10)
    train_df, test_df = time_split(df, test_months=3)
    # No overlap
    assert len(train_df) + len(test_df) == len(df)
    if len(train_df) > 0 and len(test_df) > 0:
        assert train_df["Date received"].max() < test_df["Date received"].min()


def test_pipeline_trains_and_predicts() -> None:
    """Full pipeline: fit on fake data, predict on a sample, no crash."""
    df = make_fake_df(10)
    text_col = "Consumer complaint narrative"
    label_col = "Product"

    pipeline = build_pipeline(max_features=50, C=1.0)
    pipeline.fit(df[text_col], df[label_col])

    preds = pipeline.predict(df[text_col])
    assert len(preds) == len(df)
    # All predictions should be valid product names
    valid_products = set(df[label_col].unique())
    assert all(p in valid_products for p in preds)


def test_evaluate_returns_expected_keys() -> None:
    """evaluate() should always return accuracy and f1_macro keys."""
    df = make_fake_df(10)
    text_col = "Consumer complaint narrative"
    label_col = "Product"

    pipeline = build_pipeline(max_features=50, C=1.0)
    pipeline.fit(df[text_col], df[label_col])

    metrics = evaluate(pipeline, df[text_col], df[label_col])
    assert "accuracy" in metrics
    assert "f1_macro" in metrics
    assert "f2_macro" in metrics
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["f1_macro"] <= 1.0


def test_diagnostics_shapes() -> None:
    """diagnostics() returns a report, a confusion matrix, and a baseline."""
    df = make_fake_df(10)
    text_col, label_col = "Consumer complaint narrative", "Product"
    pipeline = build_pipeline(max_features=50, C=1.0)
    pipeline.fit(df[text_col], df[label_col])

    report, confusion, baseline = diagnostics(
        pipeline, df[text_col], df[label_col], df[label_col]
    )
    assert "Mortgage" in report and "macro avg" in report
    assert int(confusion.to_numpy().sum()) == len(df)
    assert 0.0 <= baseline <= 1.0


def _raw(rows: list[tuple[str, str, str | None, str | None]]) -> pd.DataFrame:
    cols = ["Date received", "Product", "Sub-product", "Consumer complaint narrative"]
    df = pd.DataFrame(rows, columns=cols)
    df["Date received"] = pd.to_datetime(df["Date received"])
    return df


OLD_CR = "Credit reporting, credit repair services, or other personal consumer reports"


def test_normalize_labels_maps_renames_and_splits_card() -> None:
    """ADR-0009: renames mapped, card label split by sub-product, old rows dropped."""
    df = _raw(
        [
            ("2020-01-01", OLD_CR, "x", "a"),
            ("2020-01-01", "Payday loan, title loan, or personal loan", "x", "b"),
            ("2020-01-01", "Credit card or prepaid card", "Store credit card", "c"),
            ("2020-01-01", "Credit card or prepaid card", "Gift card", "d"),
            ("2020-01-01", "Credit card or prepaid card", None, "e"),
            ("2024-01-01", "Mortgage", "x", "f"),
            ("2016-01-01", "Bank account or service", "x", "g"),
        ]
    )
    out = normalize_labels(df)
    assert out["Product"].tolist() == [
        "Credit reporting or other personal consumer reports",
        "Payday loan, title loan, personal loan, or advance loan",
        "Credit card",
        "Prepaid card",
        "Mortgage",
    ]
    assert "Sub-product" not in out.columns


def test_normalize_labels_fails_on_unknown_label() -> None:
    """A label we have never seen must stop the run, not train silently."""
    with pytest.raises(ValueError):
        normalize_labels(_raw([("2024-01-01", "Brand new product", "x", "a")]))


def test_load_data_applies_crosswalk(tmp_path) -> None:
    """load_data drops no-narrative and pre-2017 rows and applies the mapping."""
    csv = tmp_path / "c.csv"
    _raw(
        [
            ("2016-01-01", "Consumer Loan", "", "too old"),
            ("2018-05-05", "Payday loan, title loan, or personal loan", "", "mapped"),
            ("2024-01-01", "Mortgage", "", "kept"),
            ("2024-01-02", "Mortgage", "", None),
        ]
    ).to_csv(csv, index=False)
    out = load_data(csv)
    assert out["Product"].tolist() == [
        "Payday loan, title loan, personal loan, or advance loan",
        "Mortgage",
    ]


def test_pr_curves_cover_each_class() -> None:
    """pr_curves() returns aligned recall/precision/threshold lists per class."""
    df = make_fake_df(10)
    text_col, label_col = "Consumer complaint narrative", "Product"
    pipeline = build_pipeline(max_features=50, C=1.0)
    pipeline.fit(df[text_col], df[label_col])
    curves = pr_curves(pipeline, df[text_col], df[label_col])
    assert set(curves) == set(df[label_col])
    for c in curves.values():
        assert len(c["recall"]) == len(c["precision"]) == len(c["threshold"])
