"""Validate benchmark inputs, predictions, metrics, and deliverables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_DATASET_FILES = ["counts.mtx", "genes.tsv", "cells.tsv", "metadata.csv"]
EXPECTED_METHODS = ["DoubletFinder", "Scrublet", "scDblFinder"]
REQUIRED_DELIVERABLES = [
    "results/benchmark_metrics.csv",
    "results/method_summary.csv",
    "results/best_method_by_dataset.csv",
    "results/doublet_type_recall.csv",
    "figures/f1_precision_recall_comparison.png",
    "figures/auprc_auroc_comparison.png",
    "figures/f1_by_dataset_heatmap.png",
    "figures/runtime_comparison.png",
    "figures/doublet_type_recall_comparison.png",
    "figures/umap_before_after_doublet_removal.png",
    "report/miniproject7_3127_report.docx",
    "report/miniproject7_3127_report.pdf",
]
REQUIRED_REAL_DELIVERABLES = [
    "results/real/benchmark_metrics.csv",
    "results/real/calibrated_metrics.csv",
    "results/real/real_method_summary.csv",
    "results/real/real_best_method_by_dataset.csv",
    "results/real/real_micro_average_summary.csv",
    "results/real/real_calibrated_method_summary.csv",
    "results/real/real_dataset_inventory_processed.csv",
    "results/real/doubletfinder_pk_sensitivity.csv",
    "results/real/doubletfinder_pk_sensitivity_summary.csv",
    "figures/real/f1_precision_recall_comparison.png",
    "figures/real/calibrated_f1_precision_recall_comparison.png",
    "figures/real/auprc_auroc_comparison.png",
    "figures/real/f1_by_dataset_heatmap.png",
    "figures/real/runtime_comparison.png",
    "figures/real/doubletfinder_pk_sensitivity.png",
    "figures/real/umap_before_after_doublet_removal.png",
    "figures/real/marker_impact_summary.png",
    "results/real/marker_impact_summary.csv",
    "results/real/marker_impact_top_markers.csv",
]


def matrix_market_shape(path: Path) -> tuple[int, int]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("%"):
                continue
            parts = line.split()
            return int(parts[0]), int(parts[1])
    raise ValueError(f"Cannot read Matrix Market header: {path}")


def validate_datasets(processed_dir: Path) -> list[str]:
    messages = []
    for dataset_dir in sorted(path for path in processed_dir.iterdir() if path.is_dir()):
        missing = [name for name in REQUIRED_DATASET_FILES if not (dataset_dir / name).exists()]
        if missing:
            messages.append(f"FAIL dataset {dataset_dir.name}: missing {missing}")
            continue
        n_genes, n_cells = matrix_market_shape(dataset_dir / "counts.mtx")
        genes = pd.read_csv(dataset_dir / "genes.tsv", header=None)
        cells = pd.read_csv(dataset_dir / "cells.tsv", header=None)
        meta = pd.read_csv(dataset_dir / "metadata.csv")
        labels = set(meta["ground_truth"].str.lower())
        ok = (
            n_genes == len(genes)
            and n_cells == len(cells)
            and set(cells[0].astype(str)) == set(meta["cell_id"].astype(str))
            and labels <= {"singlet", "doublet"}
        )
        status = "PASS" if ok else "FAIL"
        messages.append(
            f"{status} dataset {dataset_dir.name}: {n_cells} cells, "
            f"{n_genes} genes, labels={sorted(labels)}"
        )
    return messages


def validate_predictions(processed_dir: Path, pred_dir: Path) -> list[str]:
    messages = []
    for dataset_dir in sorted(path for path in processed_dir.iterdir() if path.is_dir()):
        cells = pd.read_csv(dataset_dir / "cells.tsv", header=None)[0].astype(str)
        for method in EXPECTED_METHODS:
            pred_path = pred_dir / f"{dataset_dir.name}__{method}.csv"
            if not pred_path.exists():
                messages.append(f"FAIL prediction {dataset_dir.name}/{method}: missing file")
                continue
            pred = pd.read_csv(pred_path)
            required = {"cell_id", "method", "score", "prediction", "runtime_seconds"}
            labels = set(pred["prediction"].str.lower())
            ok = (
                required <= set(pred.columns)
                and len(pred) == len(cells)
                and set(pred["cell_id"].astype(str)) == set(cells)
                and labels <= {"singlet", "doublet"}
            )
            status = "PASS" if ok else "FAIL"
            messages.append(f"{status} prediction {dataset_dir.name}/{method}: {len(pred)} cells")
    return messages


def confusion_matrices(processed_dir: Path, pred_dir: Path, results_dir: Path) -> pd.DataFrame:
    rows = []
    for dataset_dir in sorted(path for path in processed_dir.iterdir() if path.is_dir()):
        meta = pd.read_csv(dataset_dir / "metadata.csv")
        for pred_path in sorted(pred_dir.glob(f"{dataset_dir.name}__*.csv")):
            pred = pd.read_csv(pred_path)
            merged = meta.merge(pred, on="cell_id", how="inner")
            y_true = merged["ground_truth"].str.lower().eq("doublet")
            y_pred = merged["prediction"].str.lower().eq("doublet")
            rows.append(
                {
                    "dataset": dataset_dir.name,
                    "method": str(merged["method"].iloc[0]),
                    "true_positive": int((y_true & y_pred).sum()),
                    "false_positive": int((~y_true & y_pred).sum()),
                    "true_negative": int((~y_true & ~y_pred).sum()),
                    "false_negative": int((y_true & ~y_pred).sum()),
                }
            )
    out = pd.DataFrame(rows).sort_values(["dataset", "method"])
    out.to_csv(results_dir / "confusion_matrices.csv", index=False)
    return out


def plot_confusion_heatmap(conf: pd.DataFrame, figures_dir: Path) -> None:
    import matplotlib.pyplot as plt
    import seaborn as sns

    plot_data = conf.copy()
    plot_data["missed_doublets"] = plot_data["false_negative"]
    heat = plot_data.pivot(index="dataset", columns="method", values="missed_doublets")
    sns.set_theme(style="white", context="talk")
    plt.figure(figsize=(9, max(4, 0.45 * len(heat) + 2)))
    sns.heatmap(heat, annot=True, fmt=".0f", cmap="magma_r")
    plt.title("False negatives: true doublets missed")
    plt.xlabel("")
    plt.ylabel("")
    plt.tight_layout()
    plt.savefig(figures_dir / "missed_doublets_heatmap.png", dpi=300)
    plt.close()


def validate_deliverables(required: list[str] | None = None) -> list[str]:
    messages = []
    for item in required or REQUIRED_DELIVERABLES:
        path = Path(item)
        ok = path.exists() and path.stat().st_size > 0
        status = "PASS" if ok else "FAIL"
        size = path.stat().st_size if path.exists() else 0
        messages.append(f"{status} deliverable {item}: {size} bytes")
    return messages


def write_report(messages: list[str], results_dir: Path) -> None:
    passed = sum(msg.startswith("PASS") for msg in messages)
    failed = sum(msg.startswith("FAIL") for msg in messages)
    lines = [
        "# Quality Control Report",
        "",
        f"Checks passed: {passed}",
        f"Checks failed: {failed}",
        "",
        "## Details",
        "",
    ]
    lines.extend(f"- {msg}" for msg in messages)
    (results_dir / "quality_control_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    processed_dir = Path("data/processed")
    pred_dir = Path("results/method_predictions")
    results_dir = Path("results")
    figures_dir = Path("figures")
    messages = []
    messages.extend(validate_datasets(processed_dir))
    messages.extend(validate_predictions(processed_dir, pred_dir))
    conf = confusion_matrices(processed_dir, pred_dir, results_dir)
    plot_confusion_heatmap(conf, figures_dir)
    messages.extend(validate_deliverables())

    real_processed_dir = Path("data/processed_real")
    real_pred_dir = Path("results/method_predictions_real")
    real_results_dir = Path("results/real")
    real_figures_dir = Path("figures/real")
    if real_processed_dir.exists() and real_pred_dir.exists():
        messages.extend(validate_datasets(real_processed_dir))
        messages.extend(validate_predictions(real_processed_dir, real_pred_dir))
        real_conf = confusion_matrices(real_processed_dir, real_pred_dir, real_results_dir)
        plot_confusion_heatmap(real_conf, real_figures_dir)
        messages.extend(validate_deliverables(REQUIRED_REAL_DELIVERABLES))

    write_report(messages, results_dir)
    failed = [msg for msg in messages if msg.startswith("FAIL")]
    print(f"QC checks: {len(messages) - len(failed)} passed, {len(failed)} failed")
    if failed:
        raise SystemExit("\n".join(failed))


if __name__ == "__main__":
    main()
