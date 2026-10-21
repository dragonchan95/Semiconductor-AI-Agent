$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONUTF8 = '1'
$semiPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$semiSharedPython = Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'
if (Test-Path -LiteralPath $semiSharedPython) { $semiPython = $semiSharedPython }
if (-not (Test-Path -LiteralPath $semiPython)) {
    $semiUv = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
    if (Test-Path -LiteralPath $semiUv) {
        & $semiUv venv --python 3.11 .venv
        if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed.' }
        & $semiUv pip install --python $semiPython -r requirements.txt
    } else {
        & python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11 or newer, then run this file again.' }
        & $semiPython -m pip install -r requirements.txt
    }
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
Write-Host 'Open http://localhost:8700 in your browser. Keep this window open.'
& (Join-Path $PSScriptRoot 'scripts\start_local_qwen.ps1')
& $semiPython -m uvicorn app.api:app --host 127.0.0.1 --port 8700
