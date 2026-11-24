# Entrega y operación · Lotería Mazahua

## Viabilidad

Es viable como aplicación escolar de una sola instancia: Astro compilado, FastAPI y MySQL con Docker. En nube necesita Internet en la escuela, HTTPS, una VPS con almacenamiento persistente y un responsable escolar. Como referencia de dimensionamiento inicial: 2 CPU y 4 GB de RAM; es una estimación, no capacidad medida. Antes de entregar, probar una clase real con el número previsto de estudiantes, audio y WebSocket. El límite configurable de estudiantes de una partida no demuestra capacidad concurrente.

Oracle gratuito depende de cuotas, capacidad regional y políticas vigentes; una VPS contratada por la escuela ofrece un presupuesto más previsible. Dominio, alojamiento y correo deben quedar bajo cuentas institucionales, con responsables y renovación acordados. No se han contratado recursos ni publicado el sistema al preparar estos archivos.

El ESP32 y RC522 permanecen por USB en la computadora del docente. Usar Chrome/Edge de escritorio, HTTPS en nube y permiso de puerto serie. El ESP32 no se conecta al servidor remoto. Probar la lectura física después del despliegue; una prueba con datos simulados no sustituye al lector real.

## Preparación inicial (una vez)

1. Respaldar base MySQL, código, `catalogo/` y `uploads/` antes de actualizar. Las credenciales se guardan por separado y de forma privada.
2. Detener el proceso anterior. En Windows, `AUTO_MIGRATE=true` aplica las columnas nuevas al iniciar. En nube usar el servicio `migrate` de Compose. La migración es aditiva: no borra tablas, tarjetas, audios ni cuentas; las cuentas antiguas quedan como docentes aprobados sin correo.
3. Ejecutar `configurar_administracion.bat` en Windows, o `docker compose --env-file deploy/.env exec app python configurar_admin.py` en la VPS. Elegir la cuenta del responsable, correo y contraseña de al menos 6 caracteres. Si existe, el asistente la promueve y cambia su contraseña, previa confirmación. También permite recuperar el acceso administrativo desde consola si falla el correo.
4. Iniciar el proyecto y abrir `/acceso`. El responsable entra a **Mi cuenta** y puede aprobar solicitudes, desactivar cuentas y nombrar un segundo administrador. No puede desactivar o degradar al último administrador activo.
5. Cada cuenta antigua agrega su correo en Mi cuenta confirmando la contraseña. No se inventan correos ni se promueven cuentas automáticamente.

## Uso diario sin el desarrollador

1. El docente pulsa **Solicitar cuenta docente** en `/acceso`, escribe nombre, correo, usuario y contraseña, y envía.
2. La cuenta queda pendiente y no obtiene sesión. El administrador revisa **Mi cuenta → Administración escolar · Docentes**. Verifica que nombre y correo pertenecen a la persona antes de aprobar.
3. El administrador aprueba o rechaza; comunica la decisión por los medios de la escuela. No se envían notificaciones automáticas de aprobación.
4. El docente aprobado inicia sesión con su contraseña y crea partidas. Solo el administrador modifica el catálogo o gestiona cuentas.
5. Las invitaciones siguen como alternativa opcional del administrador; no son necesarias para solicitar una cuenta.
6. Rechazos no borran la cuenta: el responsable puede activarla después de revisar. Desactivar una cuenta conserva sus registros y cierra sus sesiones. Los cambios de rol también cierran sesiones.

## Correo de recuperación

Completar las variables del ejemplo `.env.example` (Windows) o `deploy/.env.example` (nube). No publicar `.env` ni compartir claves SMTP. Usar proveedor SMTP con remitente autorizado y, si corresponde, contraseña de aplicación.

| Variable | Valor esperado |
|---|---|
| `PUBLIC_URL` | Origen del sitio, por ejemplo `https://loteria.escuela.mx`; Compose lo forma con `DOMAIN`. |
| `SMTP_HOST` | Servidor del proveedor. |
| `SMTP_PORT` | Normalmente 587 para STARTTLS o 465 para SSL. |
| `SMTP_SECURITY` | `starttls` o `ssl`; no se permite correo sin cifrado. |
| `SMTP_FROM` | Remitente autorizado. |
| `SMTP_USER` / `SMTP_PASSWORD` | Credenciales del proveedor. |

Reiniciar el servicio después de configurar. Algunos proveedores VPS restringen SMTP: confirmar puerto de salida y autorización del remitente. Hacer una prueba real de entrega y revisar spam. La configuración presente solo habilita el intento; no garantiza que el proveedor entregue el mensaje. Los errores de transporte quedan en registros sin revelar enlaces, destinatarios ni contraseñas.

**Olvidé mi contraseña** envía un enlace solo a cuentas aprobadas y activas. Dura 30 minutos, sirve una vez y cierra las sesiones al cambiar la contraseña. Se almacena solo el hash del token. El enlace usa fragmento del navegador para no enviar el token en la URL de la petición al servidor. La solicitud da la misma respuesta para correos existentes y desconocidos. Hay límite por IP y espera de dos minutos por cuenta. Sin configuración, el sitio informa que debe contactarse al responsable escolar.

## Publicación y respaldo

Seguir `deploy/ORACLE.md`: crear VPS, configurar dominio/HTTPS, copiar código, definir secretos, arrancar Compose e importar datos existentes junto con todos sus archivos. Una instalación nueva sin importar MySQL no tiene las tarjetas de la laptop.

`deploy/backup.sh` y el temporizador de systemd ya preparan copias diarias locales, con retención de siete días. Deben instalarse/activarse en la VPS siguiendo la guía; no se activan por compilar el código. Descargar regularmente copias fuera del servidor y probar restaurarlas en un entorno aparte. El envío automático a almacenamiento externo requiere elegir y configurar ese destino.

## Comprobación de entrega

- Responsable y suplente pueden iniciar sesión; un docente pendiente no puede entrar.
- Solicitud → aprobación → partida funciona sin usar la consola.
- Un docente no puede gestionar cuentas ni modificar el catálogo.
- El correo real de recuperación llega y el enlace no se puede reutilizar.
- Las tarjetas importadas tienen sus imágenes y audios.
- Una clase completa puede unirse y jugar; el lector real anuncia las cartas.
- HTTPS funciona, el sistema vuelve tras reiniciar la VPS y existe un respaldo restaurable fuera de ella.

Las pruebas automatizadas usan SQLite temporal, correo simulado y HTTPS simulado. No verifican conectividad SMTP, migración MySQL real, capacidad de una clase ni hardware físico. Estas comprobaciones se hacen en la instalación final.
