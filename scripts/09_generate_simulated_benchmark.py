"""Generate multiple controlled simulated benchmark datasets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import mmwrite
from scipy import sparse


@dataclass(frozen=True)
class Scenario:
    dataset_id: str
    n_singlets: int
    n_doublets: int
    marker_boost: float
    homotypic_fraction: float
    seed: int


SCENARIOS = [
    Scenario("sim_easy_13pct", 260, 40, 3.0, 0.15, 11),
    Scenario("sim_low_rate_3pct", 300, 10, 3.0, 0.15, 13),
    Scenario("sim_homotypic_13pct", 260, 40, 3.0, 0.85, 17),
    Scenario("sim_subtle_13pct", 260, 40, 1.2, 0.25, 19),
]


def make_profiles(rng: np.random.Generator, n_genes: int, marker_boost: float) -> dict[str, np.ndarray]:
    base = rng.gamma(shape=1.4, scale=1.0, size=n_genes)
    profiles = {}
    marker_blocks = {"A": (0, 80), "B": (80, 160), "C": (160, 240)}
    for cell_type, (start, end) in marker_blocks.items():
        profile = base.copy()
        profile[start:end] += marker_boost
        profile += rng.gamma(shape=0.7, scale=0.3, size=n_genes)
        profiles[cell_type] = profile / profile.sum()
    return profiles


def simulate_singlets(
    rng: np.random.Generator,
    profiles: dict[str, np.ndarray],
    n_singlets: int,
) -> tuple[list[np.ndarray], list[str]]:
    cell_types = rng.choice(["A", "B", "C"], size=n_singlets, p=[0.38, 0.34, 0.28])
    singlets = []
    for cell_type in cell_types:
        library = rng.lognormal(mean=7.2, sigma=0.28)
        singlets.append(rng.multinomial(int(library), profiles[cell_type]))
    return singlets, cell_types.tolist()


def simulate_doublets(
    rng: np.random.Generator,
    singlets: list[np.ndarray],
    cell_types: list[str],
    n_doublets: int,
    homotypic_fraction: float,
) -> tuple[list[np.ndarray], list[str], list[str]]:
    by_type = {
        cell_type: [i for i, label in enumerate(cell_types) if label == cell_type]
        for cell_type in sorted(set(cell_types))
    }
    doublets = []
    doublet_types = []
    source_types = []
    for _ in range(n_doublets):
        if rng.random() < homotypic_fraction:
            cell_type = rng.choice(list(by_type))
            i, j = rng.choice(by_type[cell_type], size=2, replace=True)
            doublet_type = "homotypic"
        else:
            type_a, type_b = rng.choice(list(by_type), size=2, replace=False)
            i = rng.choice(by_type[type_a])
            j = rng.choice(by_type[type_b])
            doublet_type = "heterotypic"
        doublets.append(singlets[i] + singlets[j])
        source = f"{cell_types[i]}+{cell_types[j]}"
        doublet_types.append(doublet_type)
        source_types.append(source)
    return doublets, doublet_types, source_types


def write_dataset(output_dir: Path, scenario: Scenario) -> None:
    rng = np.random.default_rng(scenario.seed)
    dataset_dir = output_dir / scenario.dataset_id
    dataset_dir.mkdir(parents=True, exist_ok=True)

    n_genes = 500
    profiles = make_profiles(rng, n_genes, scenario.marker_boost)
    singlets, singlet_types = simulate_singlets(rng, profiles, scenario.n_singlets)
    doublets, doublet_types, source_types = simulate_doublets(
        rng,
        singlets,
        singlet_types,
        scenario.n_doublets,
        scenario.homotypic_fraction,
    )

    counts = np.vstack(singlets + doublets).T
    cells = [f"{scenario.dataset_id}_cell_{i:03d}" for i in range(counts.shape[1])]
    genes = [f"gene_{i:04d}" for i in range(n_genes)]
    labels = ["singlet"] * scenario.n_singlets + ["doublet"] * scenario.n_doublets
    cell_type = singlet_types + ["doublet"] * scenario.n_doublets
    doublet_type = ["none"] * scenario.n_singlets + doublet_types
    source_pair = ["none"] * scenario.n_singlets + source_types

    mmwrite(dataset_dir / "counts.mtx", sparse.coo_matrix(counts.astype(np.int64)))
    pd.Series(genes).to_csv(dataset_dir / "genes.tsv", index=False, header=False)
    pd.Series(cells).to_csv(dataset_dir / "cells.tsv", index=False, header=False)
    pd.DataFrame(
        {
            "cell_id": cells,
            "ground_truth": labels,
            "cell_type": cell_type,
            "doublet_type": doublet_type,
            "source_pair": source_pair,
            "n_counts": counts.sum(axis=0),
            "n_genes": (counts > 0).sum(axis=0),
            "scenario": scenario.dataset_id,
        }
    ).to_csv(dataset_dir / "metadata.csv", index=False)
    print(f"Wrote {dataset_dir}")


def main() -> None:
    output_dir = Path("data/raw")
    for scenario in SCENARIOS:
        write_dataset(output_dir, scenario)


if __name__ == "__main__":
    main()
