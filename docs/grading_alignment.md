# Miniproject 7 Grading Alignment

This file maps the assignment requirements to the completed project artifacts.

| Assignment requirement | Completed artifact |
|---|---|
| ICA2 main report length and display-item limits | `report/miniproject7_3127_ica2_main_report.docx`: 56-word abstract, 576-word main text, 2 display items |
| ICA2 supporting material limits | `report/miniproject7_3127_ica2_supporting_materials.docx`: 228-word Supporting Methods, 96-word Reflection, 5 supplementary figures |
| Understand doublets, sources, and impact | ICA2 main report Background/Discussion; detailed technical report in `report/miniproject7_3127_report.docx` |
| Use public scRNA-seq data with ground-truth labels or simulations | All 16 Xi and Li real datasets from Zenodo 4562782, plus five controlled simulations |
| Perform preprocessing including QC, normalization, and filtering | Methods section; `docs/method_parameters.csv`; `scripts/07_downstream_clustering.py`; `scripts/17_marker_impact_analysis.py` |
| Explore Scrublet | `scripts/03_run_scrublet.py`; predictions in `results/method_predictions_real/` |
| Explore DoubletFinder | `scripts/04_run_doubletfinder.R`; predictions in `results/method_predictions_real/` |
| Explore scDblFinder | `scripts/05_run_scdblfinder.R`; predictions in `results/method_predictions_real/` |
| Solo optional | Report Methods explains why Solo was not included |
| Compare against known doublet labels | `results/real/benchmark_metrics.csv`; `results/real/confusion_matrices.csv` |
| Precision, recall, F1 | `results/real/benchmark_metrics.csv`; `results/real/calibrated_metrics.csv`; report Real Data Benchmark section |
| AUROC and AUPRC | `results/real/benchmark_metrics.csv`; real-data AUROC/AUPRC figure |
| Downstream clustering impact | `figures/real/umap_before_after_doublet_removal.png`; report Downstream UMAP Effect section |
| Differential-expression or marker impact | `scripts/17_marker_impact_analysis.py`; `results/real/marker_impact_summary.csv`; report Differential Marker Impact section |
| Discuss biological implications | Report Discussion and Conclusion |
| Discuss limitations | Report Discussion; `docs/final_delivery_checklist.md` |
| Reproducible code | `scripts/run_full_pipeline.ps1`; `scripts/run_real_pipeline.ps1`; all method scripts |
| Teacher requirement files preserved | `assignment/source_requirements/` and `docs/ica2_exact_submission_requirements.md` |
| Quality control | `results/quality_control_report.md` with 115 checks passed and 0 failed |
| Reproducibility manifest | `results/reproducibility_manifest.json`; `results/file_manifest.csv` |
| Submission package sanity check | `scripts/19_submission_audit.py`; `results/submission_audit.md` |
| Submission package generation | `scripts/22_make_submission_packages.py`; light and full ZIP files |

## Current Headline Results

- Real-data unweighted mean F1: DoubletFinder 0.472, scDblFinder 0.383,
  Scrublet 0.381.
- Real-data micro F1: DoubletFinder 0.509, Scrublet 0.484, scDblFinder 0.333.
- Best score-ranking metrics: scDblFinder had the highest mean AUROC and AUPRC.
- Equal-call-budget calibrated F1: scDblFinder 0.602, Scrublet 0.534,
  DoubletFinder 0.498.
- Representative DoubletFinder pK sensitivity: pK=0.05 gave mean F1 0.551,
  pK=0.10 gave 0.523, and pK=0.15 gave 0.506 across three real datasets.
- Fastest method: Scrublet.
- Downstream marker-impact result: after scDblFinder doublet removal in
  `pbmc-1A-dm`, mean top-10 marker overlap was 0.920, but shared marker
  effect sizes shifted by a mean absolute logFC of 0.524.
