# Sistema de control de horarios para farmacia

Sistema web para control de horarios de trabajadores mediante huella digital.

Stack:

- Backend: Python Flask, SQLAlchemy, Flask-Migrate, MySQL/PyMySQL.
- Frontend: React, Vite, React Router, Axios.
- Reportes: Excel con `openpyxl`, PDF con `ReportLab`.
- Biometria: proveedor `mock` para desarrollo y proveedor real preparado para ZKTeco ZK9500.

## Estado funcional

Implementado hasta FASE 20:

- Login administrativo con sesion Flask.
- CRUD de trabajadores.
- Activar y desactivar trabajadores.
- Registro y reemplazo de huella.
- Plantillas de horario.
- Asignacion individual de horarios con historial.
- Marcacion publica por huella.
- Validacion de secuencia:
  - `ENTRADA`
  - `SALIDA_ALMUERZO`
  - `REGRESO_ALMUERZO`
  - `SALIDA`
- Hora oficial tomada solo desde backend en zona `America/Guatemala`.
- Calculo de puntualidad, tardanzas y salidas anticipadas.
- Panel de marcaciones.
- Dashboard administrativo.
- Reportes en pantalla.
- Descarga Excel.
- Descarga PDF.
- Auditoria administrativa.
- Capa real para lector ZKTeco ZK9500.
- Seguridad basica: cookies `HttpOnly`, `SameSite=Lax`, CSRF y cabeceras defensivas.
- Pruebas integrales.

## Estructura

```text
backend/
  app/
    models/
    routes/
    services/
    utils/
  migrations/
  tests/
  config.py
  requirements.txt
  run.py

frontend/
  src/
    components/
    pages/
    router/
    services/
    styles.css
```

## Requisitos

- Windows 10 64 bits recomendado.
- XAMPP con MySQL en puerto `3306`.
- Python 3.12 o compatible.
- Node.js y npm.
- Para lector real: ZKTeco ZK9500, ZKFinger SDK for Windows y driver oficial instalado.

## Base de datos MySQL

Crear la base en MySQL/XAMPP:

```sql
CREATE DATABASE horarios_control CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Conexion esperada para XAMPP:

```env
DATABASE_URL=mysql+pymysql://root:@localhost:3306/horarios_control
```

Si tu XAMPP tiene password para `root`, ajusta la URL:

```env
DATABASE_URL=mysql+pymysql://root:TU_PASSWORD@localhost:3306/horarios_control
```

## Configuracion backend

Desde `C:\dev\horarios_control\backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Variables principales en `backend\.env`:

```env
SECRET_KEY=change-this-secret
DATABASE_URL=mysql+pymysql://root:@localhost:3306/horarios_control
CORS_ORIGINS=http://localhost:5173
FLASK_APP=run.py
FLASK_DEBUG=1
FINGERPRINT_PROVIDER=mock
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_NAME=horarios_session
MAX_CONTENT_LENGTH=2097152
CSRF_PROTECT=true
```

En produccion:

- Cambiar `SECRET_KEY`.
- Usar HTTPS.
- Cambiar `SESSION_COOKIE_SECURE=true`.
- Restringir `CORS_ORIGINS` al dominio real.

## Migraciones

Desde `C:\dev\horarios_control\backend`:

```powershell
.\.venv\Scripts\python.exe -m flask --app run.py db upgrade
```

La migracion inicial crea:

- `administradores`
- `trabajadores`
- `plantillas_horario`
- `horarios_trabajadores`
- `huellas`
- `marcaciones`
- `auditoria`

## Datos iniciales

Crear plantillas base:

```powershell
.\.venv\Scripts\python.exe -m flask --app run.py seed-horarios
```

Crear administrador:

```powershell
.\.venv\Scripts\python.exe -m flask --app run.py crear-admin
```

El comando solicita la contrasena por consola y guarda hash seguro, no texto plano.

## Ejecutar backend

Desde `C:\dev\horarios_control`:

```powershell
backend\.venv\Scripts\python.exe backend\run.py
```

Salud:

```text
GET http://127.0.0.1:5000/api/health
```

Respuesta esperada:

```json
{"status":"ok"}
```

## Configuracion frontend

Desde `C:\dev\horarios_control\frontend`:

```powershell
npm install
copy .env.example .env
```

Variable principal:

```env
VITE_API_URL=http://localhost:5000/api
```

Ejecutar:

```powershell
npm run dev -- --host 127.0.0.1 --port 5173
```

Abrir:

```text
http://127.0.0.1:5173
```

Build:

```powershell
npm run build
```

## Rutas principales

Frontend:

- `/`
- `/marcar`
- `/admin/login`
- `/admin`
- `/admin/trabajadores`
- `/admin/horarios`
- `/admin/marcaciones`
- `/admin/reportes`

API:

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `GET|POST|PUT|PATCH /api/admin/trabajadores`
- `GET|POST|PUT|PATCH /api/admin/horarios`
- `GET /api/admin/marcaciones`
- `GET /api/admin/marcaciones/dashboard`
- `GET /api/admin/reportes`
- `GET /api/admin/reportes/excel`
- `GET /api/admin/reportes/pdf`
- `POST /api/biometria/trabajadores/<id>/registrar`
- `POST /api/biometria/identificar`
- `POST /api/marcaciones/biometrica`

## Flujo trabajador

La pantalla publica `/marcar` no solicita usuario, password, codigo, nombre ni ID.

Flujo:

1. Trabajador selecciona tipo de marcacion.
2. Sistema solicita huella.
3. Backend identifica trabajador por huella.
4. Backend toma la hora oficial del servidor.
5. Backend consulta horario individual vigente.
6. Backend valida secuencia y duplicados.
7. Backend calcula estado y minutos.
8. Backend guarda marcacion.

React no debe enviar:

- `trabajador_id`
- `fecha`
- `hora`
- `estado`
- `minutos_diferencia`

Si esos campos se envian manualmente, el backend los ignora.

## Biometria

### Modo desarrollo

```env
FINGERPRINT_PROVIDER=mock
```

En modo mock se usa un identificador como `FP0001`.

### Modo lector real ZKTeco ZK9500

Datos esperados:

- Marca: ZKTeco.
- Modelo: ZK9500.
- Sistema principal: Windows 10 64 bits.
- Compatibilidad secundaria: Windows 7 y Windows XP.
- SDK: ZKFinger SDK for Windows.
- Driver: incluido en ZKFinger SDK for Windows.
- Conexion: USB 2.0, compatible USB 1.1, USB Type-A.
- Algoritmo: ZKFinger V10.0.
- Resolucion: 500 dpi.
- Imagen: 300 x 400 px.

Config:

```env
FINGERPRINT_PROVIDER=real
ZKTECO_DEVICE_INDEX=0
ZKTECO_CAPTURE_TIMEOUT_SECONDS=15
ZKTECO_ENROLL_SAMPLES=3
ZKTECO_MATCH_THRESHOLD=1
```

Requisitos antes de activar `real`:

1. Instalar driver oficial.
2. Instalar ZKFinger SDK for Windows.
3. Verificar que Windows reconoce el lector.
4. Exponer un wrapper Python compatible con `ZKFP2`.

Si falta SDK, driver o lector, la API responde:

```json
{
  "success": false,
  "code": "LECTOR_NO_DISPONIBLE"
}
```

## Reportes

Pantalla:

```text
/admin/reportes
```

Formatos:

- Excel: `GET /api/admin/reportes/excel`
- PDF: `GET /api/admin/reportes/pdf`

Ambos respetan filtros:

- Trabajador.
- Tipo de marcacion.
- Estado.
- Fecha.
- Desde.
- Hasta.

## Auditoria

Se registran acciones administrativas en `auditoria`:

- `CREAR_TRABAJADOR`
- `EDITAR_TRABAJADOR`
- `ACTIVAR_TRABAJADOR`
- `DESACTIVAR_TRABAJADOR`
- `ASIGNAR_HORARIO`
- `MODIFICAR_HORARIO`
- `REGISTRAR_HUELLA`
- `REEMPLAZAR_HUELLA`

Cada registro guarda administrador, entidad, entidad_id, descripcion, fecha_hora e IP.

## Seguridad

Medidas implementadas:

- Passwords con hash.
- Sesion Flask.
- Cookie `HttpOnly`.
- Cookie `SameSite=Lax`.
- CSRF por sesion para mutaciones administrativas.
- Cabeceras:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `Cache-Control: no-store`
- CORS restringido por `CORS_ORIGINS`.
- Templates biometricos no se devuelven en APIs normales.
- Hora oficial tomada solo en backend.

Pendiente para produccion real:

- HTTPS.
- `SESSION_COOKIE_SECURE=true`.
- Rotacion segura de `SECRET_KEY`.
- Politica de backup automatizado.
- Hardening del servidor web usado para despliegue.

## Pruebas

El proyecto no usa `pytest` instalado. Se ejecuta con runner directo:

```powershell
backend\.venv\Scripts\python.exe -B -c "import sys, importlib.util; from pathlib import Path; sys.path.insert(0, 'backend'); total=0; failures=[]; base=Path('backend/tests');\nfor path in sorted(base.glob('test_*.py')):\n    spec=importlib.util.spec_from_file_location(path.stem, path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)\n    for name in sorted(n for n in dir(mod) if n.startswith('test_')):\n        total += 1\n        try:\n            getattr(mod, name)()\n        except Exception as exc:\n            failures.append((path.name, name, repr(exc)))\nif failures:\n    print('failures:')\n    [print(f'{file}::{name} {err}') for file,name,err in failures]\n    raise SystemExit(1)\nprint(f'{total} tests ok')"
```

Pruebas cubiertas:

- Salud API.
- Modelos.
- Autenticacion.
- Trabajadores.
- Horarios.
- Biometria mock.
- Secuencia de marcaciones.
- Puntualidad.
- Registro completo.
- Panel de marcaciones.
- Dashboard.
- Reportes pantalla.
- Excel.
- PDF.
- Auditoria.
- Proveedor real ZK9500 con SDK falso.
- Seguridad CSRF.
- Pruebas integrales.

## Backups

Backup manual con XAMPP:

```powershell
C:\xampp\mysql\bin\mysqldump.exe -u root horarios_control > C:\backups\horarios_control.sql
```

Si MySQL root tiene password:

```powershell
C:\xampp\mysql\bin\mysqldump.exe -u root -p horarios_control > C:\backups\horarios_control.sql
```

Restaurar:

```powershell
C:\xampp\mysql\bin\mysql.exe -u root horarios_control < C:\backups\horarios_control.sql
```

Recomendacion operativa:

- Backup diario de MySQL.
- Copia externa semanal.
- Probar restauracion periodicamente.
- Respaldar tambien `.env` de produccion fuera del repositorio.

## Revision final FASE 20

Checklist revisado:

- Backend Flask modular.
- Frontend React modular.
- Base de datos MySQL documentada.
- Migracion inicial disponible.
- Horarios individuales e historial.
- Secuencia obligatoria.
- Marcacion por huella.
- Reportes Excel y PDF.
- Auditoria administrativa.
- Seguridad base.
- Integracion biometrica desacoplada.
- Pruebas integrales.

No se avanza a FASE 21 desde esta fase.

## PRUEBA LOCAL CON ZK9500

Arquitectura local de validacion:

- Backend Flask: `http://127.0.0.1:5000`
- Frontend React: `http://127.0.0.1:5173`
- ControlHorarioBiometricAgent: `http://127.0.0.1:8765`
- MySQL local
- ZKTeco ZK9500 por USB

Orden de inicio:

1. Iniciar MySQL.
2. Iniciar backend Flask en `http://127.0.0.1:5000`.
3. Iniciar frontend React en `http://127.0.0.1:5173`.
4. Iniciar `ControlHorarioBiometricAgent`.
5. Conectar el ZKTeco ZK9500.
6. Comprobar `GET http://127.0.0.1:8765/health`.
7. Comprobar `GET http://127.0.0.1:8765/device/status`.
8. Abrir el sistema local.
9. Registrar huella real.
10. Probar marcacion automatica.

Variables locales esperadas:

Frontend `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:5000/api
VITE_BIOMETRIC_MODE=local-agent
VITE_BIOMETRIC_AGENT_URL=http://127.0.0.1:8765
```

Backend `backend/.env`:

```env
FINGERPRINT_PROVIDER=local_agent
BIOMETRIC_AGENT_TOKEN=local-agent-dev-token
APP_URL=http://127.0.0.1:5000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Agente `local-agent/appsettings.json` o `local-agent/appsettings.example.json`:

```json
{
  "ListenUrl": "http://127.0.0.1:8765/",
  "ServerUrl": "http://127.0.0.1:5000",
  "AllowedOrigins": ["http://localhost:5173", "http://127.0.0.1:5173"],
  "DeviceToken": "local-agent-dev-token",
  "BridgePath": "..\..\backend\zk9500_bridge\bin\Zk9500Bridge.exe"
}
```

El agente solo debe escuchar en `127.0.0.1`. No usar `0.0.0.0`.

Estados esperados:

- `/health` confirma que el agente esta vivo.
- `/device/status` confirma si el SDK y ZK9500 estan realmente disponibles.
- Si `/health` falla: iniciar o instalar Control Horario Biometric Agent.
- Si `/health` responde pero `connected=false`: conectar el ZKTeco ZK9500.
- Si `sdkLoaded=false`: instalar driver/runtime oficial ZKTeco.

Pruebas fisicas pendientes para ejecutar con el lector:

1. Conectar ZK9500.
2. Abrir `/device/status` y confirmar `connected=true` y `ready=true`.
3. Crear trabajador desde el panel administrativo.
4. Registrar huella con tres capturas reales del mismo dedo.
5. Confirmar que el trabajador queda activo y con huella registrada.
6. Abrir `/marcar`.
7. Presionar MARCAR.
8. Colocar el mismo dedo.
9. Confirmar identificacion del trabajador correcto.
10. Confirmar que el backend registra automaticamente Entrada.
11. Repetir marcacion y confirmar la siguiente funcion segun el horario.
12. Probar dedo no registrado y confirmar que no crea marcacion.
13. Cerrar el agente y confirmar mensaje de servicio biometrico no disponible.
14. Apagar backend con agente activo y confirmar mensaje de no conexion con el sistema.

Esta rama `uso-local` es para prueba local. No requiere dominio ni HTTPS local.
