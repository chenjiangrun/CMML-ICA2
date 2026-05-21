"""Compare clustering before and after removing predicted doublets."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from scipy.io import mmread


def choose_prediction(pred_dir: Path, dataset_id: str) -> Path:
    priority = ["scDblFinder", "Scrublet", "DoubletFinder"]
    for method in priority:
        path = pred_dir / f"{dataset_id}__{method}.csv"
        if path.exists():
            return path
    matches = sorted(pred_dir.glob(f"{dataset_id}__*.csv"))
    if not matches:
        raise FileNotFoundError(f"No prediction file found for {dataset_id}")
    return matches[0]


def run_one(dataset_dir: Path, prediction_path: Path, figures_dir: Path) -> None:
    import matplotlib.pyplot as plt
    import scanpy as sc
    import seaborn as sns
    import anndata as ad

    dataset_id = dataset_dir.name
    counts = mmread(dataset_dir / "counts.mtx").T.tocsr()
    genes = pd.read_csv(dataset_dir / "genes.tsv", header=None)[0].astype(str)
    cells = pd.read_csv(dataset_dir / "cells.tsv", header=None)[0].astype(str)
    metadata = pd.read_csv(dataset_dir / "metadata.csv").set_index("cell_id")
    predictions = pd.read_csv(prediction_path).set_index("cell_id")

    obs = metadata.loc[cells].join(predictions[["prediction"]])
    adata = ad.AnnData(counts, obs=obs)
    adata.var_names = genes

    def preprocess(x):
        sc.pp.filter_cells(x, min_genes=50)
        sc.pp.filter_genes(x, min_cells=3)
        sc.pp.normalize_total(x, target_sum=1e4)
        sc.pp.log1p(x)
        sc.pp.highly_variable_genes(x, n_top_genes=min(2000, x.n_vars))
        x = x[:, x.var["highly_variable"]].copy()
        sc.pp.scale(x, max_value=10)
        sc.tl.pca(x, svd_solver="arpack")
        sc.pp.neighbors(x, n_neighbors=15, n_pcs=min(30, x.obsm["X_pca"].shape[1]))
        sc.tl.umap(x)
        sc.tl.leiden(x, resolution=0.5)
        return x

    all_cells = preprocess(adata.copy())
    singlets = preprocess(adata[adata.obs["prediction"] != "doublet"].copy())

    sns.set_theme(style="white", context="talk")
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    for ax, obj, title in [
        (axes[0], all_cells, "Before doublet removal"),
        (axes[1], singlets, "After predicted doublet removal"),
    ]:
        coords = obj.obsm["X_umap"]
        plot_df = pd.DataFrame(
            {
                "UMAP1": coords[:, 0],
                "UMAP2": coords[:, 1],
                "ground_truth": obj.obs["ground_truth"].values,
            }
        )
        sns.scatterplot(
            data=plot_df,
            x="UMAP1",
            y="UMAP2",
            hue="ground_truth",
            s=12,
            linewidth=0,
            ax=ax,
        )
        ax.set_title(title)
        ax.legend(loc="best", fontsize=8)

    figures_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(figures_dir / "umap_before_after_doublet_removal.png", dpi=300)
    plt.close(fig)
    print(f"Downstream clustering figure written for {dataset_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", default="data/processed")
    parser.add_argument("--pred-dir", default="results/method_predictions")
    parser.add_argument("--figures-dir", default="figures")
    parser.add_argument("--dataset", default=None)
    args = parser.parse_args()

    processed_dir = Path(args.processed_dir)
    dataset_dirs = sorted(path for path in processed_dir.iterdir() if path.is_dir())
    if args.dataset:
        dataset_dirs = [processed_dir / args.dataset]
    if not dataset_dirs:
        raise FileNotFoundError("No processed datasets found")

    dataset_dir = dataset_dirs[0]
    prediction_path = choose_prediction(Path(args.pred_dir), dataset_dir.name)
    run_one(dataset_dir, prediction_path, Path(args.figures_dir))


if __name__ == "__main__":
    main()
