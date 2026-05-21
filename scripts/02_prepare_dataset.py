"""Standardize raw benchmark datasets into the project format."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd


REQUIRED_FILES = ["counts.mtx", "genes.tsv", "cells.tsv", "metadata.csv"]


def matrix_market_shape(path: Path) -> tuple[int, int]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("%"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                return int(parts[0]), int(parts[1])
    raise ValueError(f"Could not read Matrix Market shape from {path}")


def validate_dataset(dataset_dir: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (dataset_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"{dataset_dir} is missing: {', '.join(missing)}")

    count_shape = matrix_market_shape(dataset_dir / "counts.mtx")
    genes = pd.read_csv(dataset_dir / "genes.tsv", header=None)
    cells = pd.read_csv(dataset_dir / "cells.tsv", header=None)
    metadata = pd.read_csv(dataset_dir / "metadata.csv")

    if count_shape != (len(genes), len(cells)):
        raise ValueError(
            f"Shape mismatch in {dataset_dir}: counts {count_shape}, "
            f"genes {len(genes)}, cells {len(cells)}"
        )
    required_columns = {"cell_id", "ground_truth"}
    if not required_columns.issubset(metadata.columns):
        raise ValueError(f"metadata.csv must contain {required_columns}")
    if set(cells[0]) != set(metadata["cell_id"]):
        raise ValueError("Cell IDs in cells.tsv and metadata.csv do not match")


def copy_standard_dataset(dataset_dir: Path, output_dir: Path) -> None:
    validate_dataset(dataset_dir)
    target = output_dir / dataset_dir.name
    target.mkdir(parents=True, exist_ok=True)
    for filename in REQUIRED_FILES:
        shutil.copy2(dataset_dir / filename, target / filename)

    print(f"Prepared {dataset_dir.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw")
    parser.add_argument("--output", default="data/processed")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates = [
        path for path in input_dir.iterdir()
        if path.is_dir() and all((path / name).exists() for name in REQUIRED_FILES)
    ]
    if not candidates:
        raise FileNotFoundError(
            "No standardized raw dataset folders found. Expected counts.mtx, "
            "genes.tsv, cells.tsv, and metadata.csv in a dataset subfolder."
        )

    for dataset_dir in candidates:
        copy_standard_dataset(dataset_dir, output_dir)


if __name__ == "__main__":
    main()
