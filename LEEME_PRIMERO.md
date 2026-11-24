# Lotería Interactiva Mazahua · Léeme primero

Sistema web de la Lotería Mazahua para **Sistemas Operativos II**: backend con **FastAPI**, frontend con **Astro** y base de datos **MySQL** (la misma base `loteria_mazahua` de siempre).

## Arranque rápido (Windows)

| Paso | Qué hacer | Archivo |
|---|---|---|
| 0 | Encender **MySQL** desde el panel de XAMPP (botón *Start* de MySQL). | — |
| 1 | Instalar todo (solo la primera vez). | `1_INSTALAR.bat` |
| 2 | Iniciar el sistema y abrir el navegador. | `2_INICIAR_SISTEMA.bat` |
| 3 | En la portada: **Crear cuenta de docente** (nombre, correo, contraseña de 6+) y luego **Iniciar sesión** con tu correo. | (respaldo: `3_CREAR_O_RECUPERAR_CUENTA.bat`) |
| 0.5 | Solo en una computadora nueva: importar `sql/base_de_datos_mazahua.sql` en phpMyAdmin. Si ya tienes tu base, se convierte sola al iniciar. | — |
| 4 | (Opcional) agregar las palabras del catálogo que falten, sin borrar nada. | `4_CARGAR_PALABRAS_DEMO.bat` |
| 5 | (Solo para tarjetas nuevas sin audio en español) generarlo con la voz de Windows. Las 54 cartas ya traen su audio en español grabado. | `5_GENERAR_AUDIOS_ESPANOL.bat` |

Después abre **http://127.0.0.1:8000**. Para modificar el vocabulario inicia sesión en **/acceso** y entrarás al editor sencillo **/editar**. El paso a paso detallado, con capturas de qué esperar y solución de problemas, está en **`MANUAL_DE_EJECUCION.pdf`** (misma información en `MANUAL_DE_EJECUCION.md`).

> **Importante:** si ya usabas el proyecto, copia tu carpeta **`uploads/`** original dentro de esta carpeta. Ahí están las imágenes y audios que subiste desde Administración; la copia comprimida que se recibió no la incluía. La carpeta `catalogo/` sí viene completa.

---

## ¿Dónde está cada cosa?

### BACKEND (FastAPI · Python) → archivos `.py` de la carpeta principal

| Archivo | Para qué sirve |
|---|---|
| `main.py` | **Archivo principal del backend.** Tabla única `tarjetas` (nombres, descripción, imagen y audios) y los endpoints para agregar, consultar, buscar, editar y eliminar tarjetas, subir/eliminar imágenes y audios, QR y videos de YouTube. |
| `database.py` | Conexión con MySQL (lee el archivo `.env`). |
| `configuracion.py` | Variables de configuración (desarrollo/producción, sesiones, tiempos). |
| `autenticacion.py` | Tabla `usuarios`: crear cuenta, iniciar sesión con correo, sesiones y recuperación de contraseña. |
| `seguridad.py` | Qué rutas son públicas (alumnos) y cuáles requieren sesión de docente. |
| `migracion.py` | Convierte sola la base de datos anterior a la nueva estructura (con respaldo). |
| `middleware.py` | Protección HTTP: sesión, CSRF, límite de tamaño de archivos (30 MB). |
| `partidas.py` | Tablas `partidas`, `participantes`, `tableros`, `tablero_tarjetas` y `anuncios`; juego en vivo (WebSocket). |
| `almacenamiento.py` | Guardado de archivos en la nube (solo para la versión publicada). |
| `frontend_web.py` | Entrega las páginas compiladas de Astro desde FastAPI. |
| `cargar_datos_demo.py` | Carga el catálogo en MySQL con UID de demostración. |
| `generar_audios_espanol.py` | Genera los audios en español faltantes con la voz de Windows. |
| `abrir_navegador.py` | Abre el navegador cuando el servidor ya está listo. |
| `configurar_admin.py` | Respaldo: crear una cuenta docente o ponerle una contraseña nueva desde la consola. |
| `serial_bridge.py` | Puente opcional del lector RFID por USB. |
| `requirements.txt` | Lista de librerías de Python del backend. |
| `.env` | Datos de conexión a MySQL (usuario, contraseña, nombre de la base). |
| `videos_youtube.json` | **Aquí van los enlaces de YouTube** (también se editan desde Administración). |

### FRONTEND (Astro) → carpetas `frontend/` y `static/`

| Ruta | Para qué sirve |
|---|---|
| `frontend/src/pages/` | **Páginas de Astro**: `index` (inicio), `acceso` (iniciar sesión / crear cuenta / recuperar), `panel` (panel del docente), `editar` (tarjetas), `docente` (partidas), `estudiante` (alumnos), `vocabulario`, `simulador`, `videos`, `administracion`, `docente`, `estudiante`, `acceso`, `cuenta`. |
| `frontend/src/layouts/` | Plantillas compartidas (encabezado, menú y pie de página). |
| `frontend/astro.config.mjs` | Configuración de Astro (incluye el enlace con el backend en modo desarrollo). |
| `frontend/package.json` | Dependencias y comandos del frontend (`npm run build`, `npm run dev`). |
| `frontend/dist/` | Páginas ya compiladas que sirve FastAPI (se generan solas). |
| `static/` | Estilos (`.css`) y scripts (`.js`) del navegador. Los más relevantes: `acceso-docente.js` (cuentas), `navegacion.js` (Inicio/Regresar y menú de la cuenta del docente en la esquina), `salas.js` (partidas y alumnos), `vocabulario.js` (catálogo y búsqueda), `simulador.js` (dinámica de lotería), `videos.js` (miniaturas de YouTube), `administracion.html` + `admin-videos.js` (CRUD y enlaces), `extras.css` (estilos de videos y simulador). |

### BASE DE DATOS (MySQL) → carpeta `sql/`

| Archivo | Para qué sirve |
|---|---|
| `sql/base_de_datos_mazahua.sql` | **Tu base de datos en la nueva estructura** (tabla única `tarjetas` con nombres, descripción, imagen y audios; usuarios, partidas, participantes y tableros) con tus 55 tarjetas. Se importa en phpMyAdmin. |
| `sql/estructura_anterior/` | Tu base y los scripts de la versión anterior (solo como referencia). |
| `sql/respaldos/` | Se crea sola: respaldo automático antes de convertir tu base. |
| `sql/estructura_completa.sql` | Estructura de las 11 tablas. Es seguro: no borra nada. |
| `sql/crear_base_datos.sql` | Crea la base `loteria_mazahua` vacía. |
| `EXPORTAR_BASE_DATOS.bat` | Genera `sql/respaldo_loteria_mazahua.sql` con **estructura y registros** de tu base real (para entregar). |

### MULTIMEDIA

| Carpeta | Contenido |
|---|---|
| `catalogo/` | Material **Loteria_Mazahua** (54 cartas): `imagen`, `audio_mazahua.m4a`, **`audio_espanol.m4a`** (grabación en español), `datos.txt` y `miniatura.webp` (versión ligera para las listas). |
| `uploads/imagenes`, `uploads/audios` | Archivos subidos desde Administración (se crean solos). |
| `docs/MATERIAL_VOCABULARIO.md` | Lista de las 55 tarjetas con la ruta exacta de su imagen y sus audios. |

### DOCUMENTACIÓN → carpeta `docs/`

| Archivo | Contenido |
|---|---|
| `MANUAL_DE_EJECUCION.pdf` / `.md` (carpeta principal) | Cómo instalar, ejecutar y usar el sistema paso a paso. |
| `docs/CAMBIOS_ACCESO_Y_BASE_DE_DATOS.md` | **Qué cambió en esta versión**, qué archivos se modificaron y qué ejecutar. |
| `docs/DOCUMENTACION_TECNICA.md` | Arquitectura, tecnologías, base de datos, configuración y endpoints. |
| `docs/CUMPLIMIENTO.md` | Cada requisito del documento del proyecto y dónde se cumple. |
| `docs/DEMOSTRACIONES.md` | Guion sugerido de los videos de YouTube. |
| `README.md` | Documentación general previa del proyecto (seguridad, despliegue). |

### OTROS

| Ruta | Contenido |
|---|---|
| `esp32/` | Programa del lector RFID (ESP32 + RC522). Corresponde a otras asignaturas. |
| `deploy/`, `Dockerfile`, `compose.yaml`, `render.yaml` | Archivos para publicar en la nube (no se necesitan para ejecutarlo localmente). |
| `tests/` | Pruebas automáticas del proyecto. |

## Publicar en internet (GitHub + Vercel + Render + Supabase)

Ver **`docs/DESPLIEGUE_VERCEL_RENDER_SUPABASE.md`**: pasos y una instrucción lista para tu asistente de IA.

## Novedades del 23 de noviembre

Nuevo diseño con el logo, menú con botones, títulos animados, tarjetas tipo burbuja, tablero que cabe en la pantalla, avatar del alumno, reacciones en vivo y modo proyector. Detalle en `docs/CAMBIOS_ACCESO_Y_BASE_DE_DATOS.md` (sección 10). Si ya tenías el proyecto: copia tu carpeta `uploads\` (imágenes y audios que subiste) a la carpeta nueva y ejecuta `2_INICIAR_SISTEMA.bat`; la base se actualiza sola (agrega la columna del avatar).

## Publicar en internet con un solo enlace

GitHub + Render + TiDB Cloud (todo gratis): ver **`docs/PUBLICAR_EN_INTERNET.md`**.
