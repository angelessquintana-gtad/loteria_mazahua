# Cambios: acceso docente, alumnos por QR, navegación y base de datos

Este documento resume las modificaciones hechas sobre el proyecto existente, qué archivos se tocaron y qué hay que ejecutar para aplicarlas. Se conservaron las tecnologías (FastAPI, Astro, MariaDB), el diseño visual y las funciones que ya existían (lector RFID, simulador, vocabulario, videos, audios en español).

## Qué debo ejecutar

1. Encender **MySQL** en XAMPP.
2. Si descomprimes en una carpeta nueva, ejecuta **`1_INSTALAR.bat`** (instala y compila).
3. Ejecuta **`2_INICIAR_SISTEMA.bat`**. Al arrancar, el sistema detecta la estructura anterior de la base de datos y la convierte sola:
   - primero guarda un respaldo completo en `sql/respaldos/respaldo_antes_de_migrar_<fecha>.sql`;
   - después crea las tablas nuevas, copia la información y elimina las tablas anteriores;
   - si algo fallara, restaura las tablas anteriores sin perder datos.
   En la ventana negra aparece «Migración terminada: … tarjetas, … imágenes, … audios».
4. Abre http://127.0.0.1:8000 → **Crear cuenta de docente** → inicia sesión con tu correo.

Alternativa: importar `sql/base_de_datos_mazahua.sql` en phpMyAdmin (tu base ya convertida). Reemplaza las tablas.

## 1. Registro e inicio de sesión del docente

- Portada con **Iniciar sesión como docente** y **Crear cuenta de docente**.
- Registro: nombre completo, correo, contraseña (mínimo 6) y confirmación. Se valida el formato del correo, que no esté repetido y que las contraseñas coincidan (en el navegador y en el servidor). Al registrarse aparece el mensaje de confirmación y el formulario de inicio de sesión con su correo.
- Inicio de sesión: **solo correo y contraseña**, con «¿Olvidaste tu contraseña?».
- Se eliminaron las solicitudes de cuenta, aprobaciones, roles de administrador e invitaciones.

## 2. Recuperación de contraseña

- «¿Olvidaste tu contraseña?» → correo → enlace válido **30 minutos y de un solo uso**. En la base solo se guarda el hash del enlace; las contraseñas se guardan con hash PBKDF2-SHA256.
- Al cambiarla se cierran las sesiones anteriores y se muestra la confirmación.
- Con correo SMTP configurado en `.env` (por ejemplo Gmail), el enlace llega por correo. Sin correo configurado (uso local), el enlace aparece en la ventana del servidor y en pantalla solo si la solicitud se hace desde la misma computadora del servidor.
- Respaldo: `3_CREAR_O_RECUPERAR_CUENTA.bat` pone una contraseña nueva desde la computadora del servidor.

## 3. Permisos del docente

Con la sesión iniciada, todo docente entra a su **panel** (`/panel`) y puede: crear partidas (nombre y límite de alumnos), generar el QR, ver los alumnos que se unen, iniciar, anunciar cartas (lector RFID o **número de carta**) y finalizar; agregar, editar y eliminar tarjetas; subir, reemplazar y eliminar imágenes y audios, y reproducirlos. Cada partida solo la administra el docente que la creó.

## 4. Alumnos solo por código QR

- El QR lleva a `/estudiante?codigo=XXXXXX`. Antes de pedir el nombre se valida que la partida exista, esté en espera y tenga lugares; si no, se explica el motivo y el botón se desactiva.
- El servidor vuelve a validar al unirse: partida inexistente, ya comenzada, cerrada o llena.
- Los alumnos solo pueden: entrar, esperar, ver su tablero, marcar, escuchar la pronunciación (botón «🔊 Escuchar pronunciación») y cantar lotería.
- Rutas protegidas en el servidor: si un alumno escribe `/panel`, `/editar`, `/docente`, `/administracion` o `/cuenta`, se le envía a la pantalla de acceso; la API responde 401 a cualquier operación de docente.
- La pantalla del alumno ya no tiene enlaces al resto del sistema.

## 5. Navegación

En todas las pantallas (excepto la del alumno): **⌂ Inicio** (lleva al panel si hay sesión o a la portada si no), **← Regresar** y, con sesión, el nombre del docente y **Cerrar sesión**.

## 6. Base de datos (MariaDB)

| Tabla nueva | Contenido | Relaciones |
|---|---|---|
| `usuarios` | id, nombre, correo (único), password_hash, fecha_registro | — |
| `tarjetas` | **tabla única:** id, numero (único), nombre_espanol, nombre_mazahua, descripcion, imagen, audio_mazahua, audio_espanol, uid_rfid (opcional, único) | — |
| `partidas` | id, codigo (único), nombre, usuario_id, limite, estado, fecha_creacion, iniciada, finalizada… | FK → usuarios, FK → tarjetas (última carta) |
| `participantes` | id, partida_id, nombre, dispositivo, fecha_ingreso, gano | FK → partidas (cascada) |
| `tableros` | id, participante_id, creado | FK → participantes (cascada) |
| `tablero_tarjetas` | tablero_id, posicion, tarjeta_id, marcada | FK → tableros (cascada), FK → tarjetas |
| `anuncios` | id, partida_id, tarjeta_id, fecha | FK → partidas (cascada), FK → tarjetas |
| `sesiones` | jti, usuario_id, vence | FK → usuarios (cascada) |
| `recuperaciones_password` | token_hash, usuario_id, creada, vence | FK → usuarios (cascada) |

Tablas eliminadas o reorganizadas: `docentes` → `usuarios`; `tarjetas_rfid` → `tarjetas` (tabla única); `catalogo_asignaciones` → `tarjetas.numero`; `resultados_partida` → `participantes.gano`; `anuncios_partida` (guardaba una copia JSON de cada carta) → `anuncios`; `tableros` con JSON → `tableros` + `tablero_tarjetas`; `invitaciones_docentes` y `sesiones_docentes` se eliminaron. La columna `categoria` (no la pide el documento y estaba vacía) ya no se guarda.

Con tus datos: 55 tarjetas, 55 imágenes, 57 audios y 3 partidas con su historial se conservaron. `docentes` estaba vacía en tu respaldo, por eso cada docente crea su cuenta.

## 7. Material Loteria_Mazahua (audios, imágenes y textos)

- Se incorporaron las **54 grabaciones en español** (`audio_espanol.webm`), convertidas a `audio_espanol.m4a` para que también se escuchen en iPhone, en cada carpeta de `catalogo/`.
- **Corrección:** la tortilla ahora es **T'zeyi** (antes «Segi») con su nueva imagen; su descripción se actualizó.
- Las demás imágenes, audios en mazahua y textos eran iguales a los del proyecto. Se quitaron las copias PNG/WEBP repetidas que no se usaban: `catalogo/` pasó de 139 MB a 20 MB y quedó idéntico a tu material.
- Al iniciar, `sincronizar_material_catalogo()` (en `main.py`) aplica este material a tu base existente por número de carta: agrega el audio en español si la tarjeta no tenía, si era uno generado automáticamente o si su archivo ya no existe (los audios que subió o grabó el docente se respetan), y aplica la corrección de nombre.
- `sql/base_de_datos_mazahua.sql` y `docs/MATERIAL_VOCABULARIO.md` ya incluyen estos audios.

## 8. Mejoras del 20 de noviembre (tarde)

- **Grabar el audio en mazahua:** en *Administrar tarjetas* (`/editar`), junto al campo del audio en mazahua está **🎙 Grabar en mazahua con el micrófono** (igual que el de español). Al agregar una tarjeta, el audio en mazahua se puede subir **o** grabar. Archivos: `frontend/src/pages/editar.astro`, `static/editar-vocabulario.js`.
- **Ojito para ver la contraseña:** todos los campos de contraseña (iniciar sesión, crear cuenta, nueva contraseña y Mi cuenta) tienen un botón 👁 para mostrarla u ocultarla. Archivos: `static/ver-contrasena.js` (nuevo), `frontend/src/layouts/Pagina.astro`, `static/extras.css`.
- **Una sola tabla de tarjetas:** `imagenes` y `audios` se unieron a `tarjetas`, que ahora tiene en cada registro: `numero`, `nombre_espanol`, `nombre_mazahua`, `descripcion`, `imagen`, `audio_mazahua`, `audio_espanol` y `uid_rfid`. Al iniciar, `migracion.unificar_tarjetas()` convierte sola tu base actual (con respaldo previo en `sql/respaldos/`). Archivos: `main.py`, `migracion.py`, `generar_audios_espanol.py`, `sql/base_de_datos_mazahua.sql`, `sql/estructura_completa.sql`, `tests/verificar_acceso_jwt.py`.

## 9. Simulador con frijol y menú del docente

- **Simulador:** la casilla marcada muestra un **frijolito** (la misma imagen `static/frijol.svg` del juego real, de tamaño mediano) en lugar del círculo café. Archivo: `static/extras.css` (regla `.sim-casilla.marcada::after`).
- **Docente:** con sesión iniciada solo aparecen *Partidas*, *Tarjetas* y *Vocabulario* en todas las páginas (se quitaron Videos, Simulador y la opción *Lector RFID y videos* del panel). *Mi cuenta* y *Cerrar sesión* pasaron a un menú en la esquina superior derecha (inicial + nombre) con *Editar mis datos*, *Cambiar contraseña* y *Cerrar sesión*. Archivos: `static/navegacion.js`, `frontend/src/pages/panel.astro`, `frontend/src/layouts/Pagina.astro`, `frontend/src/pages/cuenta.astro`, `static/docente.html`, `static/extras.css`.

## 10. Nueva imagen e interactividad (23 de noviembre)

- **Logo** de la Lotería Mazahua en la barra superior, en la portada (animado; al tocarlo suelta flores, maíz y frijoles) y como ícono de la pestaña. Archivos: `static/img/` (logo sin fondo en .webp, favicon), `static/tema.js`.
- **Menú superior con botones** (íconos, efecto al pasar el mouse, botón de la página actual resaltado) y **títulos animados**: las letras entran rebotando, saltan al pasar el mouse y hacen «la ola» al tocarlas. Fuente Fredoka (SIL OFL) en `static/fonts/`.
- **Tarjetas estilo burbuja** en vocabulario, simulador, tablero y administración: esquinas redondeadas, brillo, sombra suave y animación al aparecer. En vocabulario, los audios son botones burbuja (🔊 Mazahua / 🔊 Español) y tocar la imagen reproduce la palabra en mazahua.
- **Tablero compacto**: el tablero del alumno y el del simulador caben completos en la pantalla (en celular la carta anunciada queda en una franja fija arriba).
- **Imágenes que no aparecían**: si falta el archivo, ahora se muestra una burbuja con la inicial y la palabra (en lugar de un hueco), y en *Tarjetas* la ficha se marca con «⚠ Falta el archivo de imagen» para volver a subirla. Causa encontrada: imágenes subidas desde el sistema que solo existían en la carpeta `uploads/` de otra computadora; el zip ahora incluye `uploads/`.
- **Avatar del alumno**: al entrar a la partida arma su avatar (7 categorías, «🎲 Sorpréndeme»). Se guarda en `participantes.avatar` y lo ve el docente, sus compañeros y la pantalla del ganador. Archivos: `static/avatar.js`, `partidas.py`, `migracion.asegurar_columnas()`.
- **Reacciones en vivo** por WebSocket (👏 😄 🌽 ❤️ 🎉 🤔, máximo una por segundo por alumno) que flotan con el avatar en todas las pantallas.
- **Modo proyector** para el docente: carta en pantalla completa con avatares y reacciones.
- **Celebraciones**: confeti con frijolitos al ganar, al completar el simulador y al entrar a la partida; frijol que cae al marcar.

## 11. Tablero a la medida, cartas en verde y avatares de animalitos (23 de noviembre, noche)

- **El tablero cabe en la pantalla de la computadora** (simulador y partida): su tamaño se calcula según el alto de la ventana (`ajustarTablero` en `static/tema.js`) y las imágenes se ven completas (proporción 3:4, sin recortar).
- **Cartas en verde:** las cartas del tablero que ya salieron y aún no tienen frijol se pintan de verde con la etiqueta «¡La tienes!». Las que no han salido no se pueden seleccionar (en el simulador y en la partida).
- **Avatares de animalitos:** conejo, gato, perrito, oso, coyote, búho, ajolote y venado, cada uno con 4 colores, 4 caras, 6 accesorios (flor, sombrero, moño, lentes, corona de flores) y 6 fondos, con paliacate. Archivo: `static/avatar.js`.
- **Imágenes que no se veían (niño, niña, bañarse, leña):** sus carpetas tenían «ñ» en el nombre (`0029_niño`…) y al descomprimir en Windows ese nombre se alteraba, así que el sistema no encontraba los archivos. Se renombraron sin «ñ» (`0029_nino`, `0030_nina`, `0044_banarse`, `0047_lena`) y al iniciar se corrigen solas las rutas en la base de datos (`RENOMBRES_CATALOGO` en `main.py`). Si usas la nube, vuelve a ejecutar `python deploy/subir_multimedia.py --subir`.

## Archivos modificados

**Backend**
- `autenticacion.py`: reescrito (usuarios, registro, login por correo, perfil, contraseña, recuperación).
- `seguridad.py`: permisos (público/alumno y docente).
- `middleware.py`: rutas protegidas, límites de intentos.
- `main.py`: tablas `tarjetas`, `imagenes`, `audios`; número de tarjeta, UID opcional, eliminar audios, `/panel`.
- `partidas.py`: nombre y dueño de la partida, tableros normalizados, anuncio por número, validaciones de ingreso, sin clave interna.
- `migracion.py` (nuevo): conversión automática con respaldo.
- `configurar_admin.py`, `cargar_datos_demo.py`, `generar_audios_espanol.py`, `configuracion.py`, `deploy/migrar_nube.py`: adaptados.

**Frontend**
- `frontend/src/pages/acceso.astro`, `cuenta.astro`, `editar.astro`, `panel.astro` (nuevo); `frontend/src/layouts/Pagina.astro`, `PaginaJuego.astro`.
- `static/acceso-docente.js`, `cuenta-docente.js`, `panel-docente.js` (nuevo), `navegacion.js` (nuevo), `sesion-docente.js`, `salas.js`, `editar-vocabulario.js`, `inicio.html`, `docente.html`, `estudiante.html`, `administracion.html`, `extras.css`, `partida.css`.

**Base de datos y scripts**
- `sql/base_de_datos_mazahua.sql` (tu base en la nueva estructura), `sql/estructura_completa.sql`; los scripts anteriores quedaron en `sql/estructura_anterior/`.
- `3_CREAR_O_RECUPERAR_CUENTA.bat` (antes `3_CREAR_ADMINISTRADOR.bat`); `iniciar_proyecto.bat` ahora llama a `2_INICIAR_SISTEMA.bat`.
- Eliminados por quedar sin uso: `invitar_docente.py`, `generar_clave.py`, `configurar_administracion.bat`, `tests/verificar_escuela.py`.

**Pruebas**: `tests/verificar_acceso_jwt.py` (reescrita para el nuevo sistema), `tests/verificar_salas.cjs`.
