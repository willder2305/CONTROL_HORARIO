# Backend - Control de Horarios

Base Flask creada para la FASE 1 y esquema inicial agregado en FASE 2.

La documentacion completa del proyecto esta en:

```text
..\README.md
```

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

## Endpoint inicial

- `GET /api/health` responde `{"status":"ok"}`.

La base de datos queda configurada mediante `DATABASE_URL` para MySQL usando PyMySQL.
Para XAMPP en el puerto `3306`, la configuracion inicial esperada es:

```env
DATABASE_URL=mysql+pymysql://root:@localhost:3306/horarios_control
```

La base `horarios_control` debe existir en MySQL antes de ejecutar migraciones. La FASE 2 agrega los modelos principales y la migracion inicial del esquema.

## Seguridad

Las rutas administrativas usan sesion Flask con cookie `HttpOnly`, `SameSite=Lax`
y token CSRF por sesion. El frontend envia el token en `X-CSRF-Token` para
operaciones `POST`, `PUT`, `PATCH` y `DELETE` despues del login.

Variables relevantes:

```env
SECRET_KEY=change-this-secret
SESSION_COOKIE_SECURE=false
CSRF_PROTECT=true
MAX_CONTENT_LENGTH=2097152
```

En produccion debe usarse un `SECRET_KEY` unico y `SESSION_COOKIE_SECURE=true`
cuando la aplicacion se sirva sobre HTTPS.

## Migraciones

```bash
.venv\Scripts\python.exe -m flask --app run.py db upgrade
```

## Datos iniciales

Crear plantillas base:

```bash
.venv\Scripts\python.exe -m flask --app run.py seed-horarios
```

Crear administrador inicial con contrasena solicitada en consola:

```bash
.venv\Scripts\python.exe -m flask --app run.py crear-admin
```

## Lector ZKTeco ZK9500

Por defecto el sistema usa biometria simulada:

```env
FINGERPRINT_PROVIDER=mock
```

Para usar el lector real ZKTeco ZK9500 en Windows 10 64 bits:

1. Instalar el driver incluido en `ZKFinger SDK for Windows`.
2. Verificar que el lector USB aparezca correctamente en Windows.
3. Instalar o exponer un wrapper Python compatible con `ZKFP2`.
4. Cambiar la configuracion:

```env
FINGERPRINT_PROVIDER=real
ZKTECO_DEVICE_INDEX=0
ZKTECO_CAPTURE_TIMEOUT_SECONDS=15
ZKTECO_ENROLL_SAMPLES=3
ZKTECO_MATCH_THRESHOLD=1
```

En modo real, React no debe enviar `fingerprint_id`; el backend captura la huella
directamente desde el lector. Si el SDK, driver o dispositivo no estan disponibles,
las APIs biometricas devuelven `LECTOR_NO_DISPONIBLE` con estado HTTP `503`.

## Pruebas

Desde la raiz del proyecto:

```powershell
backend\.venv\Scripts\python.exe -B -c "import sys, importlib.util; from pathlib import Path; sys.path.insert(0, 'backend'); total=0; failures=[]; base=Path('backend/tests');\nfor path in sorted(base.glob('test_*.py')):\n    spec=importlib.util.spec_from_file_location(path.stem, path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)\n    for name in sorted(n for n in dir(mod) if n.startswith('test_')):\n        total += 1\n        try:\n            getattr(mod, name)()\n        except Exception as exc:\n            failures.append((path.name, name, repr(exc)))\nif failures:\n    print('failures:')\n    [print(f'{file}::{name} {err}') for file,name,err in failures]\n    raise SystemExit(1)\nprint(f'{total} tests ok')"
```

## Backup MySQL

```powershell
C:\xampp\mysql\bin\mysqldump.exe -u root horarios_control > C:\backups\horarios_control.sql
```
