"""Summarize real Xi & Li benchmark results."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def processed_inventory(processed_dir: Path, original_inventory_path: Path) -> pd.DataFrame:
    rows = []
    for dataset_dir in sorted(path for path in processed_dir.iterdir() if path.is_dir()):
        meta = pd.read_csv(dataset_dir / "metadata.csv")
        is_doublet = meta["ground_truth"].str.lower().eq("doublet")
        rows.append(
            {
                "dataset": dataset_dir.name,
                "processed_cells": len(meta),
                "processed_doublets": int(is_doublet.sum()),
                "processed_doublet_rate": float(is_doublet.mean()),
            }
        )
    processed = pd.DataFrame(rows)
    if original_inventory_path.exists():
        original = pd.read_csv(original_inventory_path)
        original = original.rename(
            columns={
                "cells": "original_cells",
                "doublets": "original_doublets",
                "doublet_rate": "original_doublet_rate",
            }
        )
        keep = [
            "dataset",
            "genes",
            "original_cells",
            "original_doublets",
            "original_doublet_rate",
            "file_mb",
        ]
        return original[keep].merge(processed, on="dataset", how="right")
    return processed


def main() -> None:
    metrics_path = Path("results/real/benchmark_metrics.csv")
    calibrated_path = Path("results/real/calibrated_metrics.csv")
    confusion_path = Path("results/real/confusion_matrices.csv")
    original_inventory_path = Path("results/real_dataset_inventory.csv")
    processed_dir = Path("data/processed_real")
    out_dir = Path("results/real")
    if not metrics_path.exists():
        raise FileNotFoundError(metrics_path)
    metrics = pd.read_csv(metrics_path)
    summary = (
        metrics.groupby("method", as_index=False)
        .agg(
            mean_precision=("precision", "mean"),
            mean_recall=("recall", "mean"),
            mean_f1=("f1", "mean"),
            mean_auroc=("auroc", "mean"),
            mean_auprc=("auprc", "mean"),
            mean_runtime_seconds=("runtime_seconds", "mean"),
        )
        .sort_values("mean_f1", ascending=False)
    )
    best = metrics.loc[metrics.groupby("dataset")["f1"].idxmax()]
    best = best[["dataset", "method", "f1", "precision", "recall", "auprc"]].sort_values("dataset")

    if confusion_path.exists():
        conf = pd.read_csv(confusion_path)
        micro = (
            conf.groupby("method", as_index=False)
            .agg(
                true_positive=("true_positive", "sum"),
                false_positive=("false_positive", "sum"),
                true_negative=("true_negative", "sum"),
                false_negative=("false_negative", "sum"),
            )
            .sort_values("method")
        )
        micro["micro_precision"] = micro["true_positive"] / (
            micro["true_positive"] + micro["false_positive"]
        )
        micro["micro_recall"] = micro["true_positive"] / (
            micro["true_positive"] + micro["false_negative"]
        )
        micro["micro_f1"] = (
            2
            * micro["micro_precision"]
            * micro["micro_recall"]
            / (micro["micro_precision"] + micro["micro_recall"])
        )
    else:
        micro = pd.DataFrame()

    summary.to_csv(out_dir / "real_method_summary.csv", index=False)
    best.to_csv(out_dir / "real_best_method_by_dataset.csv", index=False)
    if not micro.empty:
        micro.to_csv(out_dir / "real_micro_average_summary.csv", index=False)
    if processed_dir.exists():
        inventory = processed_inventory(processed_dir, original_inventory_path)
        inventory.to_csv(out_dir / "real_dataset_inventory_processed.csv", index=False)
    if calibrated_path.exists():
        calibrated = pd.read_csv(calibrated_path)
        calibrated_summary = (
            calibrated.groupby("method", as_index=False)
            .agg(
                mean_calibrated_precision=("calibrated_precision", "mean"),
                mean_calibrated_recall=("calibrated_recall", "mean"),
                mean_calibrated_f1=("calibrated_f1", "mean"),
            )
            .sort_values("mean_calibrated_f1", ascending=False)
        )
        calibrated_summary.to_csv(out_dir / "real_calibrated_method_summary.csv", index=False)
    else:
        calibrated_summary = pd.DataFrame()

    print("Real-data method summary")
    print(summary.to_string(index=False))
    print("\nBest method by real dataset")
    print(best.to_string(index=False))
    if not micro.empty:
        print("\nMicro-averaged real-data summary")
        print(micro.to_string(index=False))
    if processed_dir.exists():
        print("\nProcessed real-data inventory")
        print(inventory.to_string(index=False))
    if not calibrated_summary.empty:
        print("\nCalibrated real-data method summary")
        print(calibrated_summary.to_string(index=False))


if __name__ == "__main__":
    main()
