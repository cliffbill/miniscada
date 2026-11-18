$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
& $Python -m PyInstaller (Join-Path $Root "MiniScada.spec") --noconfirm

$Out = Join-Path $Root "dist\MiniScada"
New-Item -ItemType Directory -Force -Path (Join-Path $Out "scripts") | Out-Null

& $Python -c @"
import json
from pathlib import Path
src = Path(r'$Root') / 'config.json'
dst = Path(r'$Out') / 'config.json'
data = json.loads(src.read_text(encoding='utf-8'))
data['demo'] = False
dst.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
"@

Copy-Item (Join-Path $Root "scripts\start-kiosk.ps1") (Join-Path $Out "scripts\start-kiosk.ps1") -Force
Copy-Item (Join-Path $Root "INSTALACION.md") (Join-Path $Out "INSTALACION.md") -Force
Write-Host "Listo: $Out"
