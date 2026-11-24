# Publicar el proyecto: GitHub + Vercel + Render + Supabase

## Cómo queda repartido

| Parte | Servicio | Qué hace |
|---|---|---|
| Código | **GitHub** (`Jose78123/loteria-mazahua`) | Guarda el proyecto. Vercel y Render toman el código de ahí. |
| Frontend | **Vercel** | Sirve las páginas (Astro compilado) y los archivos de `static/`. Reenvía `/api`, `/catalogo` y `/uploads` al backend, así la sesión del docente funciona como si todo fuera un solo sitio. |
| Backend | **Render** (`loteria-mazahua-escuela.onrender.com`) | FastAPI: cuentas, partidas, tarjetas, WebSocket del juego en vivo. Se conecta a la base de datos MySQL. |
| Base de datos | MySQL en la nube (la que ya usa Render, configurada en sus variables `DB_*`) | Tablas `usuarios`, `tarjetas` (tabla única), `partidas`, etc. Render no ofrece MySQL propio; su PostgreSQL gratuito caduca a los 30 días, por eso se conserva la base MySQL actual. |
| Imágenes y audios | **Supabase Storage** (bucket `loteria-media`) | Guarda los archivos del catálogo y los que suben o graban los docentes. |

```
Navegador ──► Vercel (páginas)  ──/api, /catalogo, /uploads──►  Render (FastAPI) ──► MySQL
     │                                                            │
     └────────── WebSocket wss:// directo ──────────────────────►│──► Supabase Storage (archivos)
```

El WebSocket va directo a Render porque Vercel no reenvía WebSockets. El docente se identifica ahí con un
**ticket firmado de 2 minutos** que pide a `/api/tiempo-real/{codigo}` con su sesión; los alumnos usan su
identificador de dispositivo, como antes.

## Archivos que se agregaron o cambiaron para esto

- `vercel.json` — compilación (`frontend/` + `deploy/preparar_vercel.mjs`) y reenvíos a Render.
- `deploy/preparar_vercel.mjs` — copia `static/` dentro de `frontend/dist/static`.
- `deploy/subir_multimedia.py` — sube a Supabase los archivos del catálogo que falten (audios en español, tortilla, miniaturas) y actualiza `catalogo_manifest.json`.
- `configuracion.py` — variables `FRONTEND_URL`, `ALLOWED_ORIGINS`.
- `middleware.py`, `partidas.py` — aceptan peticiones y WebSocket desde el dominio de Vercel.
- `autenticacion.py` — ticket del WebSocket (`crear_ticket_ws`, `docente_por_ticket`).
- `main.py` — `/api/tiempo-real/{codigo}`; el QR usa `FRONTEND_URL`; miniaturas en la nube.
- `static/salas.js` — pide la dirección del WebSocket y el ticket antes de conectarse.
- `render.yaml` — variable `FRONTEND_URL`.

En la computadora (sin `FRONTEND_URL`) todo funciona igual que antes.

## Pasos

### 1. Respaldo de la base en la nube (antes de publicar)
Al arrancar, Render convierte sola la base a la tabla única `tarjetas`. Antes, exporta la base actual
(phpMyAdmin del proveedor → Exportar, o `mysqldump`) y guarda el archivo.

### 2. Subir los archivos nuevos a Supabase
Desde la carpeta del proyecto en tu computadora (con internet y con `deploy/.cloud-secrets.json`, que ya tenías
en la carpeta anterior del proyecto):

```bat
.venv\Scripts\python deploy\subir_multimedia.py          REM muestra qué falta
.venv\Scripts\python deploy\subir_multimedia.py --subir  REM lo sube
```

En Supabase → Storage → `loteria-media` → configuración del bucket, revisa que los tipos permitidos
incluyan `image/webp`, `audio/webm` y `video/webm` (las grabaciones del micrófono se guardan como `.webm`),
o deja la lista vacía para permitir todos.

### 3. Subir el código a GitHub
```bat
git add -A
git commit -m "Frontend en Vercel, backend en Render y archivos en Supabase"
git push origin main
```
`git status` no debe mostrar `.env`, `deploy/.cloud-secrets.json` ni `.jwt-secret` (están en `.gitignore`).

### 4. Vercel (frontend)
1. vercel.com → **Add New → Project** → importar `Jose78123/loteria-mazahua`.
2. *Root Directory*: la raíz del repositorio. *Framework Preset*: **Other** (lo demás lo toma de `vercel.json`).
3. **Deploy**. Anota la dirección, por ejemplo `https://loteria-mazahua.vercel.app`.
4. Si el backend de Render tiene otra dirección, cámbiala en los `rewrites` de `vercel.json` y vuelve a subir.

### 5. Render (backend)
1. Servicio `loteria-mazahua-escuela` → **Environment** → agregar `FRONTEND_URL` = la dirección de Vercel (sin `/` al final).
2. Comprobar que siguen `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSL=true`,
   `STORAGE_BACKEND=supabase`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_BUCKET=loteria-media`, `JWT_SECRET`.
3. **Manual Deploy → Deploy latest commit** (el despliegue automático está apagado en `render.yaml`).
4. Abrir `https://loteria-mazahua-escuela.onrender.com/api/ready` → debe responder `ok`.

### 6. Probar
1. Abrir la dirección de Vercel → crear cuenta de docente → iniciar sesión.
2. Crear partida: el QR debe llevar a `https://…vercel.app/estudiante?codigo=…`.
3. Entrar desde un celular con el QR, iniciar la partida y anunciar una carta: debe aparecer en el celular.
4. En **Tarjetas**, revisar que se ven imágenes y audios, y grabar un audio de prueba.

Render gratuito se duerme tras 15 minutos sin uso: la primera carga puede tardar alrededor de un minuto.

## Instrucción lista para el asistente de IA de tu computadora

Si usas un asistente con acceso a tu computadora y a tus cuentas (por ejemplo OpenCode), puedes pegarle esto:

> Lee `docs/MEMORIA_LOTERIA.md` y `docs/DESPLIEGUE_VERCEL_RENDER_SUPABASE.md`. Quiero publicar el proyecto así:
> el código en GitHub (repositorio `Jose78123/loteria-mazahua`, rama `main`), el **frontend en Vercel**,
> el **backend en Render** (servicio `loteria-mazahua-escuela`, conectado a la base de datos MySQL actual) y
> **Supabase Storage** (bucket `loteria-media`) para imágenes, audios y demás archivos.
> 1) Haz un respaldo de la base MySQL de la nube antes de cambiar nada.
> 2) Ejecuta `python deploy/subir_multimedia.py --subir` y revisa que el bucket acepte `image/webp`, `audio/webm` y `video/webm`.
> 3) Sube el código a GitHub sin `.env`, `deploy/.cloud-secrets.json` ni `.jwt-secret`.
> 4) Crea el proyecto en Vercel desde ese repositorio (Framework: Other; usa `vercel.json`) y dime su dirección.
> 5) En Render agrega `FRONTEND_URL` con esa dirección y despliega el último commit.
> 6) Comprueba `/api/ready`, el registro e inicio de sesión del docente, el QR, una partida con un celular,
>    y que las imágenes y audios cargan desde Supabase. No borres datos ni recursos existentes, y avísame antes de cualquier acción que no se pueda deshacer.
