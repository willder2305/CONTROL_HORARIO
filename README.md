# Sistema de Control de Horarios

Sistema web para administrar trabajadores, horarios, huellas digitales, marcaciones, reportes, auditoria y control biometrico con lector ZKTeco ZK9500.

El sistema esta preparado para uso local en farmacia y para despliegue en una computadora Windows con MySQL y lector biometrico conectado por USB.

## Caracteristicas

- Panel administrativo con inicio de sesion.
- Gestion de trabajadores activos/inactivos.
- Registro obligatorio de huella al crear trabajadores en modo biometrico real.
- Integracion con lector ZKTeco ZK9500.
- Captura de 3 muestras para registro de huella.
- Validacion de duplicados biometricos.
- Asignacion de horarios con o sin almuerzo.
- Marcacion automatica del trabajador: el trabajador solo presiona `MARCAR`.
- El backend determina la siguiente marcacion segun horario y jornada.
- Control de entrada, salida de almuerzo, entrada de almuerzo y salida.
- Reportes administrativos con filtros.
- Exportacion a Excel y PDF.
- Dashboard de marcaciones.
- Auditoria de acciones administrativas.
- Proteccion CSRF en rutas administrativas.
- Sesiones con cookies HttpOnly.
- Preparado para produccion con Waitress.
- Frontend React compilado servido por Flask en produccion.

## Arquitectura

```text
React + Vite
     ↓
Flask
     ↓
MySQL

ZKTeco ZK9500
     ↓
Driver oficial ZKTeco / FPSensor
     ↓
ZKFinger Standard SDK 5.3.0.33
     ↓
Bridge C# compilado
     ↓
Backend Flask
     ↓
Sistema de marcacion
```

En desarrollo se puede ejecutar frontend y backend por separado.

En produccion se recomienda:

```text
Usuario
  ↓
Waitress + Flask http://127.0.0.1:5000
  ├── React compilado desde frontend/dist
  └── API bajo /api
```

## Requisitos

### Desarrollo

- Git.
- Python 3.12 probado en el equipo actual.
- Node.js y npm para compilar frontend.
- MySQL Server o XAMPP/MariaDB-MySQL.
- ZKTeco ZK9500, driver oficial y SDK si se prueba biometria real.

### Produccion

- Windows 10 o Windows 11 recomendado.
- Python instalado en la PC final.
- MySQL Server o XAMPP/MariaDB-MySQL.
- Base de datos `horarios_control`.
- ZKTeco ZK9500 conectado por USB.
- Driver oficial ZKTeco / FPSensor.
- ZKFinger Standard SDK 5.3.0.33.
- .NET Framework compatible con el bridge C# compilado.
- No se requiere Visual Studio en la PC final.
- Node.js no es necesario en ejecucion si `frontend/dist` ya fue generado.

## Compatibilidad Windows

| Sistema | Aplicacion | ZK9500 | Estado |
| --- | --- | --- | --- |
| Windows 11 | Si, recomendado | Si, validar SDK/driver | Principal |
| Windows 10 | Si, probado como objetivo | Si | Principal |
| Windows 7 | Depende de versiones compatibles de Python, Node y dependencias | Si, si SDK/driver lo soportan | Compatible/legacy |
| Windows XP | No se promete el sistema web moderno completo | Solo posible como compatibilidad legacy del SDK/driver | Legacy limitado |

Notas importantes:

- El entorno local probado usa Python 3.12.13, adecuado para Windows 10/11.
- Windows 7 no debe asumirse compatible con Python moderno. Si se necesita Windows 7, validar una version de Python compatible y las dependencias reales antes del despliegue.
- Para equipos antiguos, compilar el frontend en una maquina moderna y copiar `frontend/dist` evita instalar Node.js en la PC final.
- Windows XP no debe usarse como plataforma principal del sistema web.

## Clonar Repositorio

```bash
git clone https://github.com/willder2305/CONTROL_HORARIO.git
cd CONTROL_HORARIO
git checkout deploy-ready
```

## Base de Datos

El sistema usa MySQL mediante SQLAlchemy y PyMySQL.

Opciones compatibles:

- XAMPP / MariaDB-MySQL.
- MySQL Server.

Base recomendada:

```sql
CREATE DATABASE horarios_control
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

La conexion se configura en `backend/.env`:

```env
DATABASE_URL=mysql+pymysql://usuario:password@localhost:3306/horarios_control
```

No versionar contrasenas reales.

## Backend

### 1. Crear entorno virtual

Desde la raiz del proyecto:

```powershell
py -3 -m venv backend\.venv
```

### 2. Instalar dependencias

```powershell
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Dependencias principales:

- Flask 3.0.3.
- Flask-SQLAlchemy.
- Flask-Migrate.
- Flask-CORS.
- PyMySQL.
- Waitress 2.1.2 para produccion.
- openpyxl para Excel.
- reportlab para PDF.
- pyzkfp como soporte de integracion biometrica.

### 3. Configurar variables de entorno

Para produccion:

```powershell
Copy-Item backend\.env.production.example backend\.env
```

Editar `backend/.env` y configurar valores reales.

Variables relevantes:

```env
SECRET_KEY=CAMBIAR_POR_UN_VALOR_LARGO_Y_ALEATORIO
DATABASE_URL=mysql+pymysql://usuario:password@localhost:3306/horarios_control
CORS_ORIGINS=http://127.0.0.1:5000,http://localhost:5000
FLASK_DEBUG=0
FINGERPRINT_PROVIDER=zk9500
ZKTECO_DEVICE_INDEX=0
ZKTECO_CAPTURE_TIMEOUT_SECONDS=30
ZKTECO_ENROLL_SAMPLES=3
ZKTECO_MATCH_THRESHOLD=1
SESSION_COOKIE_SECURE=false
CSRF_PROTECT=true
WAITRESS_HOST=127.0.0.1
WAITRESS_PORT=5000
```

Para HTTPS, usar:

```env
SESSION_COOKIE_SECURE=true
```

### 4. Migraciones

Desde `backend/`:

```powershell
cd backend
.\.venv\Scripts\python.exe -m flask --app run.py db upgrade
```

Esto crea o actualiza las tablas segun las migraciones existentes.

### 5. Crear administrador inicial

Desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m flask --app run.py crear-admin
```

El comando solicita usuario, nombre, apellido y contrasena. No hay credenciales por defecto.

### 6. Crear plantillas iniciales de horario

Opcional:

```powershell
.\.venv\Scripts\python.exe -m flask --app run.py seed-horarios
```

Crea plantillas iniciales si no existen.

## Frontend

### Desarrollo

```powershell
cd frontend
npm install
npm run dev
```

En desarrollo, `frontend/.env` puede usar:

```env
VITE_API_URL=http://localhost:5000/api
```

### Build de Produccion

```powershell
cd frontend
npm install
npm run build
```

Resultado:

```text
frontend/dist/
```

En produccion, Flask sirve `frontend/dist` y el frontend usa `/api` como base cuando se compila sin `VITE_API_URL`.

## ZKTeco ZK9500

La integracion real usa:

```text
Marca: ZKTeco
Modelo: ZK9500
SDK: ZKFinger Standard SDK 5.3.0.33
Driver: ZKTeco / FPSensor
Conexion: USB
```

El lector fue probado fisicamente en el equipo de desarrollo. El demo oficial C# logro captura real (`MESSAGE_CAPTURED_OK`) y obtuvo template (`CapTmp`).

### Instalacion del lector

1. Conectar el ZK9500 por USB directo a la computadora.
2. Instalar el driver oficial ZKTeco incluido con el SDK.
3. Confirmar en Administrador de dispositivos que el lector aparece correctamente y sin errores.
4. Instalar ZKFinger Standard SDK 5.3.0.33.
5. Confirmar que existen archivos del bridge en:

```text
backend/zk9500_bridge/bin/
```

Archivos esperados, segun instalacion actual:

```text
Zk9500Bridge.exe
libzkfp.dll
libzkfpcsharp.dll
libzksensorcore.dll
ZKFPCap.dll
zkfinger10.dll
zkfinger10-32.dll
zkfpslibLow.dll
ZKFPSensors/
```

6. Activar proveedor real en `backend/.env`:

```env
FINGERPRINT_PROVIDER=zk9500
```

`FINGERPRINT_PROVIDER=mock` queda reservado solo para desarrollo y pruebas automatizadas.

### Verificar lector

Desde la raiz del proyecto:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\diagnostico_zkteco.py
```

Tambien puede comprobarse el bridge directamente:

```powershell
backend\zk9500_bridge\bin\Zk9500Bridge.exe status
```

No se requiere Visual Studio en la PC final porque el bridge ya esta compilado. Si se recompila el bridge, usar el SDK oficial y respetar la arquitectura compatible con las DLL incluidas.

## Ejecutar en Desarrollo

Terminal 1:

```powershell
cd backend
.\.venv\Scripts\python.exe run.py
```

Terminal 2:

```powershell
cd frontend
npm run dev
```

URLs comunes en desarrollo:

```text
Frontend: http://127.0.0.1:5173
Backend API: http://127.0.0.1:5000/api
```

## Deploy Produccion

### Opcion recomendada con scripts

Desde la raiz del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
```

Configurar entorno:

```powershell
Copy-Item backend\.env.production.example backend\.env
notepad backend\.env
```

Crear base de datos en MySQL:

```sql
CREATE DATABASE horarios_control
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

Ejecutar migraciones:

```powershell
cd backend
.\.venv\Scripts\python.exe -m flask --app run.py db upgrade
cd ..
```

Crear administrador:

```powershell
cd backend
.\.venv\Scripts\python.exe -m flask --app run.py crear-admin
cd ..
```

Compilar frontend:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-production.ps1
```

Iniciar produccion:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-production.ps1
```

Abrir:

```text
http://127.0.0.1:5000
```

### Opcion manual

```powershell
py -3 -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm install
npm run build
cd ..
cd backend
.\.venv\Scripts\python.exe wsgi.py
```

## Primer Uso

```text
Crear administrador
      ↓
Iniciar sesion en panel administrativo
      ↓
Crear trabajador
      ↓
Registrar huella con 3 capturas
      ↓
Asignar horario
      ↓
Trabajador abre pantalla de marcaje
      ↓
Presiona MARCAR
      ↓
Coloca dedo en el ZK9500
      ↓
Sistema registra automaticamente la marcacion correspondiente
```

## Uso del Trabajador

El trabajador no inicia sesion y no selecciona el tipo de marcacion.

Flujo:

```text
Pantalla de marcaje
      ↓
MARCAR
      ↓
Colocar dedo
      ↓
ZK9500 captura huella
      ↓
Backend identifica trabajador
      ↓
Backend consulta horario y marcaciones existentes
      ↓
Backend determina siguiente funcion
      ↓
Guarda hora real del servidor
```

Secuencia con almuerzo:

```text
ENTRADA
↓
SALIDA DE ALMUERZO
↓
ENTRADA DE ALMUERZO
↓
SALIDA
```

Secuencia sin almuerzo:

```text
ENTRADA
↓
SALIDA
```

Si la jornada ya esta completa, no se crea otra marcacion.

## Uso del Administrador

El administrador puede:

- Iniciar sesion.
- Crear trabajadores.
- Registrar huella obligatoria para trabajadores en modo real.
- Asignar horarios.
- Crear plantillas de horario con o sin almuerzo.
- Consultar marcaciones.
- Ver dashboard.
- Generar reportes.
- Descargar Excel.
- Descargar PDF.
- Activar o desactivar trabajadores.
- Consultar parametros operativos.

## Creacion de Trabajadores

En modo biometrico real:

```text
Datos personales
      ↓
Registrar huella
      ↓
3 capturas del mismo dedo
      ↓
Template biometrico
      ↓
Guardar trabajador activo
```

El sistema evita duplicar huellas ya registradas.

## Seguridad

Antes de produccion revisar:

- `backend/.env` no debe subirse al repositorio.
- `SECRET_KEY` debe ser largo y aleatorio.
- `FLASK_DEBUG=0` en produccion.
- `SESSION_COOKIE_SECURE=true` si se usa HTTPS.
- `CSRF_PROTECT=true`.
- `CORS_ORIGINS` debe contener solo origenes permitidos.
- No usar `*` con sesiones/cookies.
- No registrar templates biometricos completos en logs.
- Proteger backups de base de datos.
- Restringir acceso fisico al equipo con lector.

## Backups

Con XAMPP instalado en la ruta predeterminada:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup-db.ps1
```

El script genera archivos en:

```text
backups/
```

Comando manual equivalente:

```powershell
C:\xampp\mysql\bin\mysqldump.exe -u root --databases horarios_control --result-file=backups\horarios_control.sql
```

Si su MySQL usa contrasena, ajustar el comando segun la politica local y no escribir contrasenas en archivos versionados.

## Restauracion

Crear la base si no existe y restaurar:

```powershell
C:\xampp\mysql\bin\mysql.exe -u root < backups\horarios_control.sql
```

Si usa usuario con contrasena, ejecutar el comando de forma segura segun su instalacion.

## Actualizacion del Sistema

```powershell
git pull origin deploy-ready
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd backend
.\.venv\Scripts\python.exe -m flask --app run.py db upgrade
cd ..
powershell -ExecutionPolicy Bypass -File scripts\build-production.ps1
```

Reiniciar el proceso de produccion despues de actualizar.

## Pruebas

### Backend

Desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

### Frontend

Desde `frontend/`:

```powershell
npm run build
```

### Salud del sistema

Con el backend iniciado:

```text
http://127.0.0.1:5000/api/health
```

## Solucion de Problemas

### ZK9500 no detectado

- Revisar cable USB.
- Probar otro puerto USB directo.
- Revisar Administrador de dispositivos.
- Confirmar driver oficial ZKTeco / FPSensor.
- Confirmar instalacion del ZKFinger SDK.
- Ejecutar `backend\zk9500_bridge\bin\Zk9500Bridge.exe status`.

### Lector detectado pero no lee

- Confirmar `FINGERPRINT_PROVIDER=zk9500`.
- Confirmar DLLs en `backend/zk9500_bridge/bin/`.
- Cerrar demos oficiales u otros procesos que puedan estar usando el lector.
- Ejecutar `backend\scripts\diagnostico_zkteco.py`.
- Confirmar que el trabajador tenga huella activa.

### Base de datos no conecta

- Verificar que MySQL/XAMPP este iniciado.
- Confirmar que el puerto configurado coincida con `DATABASE_URL`.
- Confirmar usuario, contrasena y nombre de base.
- Ejecutar migraciones con `flask db upgrade`.

### Login no funciona

- Confirmar backend iniciado.
- Confirmar que existe administrador activo.
- Revisar cookies del navegador.
- Revisar `CORS_ORIGINS` si frontend y backend estan separados.
- Confirmar `CSRF_PROTECT=true` y que el frontend use la API actual.

### Frontend no carga

- Ejecutar `npm run build`.
- Confirmar que exista `frontend/dist/index.html`.
- Iniciar produccion con `scripts/start-production.ps1`.
- Abrir `http://127.0.0.1:5000`.

### Marcacion no se registra

- Confirmar que el trabajador este activo.
- Confirmar que tenga huella activa.
- Confirmar que tenga horario asignado para la jornada.
- Confirmar que la jornada no este completa.
- Revisar estado del lector ZK9500.

## Archivos que no deben versionarse

El repositorio ignora:

- `backend/.env`.
- `frontend/.env`.
- entornos virtuales.
- `node_modules`.
- `frontend/dist`.
- caches.
- backups.
- logs.

Las DLL necesarias del bridge biometrico no se ignoran porque forman parte del despliegue local del ZK9500.
