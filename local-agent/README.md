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
