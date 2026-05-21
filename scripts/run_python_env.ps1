param(
    [Parameter(Mandatory = $true)]
    [string]$Script,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$EnvRoot = Join-Path $ProjectRoot ".conda_env"
$env:PYTHONIOENCODING = "utf-8"
$env:MPLBACKEND = "Agg"
$env:PATH = "$EnvRoot;$EnvRoot\Scripts;$EnvRoot\Library\bin;$env:PATH"

& "$EnvRoot\python.exe" $Script @Arguments
exit $LASTEXITCODE
