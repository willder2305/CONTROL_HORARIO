<#
Genera un instalador de estacion biometrica listo para un dominio desplegado.
La configuracion privada se lee desde un archivo local y se elimina del area de compilacion al terminar.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$ConfigPath
)

$ErrorActionPreference = "Stop"
$agentRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $agentRoot
$runtimeDir = Join-Path $agentRoot "runtime"
$runtimeConfig = Join-Path $runtimeDir "appsettings.json"
$source = Join-Path $agentRoot "src\ControlHorarioBiometricAgent.cs"
$agentBinary = Join-Path $agentRoot "bin\ControlHorarioBiometricAgent.exe"
$bridgeSource = Join-Path $projectRoot "backend\zk9500_bridge\Zk9500Bridge.cs"
$installerSource = Join-Path $agentRoot "installer\ControlHorarioBiometricAgent.iss"
$bridgeRuntime = Join-Path $projectRoot "backend\zk9500_bridge\bin"
$bridgeBinary = Join-Path $bridgeRuntime "Zk9500Bridge.exe"
$bridgeReference = Join-Path $bridgeRuntime "libzkfpcsharp.dll"
$output = Join-Path $projectRoot "output\biometric-agent\ControlHorarioBiometricAgent-Setup.exe"

if (!(Test-Path -LiteralPath $ConfigPath)) { throw "No existe el archivo de configuracion indicado." }
if (!(Test-Path -LiteralPath $bridgeRuntime)) { throw "No existe el runtime del bridge ZK9500." }
if (!(Test-Path -LiteralPath $bridgeSource)) { throw "No existe el codigo fuente del bridge ZK9500." }

$config = Get-Content -Raw -LiteralPath $ConfigPath | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($config.DeviceToken)) { throw "DeviceToken es obligatorio." }
if ($config.ServerUrl -notmatch '^https://') { throw "ServerUrl debe utilizar HTTPS." }
if (!$config.AllowedOrigins -or @($config.AllowedOrigins).Count -eq 0) { throw "AllowedOrigins es obligatorio." }
if (@($config.AllowedOrigins | Where-Object { $_ -notmatch '^https://' }).Count -gt 0) {
    throw "Todos los AllowedOrigins deben utilizar HTTPS."
}

# El agente se comunica con el bridge instalado en la misma estacion.
$config.BridgePath = "bridge\\Zk9500Bridge.exe"
$config.ListenUrl = "http://127.0.0.1:8765/"

$requiredBridgeFiles = @("Zk9500Bridge.exe", "libzkfpcsharp.dll", "libzkfp.dll")
foreach ($file in $requiredBridgeFiles) {
    if (!(Test-Path -LiteralPath (Join-Path $bridgeRuntime $file))) {
        throw "Falta $file en el runtime del bridge."
    }
}

$cscCandidates = @(
    (Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe"),
    (Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe")
)
$csc = $cscCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (!$csc) { throw "No se encontro el compilador C# de .NET Framework." }

$isccCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:USERPROFILE "AppData\Local\Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
)
$iscc = $isccCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (!$iscc) { throw "No se encontro Inno Setup 6. Instale Inno Setup antes de compilar." }

$previousRuntimeConfig = $null
if (Test-Path -LiteralPath $runtimeConfig) {
    $previousRuntimeConfig = [System.IO.File]::ReadAllBytes($runtimeConfig)
}

New-Item -ItemType Directory -Path (Split-Path -Parent $agentBinary), $runtimeDir, (Split-Path -Parent $output) -Force | Out-Null

try {
    & $csc /nologo /target:exe /platform:x86 "/out:$bridgeBinary" "/reference:$bridgeReference" $bridgeSource
    if ($LASTEXITCODE -ne 0) { throw "No se pudo compilar Zk9500Bridge.exe." }

    & $csc /nologo /target:exe /platform:x86 "/out:$agentBinary" /reference:System.Web.Extensions.dll $source
    if ($LASTEXITCODE -ne 0) { throw "No se pudo compilar ControlHorarioBiometricAgent.exe." }

    $configJson = $config | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText(
        $runtimeConfig,
        $configJson,
        (New-Object System.Text.UTF8Encoding($false))
    )
    & $iscc $installerSource
    if ($LASTEXITCODE -ne 0) { throw "No se pudo compilar ControlHorarioBiometricAgent-Setup.exe." }
}
finally {
    if ($null -ne $previousRuntimeConfig) {
        [System.IO.File]::WriteAllBytes($runtimeConfig, $previousRuntimeConfig)
    }
    elseif (Test-Path -LiteralPath $runtimeConfig) {
        Remove-Item -LiteralPath $runtimeConfig -Force
    }
}

if (!(Test-Path -LiteralPath $output)) { throw "El instalador no fue generado." }
Write-Host "Instalador generado: $output"
