$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = if ($env:PYTHON) { $env:PYTHON } else { "python" }

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name UnityAssetClassifier `
  --icon "assets\unity-asset-classifier-icon.ico" `
  --add-data "webui;webui" `
  local_app\launcher.py `
  --distpath dist `
  --workpath build

Write-Host "Built dist\UnityAssetClassifier.exe"
