$ErrorActionPreference = "SilentlyContinue"
$taskName = "ControlHorarioBiometricAgent"
Get-Process ControlHorarioBiometricAgent | Stop-Process -Force
& schtasks.exe /Delete /TN $taskName /F | Out-Null
