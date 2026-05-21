# Manual Real Dataset Download Steps

Use this when automated Zenodo download is too slow.

## Download

1. Open this page in a browser:
   `https://zenodo.org/records/4562782`
2. Download `real_datasets.zip`.
3. Save it here:
   `data/raw/zenodo_4562782/real_datasets.zip`

The file is about 715 MB. The verified MD5 checksum is:

```text
72D393ECC0FECF5BB91571CCD985F233
```

## Extract

Open PowerShell in the project folder and run:

```powershell
New-Item -ItemType Directory -Force data\raw\zenodo_4562782 | Out-Null
Expand-Archive -Force data\raw\zenodo_4562782\real_datasets.zip data\raw\real_datasets
```

## Convert All 16 RDS Datasets

The converter prepares all `.rds` datasets and limits large datasets to at most
3000 cells for local runtime:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_r_env.ps1 scripts\15_prepare_real_rds.R data\raw\real_datasets data\processed_real 99 3000
```

## Run the Real Benchmark

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_real_pipeline.ps1
```

This runs Scrublet, DoubletFinder, scDblFinder, metric evaluation, real-data
summary tables, downstream UMAP analysis, marker-impact analysis, report
building, QC, and the reproducibility manifest.
