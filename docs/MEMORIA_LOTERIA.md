# Memoria de la conversación · Lotería Mazahua

Última actualización: 19 de noviembre de 2026.

## Estado vigente: publicado en nube gratuita, conservando MySQL

Esta sección sustituye las afirmaciones históricas de «no publicado» de más abajo.

- URL final: **https://loteria-mazahua-escuela.onrender.com**. Panel Render: servicio `srv-dbvdvge7bikc738bdlvg`, región Frankfurt, plan Free, proyecto existente Loteria_mazahua. Docker command `python deploy/iniciar_render.py`; health `/api/ready`; despliegues automáticos desactivados. Última versión de ejecución verificada: commit `fc28db7`.
- El usuario confirmó que MySQL es obligatorio por su documentación. **No se migró a PostgreSQL.** Filess.io Shared Free aloja MySQL 8 en Nürnberg; pool de app 2+1, espera de 60 s y conexión TLS comprobada.
- Supabase se usa exclusivamente como Storage, proyecto `ocgiurkiiadfdhwlzcmf`, organización separada Loteria Mazahua, bucket `loteria-media`. Se copiaron 271 archivos de catálogo y uploads referenciados (148,181,937 bytes). Lectura pública de materiales educativos; escrituras privadas del backend. No se tocaron los otros proyectos de Supabase.
- El usuario autorizó explícitamente crear repositorio privado y subir código. Repositorio: **https://github.com/Jose78123/loteria-mazahua**. Se inició Git local y se subió código, metadata de catálogo, manifiesto y verificaciones; se excluyeron credenciales, `.venv`, node_modules, uploads, binarios del catálogo y respaldos. `sql/Practica VUELOS.sql` es trabajo ajeno a esta tarea y quedó sin agregar ni modificar.
- Se copió la base a tablas remotas vacías: 54 tarjetas, 54 asignaciones de catálogo, 1 docente, 2 partidas, 1 participante, 1 tablero y anuncios existentes. No se copiaron sesiones/invitaciones; se usa otra firma JWT. La cuenta existente se designó administradora **solo en el destino** y se comprobó igualdad del hash de contraseña con el origen. No se sobrescribió `.env` local ni se borraron los archivos locales.
- La instancia inicial de Oregón `srv-dbv7bdajnfac73cr3gl0`, URL `loteria-mazahua-asfa.onrender.com`, quedó **suspendida** tras detectar latencia alta. No usar ni reactivar esa URL para operación normal; no se eliminaron recursos ajenos.
- `almacenamiento.py` guarda/borrar objetos con clave privada, conserva rutas de MySQL `/uploads` y `/catalogo` mediante redirecciones y normaliza nombres con acentos mediante claves ASCII deterministas. `catalogo_manifest.json` permite registrar tarjetas del catálogo sin subir binarios al repositorio.
- Se corrigió el coste de conexiones por alumno: un productor WebSocket por sala consulta estado y tableros en lote, sin exponer tableros ajenos ni tokens. Se verifican las sesiones docentes vigentes en cada actualización. Tableros se insertan en lote; marcas usan bloqueo compartido de sala y exclusivo por tablero para preservar actualizaciones concurrentes.
- Render Free bloquea SMTP habitual. Se dejó soporte opcional Brevo por HTTPS, **sin configurar cuenta ni clave de correo real**. El administrador puede generar enlaces de recuperación de un uso desde Mi cuenta, por lo que los docentes no necesitan al desarrollador. Para emergencia del último administrador existe `deploy/configurar_admin_nube.py` con configuración privada y confirmación interactiva.

### Pruebas reales y límites actuales

Prueba corta contra la publicación final: 25 ingresos y 25 WebSocket correctos, 16 cartas por tablero, inicio, anuncios, marcas de 12 alumnos y dos marcas simultáneas de un alumno sin pérdida; limpieza exclusiva de sala/sesión de prueba. Métricas en `docs/PRUEBA_NUBE.json`: ingreso conjunto 3.369 s; iniciar 0.387 s; apertura+primer tablero máximo 16.07 s desde el cliente de prueba; anunciar 0.404 s; recibir anuncio máximo 0.682 s; marcar máximo 1.309 s. Datos+índices durante prueba: 704,512 bytes.

Se comprobaron 18 muestras multimedia con rangos HTTP 206, acentos y tipos de contenido correctos, y metadata de dos audios en navegador. También pasaron las suites aisladas `verificar_acceso_jwt`, `verificar_produccion`, `verificar_archivos_nube`, regresión JS de salas, Astro check y build, y Docker se construyó y arrancó realmente en Render. No afirmar prueba física del lector, reproducción escuchada de todos los audios, 25 dispositivos reales ni disponibilidad garantizada o clase prolongada.

### Secretos y operación

No hay secretos en esta memoria ni en Git. La configuración de despliegue quedó en `deploy/.cloud-secrets.json`, ignorada y restringida por permisos Windows al usuario y SYSTEM; `deploy/.cloud-uploaded.json` guarda el progreso de archivos. El puente de configuración solo escuchó en loopback y se **cerró** al terminar de transferir variables a Render. No publicar ni adjuntar esos archivos.

Guía actual: `docs/NUBE_GRATUITA.md`. Render duerme tras inactividad; Supabase puede pausar; Filess.io limita a 10 MB. Retención de partidas en nube: 1 día, sin borrar catálogo/cuentas. Los respaldos de migración están en `deploy/backups/`; aún hace falta establecer una rutina institucional de respaldos externos de los datos nuevos. El temporizador de Oracle no se ejecuta en Render. Siguiente paso con el usuario: iniciar sesión en `/acceso` con su cuenta anterior, nombrar segundo responsable y probar lector físico en Chrome/Edge mediante HTTPS.

## Actualización vigente: entrega autónoma a la secundaria

Esta sección sustituye las instrucciones históricas de invitaciones y permisos que aparecen más abajo. El proyecto está en `C:\Users\213w3\OneDrive\Escritorio\registro_rfid_mazahua`; se movió desde `OneDrive\Documentos\Carpetas del escritorio\registro_rfid_mazahua` a petición del usuario. No borrar este proyecto ni sus recursos durante limpiezas.

El usuario pidió implementar administración escolar sin depender de su presencia y preparar publicación en nube. Se implementó:

- Roles `administrador` y `docente`, estado de solicitud y correo único opcional para cuentas anteriores. Nuevas solicitudes exigen correo. Migración aditiva en `main.inicializar_base`; no promueve cuentas antiguas ni modifica catálogo/audios.
- `/acceso` permite **Solicitar cuenta docente** sin invitación. `POST /api/auth/solicitudes` crea cuenta pendiente/inactiva y no emite sesión. Rechazar/aprobar requiere administrador.
- `/cuenta` muestra al administrador una lista paginada y filtrada de cuentas, aprobación/rechazo, activar/desactivar y cambio de rol. Impide desactivar/degradar al último administrador activo. Los cambios revocan sesiones y enlaces de recuperación de la cuenta; al retirar permisos administrativos invalida sus invitaciones pendientes.
- Solo administradores pueden gestionar cuentas, invitaciones y catálogo (incluidas escrituras de tarjetas). Docentes aprobados pueden consultar tarjetas, crear/controlar partidas y utilizar el lector. El rol se consulta en MySQL en cada solicitud. Invitaciones quedan opcionales y crean docentes sin permisos administrativos.
- `configurar_administracion.bat` ahora ejecuta un asistente de **creación/promoción/recuperación del administrador escolar**, no genera invitaciones. Pide usuario, nombre si es nuevo, correo, contraseña oculta y confirmación. Si existe cambia contraseña y promueve esa cuenta. Ejecutarlo una vez con el responsable y nombrar luego un suplente desde la web.
- Mi cuenta permite actualizar correo confirmando contraseña. Recuperación mediante SMTP cifrado (STARTTLS/SSL), enlace de 30 minutos y un uso, token almacenado con hash y revocación de sesiones. Se usa fragmento `#recuperar=` para evitar token en URL enviada al servidor; la interfaz también admite abrir el enlace en una pestaña de acceso ya abierta.
- `correo.py` implementa transporte; sin configuración informa indisponibilidad. La respuesta no revela si existe el correo. SMTP tiene timeout y errores sin secretos en registros. Aprobaciones no envían notificaciones: el responsable comunica la decisión.
- Se añadieron variables de correo a los ejemplos y Compose, red de salida SMTP para app manteniendo MySQL interno y los archivos nuevos en Dockerfile. `PUBLIC_URL` en Compose usa `https://DOMAIN`.
- `docs/ENTREGA_SECUNDARIA.md` explica operación, viabilidad, requisitos y entrega. README y `deploy/ORACLE.md` reflejan los roles y el nuevo asistente.

### Verificaciones de esta actualización

Pasaron `tests.verificar_acceso_jwt` y `tests.verificar_produccion`, ambos con SQLite aislado. Incluyen migración desde esquema sin roles/correo, repetición de migración, conservación de cuenta anterior, asistente administrador, solicitud/aprobación/rechazo, límites de permisos, último administrador, correo duplicado, recuperación caducada/reutilizada, cierre de sesiones y transporte SMTP simulado en ambas modalidades y ante fallo. Las comprobaciones nuevas están en `tests/verificar_escuela.py`, llamadas desde las dos suites.

También pasaron `node tests/verificar_salas.cjs`, `verificar_audio.cjs`, `verificar_lector.cjs`, `verificar_admin_lector.cjs`; `npm --prefix frontend run check` (11 archivos, cero errores/advertencias); `npm --prefix frontend run build` (7 páginas); y `docker compose --env-file deploy/.env.example config --quiet`.

Se comprobaron en navegador las páginas compiladas con API simulada: solicitud sin código, formulario de recuperación, cambio de contraseña, aprobación, ocultación de controles administrativos a docentes y diseño móvil de 390 px sin desbordamiento horizontal. No confundir estas comprobaciones con una sesión real contra MySQL o SMTP.

### Pendiente para la instalación real

**No está publicado en nube. No se ha ejecutado la migración contra MySQL real ni se ha creado/promovido una cuenta real en esta sesión.** Tampoco se configuraron secretos SMTP ni se enviaron correos reales, ni se probó hardware físico, Docker build/arranque ni carga de una clase.

Siguiente paso local: respaldar datos, reiniciar con MySQL activo y `AUTO_MIGRATE=true`, ejecutar `configurar_administracion.bat` con el responsable y probar solicitud/aprobación. Después elegir alojamiento/dominio bajo cuentas institucionales, configurar SMTP y desplegar según guía. El backup diario existente requiere activar el temporizador en la VPS; guardar copias fuera de ella sigue requiriendo un destino. Viabilidad condicionada a Internet, alojamiento persistente, responsable y prueba de clase; el dimensionamiento sugerido es estimación, no capacidad medida.

## Cómo recuperar el contexto

Frase elegida por el usuario para futuras sesiones: **«loteriaa!»**. También reconocer **«loteriaa»** y la frase anterior **«recuperar memoria loteria»**, ignorando mayúsculas, acentos y signos finales.

`AGENTS.md` indica leer este archivo cuando aparezca esa frase. Se añadió además una regla global en `C:\Users\213w3\.config\opencode\AGENTS.md` que apunta aquí, para recuperar el contexto aunque OpenCode se abra fuera de la carpeta del proyecto. Esta es una memoria resumida de la conversación y de las decisiones tomadas; no es una transcripción literal. Antes de actuar, comprobar el estado actual del proyecto.

### Contexto de este chat que debe recordarse

- El usuario estaba preocupado por la desaparición del proyecto tras una limpieza de la laptop y había pedido conservarlo. Se encontró `registro_rfid_mazahua` en `OneDrive\Documentos\Carpetas del escritorio\` y se movió al Escritorio a petición suya. No atribuir ni afirmar un borrado que no se haya comprobado. No borrar la lotería ni sus recursos en futuras limpiezas. También se encontró `Downloads\registro_rfid_mazahua_actualizado.zip`; no se verificó como versión más reciente.
- El usuario necesita instrucciones claras en español. Para cableado pidió usar las etiquetas impresas de los pines, **sin decir GPIO**. El firmware `esp32/esp32_rc522_post_uid.ino` utiliza RC522: SDA/SS → 5/D5, SCK → 18/D18, MOSI → 23/D23, MISO → 19/D19, RST → 2/D2, VCC → 3V3, GND → GND, IRQ sin conectar. RX/TX no se usan. No alimentar RC522 con 5 V. Confirmar modelo de placa si sus etiquetas no coinciden. USB de datos y serie a 115200 baudios; cerrar Monitor Serie antes de usar Web Serial.
- En local se arranca MySQL y `iniciar_proyecto.bat`; se abre `http://127.0.0.1:8000`. Para la entrega se usa la URL pública vigente de arriba, sin dejar computadoras de la escuela encendidas como servidores.
- El sistema se entregará a una secundaria. El usuario quiere que docentes se registren por solicitud y que responsables escolares aprueben sin depender de él ni de códigos emitidos por consola. Ese flujo y la separación de roles ya están implementados.
- La alternativa inicial fue Oracle Cloud; el registro rechazó una tarjeta Nu. No se guardan datos bancarios en la memoria. El usuario exigió alojamiento completamente gratuito y sin servidor local escolar.
- Se consideró PostgreSQL, pero el usuario corrigió que su documentación ya especifica **MySQL**. Conservar MySQL. JSON se usa para manifiestos/exportación, no como reemplazo de la base concurrente de partidas.
- Se eligió Render Free + Filess.io MySQL Free + Supabase Storage Free. Se revisó el tamaño de la base (originalmente unos 0.59 MB) y se midió multimedia. Se configuraron los servicios y la publicación final indicada arriba; no volver a presentar estos pasos como si aún no se hubieran hecho.
- El usuario autorizó mediante pregunta explícita crear y subir el repositorio privado en GitHub. Durante las pruebas se detectaron y corrigieron problemas de consultas/conexiones y se movió la aplicación de Oregón a Frankfurt; la instancia anterior está suspendida.
- La sesión se guarda como resumen de todo este contexto y del trabajo técnico, con las mediciones y pendientes de las secciones vigentes. Al oír «loteriaa!» confirmar que se trata de la Lotería Mazahua publicada para la secundaria y retomar desde la nueva petición, sin inventar memoria literal ni ejecutar cambios no solicitados.

## Proyecto y objetivo

- Carpeta: `registro_rfid_mazahua`.
- Ruta local de esta sesión: `C:\Users\213w3\OneDrive\Escritorio\registro_rfid_mazahua`.
- Nombre de la aplicación: **Lotería Mazahua**.
- Aplicación educativa bilingüe, español y mazahua, con catálogo, imágenes, pronunciación, partidas entre docente y estudiantes y lectura RFID mediante ESP32 + RC522.
- El usuario solicita acciones concretas sobre el proyecto y respuestas en español.
- Para trabajos académicos, seguir las preferencias de redacción de `AGENTS.md`.

## Requisitos solicitados por el usuario

### Backend

FastAPI, API REST, consulta y CRUD del vocabulario, MySQL, organización modular y documentación Swagger UI. Cada elemento debe tener nombre en español, nombre en mazahua, descripción, imagen y audio.

### Frontend

Astro, interfaz interactiva y responsiva, catálogo mediante tarjetas visuales, palabras bilingües, imágenes, audios y consumo de la API. Debe permitir la dinámica de lotería desde el navegador.

### Integración

Los datos del catálogo deben proceder de la API. Los recursos multimedia deben ser accesibles y el sistema debe integrarse con los componentes electrónicos.

### Aclaraciones importantes

- **YouTube corresponde a la documentación**, no es obligatorio mostrar videos en la interfaz de estudiantes.
- El usuario confirmó que ya había comprobado **MySQL, creación de registros, partidas, carga y reproducción multimedia y lectura física del RFID**.
- No presentar esas comprobaciones previas del usuario como pruebas físicas nuevas realizadas por el agente.

## Implementación realizada

### Astro y catálogo

- Se añadió el proyecto Astro en `frontend/`, con `package.json`, archivo de bloqueo de dependencias y configuración.
- Se instaló Astro **7.4.11** durante la sesión, después de detectar vulnerabilidades en una versión anterior. Verificar el archivo de bloqueo para conocer la versión efectiva futura.
- Páginas: portada, acceso, cuenta, vocabulario, docente, estudiante y administración.
- `frontend/src/layouts/PaginaJuego.astro` reutiliza las plantillas HTML existentes de `static/` durante la compilación para conservar el funcionamiento del juego.
- Las páginas nuevas de acceso, cuenta y vocabulario usan estructura Astro propia.
- `frontend_web.py` permite que FastAPI entregue `frontend/dist` bajo el mismo origen que la API y los WebSocket.
- **No borrar las plantillas HTML de `static/`**: siguen siendo entradas utilizadas por Astro.
- **No publicar `frontend/dist` con un servidor estático independiente** sin adaptar la protección: las páginas privadas deben pasar por FastAPI.
- La ruta `/vocabulario` muestra una galería con búsqueda, imágenes, palabras bilingües, descripción y controles de audio.
- `GET /api/vocabulario` es público, de solo lectura y no expone UID RFID.
- Se añadió `Tarjeta.descripcion`, su migración aditiva, los campos de formularios y su devolución en la API.
- Las descripciones anteriores quedan vacías hasta que el docente las complete; no se inventaron textos.

### Cuentas docentes y seguridad

El usuario pidió que solo los docentes pudieran administrar el vocabulario y que el registro administrativo no apareciera en la pantalla de estudiantes.

- `autenticacion.py` implementa cuentas docentes personales y las tablas `docentes`, `invitaciones_docentes` y `sesiones_docentes`.
- Contraseñas: PBKDF2-SHA256 con sal aleatoria y 600 000 iteraciones, reutilizando `claves.py`.
- Autenticación: JWT HS256 con validación de firma, emisor, audiencia y caducidad.
- Sesión en cookie HttpOnly y SameSite=Strict. En producción usa Secure y el prefijo `__Host-`.
- La duración predeterminada es de 120 minutos, configurable mediante `JWT_MINUTES`.
- Cada JWT tiene una sesión revocable en la base de datos. Cerrar sesión invalida esa sesión; cambiar la contraseña revoca todas las sesiones de la cuenta.
- Las escrituras con cookie requieren `X-CSRF-Token`. La interfaz lo añade automáticamente mediante `static/sesion-docente.js`.
- Se comprueban los orígenes de las solicitudes y se limitan los intentos de ingreso/registro por IP.
- Producción exige HTTPS para el acceso docente.
- El registro requiere una **invitación de un solo uso**, válida 24 horas por defecto. No hay alta administrativa abierta sin invitación.
- La primera invitación se genera desde la consola del servidor con `invitar_docente.py`. Después, los docentes pueden invitar a otros desde `/cuenta`.
- Todos los docentes registrados tienen permisos administrativos sobre el catálogo. No existe un rol distinto de superadministrador en esta implementación.
- Las invitaciones deben compartirse solo con docentes autorizados.
- La pantalla del estudiante no tiene controles administrativos ni enlaces de registro de docentes.
- Las rutas administrativas y el control de partidas requieren una cuenta docente, incluso en desarrollo.
- Conocer la clave de una sala no sustituye a la sesión docente; también se verifica la sesión docente en su WebSocket.
- Los estudiantes mantienen su acceso por nombre, código y token privado de participante.
- `GET /api/tarjetas` es privado. La consulta pública se hace con `/api/vocabulario`.
- `GET /api/catalogo/imagen/...` permanece público porque sirve las imágenes generadas de colores; el resto de la administración del catálogo está protegido.
- Swagger UI y OpenAPI requieren sesión docente en desarrollo y permanecen desactivados en producción.
- Las credenciales anteriores HTTP Basic y sus hashes en variables de entorno **ya no conceden acceso**.
- `configurar_admin.py` y su lanzador existente se adaptaron para generar invitaciones.

### Activación inicial en la instalación del usuario

No se creó una cuenta docente real durante la sesión. No se eligieron contraseñas por el usuario.

1. Detener el servidor anterior si está abierto.
2. Con MySQL activo, ejecutar desde la raíz:

   ```powershell
   .venv\Scripts\python.exe invitar_docente.py
   ```

3. Iniciar el proyecto con `iniciar_proyecto.bat`.
4. Abrir `http://127.0.0.1:8000/acceso?registro=1`, introducir la invitación y elegir usuario y contraseña.

La migración aditiva se aplica con `AUTO_MIGRATE=true`. Las pruebas del agente no modificaron la base MySQL real. No dar por aplicada la migración o creada la cuenta si el usuario aún no ha ejecutado estos pasos.

## Rutas principales

| Ruta | Uso |
|---|---|
| `/` | Portada pública. |
| `/vocabulario` | Catálogo público de aprendizaje. |
| `/estudiante` | Ingreso y tablero del estudiante. |
| `/acceso` | Inicio de sesión; alta con invitación. |
| `/docente` | Creación y control de partidas, con sesión docente. |
| `/administracion` | Administración del catálogo, con sesión docente. |
| `/cuenta` | Invitaciones y cambio de contraseña. |
| `/api/estado` | Estado del proceso. |
| `/api/ready` | Disponibilidad de la base de datos. |

## Limpieza solicitada y realizada

El usuario pidió eliminar cosas innecesarias creadas durante las pruebas y la elaboración de reportes.

- La raíz pasó de 73 a 38 elementos durante esa limpieza, antes de guardar esta memoria.
- Se eliminaron los reportes Word/PDF, sus generadores, capturas, evidencias, vistas previas, datos demo, pruebas obsoletas y las carpetas históricas de respaldos temporales `respaldo_*`.
- Se eliminaron `static/prueba-tablero.html`, `static/tablero-preview.css` y `static/salas.css`, que no eran utilizados por la interfaz actual.
- Las verificaciones actuales se reunieron en `tests/`.
- Se ajustaron las referencias del README y la documentación; Docker excluye `tests/`.
- Se limpiaron las cachés de Python y Astro.
- Se conservaron el código, `.env`, `.venv`, las dependencias, `frontend/dist`, el catálogo y los recursos multimedia.
- **Todo `uploads/` se conservó**, incluidas las carpetas de originales de WhatsApp: MySQL rechazó la conexión durante la limpieza y no fue posible comprobar sus referencias antes de borrar archivos.
- Se conservó el respaldo operativo SQL de `deploy/backups/`.
- No borrar esta memoria en futuras limpiezas.

## Pruebas realizadas y aprobadas

Después de implementar los cambios y después de organizar los archivos, pasaron:

```powershell
.venv\Scripts\python.exe -B -m tests.verificar_acceso_jwt
.venv\Scripts\python.exe -B -m tests.verificar_produccion
node tests/verificar_salas.cjs
node tests/verificar_audio.cjs
node tests/verificar_lector.cjs
node tests/verificar_admin_lector.cjs
npm --prefix frontend run check
npm --prefix frontend run build
```

- Las pruebas Python usan SQLite y archivos temporales aislados; no conectan a la base MySQL real.
- Cubren invitaciones, acceso, CSRF, JWT inválidos o vencidos, revocación, cambio de contraseña, límites de intentos, CRUD con descripción y acceso de estudiantes a partidas/WebSocket.
- El modo de producción de pruebas simula HTTPS con TestClient; no equivale a probar un certificado real en la nube.
- Las pruebas del lector utilizan datos simulados, no hardware físico.
- Astro comprobó 11 archivos sin errores ni advertencias y compiló 7 páginas.
- `npm audit` reportó 0 vulnerabilidades en la integración. `pip check` también pasó.
- Se verificaron en navegador las páginas compiladas con respuestas API simuladas: catálogo móvil, búsqueda, confirmación de contraseñas, redirección de registro, recuperación de descripción al editar y ausencia de enlaces administrativos en estudiantes.
- No se ejecutó una construcción de Docker ni se repitió una prueba física de RFID durante esta sesión.
- `requirements-test.txt` contiene las dependencias para las pruebas Python.

## Documentación vigente

- `README.md`: instalación, acceso, arquitectura y comandos actuales.
- `docs/CUMPLIMIENTO.md`: correspondencia con los requisitos académicos.
- `docs/DEMOSTRACIONES.md`: apartado para enlaces reales de YouTube. No se inventaron enlaces ni se publicaron videos.
- `deploy/ORACLE.md`: despliegue y migración a Oracle Cloud.

## Último tema: subir el proyecto a la nube gratuitamente

**No se ha desplegado el proyecto.** Solo se revisaron opciones y se explicó el procedimiento.

### Recomendación dada

**Oracle Cloud Always Free + una VM Ubuntu 24.04 + Docker Compose + DuckDNS + HTTPS con Caddy.**

- Mantener FastAPI, las páginas Astro y MySQL en la misma VM y bajo el mismo origen.
- MySQL se ejecuta como contenedor propio; no se cambió el motor de base de datos.
- Caddy publica HTTPS; MySQL queda en red privada.
- Imágenes y audios necesitan almacenamiento persistente.
- El ESP32 sigue conectado a la computadora del docente, no a la VM. El docente usa Chrome o Edge de escritorio mediante HTTPS.
- Configuración inicial sugerida: A1 Flex elegible para Always Free, 1–2 OCPU, 4–8 GB de RAM y 50 GB de disco, siempre comprobando las cuotas de la cuenta.
- Oracle pide tarjeta de crédito/débito para verificar identidad. La documentación indica que puede haber autorizaciones temporales.
- Distinguir Always Free del crédito de prueba de 30 días.
- No prometer gratuidad ilimitada sin condiciones: hay cuotas, disponibilidad regional, posibles recuperaciones de VMs inactivas y no hay SLA en el plan gratuito.
- No recomendar Render Free sin adaptar esta aplicación: su sistema de archivos es efímero, no ofrece disco persistente gratis y suspende servicios por inactividad. El PostgreSQL gratuito consultado caduca a los 30 días.

### Archivos de despliegue preparados

- `Dockerfile`: construcción multietapa; Node.js 24 compila Astro y la imagen final ejecuta Python.
- `compose.yaml`: MySQL 8.4, migración, aplicación y Caddy con volúmenes persistentes.
- `deploy/.env.example`: dominio, contraseñas y `JWT_SECRET` de producción.
- `deploy/Caddyfile`, `backup.sh`, `restore.sh` y configuración de respaldos.
- En producción se usa `AUTO_MIGRATE=false` para el proceso web; el servicio de migración prepara el esquema.

### Procedimiento explicado

1. Crear cuenta de Oracle y una VM Always Free.
2. Configurar la IP y un subdominio gratuito de DuckDNS.
3. Permitir 80/443 y SSH 22 restringido al operador. No publicar 3306 ni 8000 directamente.
4. Instalar Docker y Compose y copiar el proyecto, sin el entorno virtual ni las dependencias locales.
5. Configurar `deploy/.env` con dominio, `ALLOWED_HOSTS`, contraseñas y un `JWT_SECRET` aleatorio propio.
6. Ejecutar en el servidor:

   ```bash
   docker compose --env-file deploy/.env config --quiet
   docker compose --env-file deploy/.env up -d --build
   ```

7. Migrar la base local mediante exportación SQL e importar en MySQL del servidor, además de transferir **todos los archivos de `uploads/`** y conservar `catalogo/`. Seguir el orden detallado en `deploy/ORACLE.md`.
8. Si no existe una cuenta docente después de la migración, generar una invitación:

   ```bash
   docker compose --env-file deploy/.env exec app python invitar_docente.py
   ```

9. Verificar HTTPS, `/api/ready`, cuentas, partidas, multimedia y lector desde la computadora del docente.

### Punto exacto para continuar

Después de guardar esta memoria, el usuario confirmó: **«oracle cloud usare»**. La plataforma elegida es Oracle Cloud; ya no está pendiente comparar proveedores.

El siguiente paso es confirmar si ya tiene una cuenta creada y acceso a la consola de Oracle Cloud. Si no, acompañar el registro; después crear la VM elegible para Always Free, configurar el dominio y desplegar siguiendo `deploy/ORACLE.md`. Todavía no se ha confirmado una cuenta, una VM ni un despliegue. No asumir acceso a su cuenta de nube ni crear recursos de pago sin autorización.

### Fuentes oficiales consultadas

Revisarlas de nuevo antes de tomar decisiones, porque los planes pueden cambiar:

- Oracle Always Free: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- Oracle Free Tier FAQ: https://www.oracle.com/cloud/free/faq/
- Render Free: https://render.com/docs/free

Al consultarlas, Oracle indicaba A1 gratuito equivalente a 2 OCPU y 12 GB de RAM y 200 GB combinados de almacenamiento de bloques. Las cuotas efectivas y la elegibilidad deben comprobarse en la consola del usuario.

## Reglas de continuidad

- No guardar secretos ni mostrar el contenido de `.env`.
- No confundir pruebas automatizadas aisladas con pruebas del hardware o de MySQL real.
- No afirmar que hay una cuenta docente creada, una migración aplicada en la base real o un despliegue público sin comprobarlo.
- Conservar datos y medios reales. Para limpiar medios, comprobar primero sus referencias en la base.
- Consultar esta memoria para contexto y los archivos actuales para confirmar hechos antes de modificar.

## Actualización: requisitos completos de Sistemas Operativos II (19 nov 2026)

- Búsqueda por API: `?buscar=` y `?categoria=` en `/api/vocabulario` y `/api/tarjetas`; `/api/vocabulario/{id}` y `/api/vocabulario/categorias`.
- Videos de YouTube: `videos_youtube.json` + `GET/PUT /api/videos`, página `/videos` con miniaturas y editor en Administración. Enlaces reales aún pendientes.
- Página `/simulador` (partida individual sin cuenta).
- Scripts `1_INSTALAR.bat` … `4_CARGAR_PALABRAS_DEMO.bat`, `MODO_DESARROLLO_FRONTEND.bat`, `EXPORTAR_BASE_DATOS.bat`; `cargar_datos_demo.py`; `sql/estructura_completa.sql`, `sql/migrar_video.sql`.
- Documentación: `LEEME_PRIMERO.md`, `MANUAL_DE_EJECUCION.md/.pdf`, `docs/DOCUMENTACION_TECNICA.md`, `docs/CUMPLIMIENTO.md` y `docs/DEMOSTRACIONES.md` actualizados.
- La copia recibida no traía `frontend/src`, `static/`, `sql/`, `tests/` (se restauraron desde Git) ni `uploads/` (debe copiarse del proyecto original). Las carpetas del catálogo con ñ venían renombradas como `#U00f1` y se corrigieron.

## Ajuste solicitado (19 nov 2026, 20:30)

- Se quitó el video de las tarjetas (no lo pide el documento). Si una base ya tenía la columna `video_url`, el sistema la ignora.
- Descripción por defecto: si se deja vacía se guarda «X» es la palabra en lengua mazahua para «y»; al iniciar se completan las vacías.
- `sql/base_de_datos_mazahua.sql`: base del usuario (respaldo del 27/10/2026) sin las 52 cartas de prueba, con gato/gallo reales y 53 palabras del catálogo (55 tarjetas). `docs/MATERIAL_VOCABULARIO.md` lista sus archivos. El gallo y el audio español del gato dependen de `uploads/` original.

## Ajuste (20 nov 2026)
- Contraseña mínima: 6 caracteres (backend, acceso, cuenta, configurar_admin, generar_clave).
- `configurar_admin.py` ignora "conda activate base" que inyecta la terminal de VS Code y vuelve a pedir datos inválidos con el motivo.
- Nuevo editor sencillo `/editar` (solo administrador): fichas con buscar, agregar, editar (mazahua, español, descripción, imagen, audios) y eliminar. El administrador entra ahí al iniciar sesión.
- Primer administrador desde la web: si no existe ningún administrador (y no es producción), /acceso muestra "Crear cuenta de administrador" (POST /api/auth/primer-administrador). Enlace "Entrar (administrador)" en el menú público.
- Audios en español: 53 tarjetas del catálogo no tenían. `generar_audios_espanol.py` / `5_GENERAR_AUDIOS_ESPANOL.bat` los crea con pyttsx3 (voz SAPI de Windows, prefiere es-MX). Respaldo en navegador `static/voz-espanol.js` (speechSynthesis) en vocabulario, simulador y partidas; grabación con micrófono en /editar.
- Rendimiento: miniaturas `catalogo/*/miniatura.webp` (~17 KB) + `miniatura_url` en la API; Cache-Control 7 días para /catalogo y /uploads, no-cache para /static; fuentes locales en `static/fonts` (antes @import de Google Fonts, bloqueante); el .bat abre el navegador solo cuando /api/estado responde. Imagen faltante muestra recuadro "Imagen no disponible".

## Reestructura de acceso y base de datos (20 nov 2026)
- Sin roles/solicitudes/invitaciones: `usuarios` (nombre, correo único, hash, fecha). Registro libre; login por correo; recuperación 30 min un uso (sin SMTP: enlace en consola y en pantalla solo desde loopback).
- Tablas nuevas: tarjetas(numero, uid_rfid, nombre_espanol, nombre_mazahua, descripcion) + imagenes + audios(idioma); partidas(nombre, usuario_id, ultima_tarjeta_id); participantes(dispositivo, gano); tableros + tablero_tarjetas; anuncios; sesiones; recuperaciones_password. `migracion.py` convierte la estructura anterior al iniciar con respaldo en sql/respaldos.
- Partidas sin clave: el docente se identifica con su sesión y solo el creador administra (WS token 'docente'). Anuncio manual por número de carta. `/api/partidas/{codigo}/publica` para validar el QR. Alumno: botón 🔊.
- `/panel`, `static/navegacion.js` (Inicio/Regresar/Cerrar sesión), `static/sesion-docente.js` solo CSRF/redirección. Límite de intentos de acceso 30/min.

## Material Loteria_Mazahua (20 nov 2026, 11:15)
- 54 audio_espanol.webm (opus) del usuario → catalogo/*/audio_espanol.m4a (AAC 96k, iPhone). Tortilla: T'zeyi + imagen.png nueva. catalogo idéntico al material (sin png/webp duplicados, 20 MB).
- entradas_catalogo devuelve audio_espanol_url; sincronizar_material_catalogo() al importar main (AUTO_MIGRATE): por número, reemplaza audio español ausente/generado(es_*)/inexistente; CORRECCIONES_MATERIAL {('0006_tortilla','Segi'): "T'zeyi"}.

## Mejoras 20 nov 2026 (tarde)
- Tabla única `tarjetas` (numero, nombre_espanol, nombre_mazahua, descripcion, imagen, audio_mazahua, audio_espanol, uid_rfid); se eliminaron `imagenes` y `audios`. `migracion.unificar_tarjetas()` (con respaldo) para la versión intermedia; la migración desde tarjetas_rfid va directo a la tabla única.
- /editar: grabación con micrófono para mazahua y español (GRABADOR por idioma). `static/ver-contrasena.js`: ojito en todos los input password.

## Despliegue separado (20 nov 2026, noche)
- Pedido: GitHub + Vercel (frontend) + Render (backend, base MySQL actual) + Supabase Storage. Preparado en código, NO publicado desde esta sesión (sin acceso a GitHub/Vercel/Render/Supabase).
- `vercel.json` (rewrites /api, /catalogo, /uploads → loteria-mazahua-escuela.onrender.com), `deploy/preparar_vercel.mjs`, `deploy/subir_multimedia.py`.
- Backend: `FRONTEND_URL` (QR y orígenes permitidos), `ALLOWED_ORIGINS`, `WS_PUBLIC_URL`; `/api/tiempo-real/{codigo}` da la URL del WebSocket y un ticket JWT de 2 min para el docente (`autenticacion.crear_ticket_ws`/`docente_por_ticket`). `salas.js` v16 lo usa.
- Probado localmente simulando Vercel (frontend en localhost:4000 con proxy, WS directo a 127.0.0.1:8000): login, QR, alumno, anuncio en vivo, origen ajeno 403. Guía: `docs/DESPLIEGUE_VERCEL_RENDER_SUPABASE.md`.

## Rediseño 23 nov 2026
- `static/tema.css` + `static/tema.js` (cargados al final en Pagina.astro y PaginaJuego.astro, también alumno): logo en .brand, menú con botones e íconos, títulos animados (.titulo-vivo), tarjetas burbuja, tablero compacto (ancho calculado con 100dvh), respaldoImagen(img, carta), lanzarConfeti(), observarAparicion().
- `static/avatar.js` (SVG por código p-c-h-e-a-r-f). Participante.avatar VARCHAR(60) + migracion.asegurar_columnas. Reacciones: WS JSON {"reaccion": emoji} → CanalPartida.reaccion difunde {"tipo":"reaccion",...}. Modo proyector (body.proyector) en salas.js.
- Logo del usuario sin fondo en static/img (logo-mazahua*.webp, favicon.png, icono-192.png). Fuente Fredoka en static/fonts.
- El zip debe incluir uploads/ (la tarjeta «gaoo» del usuario apuntaba a uploads/ inexistente).

- 23 nov noche: avatares de animales (n-k-e-a-f), cartas disponibles en verde (.disponible / tile habilitado), tablero ajustado por JS (ajustarTablero), carpetas con ñ renombradas (RENOMBRES_CATALOGO).
