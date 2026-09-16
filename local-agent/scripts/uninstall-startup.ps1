<#
Detiene ControlHorarioBiometricAgent y elimina su tarea programada de inicio de sesión.
No elimina archivos de configuración ni datos del backend.
#>$ErrorActionPreference = "SilentlyContinue"
$taskName = "ControlHorarioBiometricAgent"
Get-Process ControlHorarioBiometricAgent | Stop-Process -Force
& schtasks.exe /Delete /TN $taskName /F | Out-Null
