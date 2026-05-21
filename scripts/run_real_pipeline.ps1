param(
    [int]$MaxCells = 3000,
    [switch]$SkipMethods
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== Miniproject 7 real-data pipeline =="
Write-Host "Working directory: $root"

function Run-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    Write-Host ""
    Write-Host "== $Name ==" -ForegroundColor Cyan
    & $Command
}

Run-Step "Convert Xi and Li real RDS datasets" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_r_env.ps1 `
        scripts/15_prepare_real_rds.R data/raw/real_datasets data/processed_real 99 $MaxCells
}

if (-not $SkipMethods) {
    Run-Step "Run Scrublet on real datasets" {
        powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_python_env.ps1 `
            scripts/03_run_scrublet.py `
            --processed-dir data/processed_real `
            --output-dir results/method_predictions_real
    }

    Run-Step "Run DoubletFinder on real datasets" {
        powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_r_env.ps1 `
            scripts/04_run_doubletfinder.R data/processed_real results/method_predictions_real
    }

    Run-Step "Run scDblFinder on real datasets" {
        powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_r_env.ps1 `
            scripts/05_run_scdblfinder.R data/processed_real results/method_predictions_real
    }

    Run-Step "Run representative DoubletFinder pK sensitivity" {
        powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_r_env.ps1 `
            scripts/04_run_doubletfinder.R data/processed_real results/pk_sensitivity_predictions/pk_005 0.05 "pbmc-1A-dm,hm-6k,pdx-MULTI"
        powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_r_env.ps1 `
            scripts/04_run_doubletfinder.R data/processed_real results/pk_sensitivity_predictions/pk_010 0.10 "pbmc-1A-dm,hm-6k,pdx-MULTI"
        powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_r_env.ps1 `
            scripts/04_run_doubletfinder.R data/processed_real results/pk_sensitivity_predictions/pk_015 0.15 "pbmc-1A-dm,hm-6k,pdx-MULTI"
    }
}

Run-Step "Evaluate real-data benchmark" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_python_env.ps1 `
        scripts/06_evaluate_and_plot.py `
        --processed-dir data/processed_real `
        --pred-dir results/method_predictions_real `
        --results-dir results/real `
        --figures-dir figures/real
}

Run-Step "Build real-data downstream UMAP" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_python_env.ps1 `
        scripts/07_downstream_clustering.py `
        --processed-dir data/processed_real `
        --pred-dir results/method_predictions_real `
        --figures-dir figures/real `
        --dataset pbmc-1A-dm
}

Run-Step "Run marker impact analysis" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_python_env.ps1 `
        scripts/17_marker_impact_analysis.py `
        --processed-dir data/processed_real `
        --pred-dir results/method_predictions_real `
        --results-dir results/real `
        --figures-dir figures/real `
        --dataset pbmc-1A-dm `
        --method scDblFinder
}

Run-Step "Summarize DoubletFinder pK sensitivity" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_python_env.ps1 `
        scripts/21_pk_sensitivity_summary.py
}

Run-Step "Build report document" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_python_env.ps1 `
        scripts/08_build_report_docx.py
}

Run-Step "Run quality control" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_python_env.ps1 `
        scripts/11_quality_control.py
}

Run-Step "Summarize real-data benchmark" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_python_env.ps1 `
        scripts/16_real_data_summary.py
}

Run-Step "Write reproducibility manifest" {
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_python_env.ps1 `
        scripts/12_create_repro_manifest.py
}
