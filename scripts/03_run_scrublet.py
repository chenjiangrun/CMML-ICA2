"""Run Scrublet on all processed datasets."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd


def read_matrix_market_cells_by_genes(path: Path):
    from scipy.io import mmread

    return mmread(path).T.tocsr()


def normalise_scores(values) -> np.ndarray:
    scores = np.asarray(values, dtype=float).ravel()
    return (scores - scores.min()) / max(scores.max() - scores.min(), 1.0)


def run_one(dataset_dir: Path, output_dir: Path, allow_fallback: bool = False) -> None:
    dataset_id = dataset_dir.name
    counts = read_matrix_market_cells_by_genes(dataset_dir / "counts.mtx")
    cells = pd.read_csv(dataset_dir / "cells.tsv", header=None)[0].astype(str).tolist()
    metadata = pd.read_csv(dataset_dir / "metadata.csv")
    expected_rate = (metadata["ground_truth"].str.lower() == "doublet").mean()

    start = time.perf_counter()
    try:
        import scrublet as scr

        np.random.seed(7)
        scrub = scr.Scrublet(counts, expected_doublet_rate=float(expected_rate))
        scores, predictions = scrub.scrub_doublets()
        method = "Scrublet"
        prediction_labels = ["doublet" if bool(x) else "singlet" for x in predictions]
    except Exception as exc:
        if not allow_fallback:
            raise RuntimeError(
                f"Scrublet failed for {dataset_id}. Re-run with --allow-fallback "
                "only for pipeline smoke tests, not for final benchmark results."
            ) from exc
        # Smoke-test fallback: high library size is a simple doublet proxy.
        # Use only to verify pipeline wiring when Scrublet is not installed or
        # when tiny toy data make Scrublet's variance fit numerically unstable.
        print(f"Scrublet failed for {dataset_id}; using labelled fallback. Reason: {exc}")
        scores = normalise_scores(counts.sum(axis=1))
        n_doublets = max(1, int(round(len(scores) * expected_rate)))
        cutoff = np.sort(scores)[-n_doublets]
        prediction_labels = ["doublet" if score >= cutoff else "singlet" for score in scores]
        method = "Scrublet_fallback_library_size"
    runtime = time.perf_counter() - start

    result = pd.DataFrame(
        {
            "cell_id": cells,
            "method": method,
            "score": scores,
            "prediction": prediction_labels,
            "runtime_seconds": runtime,
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_dir / f"{dataset_id}__Scrublet.csv", index=False)
    print(f"Scrublet complete: {dataset_id} ({runtime:.1f}s)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-dir", default="data/processed")
    parser.add_argument("--output-dir", default="results/method_predictions")
    parser.add_argument(
        "--allow-fallback",
        action="store_true",
        help="Use a labelled library-size fallback if Scrublet fails. Intended for smoke tests only.",
    )
    args = parser.parse_args()

    processed_dir = Path(args.processed_dir)
    output_dir = Path(args.output_dir)
    for dataset_dir in sorted(path for path in processed_dir.iterdir() if path.is_dir()):
        run_one(dataset_dir, output_dir, allow_fallback=args.allow_fallback)


if __name__ == "__main__":
    main()
