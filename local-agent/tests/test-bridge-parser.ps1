param(
    [Parameter(Mandatory)]
    [string]$AgentPath
)

$ErrorActionPreference = 'Stop'

$fixture = @'
provider=zk9500
sdkLoaded=true
[BIOMETRIC] Provider: zk9500
[BIOMETRIC] Inicializando ZKFinger SDK 5.3.0.33
[BIOMETRIC] SDK inicializado
[BIOMETRIC] Dispositivos encontrados: 2
deviceCount=2
connected=true
Check sum data is true!sum=9304, buf[val]=9304
Check sum data is true!sum=-35, buf[val]=-35
opts->Stripe_Reference_Point_X=850 opts->Stripe_Reference_Point_Y=600
opened=true
ready=true
'@

$assembly = [Reflection.Assembly]::LoadFile((Resolve-Path -LiteralPath $AgentPath))
$program = $assembly.GetType('ControlHorarioBiometricAgent.Program', $true)
$flags = [Reflection.BindingFlags]'NonPublic, Static'
$parser = $program.GetMethod('ParseBridgeOutput', $flags)
$data = $parser.Invoke($null, @($fixture))

foreach ($expected in @{
    sdkLoaded = 'true'
    deviceCount = '2'
    connected = 'true'
    opened = 'true'
    ready = 'true'
}.GetEnumerator()) {
    if ($data[$expected.Key] -ne $expected.Value) {
        throw "Valor inesperado para $($expected.Key)."
    }
}

if ($data.ContainsKey('Check sum data is true!sum') -or $data.ContainsKey('opts->Stripe_Reference_Point_X')) {
    throw 'El parser acepto una linea nativa ajena al protocolo.'
}

Write-Host 'Parser del bridge: OK'
