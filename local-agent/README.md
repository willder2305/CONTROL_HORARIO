# ControlHorarioBiometricAgent

Agente local para computadoras con lector ZKTeco ZK9500 conectado por USB.

Version actual: `1.0.5`.

Responsabilidad del agente:

- Escuchar solo en `http://127.0.0.1:8765`.
- Capturar huellas con el SDK/driver ZKTeco instalado en Windows.
- Descargar del backend los templates activos usando `X-Agent-Token`.
- Identificar localmente contra el ZK9500.
- Enviar al backend solo el `huella_id` identificado para registrar la marcacion.

## Configuracion de instalacion

El instalador preparado para un servidor hospedado deja la configuracion privada en:

`C:\ProgramData\ControlHorarioBiometricAgent\appsettings.json`

El archivo contiene el dominio, los origenes permitidos, el identificador del dispositivo y el token del agente. No debe subirse a Git, copiarse a equipos no autorizados ni compartirse.

Para preparar un instalador de una estacion concreta, usar:

```powershell
.\local-agent\scripts\build-installer.ps1 -ConfigPath 'C:\ProgramData\ControlHorarioBiometricAgent\appsettings.json'
```

El script compila el agente x86, incorpora el bridge ZK9500 con sus DLL requeridas y genera:

`output\biometric-agent\ControlHorarioBiometricAgent-Setup.exe`

## Endpoints locales

- GET /health
- GET /device/status
- GET /diagnostics
- POST /enroll
- POST /identify-and-mark

`GET /diagnostics` muestra un resumen seguro del agente: version, comunicacion
con el servidor, conteo de huellas reportadas y procesadas, ruta y SHA256 del
bridge, codigo de salida, longitudes de salida y estado del lector. No expone
templates, tokens ni credenciales.

El navegador del punto de marcaje llama al agente local. El agente llama al backend hospedado.

## Instalacion del equipo de marcaje

Para la computadora donde estara conectado el ZKTeco ZK9500:

1. Instalar el driver oficial del ZK9500 incluido con ZKFinger SDK for Windows.
2. Conectar el lector ZK9500 por USB y comprobar que Windows lo reconoce.
3. Ejecutar `ControlHorarioBiometricAgent-Setup.exe` como administrador.
4. Finalizar el asistente. El agente queda iniciado y se inicia automaticamente al entrar en Windows.
5. Abrir el dominio del sistema en Chrome o Edge, entrar a MARCAR y presionar MARCAR.

El usuario final no necesita abrir CMD, PowerShell, Visual Studio, Python, Node.js, XAMPP, MySQL, Git ni codigo fuente.

El instalador:

- instala en `C:\Program Files (x86)\ControlHorarioBiometricAgent\` porque el bridge y las DLL verificadas son x86;
- incluye `Zk9500Bridge.exe` y sus DLL de ejecucion requeridas;
- registra inicio automatico en Windows para cada inicio de sesion;
- inicia el agente en segundo plano;
- no deja consola negra abierta;
- crea desinstalador en Aplicaciones instaladas de Windows;
- conserva `C:\ProgramData\ControlHorarioBiometricAgent\appsettings.json` si se instala una nueva version encima.
- cierra una instancia anterior antes de actualizar los ejecutables y DLL, e inicia una unica instancia nueva.

Configuracion editable sin recompilar:

`C:\ProgramData\ControlHorarioBiometricAgent\appsettings.json`

Solo personal autorizado debe modificar:

- `ServerUrl`
- `AllowedOrigins`
- `DeviceToken`

Logs:

`C:\ProgramData\ControlHorarioBiometricAgent\logs\agent.log`

No se deben registrar templates biometricos, huellas, tokens ni credenciales.

El instalador no sustituye el driver USB oficial de ZKTeco. Si `/device/status` indica que SDK o lector no estan disponibles, reinstalar el paquete oficial de ZKTeco y reconectar el ZK9500.
