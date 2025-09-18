# FILE: bootstrap.ps1
# Windows-friendly bootstrap for CLT–E8 AGI scaffold
# - Creates venv
# - Installs dependencies
# - Sets PYTHONPATH
# - Runs unit tests (tests/ only)
# - Executes deterministic smoke

param(
  [string]$PythonExe = "python"
)

Write-Host ">>> Creating virtual environment .venv" -ForegroundColor Cyan
& $PythonExe -m venv .venv
if ($LASTEXITCODE -ne 0) { throw "Failed to create venv" }

Write-Host ">>> Activating .venv" -ForegroundColor Cyan
$venvActivate = ".\.venv\Scripts\Activate.ps1"
. $venvActivate

Write-Host ">>> Upgrading pip (best-effort)" -ForegroundColor Cyan
try { python -m pip install --upgrade pip } catch { Write-Warning "pip upgrade skipped: $_" }

Write-Host ">>> Installing core requirements" -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host ">>> Installing runtime deps for GPT-OSS wrapper" -ForegroundColor Cyan
pip install openai python-dotenv

Write-Host ">>> Ensuring package layout" -ForegroundColor Cyan
if (!(Test-Path ".\src\__init__.py")) { New-Item ".\src\__init__.py" -ItemType File -Force | Out-Null }
if (!(Test-Path ".\src\memory\__init__.py")) { New-Item ".\src\memory\__init__.py" -ItemType File -Force | Out-Null }
if (!(Test-Path ".\src\models\__init__.py")) { New-Item ".\src\models\__init__.py" -ItemType File -Force | Out-Null }
if (!(Test-Path ".\src\utils\__init__.py")) { New-Item ".\src\utils\__init__.py" -ItemType File -Force | Out-Null }

Write-Host ">>> Setting PYTHONPATH=." -ForegroundColor Cyan
$env:PYTHONPATH = "."

Write-Host ">>> Cleaning stale caches (prevents import mismatches)" -ForegroundColor Cyan
Get-ChildItem -Path . -Include "__pycache__", "*.pyc" -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host ">>> Running unit tests (tests/ only)" -ForegroundColor Cyan
pytest -q
if ($LASTEXITCODE -ne 0) { throw "Unit tests failed" }

Write-Host ">>> Running deterministic smoke" -ForegroundColor Cyan
python run_smoke.py
if ($LASTEXITCODE -ne 0) { throw "Smoke test failed" }

Write-Host ">>> All green. You're ready to fly." -ForegroundColor Green
