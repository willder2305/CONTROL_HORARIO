$ErrorActionPreference = "Stop"
$taskName = "ControlHorarioBiometricAgent"
$installDir = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $installDir "ControlHorarioBiometricAgent.exe"
if (!(Test-Path $exe)) { throw "No existe $exe" }
& schtasks.exe /Create /TN $taskName /TR "`"$exe`"" /SC ONLOGON /RL LIMITED /F | Out-Null
Start-Process -FilePath $exe -WorkingDirectory $installDir -WindowStyle Hidden
