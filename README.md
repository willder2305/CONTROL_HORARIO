# Sistema de Control de Horarios

Sistema web para administrar trabajadores, horarios, huellas digitales, marcaciones, reportes, auditoria y control biometrico con lector ZKTeco ZK9500.

Esta rama deploy-ready esta preparada para despliegue con backend/frontend en hosting y lector biometrico operando mediante un agente local instalado solo en la computadora donde esta conectado el ZK9500.

## Arquitectura final

`	ext
Usuario administrador o punto de marcaje
        |
        v
Dominio HTTPS del sistema
        |
        v
Frontend React + API Flask hospedados
        |
        v
Base de datos MySQL del hosting

Computadora local con ZK9500
        |
        v
ControlHorarioBiometricAgent http://127.0.0.1:8765
        |
        v
Zk9500Bridge.exe + SDK/driver ZKTeco
        |
        v
Lector ZKTeco ZK9500 USB
`

El backend hospedado no abre USB ni carga DLL del lector. La captura e identificacion real se hacen en la computadora local mediante ControlHorarioBiometricAgent.

## Componentes

### Servidor / hosting

Contiene:

- Backend Flask.
- Frontend React compilado.
- Base de datos MySQL.
- Templates biometricos activos.
- Endpoint protegido para agente local.

No necesita:

- Lector USB conectado.
- Driver ZKTeco.
- SDK ZKFinger instalado.
- DLL locales del lector.

### Computadora de marcaje

Contiene:

- Navegador web.
- Driver oficial ZKTeco del ZK9500.
- SDK/runtime ZKFinger requerido por el bridge.
- ControlHorarioBiometricAgent.exe.
- Zk9500Bridge.exe y DLL del SDK.
- Lector ZKTeco ZK9500 conectado por USB.

No necesita:

- Python.
- Node.js.
- Git.
- MySQL/XAMPP.
- Codigo fuente del backend o frontend.
- Visual Studio.

## Flujo biometrico

### Registro de huella

1. El administrador crea o edita un trabajador desde el dominio del sistema.
2. El navegador llama al agente local en http://127.0.0.1:8765/enroll.
3. El agente captura 3 muestras con el ZK9500.
4. El agente devuelve el template capturado al frontend.
5. El frontend envia el template al backend autenticado.
6. El backend guarda el template en MySQL y reemplaza la huella activa anterior si existe.

### Marcacion

1. El trabajador presiona MARCAR en el navegador.
2. El navegador llama al agente local en http://127.0.0.1:8765/identify-and-mark.
3. El agente descarga templates activos desde /api/agent/fingerprints usando X-Agent-Token.
4. El agente identifica localmente contra el ZK9500.
5. El agente envia al backend solo el huella_id identificado.
6. El backend registra automaticamente entrada, salida de almuerzo, regreso o salida segun la jornada.

## Variables de backend

Copiar ackend/.env.production.example como .env en el servidor y ajustar:

`nv
SECRET_KEY=CAMBIAR_POR_UN_VALOR_LARGO_Y_ALEATORIO
DATABASE_URL=mysql+pymysql://usuario:password@localhost:3306/horarios_control
APP_URL=https://control.midominio.com
CORS_ORIGINS=https://control.midominio.com
FINGERPRINT_PROVIDER=local_agent
BIOMETRIC_AGENT_TOKEN=CAMBIAR_TOKEN_DEL_AGENTE
SESSION_COOKIE_SECURE=true
FLASK_APP=wsgi.py
FLASK_DEBUG=0
`

BIOMETRIC_AGENT_TOKEN debe ser largo, privado y debe coincidir con DeviceToken en local-agent/appsettings.json.

## Variables de frontend

Para hosting normal:

`nv
VITE_API_URL=/api
VITE_BIOMETRIC_MODE=local-agent
VITE_BIOMETRIC_AGENT_URL=http://127.0.0.1:8765
`

En desarrollo local puede usarse:

`nv
VITE_API_URL=http://localhost:5000/api
`

## Endpoint protegido del agente

Rutas del backend bajo /api/agent:

- GET /health
- GET /fingerprints
- POST /marcaciones

Todas requieren header:

`http
X-Agent-Token: <BIOMETRIC_AGENT_TOKEN>
`

/api/agent/fingerprints exporta solo id, 	emplate, provider y ersion de huellas activas de trabajadores activos. No exporta nombre, apellido, codigo ni datos administrativos.

## Agente local

Archivos principales:

- local-agent/src/ControlHorarioBiometricAgent.cs
- local-agent/bin/ControlHorarioBiometricAgent.exe
- local-agent/appsettings.example.json
- local-agent/scripts/start-agent.ps1
- local-agent/scripts/install-startup.ps1

Configurar en la computadora con lector:

1. Copiar local-agent/appsettings.example.json como local-agent/appsettings.json.
2. Ajustar ServerUrl al dominio HTTPS real.
3. Ajustar AllowedOrigins al dominio HTTPS real.
4. Ajustar DeviceToken con el mismo valor de BIOMETRIC_AGENT_TOKEN.
5. Confirmar BridgePath hacia Zk9500Bridge.exe.
6. Ejecutar local-agent/scripts/start-agent.ps1.
7. Probar http://127.0.0.1:8765/health.

El agente escucha solo en loopback. No debe exponerse a la red local.

## Comandos de desarrollo

Backend:

`powershell
cd backend
.\.venv\Scripts\python.exe -m flask --app run.py db upgrade
.\.venv\Scripts\python.exe run.py
`

Frontend:

`powershell
cd frontend
npm.cmd install
npm.cmd run dev
`

Build frontend:

`powershell
cd frontend
npm.cmd run build
`

Pruebas backend:

`cmd
cd backend
set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1&& .venv\Scripts\python.exe -m pytest tests -q
`

Compilar agente local:

`powershell
& 'C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe' /nologo /target:exe /out:local-agent\bin\ControlHorarioBiometricAgent.exe /reference:System.Web.Extensions.dll local-agent\src\ControlHorarioBiometricAgent.cs
`

## Despliegue en hosting

1. Crear base de datos MySQL horarios_control.
2. Configurar .env del backend con dominio, credenciales y token de agente.
3. Instalar dependencias backend.
4. Ejecutar migraciones.
5. Compilar frontend con VITE_BIOMETRIC_MODE=local-agent.
6. Servir Flask con Waitress o servidor WSGI equivalente detras de HTTPS.
7. Configurar proxy del dominio hacia el backend.
8. Verificar /api/health desde el dominio.
9. Instalar el agente solo en la computadora del lector.

## Seguridad operativa

- No subir .env ni local-agent/appsettings.json.
- Usar HTTPS obligatorio en produccion.
- Rotar BIOMETRIC_AGENT_TOKEN si se comparte por error.
- Mantener el agente en 127.0.0.1.
- No exponer puertos del agente en firewall.
- El frontend no conoce el token del agente.
- El token solo vive en backend .env y en local-agent/appsettings.json.

## Validaciones realizadas

- Backend Python compila.
- Frontend React compila.
- Agente C# compila.
- Agente responde GET /health en 127.0.0.1:8765.
- Suite backend: 70 pruebas pasan.

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
