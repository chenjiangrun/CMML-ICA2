# Data Dictionary

Processed datasets use the same folder layout for simulated and real data:

- Simulated datasets: `data/processed/<dataset_id>/`
- Real Xi and Li datasets: `data/processed_real/<dataset_id>/`

Required dataset files:

- `counts.mtx`: sparse gene-by-cell count matrix in Matrix Market format.
- `genes.tsv`: one gene identifier per row, matching rows in `counts.mtx`.
- `cells.tsv`: one cell barcode per row, matching columns in `counts.mtx`.
- `metadata.csv`: cell-level metadata.

Required metadata columns:

- `cell_id`: unique cell identifier matching `cells.tsv`.
- `ground_truth`: `doublet` or `singlet`.

Optional metadata columns:

- `sample_id`: sample or capture identifier.
- `cell_type`: annotated cell type, if supplied by the benchmark dataset.
- `n_counts`: total UMI/read count per cell.
- `n_genes`: number of detected genes per cell.
- `scenario`: simulated benchmark scenario.
- `doublet_type`: `heterotypic`, `homotypic`, or `none`.
- `source_pair`: source cell-type pair for simulated doublets.

Prediction files are stored in:

- Simulated predictions: `results/method_predictions/`
- Real-data predictions: `results/method_predictions_real/`

Prediction filename pattern:

`<dataset_id>__<method>.csv`

Required prediction columns:

- `cell_id`
- `method`
- `score`
- `prediction`: `doublet` or `singlet`
- `runtime_seconds`

Benchmark metric tables are stored in:

- Simulated metrics: `results/benchmark_metrics.csv`
- Real-data metrics: `results/real/benchmark_metrics.csv`

The main real-data report summaries are:

- `results/real/real_method_summary.csv`
- `results/real/real_best_method_by_dataset.csv`
- `results/real/real_micro_average_summary.csv`
- `results/real/calibrated_metrics.csv`
- `results/real/real_calibrated_method_summary.csv`
- `results/real/real_dataset_inventory_processed.csv`
- `results/real/doubletfinder_pk_sensitivity.csv`
- `results/real/doubletfinder_pk_sensitivity_summary.csv`
- `results/real/marker_impact_summary.csv`
- `results/real/marker_impact_top_markers.csv`
