# Nube gratuita conservando MySQL

## Sitio publicado y comprobado (19 de noviembre de 2026)

**Dirección final: https://loteria-mazahua-escuela.onrender.com**

- Render: servicio `loteria-mazahua-escuela`, región Frankfurt, plan Free. ID `srv-dbvdvge7bikc738bdlvg`. Se eligió Frankfurt para reducir la latencia hacia MySQL en Nürnberg. La instancia de prueba en Oregón (`loteria-mazahua-asfa.onrender.com`) quedó suspendida; no usar ese enlace.
- Filess.io: base MySQL 8 compartida, 54 tarjetas y la copia de los datos existentes. Se verificó conexión TLS. No se modificó la base local durante la migración.
- Supabase: proyecto separado `loteria-mazahua`, bucket `loteria-media`, 271 archivos (~148 MB). No se crearon políticas de escritura pública.
- Repositorio privado autorizado: https://github.com/Jose78123/loteria-mazahua. No contiene secretos ni binarios del catálogo.
- La cuenta docente existente conserva su usuario y hash de contraseña y quedó como administradora **en la copia de la nube**. Iniciar sesión en `/acceso` con los datos anteriores, agregar el correo y nombrar a un segundo responsable desde `/cuenta`.

### Resultado medido en el sitio real

La prueba corta de `deploy/probar_clase_nube.py` se completó con 25 participantes simulados y 25 WebSocket simultáneos. Creó una sala temporal y la eliminó junto con sus tableros, participantes y sesión de prueba; no eliminó las partidas originales ni cambió contraseñas. Resultados completos en `docs/PRUEBA_NUBE.json`:

| Operación | Resultado observado |
|---|---|
| Ingreso simultáneo de los 25 | 3.37 segundos en total |
| Inicio y creación de 25 tableros | 0.39 segundos |
| Apertura de conexiones y primer tablero | hasta 16.07 segundos desde el equipo de prueba |
| Anunciar una tarjeta | 0.40 segundos |
| Recibir el anuncio después de responder la API | hasta 0.68 segundos |
| Marcas simultáneas de 12 alumnos que tenían esa carta | hasta 1.31 segundos |
| Dos marcas simultáneas del mismo alumno | ambas conservadas |
| Tamaño informado de datos e índices durante la clase | 704,512 bytes |

Se verificaron 18 muestras de archivos, incluidas rutas con acentos, con respuestas de rango HTTP 206 y los tipos multimedia esperados. El navegador cargó metadata de dos audios sin errores. No se afirma haber escuchado todos los archivos, probado 25 dispositivos físicos, una clase prolongada o el ESP32 real.

Las pruebas iniciales detectaron saturación del pool y latencias altas desde Oregón. Se agruparon las consultas de WebSocket por sala, se ajustó la espera del pool (60 segundos), se insertan tableros en lote y las marcas usan bloqueo compartido de sala y exclusivo por tablero. Finalmente se ubicó Render en Frankfurt; no basta con aumentar conexiones sin considerar la cuota gratuita.

## Arquitectura preparada

- Render Free: una instancia de Astro compilado + FastAPI, HTTPS y WebSocket.
- Filess.io Shared Free: MySQL 8.0, conexión TLS, pool pequeño (2 conexiones + 1 adicional).
- Supabase Free: bucket `loteria-media`, lectura pública de los materiales y escritura/borrado solo con clave privada del backend. Supabase **no sustituye MySQL**.
- GitHub: repositorio privado para código y manifiesto. No incluye `.env`, claves, backups, archivos subidos, dependencias locales ni binarios del catálogo.

Las rutas `/uploads/...` y `/catalogo/...` se conservan en MySQL y redirigen al Storage cuando `STORAGE_BACKEND=supabase`. Esto evita reescribir las referencias y los JSON de tableros. Las claves con acentos/espacios se convierten a identificadores ASCII deterministas; las URLs de la app no cambian. El catálogo para registro automático utiliza `catalogo_manifest.json`, generado desde los archivos locales antes de publicar.

## Arranque y variables de Render

Usar Docker y comando `python deploy/iniciar_render.py`, plan **Free**, una sola instancia. El arranque aplica las migraciones aditivas antes de Uvicorn. Health check: `/api/ready`. No usar varios workers ni escalar sin rediseñar la coordinación de partidas.

Variables privadas: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `JWT_SECRET`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_BUCKET`. La clave de Supabase debe ser de servidor (`service_role`), nunca publicarla en frontend ni guardar en Git.

Variables de comportamiento: `APP_ENV=production`, `SERIAL_ENABLED=false`, `DB_SSL=true`, `STORAGE_BACKEND=supabase`, `DB_POOL_SIZE=2`, `DB_MAX_OVERFLOW=1`, `DB_POOL_TIMEOUT=60`, `ROOM_RETENTION_DAYS=1`. Render proporciona `RENDER_EXTERNAL_HOSTNAME`; el código lo añade a hosts permitidos y forma `PUBLIC_URL` con HTTPS. El puerto lo proporciona `PORT`.

`render.yaml` sirve de referencia/Blueprint para despliegues posteriores. No contiene credenciales reales.

## Migración asistida

`deploy/migrar_nube.py --revisar` consulta la base local sin modificarla, mide los archivos utilizados y genera el manifiesto. `--copiar` exige tablas remotas vacías, sube el catálogo y solo los archivos de uploads referenciados por tarjetas, y copia los datos en una transacción. No borra ni actualiza la base local. Las sesiones e invitaciones locales no se trasladan, porque la nube usa otra firma JWT.

Si solo existe una cuenta docente y no tiene rol administrativo, `--primer-docente-administrador` permite designarla responsable **en la copia remota**. Se conserva su hash de contraseña. Para posteriores altas se usa la solicitud/aprobación web.

La configuración privada y el registro de transferencias se guardan en archivos ignorados `deploy/.cloud-secrets.json` y `deploy/.cloud-uploaded.json`. El primero contiene secretos: no compartir, no adjuntar a reportes ni subirlo a Git. El puente temporal `configuracion_privada.py` solo escucha en loopback y debe detenerse al terminar; no forma parte de la imagen de producción.

La copia de datos previa a la transferencia queda en `deploy/backups/` y contiene datos de cuentas protegidos con hash. Tratarla como privada. Este archivo JSON es una copia de migración; no sustituye un plan probado de backups MySQL y archivos.

## Recuperación de acceso sin una cuarta plataforma

Un administrador puede abrir Mi cuenta → cuentas aprobadas → **Recuperar acceso** y entregar al titular un enlace privado de un uso válido durante 30 minutos, después de verificar su identidad. No necesita correo SMTP ni intervención del desarrollador. El enlace no cambia la contraseña hasta que el titular lo usa.

Si todos los responsables perdieran su acceso, un operador autorizado con el archivo privado de configuración puede ejecutar `.venv\Scripts\python.exe deploy/configurar_admin_nube.py`. El asistente apunta a la nube con TLS y pide confirmación, usuario, correo y contraseña oculta. No apunta a MySQL local. El archivo privado debe entregarse únicamente al responsable técnico; no compartirlo por mensajes públicos.

Para envío automático configurar opcionalmente `MAIL_PROVIDER=brevo`, `BREVO_API_KEY` y `MAIL_FROM` con remitente verificado; se usa HTTPS. Render Free bloquea puertos SMTP habituales. Sin proveedor configurado, el formulario informa indisponibilidad y se usa la recuperación escolar anterior. No se ha contratado ni prometido un servicio de correo por disponer de los otros tres servicios.

## Límites y operación

Render duerme por inactividad y puede reiniciar. Filess.io Free tiene 10 MB y recursos compartidos, sin SLA. Supabase Free incluye 1 GB de archivos y cuotas de transferencia; puede pausar por inactividad. No mantener los servicios activos con tráfico artificial. La cuenta de alojamiento debe supervisarse especialmente tras vacaciones.

La retención del historial se reduce a un día en Render para limitar crecimiento. Esto no elimina el catálogo ni las cuentas. Hacer respaldos externos de MySQL y multimedia; el temporizador de Oracle/systemd **no se ejecuta en Render**.

Medición de origen al preparar la copia: 54 tarjetas, 1 docente, 2 partidas, 1 tablero; 271 archivos referenciados y de catálogo, 148,181,937 bytes (~148 MB decimales). El tamaño y la transferencia durante el uso real deben vigilarse en los paneles. No afirmar que los 25 alumnos están validados hasta completar una prueba concurrente y una comprobación de audio/lector real.

El ESP32 permanece en la computadora del docente con Chrome/Edge y permiso USB; no se conecta a la nube. Las pruebas simuladas del lector no equivalen a una validación física.
