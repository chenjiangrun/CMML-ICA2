"""Assess marker-gene impact before and after predicted doublet removal."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import mmread


def choose_prediction(pred_dir: Path, dataset_id: str, method: str) -> Path:
    path = pred_dir / f"{dataset_id}__{method}.csv"
    if path.exists():
        return path
    matches = sorted(pred_dir.glob(f"{dataset_id}__*.csv"))
    if not matches:
        raise FileNotFoundError(f"No prediction file found for {dataset_id}")
    return matches[0]


def build_adata(dataset_dir: Path, prediction_path: Path):
    import anndata as ad

    counts = mmread(dataset_dir / "counts.mtx").T.tocsr()
    genes = pd.read_csv(dataset_dir / "genes.tsv", header=None)[0].astype(str)
    cells = pd.read_csv(dataset_dir / "cells.tsv", header=None)[0].astype(str)
    metadata = pd.read_csv(dataset_dir / "metadata.csv").set_index("cell_id")
    predictions = pd.read_csv(prediction_path).set_index("cell_id")
    obs = metadata.loc[cells].join(predictions[["prediction", "score"]])
    adata = ad.AnnData(counts, obs=obs)
    adata.obs_names = cells
    adata.var_names = genes
    return adata


def preprocess_and_markers(adata, label: str):
    import scanpy as sc

    x = adata.copy()
    sc.pp.filter_cells(x, min_genes=50)
    sc.pp.filter_genes(x, min_cells=3)
    sc.pp.normalize_total(x, target_sum=1e4)
    sc.pp.log1p(x)
    sc.pp.highly_variable_genes(x, n_top_genes=min(2000, x.n_vars))
    x = x[:, x.var["highly_variable"]].copy()
    x.raw = x.copy()
    sc.pp.scale(x, max_value=10)
    sc.tl.pca(x, svd_solver="arpack")
    sc.pp.neighbors(x, n_neighbors=15, n_pcs=min(30, x.obsm["X_pca"].shape[1]))
    sc.tl.umap(x)
    sc.tl.leiden(x, resolution=0.5, key_added="cluster")
    sc.tl.rank_genes_groups(x, "cluster", method="t-test", n_genes=50, use_raw=True)
    x.uns["analysis_label"] = label
    return x


def marker_table(adata, top_n: int = 20) -> pd.DataFrame:
    names = pd.DataFrame(adata.uns["rank_genes_groups"]["names"]).head(top_n)
    scores = pd.DataFrame(adata.uns["rank_genes_groups"]["scores"]).head(top_n)
    logfc = pd.DataFrame(adata.uns["rank_genes_groups"]["logfoldchanges"]).head(top_n)
    rows = []
    for cluster in names.columns:
        for rank, gene in enumerate(names[cluster], start=1):
            rows.append(
                {
                    "cluster": str(cluster),
                    "rank": rank,
                    "gene": str(gene),
                    "score": float(scores.loc[rank - 1, cluster]),
                    "logfoldchange": float(logfc.loc[rank - 1, cluster]),
                }
            )
    return pd.DataFrame(rows)


def match_clusters(before, after) -> pd.DataFrame:
    rows = []
    before_clusters = sorted(before.obs["cluster"].astype(str).unique())
    after_clusters = sorted(after.obs["cluster"].astype(str).unique())
    after_sets = {
        cluster: set(after.obs_names[after.obs["cluster"].astype(str) == cluster])
        for cluster in after_clusters
    }
    retained = set(after.obs_names)
    for cluster in before_clusters:
        before_cells = set(before.obs_names[before.obs["cluster"].astype(str) == cluster])
        before_retained = before_cells & retained
        best_cluster = None
        best_jaccard = -1.0
        for after_cluster, after_cells in after_sets.items():
            union = before_retained | after_cells
            jaccard = len(before_retained & after_cells) / len(union) if union else 0.0
            if jaccard > best_jaccard:
                best_cluster = after_cluster
                best_jaccard = jaccard
        rows.append(
            {
                "before_cluster": cluster,
                "matched_after_cluster": best_cluster,
                "retained_cell_jaccard": best_jaccard,
                "before_cells": len(before_cells),
                "before_cells_retained": len(before_retained),
            }
        )
    return pd.DataFrame(rows)


def summarize_marker_changes(before_markers: pd.DataFrame, after_markers: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, match in matches.iterrows():
        before_cluster = str(match["before_cluster"])
        after_cluster = str(match["matched_after_cluster"])
        before = before_markers[before_markers["cluster"] == before_cluster]
        after = after_markers[after_markers["cluster"] == after_cluster]
        before10 = set(before[before["rank"] <= 10]["gene"])
        after10 = set(after[after["rank"] <= 10]["gene"])
        before20 = set(before[before["rank"] <= 20]["gene"])
        after20 = set(after[after["rank"] <= 20]["gene"])
        merged = before.merge(after, on="gene", suffixes=("_before", "_after"))
        rows.append(
            {
                **match.to_dict(),
                "top10_marker_overlap": len(before10 & after10) / 10,
                "top20_marker_jaccard": len(before20 & after20) / len(before20 | after20)
                if (before20 | after20)
                else np.nan,
                "shared_top20_markers": len(before20 & after20),
                "mean_abs_logfc_change_shared": float(
                    np.mean(np.abs(merged["logfoldchange_before"] - merged["logfoldchange_after"]))
                )
                if len(merged)
                else np.nan,
            }
        )
    return pd.DataFrame(rows)


def plot_summary(summary: pd.DataFrame, figures_dir: Path) -> None:
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
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    sns.barplot(data=summary, x="before_cluster", y="top10_marker_overlap", ax=axes[0], color="#4C78A8")
    axes[0].set_ylim(0, 1)
    axes[0].set_xlabel("Before-removal cluster")
    axes[0].set_ylabel("Top-10 marker overlap")
    axes[0].set_title("Marker stability after doublet removal")
    axes[0].tick_params(axis="x", rotation=0)
    sns.barplot(
        data=summary,
        x="before_cluster",
        y="mean_abs_logfc_change_shared",
        ax=axes[1],
        color="#F58518",
    )
    axes[1].set_xlabel("Before-removal cluster")
    axes[1].set_ylabel("Mean absolute logFC change")
    axes[1].set_title("Marker effect-size shift")
    axes[1].tick_params(axis="x", rotation=0)
    fig.tight_layout()
    fig.savefig(figures_dir / "marker_impact_summary.png", dpi=300)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", default="data/processed_real")
    parser.add_argument("--pred-dir", default="results/method_predictions_real")
    parser.add_argument("--results-dir", default="results/real")
    parser.add_argument("--figures-dir", default="figures/real")
    parser.add_argument("--dataset", default="pbmc-1A-dm")
    parser.add_argument("--method", default="scDblFinder")
    args = parser.parse_args()

    dataset_dir = Path(args.processed_dir) / args.dataset
    prediction_path = choose_prediction(Path(args.pred_dir), args.dataset, args.method)
    results_dir = Path(args.results_dir)
    figures_dir = Path(args.figures_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    adata = build_adata(dataset_dir, prediction_path)
    before = preprocess_and_markers(adata, "before")
    singlet_mask = adata.obs["prediction"].astype(str).str.lower() != "doublet"
    after = preprocess_and_markers(adata[singlet_mask].copy(), "after")

    before_markers = marker_table(before)
    after_markers = marker_table(after)
    matches = match_clusters(before, after)
    summary = summarize_marker_changes(before_markers, after_markers, matches)
    summary.insert(0, "dataset", args.dataset)
    summary.insert(1, "removal_method", args.method)

    before_markers.insert(0, "analysis", "before")
    after_markers.insert(0, "analysis", "after")
    pd.concat([before_markers, after_markers], ignore_index=True).to_csv(
        results_dir / "marker_impact_top_markers.csv", index=False
    )
    summary.to_csv(results_dir / "marker_impact_summary.csv", index=False)
    plot_summary(summary, figures_dir)

    removed = int((~singlet_mask).sum())
    print(
        f"Marker impact complete for {args.dataset}: removed {removed} predicted doublets; "
        f"mean top10 overlap={summary['top10_marker_overlap'].mean():.3f}; "
        f"mean abs logFC change={summary['mean_abs_logfc_change_shared'].mean():.3f}"
    )


if __name__ == "__main__":
    main()
