# ICA2 Miniproject 7: Doublet Detection Benchmark

Student ID: 3127

This repository contains the reproducible code and processed outputs for an
ICA2 project benchmarking doublet detection methods in single-cell RNA-seq
data. The report compares Scrublet, DoubletFinder, and scDblFinder on labelled
real benchmark datasets from Xi and Li, with controlled simulations used as
supporting checks.

## Contents

- `scripts/`: Python, R, and PowerShell scripts used for preprocessing,
  method execution, evaluation, plotting, quality control, and report support.
- `results/`: benchmark metric tables, method predictions, quality-control
  outputs, and reproducibility manifests.
- `figures/`: figures used in the report and supporting information.
- `docs/`: data dictionary, implementation notes, parameter tables, and
  environment notes.
- `requirements.txt`: Python package requirements for the local workflow.

Raw Xi and Li data files are not included because the archive is large. The
download source is:

https://zenodo.org/records/4562782

## Reproducing the Analysis

The workflow was run on Windows. After downloading and extracting the Xi and Li
archive as described in `docs/manual_real_data_steps.md`, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_real_pipeline.ps1
```

For the controlled simulation benchmark, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_full_pipeline.ps1
```

The main summary table is `results/real/benchmark_metrics.csv`. The main
composite figure is `figures/real/main_report_composite_figure.png`.
