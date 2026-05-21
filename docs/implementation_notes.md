# Implementation Notes

## Completed

- Created the reproducible project structure.
- Built a project-local Python conda environment at `.conda_env`.
- Installed and verified the Python analysis stack, including `numpy`,
  `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `scanpy`,
  `anndata`, `scrublet`, `igraph`, `leidenalg`, `python-docx`, `pdf2image`,
  and `pypdfium2`.
- Installed official Windows R at `C:\Program Files\R\R-4.6.0` and installed
  R packages into the ASCII-only library path `C:\Rlibs`.
- Installed and verified `Seurat`, `BiocManager`, `remotes`, `scDblFinder`,
  and `DoubletFinder`.
- Downloaded and MD5-verified `real_datasets.zip` from Zenodo record 4562782.
- Added `scripts/15_prepare_real_rds.R` to convert Xi and Li `.rds` files into
  the standardized project format.
- Converted all 16 Xi and Li real benchmark datasets. Large datasets were
  reproducibly subsampled to 3000 cells for local runtime.
- Ran Scrublet, DoubletFinder, and scDblFinder on all 16 real datasets,
  producing 48 real-data prediction files. Scrublet now reads Matrix Market
  files through sparse SciPy matrices and fails loudly unless the optional
  smoke-test fallback is explicitly requested.
- Added `scripts/09_generate_simulated_benchmark.py` to create controlled
  simulation scenarios: easy heterotypic doublets, low doublet rate, mostly
  homotypic doublets, and subtle marker separation.
- Added `scripts/10_stratified_analysis.py` for method-level summaries,
  best-method-by-scenario output, and homotypic versus heterotypic recall
  analysis.
- Added `scripts/11_quality_control.py` to validate simulated and real
  datasets, prediction coverage, deliverable presence, and confusion matrices.
- Added `scripts/12_create_repro_manifest.py` to record package versions,
  dataset names, tracked files, and SHA-256 checksums for reproducibility.
- Added `scripts/13_self_test_metrics.py` to test the custom metric
  implementations against known small examples.
- Added `scripts/14_make_pipeline_diagram.py` and `figures/pipeline_workflow.png`
  to document the end-to-end workflow visually.
- Added `scripts/16_real_data_summary.py` to summarize real-data method
  performance, processed doublet rates, and calibrated top-N score recovery.
- Added `scripts/17_marker_impact_analysis.py` to compare marker-gene
  stability and log-fold-change shifts before and after predicted doublet
  removal in a representative real PBMC dataset.
- Added `scripts/18_render_pdf_pages.py` to render the final PDF into PNG page
  previews for visual quality control.
- Added `docs/method_parameters.csv` to make benchmark method settings
  explicit.
- Added `scripts/21_pk_sensitivity_summary.py` and
  `figures/real/doubletfinder_pk_sensitivity.png` for a representative
  DoubletFinder pK sensitivity check.
- Added `scripts/22_make_submission_packages.py` to rebuild both final
  submission ZIP files reproducibly.

## Environment Notes

- Use `scripts/run_python_env.ps1` instead of calling `.conda_env/python.exe`
  directly, because the wrapper adds the environment DLL directories to `PATH`.
- R is working through `scripts/run_r_env.ps1`, which points R at the package
  library in `C:\Rlibs`.
- `scripts/04_run_doubletfinder.R` uses a local Seurat v5-compatible
  implementation of the DoubletFinder pANN classification core. This avoids an
  upstream metadata/data-frame compatibility issue observed with
  DoubletFinder 2.0.6 under Seurat 5.5.0 while keeping the same artificial
  doublet nearest-neighbour logic.
- The official DOCX render helper can still trigger a LibreOffice `libpng`
  error on this Windows setup. The final report is therefore checked by
  exporting to PDF and rendering that PDF to page PNGs with `pypdfium2`.

## Reproducible Workflows

Run the simulation workflow:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_full_pipeline.ps1
```

Run the real-data workflow after extracting `data/raw/real_datasets`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_real_pipeline.ps1
```

Render the final PDF for visual quality control:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_python_env.ps1 scripts/18_render_pdf_pages.py report/miniproject7_3127_report.pdf --output-dir report/rendered_pdf_pages
```
