<#
Inicia ControlHorarioBiometricAgent en segundo plano para una estación de marcación local.
Requiere que el ejecutable y la configuración instalados en ProgramData existan; no modifica tareas de Windows.
#>$ErrorActionPreference = "Stop"
$agentRoot = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $agentRoot "ControlHorarioBiometricAgent.exe"
$config = Join-Path $env:ProgramData "ControlHorarioBiometricAgent\appsettings.json"
if (!(Test-Path $exe)) { throw "No existe $exe. Instale el agente primero." }
if (!(Test-Path $config)) { throw "No existe $config. Configure dominio y token." }
Start-Process -FilePath $exe -WorkingDirectory $agentRoot -WindowStyle Hidden
Write-Host "ControlHorarioBiometricAgent iniciado en segundo plano."
