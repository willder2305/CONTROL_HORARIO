$ErrorActionPreference = "Stop"

Write-Host "[1/4] Creando entorno virtual backend si no existe..."
if (-not (Test-Path "backend\.venv\Scripts\python.exe")) {
    py -3 -m venv backend\.venv
}

Write-Host "[2/4] Instalando dependencias Python..."
& "backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt

Write-Host "[3/4] Instalando dependencias frontend..."
Push-Location frontend
npm install
Pop-Location

Write-Host "[4/4] Verificacion basica completada."
Write-Host "Copie backend\.env.production.example a backend\.env y configure sus valores reales."
