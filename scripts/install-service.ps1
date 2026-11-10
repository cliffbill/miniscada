param(
    [Parameter(Mandatory = $true)]
    [string]$NssmPath
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Logs = Join-Path $ProjectRoot "logs"
$ConfigPath = Join-Path $ProjectRoot "config.json"

if (-not (Test-Path $Python)) {
    Write-Error "Falta el entorno .venv. En la carpeta del proyecto ejecuta: python -m venv .venv ; .\.venv\Scripts\python.exe -m pip install -r requirements.txt"
}
if (-not (Test-Path $NssmPath)) {
    Write-Error "No se encontró NSSM en $NssmPath. Descárgalo de https://nssm.cc/ y pasa la ruta de nssm.exe."
}

$cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$bind = $cfg.server.host
$port = $cfg.server.port
New-Item -ItemType Directory -Force -Path $Logs | Out-Null

& $NssmPath install MiniScada $Python
& $NssmPath set MiniScada AppDirectory $ProjectRoot
& $NssmPath set MiniScada AppParameters "-m uvicorn app.main:app --host $bind --port $port"
& $NssmPath set MiniScada AppStdout (Join-Path $Logs "service-stdout.log")
& $NssmPath set MiniScada AppStderr (Join-Path $Logs "service-stderr.log")
& $NssmPath set MiniScada AppRotateFiles 1
& $NssmPath set MiniScada AppRotateBytes 1000000
& $NssmPath set MiniScada Start SERVICE_AUTO_START
& $NssmPath set MiniScada AppExit Default Restart
& $NssmPath set MiniScada AppRestartDelay 5000

Write-Host "Servicio MiniScada instalado. Arranca con: nssm start MiniScada"
Write-Host "El servicio no abre el navegador. Para la pantalla de la línea usa scripts\start-kiosk.ps1 al iniciar sesión."
