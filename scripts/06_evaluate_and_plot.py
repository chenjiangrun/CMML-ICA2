"""Evaluate method predictions and generate benchmark figures."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def precision_score(y_true, y_pred) -> float:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    return tp / (tp + fp) if (tp + fp) else 0.0


def recall_score(y_true, y_pred) -> float:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    return tp / (tp + fn) if (tp + fn) else 0.0


def f1_score_simple(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def ranking_auc(y_true, score) -> float:
    valid = ~pd.isna(score)
    y_true = np.asarray(y_true[valid])
    score = np.asarray(score[valid])
    positives = score[y_true == 1]
    negatives = score[y_true == 0]
    if len(positives) == 0 or len(negatives) == 0:
        return np.nan
    wins = 0.0
    total = len(positives) * len(negatives)
    for pos in positives:
        wins += np.sum(pos > negatives) + 0.5 * np.sum(pos == negatives)
    return float(wins / total)


def average_precision(y_true, score) -> float:
    valid = ~pd.isna(score)
    y_true = np.asarray(y_true[valid])
    score = np.asarray(score[valid])
    order = np.argsort(-score)
    y_sorted = y_true[order]
    positives = int(y_sorted.sum())
    if positives == 0:
        return np.nan
    tp = 0
    precisions = []
    for i, label in enumerate(y_sorted, start=1):
        if label == 1:
            tp += 1
            precisions.append(tp / i)
    return float(np.mean(precisions))


def evaluate_one(metadata: pd.DataFrame, prediction_path: Path) -> dict[str, object]:
    predictions = pd.read_csv(prediction_path)
    merged = metadata.merge(predictions, on="cell_id", how="inner")
    if len(merged) != len(metadata):
        raise ValueError(
            f"{prediction_path.name}: only {len(merged)} of {len(metadata)} cells matched"
        )

    y_true = (merged["ground_truth"].str.lower() == "doublet").astype(int)
    y_pred = (merged["prediction"].str.lower() == "doublet").astype(int)
    score = pd.to_numeric(merged["score"], errors="coerce")

    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    return {
        "dataset": prediction_path.name.split("__")[0],
        "method": str(merged["method"].iloc[0]),
        "n_cells": len(merged),
        "doublet_rate": float(y_true.mean()),
        "precision": precision,
        "recall": recall,
        "f1": f1_score_simple(precision, recall),
        "auroc": ranking_auc(y_true, score),
        "auprc": average_precision(y_true, score),
        "runtime_seconds": float(merged.get("runtime_seconds", pd.Series([np.nan])).iloc[0]),
    }


def evaluate_one_calibrated(metadata: pd.DataFrame, prediction_path: Path) -> dict[str, object]:
    predictions = pd.read_csv(prediction_path)
    merged = metadata.merge(predictions, on="cell_id", how="inner")
    if len(merged) != len(metadata):
        raise ValueError(
            f"{prediction_path.name}: only {len(merged)} of {len(metadata)} cells matched"
        )

    y_true = (merged["ground_truth"].str.lower() == "doublet").astype(int)
    score = pd.to_numeric(merged["score"], errors="coerce")
    n_doublets = int(y_true.sum())
    y_pred = np.zeros(len(merged), dtype=int)
    valid = np.where(~pd.isna(score))[0]
    if n_doublets > 0 and len(valid) > 0:
        ordered_valid = valid[np.argsort(-score.iloc[valid].to_numpy())]
        y_pred[ordered_valid[: min(n_doublets, len(ordered_valid))]] = 1

    precision = precision_score(y_true.to_numpy(), y_pred)
    recall = recall_score(y_true.to_numpy(), y_pred)
    return {
        "dataset": prediction_path.name.split("__")[0],
        "method": str(merged["method"].iloc[0]),
        "n_cells": len(merged),
        "n_true_doublets": n_doublets,
        "calibrated_precision": precision,
        "calibrated_recall": recall,
        "calibrated_f1": f1_score_simple(precision, recall),
        "thresholding": "top_true_doublet_count_by_score",
    }


def plot_metrics(metrics: pd.DataFrame, figures_dir: Path, calibrated: pd.DataFrame | None = None) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        sns.set_theme(style="whitegrid", context="notebook")
        plt.rcParams.update(
            {
                "axes.titlesize": 13,
                "axes.labelsize": 11,
                "xtick.labelsize": 10,
                "ytick.labelsize": 10,
                "legend.fontsize": 10,
                "legend.title_fontsize": 10,
            }
        )
        long = metrics.melt(
            id_vars=["dataset", "method"],
            value_vars=["precision", "recall", "f1"],
            var_name="metric",
            value_name="value",
        )
        fig, ax = plt.subplots(figsize=(8.2, 5.2))
        sns.barplot(data=long, x="method", y="value", hue="metric", errorbar="sd", ax=ax)
        ax.set_ylim(0, 1)
        ax.set_xlabel("")
        ax.set_ylabel("Score")
        ax.set_title("Doublet detection precision, recall, and F1")
        sns.move_legend(
            ax,
            "upper center",
            bbox_to_anchor=(0.5, -0.14),
            ncol=3,
            title="Metric",
            frameon=False,
        )
        fig.tight_layout(rect=(0, 0.08, 1, 1))
        fig.savefig(figures_dir / "f1_precision_recall_comparison.png", dpi=300)
        plt.close()

        long_auc = metrics.melt(
            id_vars=["dataset", "method"],
            value_vars=["auroc", "auprc"],
            var_name="metric",
            value_name="value",
        )
        fig, ax = plt.subplots(figsize=(7.8, 5.0))
        sns.barplot(data=long_auc, x="method", y="value", hue="metric", errorbar="sd", ax=ax)
        ax.set_ylim(0, 1)
        ax.set_xlabel("")
        ax.set_ylabel("Score")
        ax.set_title("Ranking performance of doublet scores")
        sns.move_legend(
            ax,
            "upper center",
            bbox_to_anchor=(0.5, -0.14),
            ncol=2,
            title="Metric",
            frameon=False,
        )
        fig.tight_layout(rect=(0, 0.08, 1, 1))
        fig.savefig(figures_dir / "auprc_auroc_comparison.png", dpi=300)
        plt.close()

        f1_matrix = metrics.pivot(index="dataset", columns="method", values="f1")
        plt.figure(figsize=(9, max(4, 0.45 * len(f1_matrix) + 2)))
        sns.heatmap(f1_matrix, annot=True, fmt=".2f", cmap="viridis", vmin=0, vmax=1)
        plt.title("F1 score by dataset and method")
        plt.xlabel("")
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig(figures_dir / "f1_by_dataset_heatmap.png", dpi=300)
        plt.close()

        plt.figure(figsize=(9, 5))
        sns.barplot(data=metrics, x="method", y="runtime_seconds", errorbar="sd")
        plt.xlabel("")
        plt.ylabel("Runtime (seconds)")
        plt.title("Runtime comparison")
        plt.tight_layout()
        plt.savefig(figures_dir / "runtime_comparison.png", dpi=300)
        plt.close()

        if calibrated is not None and not calibrated.empty:
            long_cal = calibrated.melt(
                id_vars=["dataset", "method"],
                value_vars=["calibrated_precision", "calibrated_recall", "calibrated_f1"],
                var_name="metric",
                value_name="value",
            )
            long_cal["metric"] = long_cal["metric"].str.replace("calibrated_", "", regex=False)
            fig, ax = plt.subplots(figsize=(8.2, 5.2))
            sns.barplot(data=long_cal, x="method", y="value", hue="metric", errorbar="sd", ax=ax)
            ax.set_ylim(0, 1)
            ax.set_xlabel("")
            ax.set_ylabel("Score")
            ax.set_title("Calibrated top-N precision, recall, and F1")
            sns.move_legend(
                ax,
                "upper center",
                bbox_to_anchor=(0.5, -0.14),
                ncol=3,
                title="Metric",
                frameon=False,
            )
            fig.tight_layout(rect=(0, 0.08, 1, 1))
            fig.savefig(figures_dir / "calibrated_f1_precision_recall_comparison.png", dpi=300)
            plt.close()
    except ImportError:
        write_svg_barplot(
            metrics,
            ["precision", "recall", "f1"],
            figures_dir / "f1_precision_recall_comparison.svg",
            "Doublet detection precision, recall, and F1",
        )
        write_svg_barplot(
            metrics,
            ["auroc", "auprc"],
            figures_dir / "auprc_auroc_comparison.svg",
            "Ranking performance of doublet scores",
        )


def write_svg_barplot(metrics: pd.DataFrame, columns: list[str], path: Path, title: str) -> None:
    width, height = 900, 520
    left, bottom = 90, 430
    bar_w = 42
    gap = 20
    colors = ["#2f6f9f", "#c75b39", "#4f8f5f"]
    values = metrics.groupby("method")[columns].mean().reset_index()
    bars = []
    labels = []
    x = left
    for _, row in values.iterrows():
        labels.append((x + (len(columns) * bar_w) / 2, str(row["method"])))
        for j, col in enumerate(columns):
            val = float(row[col]) if pd.notna(row[col]) else 0.0
            h = val * 330
            bars.append(
                f'<rect x="{x + j * bar_w}" y="{bottom - h:.1f}" width="{bar_w - 4}" '
                f'height="{h:.1f}" fill="{colors[j % len(colors)]}"/>'
            )
            bars.append(
                f'<text x="{x + j * bar_w + 18}" y="{bottom - h - 6:.1f}" '
                f'text-anchor="middle" font-size="12">{val:.2f}</text>'
            )
        x += len(columns) * bar_w + gap

    legend = []
    for j, col in enumerate(columns):
        lx = left + j * 150
        legend.append(f'<rect x="{lx}" y="75" width="18" height="18" fill="{colors[j]}"/>')
        legend.append(f'<text x="{lx + 26}" y="89" font-size="14">{col}</text>')

    label_svg = [
        f'<text x="{lx}" y="468" text-anchor="middle" font-size="12">{label}</text>'
        for lx, label in labels
    ]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
<rect width="100%" height="100%" fill="white"/>
<text x="{width / 2}" y="38" text-anchor="middle" font-size="22" font-family="Arial">{title}</text>
{''.join(legend)}
<line x1="{left}" y1="{bottom}" x2="820" y2="{bottom}" stroke="#333"/>
<line x1="{left}" y1="100" x2="{left}" y2="{bottom}" stroke="#333"/>
<text x="50" y="105" font-size="12">1.0</text>
<text x="50" y="{bottom}" font-size="12">0.0</text>
{''.join(bars)}
{''.join(label_svg)}
</svg>'''
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", default="data/processed")
    parser.add_argument("--pred-dir", default="results/method_predictions")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--figures-dir", default="figures")
    args = parser.parse_args()

    processed_dir = Path(args.processed_dir)
    pred_dir = Path(args.pred_dir)
    results_dir = Path(args.results_dir)
    figures_dir = Path(args.figures_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    calibrated_rows = []
    for dataset_dir in sorted(path for path in processed_dir.iterdir() if path.is_dir()):
        metadata = pd.read_csv(dataset_dir / "metadata.csv")
        for prediction_path in sorted(pred_dir.glob(f"{dataset_dir.name}__*.csv")):
            rows.append(evaluate_one(metadata, prediction_path))
            calibrated_rows.append(evaluate_one_calibrated(metadata, prediction_path))

    if not rows:
        raise FileNotFoundError("No prediction files found for processed datasets")

    metrics = pd.DataFrame(rows).sort_values(["dataset", "method"])
    metrics.to_csv(results_dir / "benchmark_metrics.csv", index=False)
    calibrated = pd.DataFrame(calibrated_rows).sort_values(["dataset", "method"])
    calibrated.to_csv(results_dir / "calibrated_metrics.csv", index=False)
    plot_metrics(metrics, figures_dir, calibrated)
    print(metrics.to_string(index=False))
    print("\nCalibrated top-N metrics")
    print(calibrated.to_string(index=False))


if __name__ == "__main__":
    main()
