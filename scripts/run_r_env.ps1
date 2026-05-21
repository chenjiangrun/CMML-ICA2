param(
    [Parameter(Mandatory = $true)]
    [string]$Script,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$env:R_LIBS_USER = "C:\Rlibs"
$env:R_LIBS = "C:\Rlibs"
$Rscript = "C:\Program Files\R\R-4.6.0\bin\Rscript.exe"

& $Rscript $Script @Arguments
exit $LASTEXITCODE
