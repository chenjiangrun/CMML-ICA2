"""Download benchmark data or create a small pilot dataset.

The preferred real data source is the Xi and Li Zenodo benchmark archive:
https://zenodo.org/records/4562782

Because the complete archive can be large, this script supports two modes:

- `--real`: download the Zenodo archive metadata and listed files.
- `--pilot`: create a small simulated dataset to test the pipeline wiring.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd


ZENODO_RECORD = "https://zenodo.org/api/records/4562782"


def write_matrix_market(path: Path, matrix: np.ndarray) -> None:
    rows, cols = matrix.shape
    nz = int(np.count_nonzero(matrix))
    with path.open("w", encoding="utf-8") as handle:
        handle.write("%%MatrixMarket matrix coordinate integer general\n")
        handle.write(f"{rows} {cols} {nz}\n")
        for row, col in zip(*np.nonzero(matrix)):
            handle.write(f"{row + 1} {col + 1} {int(matrix[row, col])}\n")


def download_real(output_dir: Path, limit: int | None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(ZENODO_RECORD, timeout=60) as response:
        record = json.loads(response.read().decode("utf-8"))

    (output_dir / "zenodo_record_4562782.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )

    files = record.get("files", [])
    if limit is not None:
        files = files[:limit]

    for item in files:
        url = item["links"]["self"]
        filename = item["key"]
        target = output_dir / filename
        if target.exists() and target.stat().st_size > 0:
            print(f"Already exists: {target}")
            continue
        print(f"Downloading {filename}")
        urllib.request.urlretrieve(url, target)


def create_pilot(output_dir: Path, seed: int = 7) -> None:
    """Create a small benchmark-shaped dataset for smoke tests only."""

    rng = np.random.default_rng(seed)
    dataset_dir = output_dir / "pilot_simulated"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    n_genes = 500
    n_singlets = 260
    n_doublets = 40
    n_cells = n_singlets + n_doublets

    base_a = rng.gamma(shape=1.5, scale=1.0, size=n_genes)
    base_b = rng.gamma(shape=1.5, scale=1.0, size=n_genes)
    base_a[:80] += 2.5
    base_b[80:160] += 2.5

    singlet_types = rng.choice(["A", "B"], size=n_singlets)
    singlets = []
    for cell_type in singlet_types:
        lam = base_a if cell_type == "A" else base_b
        library = rng.lognormal(mean=7.2, sigma=0.25)
        probs = lam / lam.sum()
        singlets.append(rng.multinomial(int(library), probs))

    doublets = []
    for _ in range(n_doublets):
        a = singlets[rng.integers(0, n_singlets)]
        b = singlets[rng.integers(0, n_singlets)]
        doublets.append(a + b)

    counts = np.vstack(singlets + doublets).T
    cells = [f"cell_{i:03d}" for i in range(n_cells)]
    genes = [f"gene_{i:04d}" for i in range(n_genes)]
    labels = ["singlet"] * n_singlets + ["doublet"] * n_doublets

    write_matrix_market(dataset_dir / "counts.mtx", counts)
    pd.Series(genes).to_csv(dataset_dir / "genes.tsv", index=False, header=False)
    pd.Series(cells).to_csv(dataset_dir / "cells.tsv", index=False, header=False)
    pd.DataFrame({"cell_id": cells, "ground_truth": labels}).to_csv(
        dataset_dir / "metadata.csv", index=False
    )
    print(f"Wrote pilot dataset: {dataset_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/raw")
    parser.add_argument("--real", action="store_true")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not args.real and not args.pilot:
        args.pilot = True

    if args.real:
        download_real(output_dir / "zenodo_4562782", args.limit)
    if args.pilot:
        create_pilot(output_dir)


if __name__ == "__main__":
    main()
