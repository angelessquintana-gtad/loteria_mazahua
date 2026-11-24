# Despliegue en Oracle Cloud Always Free

## Qué se ha preparado

Una sola VPS con **Astro compilado → Caddy (HTTPS) → FastAPI → MySQL 8.4**. Docker Compose publica
únicamente 80/443; MySQL y la API están en una red interna. La aplicación se ejecuta
como usuario no-root, con un worker y archivos del programa de solo lectura.
Los datos MySQL, audios subidos y certificados usan volúmenes persistentes.

El USB y el micrófono **siguen en la computadora del docente**, desde Chrome/Edge
en HTTPS. No conectar el ESP32 a la VPS. Estudiantes no requieren usuario: entran
con nombre y código; cada docente tiene una cuenta personal aprobada por un administrador escolar.

## 1. Elegir recursos sin costes previstos

Revisado el 27 de octubre de 2026 en la documentación oficial:
https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm

- Preferir **Ubuntu 24.04 ARM64 / VM.Standard.A1.Flex**. El Dockerfile y las imágenes
  seleccionadas soportan ARM64 y AMD64. Elegir solo recursos marcados **Always Free**.
- La página consultada indica 1,500 OCPU-horas y 9,000 GB-horas mensuales de A1,
  equivalentes a **2 OCPU y 12 GB RAM**, y 200 GB de almacenamiento de bloques total.
  Las cuotas de TU consola son la referencia final; no asumir el antiguo límite
  de 4 OCPU/24 GB. Una VM de 1–2 OCPU y 4–8 GB es un inicio razonable para esta app.
- Un volumen de arranque de 50 GB basta inicialmente. Cuenta dentro de los 200 GB,
  junto con cualquier otro volumen de la cuenta.
- No hace falta balanceador, Kubernetes ni una base administrada de pago.
- Puede no haber capacidad A1 en tu región. No garantiza disponibilidad, SLA ni
  gratuidad de recursos fuera de cuota. Oracle puede reclamar VMs inactivas.
- Mantenerse dentro de Always Free; no activar recursos de prueba con cargo al
  terminar el crédito. Usar cuotas y avisos de presupuesto. Un aviso de presupuesto
  NO es un tope de gasto. Revisar costes estimados antes de crear cada recurso.

Para un proyecto educativo es una buena opción si aceptas esas limitaciones y
mantienes copias **fuera de la VPS**. No producir carga artificial para evitar
las políticas de recuperación por inactividad.

## 2. DNS, red y sistema

1. Crear la VM en la región principal de la cuenta, con IP pública y clave SSH.
2. Usar un dominio existente o un subdominio gratuito, por ejemplo DuckDNS. Su
   registro A debe apuntar a la IP pública. Si cambia la IP, actualizar el DNS.
3. En OCI, NSG/Security List: permitir TCP 80 y 443; SSH 22 solamente desde tu IP.
   UDP 443 es opcional para HTTP/3. **No abrir 8000 ni 3306.**
4. Revisar también el firewall del sistema operativo. No borrar las reglas de
   Oracle ni desactivar el firewall completo. Mantener SSH accesible antes de
   aplicar cambios y permitir los mismos puertos HTTP/HTTPS.
5. Instalar Docker Engine y el plugin Docker Compose siguiendo la guía oficial
   de Docker para Ubuntu: https://docs.docker.com/engine/install/ubuntu/
   Activar Docker al arranque con `sudo systemctl enable --now docker`.
6. Mantener Ubuntu actualizado y usar SSH con claves. Pertenecer al grupo `docker`
   equivale prácticamente a acceso root: reservarlo para el operador.

## 3. Copiar el proyecto y configurar secretos

Colocar los archivos en `/opt/mazahua`. No subir `.venv`, `.env` local, capturas de
WhatsApp ni `audios_rosaura_originales`. Sí conservar `catalogo/`, `static/`, el
código Python, `frontend/` (incluido package-lock.json), Dockerfile, Compose y `deploy/`. Docker compila Astro en una etapa Node.js separada y copia solo el resultado a la imagen Python.

```bash
cd /opt/mazahua
cp deploy/.env.example deploy/.env
chmod 600 deploy/.env
```

Editar `deploy/.env`:
- `DOMAIN`: solo el nombre, sin `https://` ni ruta.
- `ACME_EMAIL`: correo válido para certificados.
- `ALLOWED_HOSTS`: dominio real, `127.0.0.1,localhost` para el healthcheck.
- Contraseñas aleatorias distintas para MySQL root y el usuario `mazahua`.
  Se pueden generar con `openssl rand -hex 32`.
- `JWT_SECRET`: un secreto aleatorio propio para firmar las sesiones. Generarlo con Python:
- Para recuperar contraseñas, completar `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY` (`starttls` o `ssl`), `SMTP_FROM`, `SMTP_USER` y `SMTP_PASSWORD` con un proveedor de correo de la escuela. `PUBLIC_URL` se genera como `https://DOMAIN`. El contenedor app tiene salida a Internet para SMTP; MySQL sigue aislado. Revisar que el proveedor de alojamiento permita la salida al puerto SMTP elegido y verificar el remitente con el proveedor.

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
# Pegar el resultado en JWT_SECRET dentro de deploy/.env.
```

No usar los textos de ejemplo como claves reales. La configuración de producción
rechaza una firma JWT ausente o corta, usuario MySQL root, contraseñas vacías y hosts comodín.
En desarrollo también se exige iniciar sesión docente para administrar.

La autenticación usa cuentas docentes y JWT en cookie HttpOnly, Secure y SameSite=Strict.
Los administradores modifican el catálogo y aprueban cuentas; los docentes aprobados preparan partidas; los estudiantes consultan vocabulario y juegan.
Las escrituras con cookie requieren un token CSRF. Cerrar sesión o cambiar contraseña revoca sesiones en el servidor.
Las variables de HTTP Basic de versiones anteriores ya no conceden acceso.

## 4. Arrancar

```bash
docker compose --env-file deploy/.env config --quiet
docker compose --env-file deploy/.env up -d --build
docker compose --env-file deploy/.env ps -a
docker compose --env-file deploy/.env logs --tail=100 migrate app caddy
curl --fail https://TU_DOMINIO/api/ready
```

Crear o promover al administrador escolar después de que `migrate` termine (requiere terminal interactiva):

```bash
docker compose --env-file deploy/.env exec app python configurar_admin.py
```

Introducir usuario, nombre, correo y contraseña del responsable y confirmar. Abrir `https://TU_DOMINIO/acceso` e iniciar sesión. Los docentes solicitan cuenta en esa misma página; el responsable aprueba desde `/cuenta`, sin consola ni códigos. Nombrar a un segundo responsable y comprobar recuperación por correo. El proceso web usa `AUTO_MIGRATE=false`: las migraciones se ejecutan antes en el servicio `migrate`. Si se importa la base local después, repetir el asistente si aún no existe un administrador en los datos importados.

`migrate` debe terminar con código 0. Crea las tablas y agrega las columnas
faltantes de forma aditiva; `app` no intenta modificar el esquema al arrancar.
Caddy obtiene y renueva el certificado automáticamente; requiere DNS correcto y
acceso a 80/443. No usar `tls internal` para un sitio público.

- Juego: `https://TU_DOMINIO/`
- Docente: `https://TU_DOMINIO/docente`
- Administración: `https://TU_DOMINIO/administracion`
- Estado de proceso: `/api/estado`; disponibilidad de BD: `/api/ready`.

Un contenedor `unhealthy` requiere revisar registros; Compose reinicia procesos
que terminan, pero no reinicia automáticamente uno que solo esté `unhealthy`.
No usar múltiples workers sin rediseñar el estado local del lector, límites y
coordinación. El despliegue es de una sola instancia, adecuado como punto de partida
para una clase; la capacidad real depende de pruebas de carga en esa VPS.

## 5. Migrar las tarjetas actuales de Windows

La VPS nueva empieza con su propia BD vacía. NO insertar tarjetas falsas para
rellenarla. Exportar la base actual con phpMyAdmin (SQL, estructura y datos) o
`mysqldump`, y copiar **todos** los archivos de `uploads/` junto con ese SQL.
Los registros guardan rutas: sin los archivos, las imágenes y audios no cargarán.

Tras el primer arranque, detener las escrituras para importar:

```bash
docker compose --env-file deploy/.env stop app
cat base_actual.sql | docker compose --env-file deploy/.env exec -T db sh -c \
  'MYSQL_PWD="$MYSQL_PASSWORD" exec mysql -u"$MYSQL_USER" "$MYSQL_DATABASE"'
# uploads.tar.gz debe contener la carpeta uploads/ en su raíz.
cat uploads.tar.gz | docker compose --env-file deploy/.env run --rm --no-deps -T app tar -C /data -xzf -
docker compose --env-file deploy/.env run --rm migrate
docker compose --env-file deploy/.env up -d app caddy
```

Mantener una copia local previa al importar. MySQL 8.4 debe aceptar la sintaxis y
collations del origen; revisar el resultado del comando antes de continuar. Si
se importa un dump con usuarios/definers del servidor antiguo, exportarlo de nuevo
solo con las tablas de esta aplicación. No reemplazar las bases de sistema MySQL.

Al iniciar, las partidas antiguas sin actividad docente caducarán; no se borran
tarjetas ni audios. El panel administrativo muestra todas las sesiones recientes
y permite finalizar las que sigan abiertas.

## 6. Ciclo de vida y mantenimiento

Variables por defecto (en `deploy/.env`):

| Variable | Valor | Uso |
|---|---:|---|
| `ROOM_IDLE_MINUTES` | 60 | Cierre sin latido docente |
| `ROOM_MAX_HOURS` | 8 | Duración máxima incluso con pestaña abierta |
| `ROOM_RETENTION_DAYS` | 7 | Historial finalizado antes de purgar |
| `CLEANUP_INTERVAL_SECONDS` | 60 | Frecuencia de mantenimiento |

El docente renueva cada 30 segundos. Los alumnos y el polling NO prolongan sesiones.
Cerrar una pestaña no borra inmediatamente el juego: se puede recuperar antes de
caducar. El cierre explícito es idempotente y confirma que se guardó.
La limpieza elimina resultados, anuncios, tableros y participantes antes de la
partida, en transacciones y lotes de 100. Conserva el catálogo y los multimedia.
Las partidas caducadas quedan finalizadas durante el plazo de retención.

En administración se listan las últimas 100 y se pueden finalizar por código.
Nunca es necesario conocer ni exponer la clave secreta del docente para hacerlo.
El borrado de tarjetas caduca primero las sesiones viejas para evitar bloqueos
por partidas abandonadas. Una partida realmente activa sigue protegida.

## 7. Copias y restauración

```bash
cd /opt/mazahua
bash deploy/backup.sh
sudo cp deploy/mazahua-backup.service deploy/mazahua-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now mazahua-backup.timer
systemctl list-timers mazahua-backup.timer
```

El script pausa brevemente `app` para que BD y audios sean coherentes, exporta SQL,
`uploads/`, `catalogo/` y hashes SHA256, y vuelve a iniciar la aplicación incluso
si falla. Retiene copias locales completas durante 7 días y evita ejecuciones
simultáneas con `flock`. Los contenedores de MySQL y Caddy no se detienen.

**Descargar regularmente las copias a otra computadora o almacenamiento externo.**
Copias solo en el disco de la misma VPS no sirven si Oracle elimina la instancia.
Los volúmenes MySQL y certificados NO se eliminan con `docker compose down`, pero
sí con `down -v`: no ejecutar ese comando salvo que se quiera destruir los datos.
Guardar `deploy/.env` y el código de la versión desplegada por separado y de forma
segura; el backup de datos no incluye secretos.

Restaurar con el código/configuración correctos y MySQL en marcha:

```bash
bash deploy/restore.sh deploy/backups/FECHA_UTC
```

Exige confirmar `RESTAURAR`, comprueba hashes y sustituye BD/archivos. Probar una
restauración en un entorno separado antes de depender de las copias.

## 8. Actualizar

```bash
bash deploy/backup.sh
# Copiar la nueva versión del código, sin sustituir deploy/.env ni los volúmenes.
docker compose --env-file deploy/.env build app migrate
docker compose --env-file deploy/.env run --rm migrate
docker compose --env-file deploy/.env up -d app caddy
curl --fail https://TU_DOMINIO/api/ready
```

Las migraciones incluidas son aditivas. Un rollback de código no deshace cambios
de esquema automáticamente; para una restauración completa usar el backup.

## 9. Verificación de salida

- Confirmar certificado válido y `/api/ready` con `{"ok":true}`.
- Sin credenciales, `/administracion` y `/docente` deben pedir acceso.
- Docente puede crear/finalizar, pero no modificar el catálogo.
- Alumno puede entrar, obtener tablero y recibir anuncios sin credenciales de docente.
- Conectar ESP32 en el navegador docente, leer UID y reproducir ambos audios.
- Grabar español en administración y comprobar el archivo tras reiniciar el servicio.
- Finalizar una sesión y comprobar que no reaparece activa al recargar.
- Revisar caducidad, timer de backup, espacio libre y restauración de una copia.

Pruebas automatizadas del repositorio: `verificar_produccion.py` (aislada),
`verificar_registro_automatico.py` (aislada), `verificar_eliminar_tarjeta.py`
(transacción MySQL revertida), y scripts Node de lector/audio/interfaz.
Las pruebas locales y la validación del YAML no sustituyen construir la imagen,
emitir el certificado, restaurar una copia y comprobar USB/voz en la VPS real.
