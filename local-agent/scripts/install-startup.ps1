<#
Registra ControlHorarioBiometricAgent como tarea de inicio de sesion y lo inicia inmediatamente.
Usa Task Scheduler COM para conservar rutas con espacios en Windows 7 y versiones posteriores.
#>$ErrorActionPreference = "Stop"
$taskName = "ControlHorarioBiometricAgent"
$installDir = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $installDir "ControlHorarioBiometricAgent.exe"
$config = Join-Path $env:ProgramData "ControlHorarioBiometricAgent\appsettings.json"
$bridge = Join-Path $installDir "bridge\Zk9500Bridge.exe"

if (!(Test-Path $exe)) { throw "No existe $exe" }
if (!(Test-Path $config)) { throw "No existe $config" }
if (!(Test-Path $bridge)) { throw "No existe $bridge" }

$service = New-Object -ComObject "Schedule.Service"
$service.Connect()
$root = $service.GetFolder("\")
$definition = $service.NewTask(0)
$definition.RegistrationInfo.Description = "Inicia el agente biometrico local de Control Horario."
$definition.Settings.Enabled = $true
$definition.Settings.StartWhenAvailable = $true
$definition.Settings.DisallowStartIfOnBatteries = $false

$trigger = $definition.Triggers.Create(9)
$action = $definition.Actions.Create(0)
$action.Path = $exe
$action.WorkingDirectory = $installDir

$userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$definition.Principal.UserId = $userId
$definition.Principal.LogonType = 3
$definition.Principal.RunLevel = 0
$root.RegisterTaskDefinition($taskName, $definition, 6, $userId, $null, 3, $null) | Out-Null

Get-Process "ControlHorarioBiometricAgent" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1
Start-Process -FilePath $exe -WorkingDirectory $installDir -WindowStyle Hidden
