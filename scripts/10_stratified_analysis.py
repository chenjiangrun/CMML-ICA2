"""Create stratified benchmark summaries for simulated doublets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_predictions(processed_dir: Path, pred_dir: Path) -> pd.DataFrame:
    rows = []
    for dataset_dir in sorted(path for path in processed_dir.iterdir() if path.is_dir()):
        metadata = pd.read_csv(dataset_dir / "metadata.csv")
        for pred_path in sorted(pred_dir.glob(f"{dataset_dir.name}__*.csv")):
            pred = pd.read_csv(pred_path)
            merged = metadata.merge(pred, on="cell_id", how="inner")
            merged["dataset"] = dataset_dir.name
            rows.append(merged)
    if not rows:
        raise FileNotFoundError("No prediction files found")
    return pd.concat(rows, ignore_index=True)


def doublet_type_recall(merged: pd.DataFrame) -> pd.DataFrame:
    if "doublet_type" not in merged.columns:
        return pd.DataFrame()
    doublets = merged[merged["ground_truth"].str.lower() == "doublet"].copy()
    doublets = doublets[doublets["doublet_type"].isin(["heterotypic", "homotypic"])]
    doublets["detected"] = doublets["prediction"].str.lower().eq("doublet")
    summary = (
        doublets.groupby(["dataset", "method", "doublet_type"], as_index=False)
        .agg(n_doublets=("cell_id", "size"), recall=("detected", "mean"))
        .sort_values(["dataset", "method", "doublet_type"])
    )
    return summary


def method_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    return (
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


def best_by_dataset(metrics: pd.DataFrame) -> pd.DataFrame:
    idx = metrics.groupby("dataset")["f1"].idxmax()
    best = metrics.loc[idx, ["dataset", "method", "f1", "precision", "recall", "auprc"]]
    return best.sort_values("dataset")


def plot_stratified_recall(stratified: pd.DataFrame, figures_dir: Path) -> None:
    if stratified.empty:
        return
    import matplotlib.pyplot as plt
    import seaborn as sns

    figures_dir.mkdir(parents=True, exist_ok=True)
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
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    sns.barplot(
        data=stratified,
        x="method",
        y="recall",
        hue="doublet_type",
        errorbar="sd",
        ax=ax,
    )
    ax.set_ylim(0, 1)
    ax.set_xlabel("")
    ax.set_ylabel("Recall among true doublets")
    ax.set_title("Detection of homotypic vs heterotypic doublets")
    sns.move_legend(
        ax,
        "upper center",
        bbox_to_anchor=(0.5, -0.14),
        ncol=2,
        title="Doublet type",
        frameon=False,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(figures_dir / "doublet_type_recall_comparison.png", dpi=300)
    plt.close()


def main() -> None:
    processed_dir = Path("data/processed")
    pred_dir = Path("results/method_predictions")
    results_dir = Path("results")
    figures_dir = Path("figures")
    results_dir.mkdir(parents=True, exist_ok=True)

    metrics = pd.read_csv(results_dir / "benchmark_metrics.csv")
    merged = load_predictions(processed_dir, pred_dir)

    summary = method_summary(metrics)
    summary.to_csv(results_dir / "method_summary.csv", index=False)

    best = best_by_dataset(metrics)
    best.to_csv(results_dir / "best_method_by_dataset.csv", index=False)

    stratified = doublet_type_recall(merged)
    if not stratified.empty:
        stratified.to_csv(results_dir / "doublet_type_recall.csv", index=False)
        plot_stratified_recall(stratified, figures_dir)

    print("Method summary")
    print(summary.to_string(index=False))
    if not stratified.empty:
        print("\nDoublet-type recall")
        print(stratified.to_string(index=False))


if __name__ == "__main__":
    main()
