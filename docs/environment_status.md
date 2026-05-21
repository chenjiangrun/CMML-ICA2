# Environment Status

Last checked: 2026-05-18

## Python Environment

The project-local Python environment is available at `.conda_env` inside this
project folder.

Verified working packages:

- numpy
- pandas
- scipy
- scikit-learn
- matplotlib
- seaborn
- scanpy
- anndata
- scrublet
- igraph
- leidenalg
- python-docx
- pdf2image
- pypdfium2

Use this wrapper to run project Python scripts:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_python_env.ps1 scripts/03_run_scrublet.py --processed-dir data/processed_real --output-dir results/method_predictions_real
```

The wrapper should be used instead of calling `.conda_env\python.exe`
directly, because it sets the DLL paths needed by compiled packages.

## R Environment

R is installed through the official Windows installer:

- `C:\Program Files\R\R-4.6.0\bin\Rscript.exe`

R packages are installed into:

`C:\Rlibs`

Verified installed packages:

- Seurat
- BiocManager
- remotes
- scDblFinder
- DoubletFinder

Use this wrapper to run project R scripts:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_r_env.ps1 scripts/05_run_scdblfinder.R data/processed_real results/method_predictions_real
```

Scrublet, DoubletFinder, and scDblFinder have been verified on all 16 processed
real Xi and Li benchmark datasets. The R package library is intentionally
outside the Chinese user path to avoid the Conda/R/Bioconductor resolver and
DLL-path instability seen earlier.

## Document Rendering

The final DOCX can be exported to PDF with LibreOffice using the ASCII-only
temporary directory `C:\CMML_render`. The report PDF has also been rendered to
PNG pages with `scripts/18_render_pdf_pages.py` for visual QC.
