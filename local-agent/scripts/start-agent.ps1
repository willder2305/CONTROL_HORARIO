$ErrorActionPreference = 'Stop'
$agentRoot = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $agentRoot 'bin\ControlHorarioBiometricAgent.exe'
$config = Join-Path $agentRoot 'appsettings.json'
if (!(Test-Path $exe)) { throw "No existe $exe. Compile el agente primero." }
if (!(Test-Path $config)) { throw "No existe $config. Copie appsettings.example.json como appsettings.json y configure el dominio/token." }
Start-Process -FilePath $exe -WorkingDirectory (Join-Path $agentRoot 'bin') -WindowStyle Hidden
Write-Host 'ControlHorarioBiometricAgent iniciado en http://127.0.0.1:8765'
