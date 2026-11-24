# Cumplimiento de los requisitos · Sistemas Operativos II

Relación entre cada punto del documento *Proyecto Integrador: Lotería Interactiva para el Fortalecimiento de la Lengua Mazahua* y el lugar del proyecto donde se cumple.

## A. Backend con FastAPI

| Requisito | Cumplimiento | Dónde |
|---|---|---|
| API REST con FastAPI | ✔ | `main.py`, `partidas.py`, `autenticacion.py` |
| Endpoints para consultar los elementos | ✔ `GET /api/vocabulario`, `/api/vocabulario/{id}`, `/api/tarjetas`, `/api/tarjetas/{id}`, `/api/uid/{uid}` | `main.py` |
| Registrar, modificar, consultar y eliminar | ✔ `POST`, `PUT`, `GET`, `DELETE /api/tarjetas`; editor sencillo en `/editar` | `main.py`, `static/editar-vocabulario.js` |
| Buscar | ✔ parámetro `?buscar=` (palabra, número o UID); buscadores en Vocabulario y en Administrar tarjetas | `main.py`, `static/vocabulario.js`, `static/administracion.html` |
| Nombre en español y mazahua, descripción, imagen y audio | ✔ (audio en mazahua y su equivalente en español; descripción por defecto si se deja vacía) | modelo `Tarjeta` en `main.py` |
| Base de datos | ✔ MariaDB `loteria_mazahua`: tabla única `tarjetas` (nombres, descripción, imagen y audios), usuarios, partidas, participantes y tableros (+ relaciones) | `database.py`, `sql/base_de_datos_mazahua.sql` |
| Módulos y rutas organizados | ✔ un módulo por responsabilidad y etiquetas en Swagger | ver `docs/DOCUMENTACION_TECNICA.md` §4 |
| Documentación con Swagger UI | ✔ `/docs` (y `/redoc`) | FastAPI |

## B. Frontend con Astro

| Requisito | Cumplimiento | Dónde |
|---|---|---|
| Interfaz interactiva y responsiva | ✔ | `frontend/src/pages`, `static/*.css` |
| Catálogo con tarjetas visuales | ✔ `/vocabulario` | `vocabulario.astro`, `static/vocabulario.js` |
| Imágenes y palabras en español y mazahua | ✔ | Vocabulario, Simulador, Administración |
| Reproducir los audios de pronunciación | ✔ reproductores por carta y secuencia mazahua → español | `vocabulario.js`, `simulador.js`, `audio-secuencia.js` |
| Consumir los endpoints de FastAPI por HTTP | ✔ `fetch('/api/...')` en todas las páginas | `static/*.js` |
| Simular o ejecutar la dinámica de la lotería | ✔ `/simulador` (individual, sin cuenta) y `/docente` + `/estudiante` (en grupo) | `simulador.js`, `salas.js` |
| Enlaces de YouTube con muestras del proyecto | ✔ `/videos`: miniaturas que abren YouTube; enlaces editables desde Administración o `videos_youtube.json` | `videos.astro`, `static/videos.js`, `admin-videos.js` |

## C. Integración y funcionamiento

| Requisito | Cumplimiento |
|---|---|
| Integrar Astro con FastAPI | ✔ FastAPI sirve `frontend/dist` bajo el mismo origen; en desarrollo, Astro reenvía `/api` al puerto 8000 (`astro.config.mjs`). |
| La información proviene de la API | ✔ ninguna página contiene el catálogo escrito en el código. |
| Multimedia se consulta y reproduce | ✔ `/catalogo` y `/uploads` (imágenes y audios). |
| Preparado para la electrónica | ✔ `POST /api/esp32/uid`, lectura USB desde el navegador y firmware en `esp32/`. |

## 4. Entregables

| # | Entregable | Ubicación |
|---|---|---|
| 1 | Proyecto funcional | Carpeta completa; ejecutar `1_INSTALAR.bat` y `2_INICIAR_SISTEMA.bat` |
| 2 | Base de datos (estructura y registros) | `sql/base_de_datos_mazahua.sql` (55 tarjetas con su material); `sql/estructura_completa.sql`; listado en `docs/MATERIAL_VOCABULARIO.md` |
| 3 | Integración API-Frontend | Páginas de Vocabulario, Simulador y Videos (pestaña *Red* del navegador muestra las llamadas a `/api`) y Swagger UI |
| 4 | Recursos multimedia | `catalogo/` (54 imágenes y audios) y `uploads/`; detalle en `docs/MATERIAL_VOCABULARIO.md` |
| 5 | Documentación técnica | `docs/DOCUMENTACION_TECNICA.md`, `MANUAL_DE_EJECUCION.pdf`, `LEEME_PRIMERO.md` |
| 6 | Evidencias en video (YouTube) | Página `/videos`; guion en `docs/DEMOSTRACIONES.md`. **Pendiente: pegar los enlaces reales del equipo.** |
| 7 | Código fuente | Esta carpeta (repositorio Git incluido) |

## Validación realizada

Las pruebas automáticas existentes (`tests/`) se ejecutaron correctamente después de los cambios. Además, se importó `base_de_datos_mazahua.sql` en MySQL/MariaDB, el backend la actualizó sin perder registros y desde el navegador se comprobaron el registro con imagen y audios, la búsqueda, la edición, la eliminación, la descripción por defecto, el guardado de enlaces de YouTube y una partida completa en el simulador. La lectura física con el ESP32 no se volvió a probar en esta revisión, ya que no se modificó esa parte.

## Mejoras de acceso y permisos (20 nov 2026)

Registro libre de docentes con correo, inicio de sesión con correo y contraseña (mínimo 6), recuperación por enlace temporal de un uso, panel del docente, alumnos solo por QR con validación de partida activa y cupo, navegación Inicio/Regresar/Cerrar sesión y base de datos reorganizada con claves foráneas. Detalle en `docs/CAMBIOS_ACCESO_Y_BASE_DE_DATOS.md`.
