> **Para ejecutar el proyecto rápidamente:** lee `LEEME_PRIMERO.md` (dónde está cada archivo) y `MANUAL_DE_EJECUCION.pdf` (paso a paso). Lo que cambió en esta versión está en `docs/CAMBIOS_ACCESO_Y_BASE_DE_DATOS.md`. Documentación técnica: `docs/DOCUMENTACION_TECNICA.md`.

# Lotería Interactiva Mazahua

Sistema bilingüe de vocabulario y lotería: **Astro + FastAPI + MariaDB/MySQL**, con lectura física opcional **ESP32 + RC522** por USB.

- **Docentes:** crean su propia cuenta (nombre, correo y contraseña de 6 caracteres o más) e inician sesión con su correo. Con la sesión iniciada tienen el panel completo: partidas, código QR, alumnos, tarjetas, imágenes y audios. Recuperan su contraseña con un enlace temporal de un solo uso.
- **Alumnos:** no tienen cuenta. Escanean el QR (o escriben el código), ponen su nombre y juegan. Solo pueden entrar a una partida abierta con lugares, ver su tablero, marcar casillas, escuchar las cartas y cantar lotería.

## Inicio local (Windows)

1. Encender MySQL en XAMPP.
2. `1_INSTALAR.bat` (una vez).
3. `2_INICIAR_SISTEMA.bat` → abre http://127.0.0.1:8000. Si la base tiene la estructura anterior, se convierte sola al iniciar (con respaldo previo en `sql/respaldos/`).
4. En `/acceso` → **Crear cuenta** → iniciar sesión.

Manual:
```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
npm --prefix frontend install
npm --prefix frontend run build
.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## Rutas

| Ruta | Acceso | Uso |
|---|---|---|
| `/` | Público | Portada: iniciar sesión / crear cuenta de docente, entrar como alumno, simulador. |
| `/acceso` | Público | Iniciar sesión (correo y contraseña), crear cuenta, «¿Olvidaste tu contraseña?». |
| `/estudiante?codigo=XXXXXX` | Público (alumno) | Ingreso a la partida desde el QR. |
| `/vocabulario`, `/simulador`, `/videos` | Público | Catálogo con audios, práctica individual y videos de YouTube. |
| `/panel` | Docente | Panel principal y partidas recientes. |
| `/docente` | Docente | Crear partida (nombre y límite), QR, alumnos, iniciar, anunciar y finalizar. |
| `/editar` | Docente | Agregar, editar y eliminar tarjetas, imágenes y audios. |
| `/administracion` | Docente | Lector RFID, grabación de audio y enlaces de YouTube. |
| `/cuenta` | Docente | Nombre, correo y contraseña. |
| `/docs` | Docente (solo desarrollo) | Swagger UI. |

## Seguridad

- Contraseñas con PBKDF2-SHA256 (600 000 iteraciones); nunca en texto plano.
- Sesión: JWT firmado en cookie HttpOnly + registro en la tabla `sesiones` (cerrar sesión o cambiar la contraseña la invalida). Las escrituras exigen `X-CSRF-Token` y se verifica el origen.
- Los permisos se validan en el servidor (`seguridad.py` + `middleware.py`): sin sesión, las páginas del docente redirigen a `/acceso` y la API responde 401. Cada partida solo la administra el docente que la creó.
- Recuperación: enlace de 30 minutos y un solo uso; en la base solo se guarda su hash. Con SMTP configurado se envía por correo; sin SMTP (uso local) aparece en la ventana del servidor y en pantalla únicamente si se solicita desde la misma computadora.
- Límite de intentos de acceso por IP (30 por minuto).

## API principal

| Método | Ruta | Acceso |
|---|---|---|
| POST | `/api/auth/registro` | Público: nombre, correo, contraseña y confirmación. |
| POST | `/api/auth/login` | Público: correo y contraseña. |
| POST | `/api/auth/recuperar`, `/api/auth/restablecer` | Público: enlace temporal de un uso. |
| GET | `/api/auth/me` · POST `/api/auth/logout` · PUT `/api/auth/perfil` · POST `/api/auth/password` | Docente. |
| GET | `/api/vocabulario` | Público (sin UID). `?buscar=` |
| GET · POST · PUT · DELETE | `/api/tarjetas`, `/api/tarjetas/{id}` | Docente + CSRF en escrituras. |
| POST | `/api/partidas` · GET `/api/partidas/mias` · POST `/api/partidas/{codigo}/iniciar|finalizar` | Docente (dueño de la partida). |
| GET | `/api/partidas/{codigo}/publica` · POST `/api/partidas/unirse` | Público (alumno). |
| POST | `/api/juego/{codigo}/marcar`, `/api/juego/{codigo}/loteria` | Alumno de esa partida. |
| POST | `/api/juego/{codigo}/anunciar` | Docente: UID RFID o número de carta. |
| WS | `/ws/partidas/{codigo}` | Alumno (su tablero) o docente con sesión. |

## Estructura

```text
main.py            API de tarjetas, imágenes, audios, catálogo, QR y arranque
autenticacion.py   Usuarios, registro, inicio de sesión, sesiones y recuperación
seguridad.py       Qué rutas son públicas y cuáles requieren sesión docente
middleware.py      Autenticación, CSRF, origen y límites
partidas.py        Partidas, participantes, tableros, anuncios y WebSocket
migracion.py       Conversión automática de la estructura anterior (con respaldo)
                   La tabla `tarjetas` guarda en un solo registro nombres, descripción, imagen y audios
database.py        Conexión SQLAlchemy / MariaDB
frontend/          Proyecto Astro (src/pages, src/layouts, dist)
static/            Estilos y scripts del navegador
sql/               base_de_datos_mazahua.sql (estructura + registros), estructura_completa.sql
catalogo/          Material original: imagen y audio mazahua de cada carta
uploads/           Imágenes y audios subidos (se crea solo)
tests/             Pruebas automáticas
```

## Pruebas

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-test.txt
.venv\Scripts\python.exe -m tests.verificar_acceso_jwt
.venv\Scripts\python.exe -m tests.verificar_produccion
node tests/verificar_salas.cjs
node tests/verificar_audio.cjs
node tests/verificar_lector.cjs
node tests/verificar_admin_lector.cjs
```

Las pruebas de Python usan SQLite en memoria y carpetas temporales: no modifican MySQL ni los archivos reales. Comprueban la migración con respaldo, registro y validaciones, inicio de sesión con correo, recuperación de un uso, sesiones, CSRF, permisos de alumno y docente, tarjetas con imágenes y audios, partidas, QR, límite de alumnos y WebSocket.

Publicación en la nube (opcional): [docs/NUBE_GRATUITA.md](docs/NUBE_GRATUITA.md) y [deploy/ORACLE.md](deploy/ORACLE.md).
