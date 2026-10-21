$ErrorActionPreference = 'Stop'
$semiRoot = Split-Path -Parent $PSScriptRoot
$semiOllama = Join-Path $semiRoot 'var\runtime\ollama\ollama.exe'
if (-not (Test-Path -LiteralPath $semiOllama)) { return }
try {
    $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2
    return
} catch {}
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_MODELS = Join-Path $semiRoot 'var\qwen-models'
$env:OLLAMA_NO_CLOUD = '1'
$env:OLLAMA_MAX_LOADED_MODELS = '1'
$env:OLLAMA_NUM_PARALLEL = '1'
$env:OLLAMA_CONTEXT_LENGTH = '4096'
Start-Process -FilePath $semiOllama -ArgumentList 'serve' -WindowStyle Hidden -WorkingDirectory $semiRoot
