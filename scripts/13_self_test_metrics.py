"""Self-test metric implementations used in the benchmark."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def load_eval_module():
    spec = importlib.util.spec_from_file_location("evaluate", Path("scripts/06_evaluate_and_plot.py"))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load evaluation module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_close(actual: float, expected: float, name: str, tol: float = 1e-9) -> None:
    if abs(actual - expected) > tol:
        raise AssertionError(f"{name}: expected {expected}, got {actual}")


def main() -> None:
    import numpy as np
    import pandas as pd

    evaluate = load_eval_module()
    y_true = pd.Series([1, 1, 0, 0])
    y_pred = pd.Series([1, 0, 1, 0])
    scores = pd.Series([0.9, 0.8, 0.7, 0.1])

    precision = evaluate.precision_score(y_true, y_pred)
    recall = evaluate.recall_score(y_true, y_pred)
    f1 = evaluate.f1_score_simple(precision, recall)
    auroc = evaluate.ranking_auc(y_true, scores)
    auprc = evaluate.average_precision(y_true, scores)

    assert_close(precision, 0.5, "precision")
    assert_close(recall, 0.5, "recall")
    assert_close(f1, 0.5, "f1")
    assert_close(auroc, 1.0, "auroc")
    assert_close(auprc, 1.0, "auprc")

    tied_scores = pd.Series([0.5, 0.5, 0.5, 0.5])
    tied_auc = evaluate.ranking_auc(y_true, tied_scores)
    assert_close(tied_auc, 0.5, "tied_auroc")

    no_positive = np.array([0, 0, 0])
    no_positive_scores = np.array([0.1, 0.2, 0.3])
    if not np.isnan(evaluate.average_precision(no_positive, no_positive_scores)):
        raise AssertionError("average_precision should be NaN when there are no positives")

    print("Metric self-tests passed")


if __name__ == "__main__":
    main()
