# Documentación técnica · Lotería Interactiva Mazahua

## 1. Descripción general

La plataforma es el componente digital de la Lotería Interactiva Mazahua. Permite administrar el vocabulario (palabra en mazahua, traducción al español, descripción, imagen y audios en mazahua y español), consultarlo desde una galería pública, reproducir las pronunciaciones y ejecutar la dinámica de la lotería desde el navegador. Además, está preparada para recibir las lecturas de las tarjetas RFID del ESP32, lo que facilita su integración con los componentes electrónicos de las demás asignaturas.

## 2. Arquitectura

```
 Navegador (Chrome/Edge)
   │  páginas HTML/CSS/JS compiladas por Astro
   │  fetch() → /api/...      WebSocket → /ws/partidas/{codigo}
   ▼
 FastAPI + Uvicorn (puerto 8000)  ─────────────►  MySQL (loteria_mazahua)
   │  main.py, partidas.py, autenticacion.py         SQLAlchemy + PyMySQL
   │  sirve también frontend/dist, /static, /catalogo y /uploads
   ▼
 Archivos multimedia: catalogo/ (originales) y uploads/ (subidos)
```

Se trata de una arquitectura cliente-servidor de tres capas. Astro compila las páginas a HTML estático en `frontend/dist`, y FastAPI las entrega bajo el mismo origen que la API. Debido a ello, las cookies de sesión y los WebSocket funcionan sin configurar CORS. Toda la información que muestra la interfaz se obtiene de la API mediante solicitudes HTTP; el frontend no guarda una copia del catálogo.

## 3. Tecnologías

| Capa | Tecnología | Uso |
|---|---|---|
| Backend | Python 3.10+, **FastAPI**, Uvicorn | API REST, WebSocket, documentación Swagger UI |
| Acceso a datos | SQLAlchemy 2, PyMySQL | ORM y conexión con MySQL |
| Base de datos | **MySQL 8** / MariaDB (XAMPP) | Almacenamiento de vocabulario, cuentas y partidas |
| Frontend | **Astro 7**, HTML, CSS, JavaScript | Páginas responsivas que consumen la API |
| Seguridad | PyJWT, PBKDF2-SHA256 | Sesiones JWT en cookie HttpOnly, CSRF, roles |
| Otros | python-multipart, qrcode, pyserial | Subida de archivos, QR de partidas, lector USB |

## 4. Organización del código

| Módulo | Responsabilidad |
|---|---|
| `main.py` | Modelo `Tarjeta`, migración aditiva, endpoints del vocabulario, archivos multimedia, búsqueda y videos de YouTube |
| `database.py` | Motor y sesiones de SQLAlchemy |
| `configuracion.py` | Variables de entorno y validaciones de producción |
| `autenticacion.py` | Usuarios (docentes): registro, inicio de sesión con correo, sesiones JWT, perfil y recuperación de contraseña |
| `seguridad.py` | Política de acceso por ruta y método (público/alumno o docente con sesión) |
| `migracion.py` | Conversión automática de la estructura anterior de la base, con respaldo |
| `middleware.py` | Autenticación, CSRF, verificación de origen y límites |
| `partidas.py` | Salas, tableros, anuncios, validación de lotería y WebSocket |
| `frontend_web.py` | Entrega de páginas Astro |
| `frontend/src/pages/*.astro` | Páginas del frontend |
| `static/*.js`, `static/*.css` | Lógica y estilos del navegador |

## 5. Base de datos

Base: `loteria_mazahua` (utf8mb4, MariaDB/MySQL). Con registros: `sql/base_de_datos_mazahua.sql`; solo estructura: `sql/estructura_completa.sql`. El backend crea las tablas que falten al iniciar (`AUTO_MIGRATE=true`) y, si encuentra la estructura anterior, la convierte con `migracion.py` (respaldo previo en `sql/respaldos/`).

```
usuarios ─1───N─ partidas ─1───N─ participantes ─1───1─ tableros ─1───N─ tablero_tarjetas ─N───1─ tarjetas
    │                 └────1───N─ anuncios ─N──────────────────────────────────────────────1─┘
    ├─1───N─ sesiones
    └─1───N─ recuperaciones_password
```

| Tabla | Columnas principales | Claves |
|---|---|---|
| `usuarios` | id, nombre, correo, password_hash (PBKDF2-SHA256), fecha_registro | PK id; correo único |
| `tarjetas` | **Tabla única de las tarjetas:** id, numero, nombre_espanol, nombre_mazahua, descripcion, imagen, audio_mazahua, audio_espanol, uid_rfid | PK id; numero y uid_rfid únicos (opcionales) |
| `partidas` | id, codigo, nombre, usuario_id, limite, estado, fecha_creacion, iniciada, finalizada, ultima_tarjeta_id, secuencia, ultima_actividad_docente, cierre_motivo | FK usuario_id → usuarios; FK ultima_tarjeta_id → tarjetas; codigo único |
| `participantes` | id, partida_id, nombre, dispositivo, fecha_ingreso, gano | FK → partidas (cascada) |
| `tableros` | id, participante_id, creado | FK → participantes (cascada) |
| `tablero_tarjetas` | tablero_id, posicion, tarjeta_id, marcada | PK (tablero_id, posicion); FK → tableros, tarjetas |
| `anuncios` | id, partida_id, tarjeta_id, fecha | FK → partidas (cascada), tarjetas; único (partida_id, tarjeta_id) |
| `sesiones` | jti, usuario_id, vence | FK → usuarios (cascada) |
| `recuperaciones_password` | token_hash, usuario_id, creada, vence | FK → usuarios (cascada); solo el hash del enlace |

Las imágenes y audios son **archivos** (`catalogo/` para el material original, `uploads/imagenes` y `uploads/audios` para los subidos, con nombre aleatorio); la tabla `tarjetas` guarda su ruta en las columnas `imagen`, `audio_mazahua` y `audio_espanol` (por ejemplo `/catalogo/0010_gato/audio_mazahua.m4a`). `dispositivo` es un identificador aleatorio del navegador del alumno que le permite recargar la página sin perder su tablero (el alumno no tiene cuenta). Los enlaces de YouTube se guardan en `videos_youtube.json`.

## 6. Instalación y configuración

Los pasos completos están en `MANUAL_DE_EJECUCION.md`. En resumen:

1. `1_INSTALAR.bat`: crea `.venv`, instala `requirements.txt`, ejecuta `npm install` y `npm run build` en `frontend/`.
2. `2_INICIAR_SISTEMA.bat`: compila Astro y ejecuta `uvicorn main:app --host 0.0.0.0 --port 8000`.

Variables principales del archivo `.env`:

| Variable | Valor local | Descripción |
|---|---|---|
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` | `root`, vacío, `127.0.0.1`, `3306`, `loteria_mazahua` | Conexión MySQL |
| `APP_ENV` | `development` | En producción desactiva Swagger y exige HTTPS |
| `AUTO_MIGRATE` | `true` | Crea o actualiza las tablas al iniciar |
| `SERIAL_ENABLED` | `false` | Puente serial antiguo; el lector se conecta desde el navegador |
| `JWT_SECRET` | vacío en desarrollo | Firma de sesiones (se genera `.jwt-secret` automáticamente) |
| `PUBLIC_URL`, `SMTP_*` | vacío | Correo para enviar el enlace de recuperación (opcional; ver `.env.example`) |

## 7. Endpoints principales

La documentación interactiva completa está en **Swagger UI: `/docs`** (requiere sesión docente, en modo desarrollo). Los endpoints aparecen agrupados por etiquetas.

### Público y alumnos (sin sesión)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/vocabulario` | Tarjetas sin UID. Búsqueda opcional `?buscar=gato` |
| GET | `/api/vocabulario/{id}` | Una tarjeta |
| GET | `/api/videos` | Videos de YouTube con `miniatura`, `enlace` y estado `pendiente` |
| GET | `/api/partidas/{codigo}/publica` | Nombre, estado, límite y lugares disponibles (lo usa la pantalla del QR) |
| POST | `/api/partidas/unirse` | Alumno: código, nombre e identificador del dispositivo. Valida que exista, esté en espera y tenga lugar |
| POST | `/api/juego/{codigo}/marcar`, `/api/juego/{codigo}/loteria` | Alumno de esa partida: marcar casilla y cantar lotería |
| WS | `/ws/partidas/{codigo}` | Actualizaciones en vivo (el alumno solo recibe su tablero) |

### Cuenta docente

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/auth/registro` | Crear cuenta: nombre, correo, password, confirmacion |
| POST | `/api/auth/login` | Iniciar sesión: correo y password |
| POST | `/api/auth/recuperar` | Generar enlace de recuperación (30 min, un uso) |
| POST | `/api/auth/restablecer` | Nueva contraseña con el código del enlace |
| GET | `/api/auth/me` | Datos del docente y `csrf_token` |
| PUT | `/api/auth/perfil` | Cambiar nombre y correo |
| POST | `/api/auth/password` | Cambiar contraseña (cierra las sesiones) |
| POST | `/api/auth/logout` | Cerrar sesión |

### Docente con sesión (las escrituras requieren `X-CSRF-Token`)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/tarjetas` | Lista con número y UID; `?buscar=` (palabra, número o UID) |
| GET | `/api/tarjetas/{id}` · `/api/uid/{uid}` | Consultar una tarjeta |
| POST | `/api/tarjetas` | **Agregar** (multipart: `palabra_mazahua`, `traduccion_espanol`, `descripcion`, `numero`, `uid`, `imagen`, `audio_mazahua`, `audio_espanol` opcional) |
| PUT | `/api/tarjetas/{id}` | **Editar**; archivos opcionales; `eliminar_audio_mazahua` / `eliminar_audio_espanol` |
| DELETE | `/api/tarjetas/{id}` | **Eliminar** la tarjeta con su imagen y audios |
| POST | `/api/tarjetas/{id}/audio-espanol` | Guardar la grabación del micrófono |
| POST | `/api/partidas` | Crear partida: `nombre`, `limite` (1–100) |
| GET | `/api/partidas/mias` | Partidas del docente |
| POST | `/api/partidas/{codigo}/iniciar` · `/finalizar` · `/latido` | Solo el docente que la creó |
| POST | `/api/juego/{codigo}/anunciar` | Cantar carta por UID RFID o por número |
| GET | `/api/invitacion/{codigo}` · `/qr` | Enlace y código QR para los alumnos (usa la IP de la red local) |
| POST | `/api/catalogo/registrar` · GET `/api/catalogo/estado` | Registro automático con el lector RFID |
| POST | `/api/esp32/uid` · GET `/api/ultimo-uid` | Lecturas del lector |
| PUT | `/api/videos` | Guardar los enlaces de YouTube |

Límites de archivos: imagen 5 MB (JPG, PNG, WEBP); audio 12 MB (MP3, WAV, OGG, M4A, WEBM, MP4); solicitud completa 30 MB.

Ejemplo de `GET /api/vocabulario?buscar=gato`:

```json
[{"id": 5, "numero": 10, "palabra_mazahua": "Mixi", "traduccion_espanol": "Gato",
  "descripcion": "«Mixi» es la palabra en lengua mazahua para «gato». Escucha su pronunciación en mazahua y en español.",
  "imagen_url": "/catalogo/0010_gato/imagen.jpg", "miniatura_url": "/catalogo/0010_gato/miniatura.webp",
  "audio_mazahua_url": "/catalogo/0010_gato/audio_mazahua.m4a", "audio_espanol_url": "/uploads/audios/f59c8f1b….mp3"}]
```

### Permisos

`seguridad.py` decide, para cada ruta y método, si es pública o requiere sesión docente; `middleware.py` lo aplica antes de llegar al código: sin sesión, las páginas del docente redirigen a `/acceso` y la API responde 401. Cambiar la URL no permite saltarse la validación. Además, cada partida guarda su `usuario_id` y solo ese docente puede iniciarla, anunciar cartas o finalizarla.

## 8. Frontend

| Página | Archivo | Endpoints consumidos |
|---|---|---|
| Inicio `/` | `pages/index.astro` (`static/inicio.html`) | — |
| Vocabulario `/vocabulario` | `pages/vocabulario.astro` + `static/vocabulario.js` | `GET /api/vocabulario` |
| Simulador `/simulador` | `pages/simulador.astro` + `static/simulador.js` | `GET /api/vocabulario` |
| Videos `/videos` | `pages/videos.astro` + `static/videos.js` | `GET /api/videos` |
| Administrar tarjetas `/editar` | `pages/editar.astro` + `static/editar-vocabulario.js` | CRUD `/api/tarjetas` |
| Administración `/administracion` | `pages/administracion.astro` (`static/administracion.html`, `admin-videos.js`) | CRUD `/api/tarjetas`, `/api/videos`, lector |
| Docente / Estudiante | `pages/docente.astro`, `pages/estudiante.astro` (`static/salas.js`) | `/api/partidas`, `/api/juego`, WebSocket |
| Acceso / Cuenta | `pages/acceso.astro` + `static/acceso-docente.js`, `pages/cuenta.astro` + `static/cuenta-docente.js` | `/api/auth/*` |
| Panel del docente `/panel` | `pages/panel.astro` + `static/panel-docente.js` | `/api/auth/me`, `/api/partidas/mias` |
| Navegación (Inicio · Regresar · Cerrar sesión) | `static/navegacion.js` | `/api/auth/me`, `/api/auth/logout` |

Todas las páginas tienen reglas responsivas para computadora, tableta y celular.

## 9. Integración con la electrónica

El ESP32 con lector RC522 envía `UID:AA BB CC DD` por USB a 115200 baudios. El navegador del docente lee el puerto con Web Serial (`static/lector-usb.js`) y llama a la API; como alternativa, `serial_bridge.py` publica la lectura en `POST /api/esp32/uid`. De esta manera, cuando las otras asignaturas terminen el circuito de luces, botones y audio, solo deberán consumir los mismos endpoints.

## 10. Pruebas

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-test.txt
.venv\Scripts\python.exe -m tests.verificar_acceso_jwt
.venv\Scripts\python.exe -m tests.verificar_produccion
node tests/verificar_salas.cjs
node tests/verificar_audio.cjs
node tests/verificar_lector.cjs
node tests/verificar_admin_lector.cjs
```
