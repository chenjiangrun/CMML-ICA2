"""Summarise DoubletFinder pK sensitivity checks on representative datasets."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pandas as pd


def load_evaluation_module():
    spec = importlib.util.spec_from_file_location("evaluate_and_plot", "scripts/06_evaluate_and_plot.py")
    if spec is None or spec.loader is None:
        raise ImportError("Could not load scripts/06_evaluate_and_plot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


eval_mod = load_evaluation_module()


def evaluate_pk(processed_dir: Path, pred_dir: Path, pk: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for prediction_path in sorted(pred_dir.glob("*__DoubletFinder.csv")):
        dataset = prediction_path.name.split("__", 1)[0]
        metadata_path = processed_dir / dataset / "metadata.csv"
        if not metadata_path.exists():
            raise FileNotFoundError(metadata_path)
        metadata = pd.read_csv(metadata_path)
        row = eval_mod.evaluate_one(metadata, prediction_path)
        row["pK"] = float(pk)
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", default="data/processed_real")
    parser.add_argument("--pred-root", default="results/pk_sensitivity_predictions")
    parser.add_argument("--output", default="results/real/doubletfinder_pk_sensitivity.csv")
    args = parser.parse_args()

    processed_dir = Path(args.processed_dir)
    pred_root = Path(args.pred_root)
    rows: list[dict[str, object]] = []
    for pred_dir in sorted(path for path in pred_root.iterdir() if path.is_dir()):
        pk = pred_dir.name.replace("pk_", "")
        if len(pk) == 3:
            pk = f"0.{pk[-2:]}"
        rows.extend(evaluate_pk(processed_dir, pred_dir, pk))

    out = pd.DataFrame(rows)
    if out.empty:
        raise SystemExit("No pK sensitivity predictions found")
    cols = ["dataset", "pK", "precision", "recall", "f1", "auroc", "auprc", "runtime_seconds"]
    out = out[cols].sort_values(["dataset", "pK"])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output, index=False)

    summary = out.groupby("pK", as_index=False).agg(
        mean_precision=("precision", "mean"),
        mean_recall=("recall", "mean"),
        mean_f1=("f1", "mean"),
        mean_auroc=("auroc", "mean"),
        mean_auprc=("auprc", "mean"),
    )
    summary_path = output.with_name("doubletfinder_pk_sensitivity_summary.csv")
    summary.to_csv(summary_path, index=False)

    import matplotlib.pyplot as plt

    fig_path = Path("figures/real/doubletfinder_pk_sensitivity.png")
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6.5, 4.0))
    for metric in ["mean_f1", "mean_auroc", "mean_auprc"]:
        plt.plot(summary["pK"], summary[metric], marker="o", label=metric.replace("mean_", "").upper())
    plt.xlabel("DoubletFinder pK")
    plt.ylabel("Mean metric across representative datasets")
    plt.ylim(0, 1)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(fig_path, dpi=300)
    plt.close()

    print("DoubletFinder pK sensitivity")
    print(out.to_string(index=False))
    print("\nSummary")
    print(summary.to_string(index=False))
    print(f"\nWrote {fig_path}")


if __name__ == "__main__":
    main()
