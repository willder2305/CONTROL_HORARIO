$ErrorActionPreference = "Stop"

Write-Host "[1/2] Instalando dependencias frontend..."
Push-Location frontend
npm install

Write-Host "[2/2] Compilando frontend..."
npm run build
Pop-Location

Write-Host "Build de produccion generado en frontend\dist."
