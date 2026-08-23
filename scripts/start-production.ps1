$ErrorActionPreference = "Stop"

if (-not (Test-Path "backend\.env")) {
    throw "No existe backend\.env. Copie backend\.env.production.example a backend\.env y configure sus valores."
}

if (-not (Test-Path "frontend\dist\index.html")) {
    throw "No existe frontend\dist\index.html. Ejecute scripts\build-production.ps1 antes de iniciar produccion."
}

if (-not (Test-Path "backend\.venv\Scripts\python.exe")) {
    throw "No existe backend\.venv. Ejecute scripts\setup-windows.ps1 antes de iniciar produccion."
}

Write-Host "Iniciando Sistema de Control de Horarios en http://127.0.0.1:5000"
Push-Location backend
& ".venv\Scripts\python.exe" wsgi.py
Pop-Location
