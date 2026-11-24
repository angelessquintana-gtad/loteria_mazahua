# Publicar la Lotería Mazahua en internet (un solo enlace para todos)

Resultado: una dirección como `https://loteria-mazahua.onrender.com` que cualquiera abre desde su celular o
computadora, sin estar en la misma red Wi-Fi. El código QR de las partidas usa esa dirección.

| Parte | Servicio gratuito | Para qué |
|---|---|---|
| Código | GitHub (repositorio público) | Guarda el proyecto; Render lo toma de ahí. Incluye las imágenes y audios del catálogo. |
| Sistema (backend + páginas) | Render (Web Service, plan Free) | Ejecuta FastAPI y entrega las páginas de Astro. Usa `render.yaml` y `Dockerfile`. |
| Base de datos | TiDB Cloud Starter (compatible con MySQL, gratis) | Tablas `tarjetas`, `usuarios`, `partidas`… Al primer arranque se crean solas y se cargan las 54 cartas del catálogo. |

## 1. Subir el proyecto a GitHub
Ver los pasos en la respuesta del asistente o en `LEEME_PRIMERO.md`. El repositorio debe ser **Public**.
`.gitignore` ya excluye `.env`, `deploy/.cloud-secrets.json` y `.jwt-secret` (contraseñas) y sí incluye `catalogo/`.

## 2. Base de datos en TiDB Cloud
1. Entrar a **tidbcloud.com** → crear cuenta (con Google o GitHub) → **Create Cluster/Instance** → plan **Starter** (gratis) → región cercana (por ejemplo AWS Oregon `us-west-2`) → **Create**.
2. En el clúster: **Connect** → *Connect With: General* → **Generate Password** y copiar: **HOST**, **PORT** (4000), **USERNAME** (algo como `2AbCd.root`) y **PASSWORD**.
3. **SQL Editor** (o *Chat2Query*) → ejecutar: `CREATE DATABASE loteria_mazahua;`

## 3. Render
1. Entrar a **render.com** → **Sign in with GitHub**.
2. **New + → Blueprint** → elegir tu repositorio → Render lee `render.yaml`.
3. Llenar las variables que pide: `DB_HOST`, `DB_PORT` = 4000, `DB_NAME` = `loteria_mazahua`, `DB_USER`, `DB_PASSWORD` (las de TiDB) → **Apply**.
4. Esperar 5–10 minutos a que diga **Live**. La dirección aparece arriba (`https://….onrender.com`).
5. Probar `https://….onrender.com/api/ready` → `{"ok":true}`.

## 4. Usar
- Abrir la dirección → **Docentes → Crear cuenta** → crear partida → el QR ya lleva a la dirección pública.
- Compartir la dirección: cualquiera puede ver el vocabulario, el simulador y los videos; los alumnos entran con el QR.

## Notas
- **Render Free se duerme** tras 15 minutos sin uso: la primera visita tarda alrededor de un minuto.
- Las imágenes y audios **del catálogo** vienen en el repositorio y no se pierden. Los archivos que un docente
  **suba o grabe** en la versión de internet se guardan en el servidor de Render, que se borra al reiniciar o volver
  a publicar. Para que sean permanentes: `STORAGE_BACKEND=supabase` y las variables `SUPABASE_URL`,
  `SUPABASE_SERVICE_KEY` y `SUPABASE_BUCKET` (ver `docs/NUBE_GRATUITA.md`).
- Cada `git push` a `main` vuelve a publicar solo (`autoDeployTrigger: commit`).
