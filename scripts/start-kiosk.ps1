$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $ProjectRoot "config.json"
$cfg = Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
$port = $cfg.server.port
$health = "http://127.0.0.1:$port/health"
$page = "http://127.0.0.1:$port/"

$deadline = (Get-Date).AddMinutes(3)
$ready = $false
while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-WebRequest -Uri $health -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $ready) {
    Write-Error "La pantalla no respondió en $health"
}

$edge = Join-Path ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) {
    $edge = Join-Path $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"
}
if (-not (Test-Path $edge)) {
    Write-Error "No está instalado Microsoft Edge."
}

Start-Process $edge -ArgumentList @("--kiosk", $page, "--edge-kiosk-type=fullscreen", "--no-first-run")
