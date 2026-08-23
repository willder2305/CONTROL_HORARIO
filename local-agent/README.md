# ControlHorarioBiometricAgent

Agente local para computadoras con lector ZKTeco ZK9500 conectado por USB.

Responsabilidad del agente:

- Escuchar solo en http://127.0.0.1:8765.
- Capturar huellas con el SDK/driver ZKTeco instalado en Windows.
- Descargar del backend los templates activos usando X-Agent-Token.
- Identificar localmente contra el ZK9500.
- Enviar al backend solo el huella_id identificado para registrar la marcacion.

## Archivos de configuracion

Copiar ppsettings.example.json como ppsettings.json y ajustar:

- ServerUrl: dominio HTTPS del sistema hospedado.
- AllowedOrigins: dominio del frontend hospedado.
- DeviceToken: mismo valor que BIOMETRIC_AGENT_TOKEN en el backend.
- BridgePath: ruta a Zk9500Bridge.exe con las DLL del SDK.

No subir ppsettings.json a Git.

## Endpoints locales

- GET /health
- GET /device/status
- POST /enroll
- POST /identify-and-mark

El navegador del punto de marcaje llama al agente local. El agente llama al backend hospedado.

## INSTALACION DEL EQUIPO DE MARCAJE

Para la computadora donde estara conectado el ZKTeco ZK9500:

1. Instalar el driver oficial de ZKTeco.
2. Instalar el runtime o SDK oficial ZKFinger si el driver no lo incluye.
3. Ejecutar `ControlHorarioBiometricAgent-Setup.exe`.
4. Seguir el asistente de instalacion.
5. Finalizar la instalacion.
6. Conectar el lector ZK9500 por USB.
7. Verificar que Windows detecte el dispositivo.
8. Abrir el dominio del sistema en Chrome o Edge.
9. Entrar a MARCAR y presionar MARCAR.

El usuario final no necesita abrir CMD, PowerShell, Visual Studio, Python, Node.js, XAMPP, MySQL, Git ni codigo fuente.

El instalador:

- instala en `C:\Program Files (x86)\ControlHorarioBiometricAgent\` porque el bridge y las DLL verificadas son x86;
- registra inicio automatico con una tarea programada de usuario al iniciar sesion;
- inicia el agente en segundo plano;
- no deja consola negra abierta;
- crea desinstalador en Aplicaciones instaladas de Windows;
- conserva `C:\ProgramData\ControlHorarioBiometricAgent\appsettings.json` si se instala una nueva version encima.

Configuracion editable sin recompilar:

`C:\ProgramData\ControlHorarioBiometricAgent\appsettings.json`

Ajustar ahi:

- `ServerUrl`
- `AllowedOrigins`
- `DeviceToken`

Logs:

`C:\ProgramData\ControlHorarioBiometricAgent\logs\agent.log`

No se deben registrar templates biometricos, huellas, tokens ni credenciales.

Nota sobre ZKTeco: no se encontro una licencia local clara que autorice redistribuir las DLL oficiales del SDK. Por eso el instalador no debe presentarse como reemplazo del driver/runtime oficial. Si `/device/status` indica que SDK o lector no estan disponibles, instalar el paquete oficial de ZKTeco y reconectar el ZK9500.
