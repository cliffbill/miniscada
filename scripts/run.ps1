$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "Falta .venv. En la carpeta MiniScada ejecuta: python -m venv .venv ; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}
& $Python -m uvicorn app.main:app --host 127.0.0.1 --port 8080
