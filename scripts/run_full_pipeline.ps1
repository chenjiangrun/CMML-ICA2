param(
    [switch]$SkipMethods
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== Miniproject 7 full pipeline =="
Write-Host "Working directory: $root"

Write-Host "`n[1/8] Check Python/R environment"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\00_check_environment.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\13_self_test_metrics.py

Write-Host "`n[2/8] Generate controlled simulation datasets"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\09_generate_simulated_benchmark.py

Write-Host "`n[3/8] Prepare processed datasets"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\02_prepare_dataset.py --input data\raw --output data\processed

if (-not $SkipMethods) {
    Write-Host "`n[4/8] Run Scrublet"
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\03_run_scrublet.py --processed-dir data\processed --output-dir results\method_predictions

    Write-Host "`n[5/8] Run DoubletFinder"
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_r_env.ps1 scripts\04_run_doubletfinder.R data\processed results\method_predictions

    Write-Host "`n[6/8] Run scDblFinder"
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_r_env.ps1 scripts\05_run_scdblfinder.R data\processed results\method_predictions
} else {
    Write-Host "`n[4/8-6/8] Skipping method runs; using existing prediction files"
}

Write-Host "`n[7/8] Evaluate, plot, and run stratified analysis"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\06_evaluate_and_plot.py --processed-dir data\processed --pred-dir results\method_predictions --results-dir results --figures-dir figures
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\07_downstream_clustering.py --processed-dir data\processed --pred-dir results\method_predictions --figures-dir figures --dataset sim_easy_13pct
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\10_stratified_analysis.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\14_make_pipeline_diagram.py

Write-Host "`n[8/8] Build Word report, QC, and manifest"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\08_build_report_docx.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\11_quality_control.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_python_env.ps1 scripts\12_create_repro_manifest.py

Write-Host "`nPipeline complete."
Write-Host "Main report: report\miniproject7_3127_report.docx"
Write-Host "Metrics: results\benchmark_metrics.csv"
