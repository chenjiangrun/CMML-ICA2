# Final Delivery Checklist

Student ID: 3127

## Main Submission Files

- `report/miniproject7_3127_ica2_main_report.docx`
- `report/miniproject7_3127_ica2_main_report.pdf`
- `report/miniproject7_3127_ica2_supporting_materials.docx`
- `report/miniproject7_3127_ica2_supporting_materials.pdf`
- `report/miniproject7_3127_ica2_main_report.md`
- `report/miniproject7_3127_ica2_supporting_materials.md`
- `report/miniproject7_3127_report.docx`
- `report/miniproject7_3127_report.pdf`
- `results/real/benchmark_metrics.csv`
- `results/real/calibrated_metrics.csv`
- `results/real/real_method_summary.csv`
- `results/real/real_calibrated_method_summary.csv`
- `results/real/real_best_method_by_dataset.csv`
- `results/real/real_micro_average_summary.csv`
- `results/real/real_dataset_inventory_processed.csv`
- `results/real/doubletfinder_pk_sensitivity.csv`
- `results/real/doubletfinder_pk_sensitivity_summary.csv`
- `results/real/marker_impact_summary.csv`
- `results/real/marker_impact_top_markers.csv`
- `results/benchmark_metrics.csv`
- `results/method_summary.csv`
- `results/best_method_by_dataset.csv`
- `results/doublet_type_recall.csv`
- `results/confusion_matrices.csv`
- `results/real/confusion_matrices.csv`
- `results/quality_control_report.md`
- `results/submission_audit.md`
- `results/reproducibility_manifest.json`
- `results/reproducibility_manifest.md`
- `results/file_manifest.csv`
- `figures/*.png`
- `figures/real/*.png`
- `scripts/*.py`, `scripts/*.R`, and wrapper scripts
- `scripts/22_make_submission_packages.py`
- `docs/method_parameters.csv`
- `docs/grading_alignment.md`
- `docs/ica2_exact_submission_requirements.md`
- `assignment/source_requirements/`

## ICA2 Format Compliance

- Main report abstract: 54 words, within the 70-word limit.
- Main report text: 576 words, within the 1000-word limit.
- Main report display items: 2, within the maximum of 2 figures/tables.
  Figure 1 is a multi-panel composite figure, which is allowed by the ICA2
  guidance as one display item.
- Supporting Methods: 228 words, within the 500-word limit.
- Reflection: 96 words, within the 200-word limit.
- Supplementary figures: 5, within the maximum of 5.
- Supplementary figures are cited in the main report text and provide
  supporting evidence rather than duplicating the main display figure.
- The previous long report is retained as a detailed technical version, while
  the ICA2 main report and supporting materials should be treated as the primary
  submission documents.

## Completed Analyses

- Five controlled simulated datasets are included:
  - `pilot_simulated`
  - `sim_easy_13pct`
  - `sim_homotypic_13pct`
  - `sim_low_rate_3pct`
  - `sim_subtle_13pct`
- All 16 Xi and Li real benchmark datasets are included. Large datasets were
  reproducibly subsampled to 3000 cells for local runtime.
- Three doublet detection methods were run:
  - Scrublet
  - DoubletFinder
  - scDblFinder
- Metrics computed:
  - precision
  - recall
  - F1
  - AUROC
  - AUPRC
  - runtime
- Additional analyses:
  - best method by real dataset and simulated scenario
  - method-level averages
  - calibrated top-N score-ranking comparison under equal doublet-call budgets
  - representative DoubletFinder pK sensitivity analysis
  - micro-averaged real-data metrics
  - homotypic versus heterotypic recall
  - confusion matrices and false-negative heatmaps
  - before/after UMAP after predicted doublet removal
  - marker-gene impact analysis after predicted doublet removal
  - automated quality-control checks
  - reproducibility manifest and file checksums
  - metric implementation self-tests
  - documented method parameters
  - PDF page rendering for visual report QC
  - final submission ZIP audit
  - reproducible light/full submission ZIP generation
  - grading alignment map from assignment requirements to project artifacts

## Reproducibility

Run the full simulated workflow:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_full_pipeline.ps1
```

Run the real-data workflow after extracting `data/raw/real_datasets`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_real_pipeline.ps1
```

To rebuild figures and the report from existing prediction files:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_full_pipeline.ps1 -SkipMethods
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_real_pipeline.ps1 -SkipMethods
```

## Known Limitations

- The largest real datasets were subsampled to 3000 cells, so this is not a
  full-cell reproduction of the original Xi and Li benchmark.
- DoubletFinder uses a Seurat-v5-compatible pANN implementation to avoid a
  local package compatibility issue; the default pK is fixed at 0.10, with an
  optional command-line pK argument for sensitivity checks.
- The marker-impact analysis was run on one representative PBMC dataset rather
  than all 16 real datasets.
