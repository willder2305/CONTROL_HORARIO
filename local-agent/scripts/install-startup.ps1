$ErrorActionPreference = 'Stop'
$agentRoot = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $agentRoot 'bin\ControlHorarioBiometricAgent.exe'
if (!(Test-Path $exe)) { throw "No existe $exe. Compile el agente primero." }
$taskName = 'ControlHorarioBiometricAgent'
$action = New-ScheduledTaskAction -Execute $exe -WorkingDirectory (Join-Path $agentRoot 'bin')
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description 'Agente local ZKTeco ZK9500 para Control Horario' -Force
Write-Host "Tarea programada creada: $taskName"
