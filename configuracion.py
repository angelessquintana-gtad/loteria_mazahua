"""Configuración compartida. Producción falla al arrancar si faltan credenciales."""
import os
from pathlib import Path
from dotenv import load_dotenv
import secrets

load_dotenv(Path(__file__).resolve().parent / '.env')

PRODUCCION = os.getenv('APP_ENV', 'development').lower() == 'production'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]').split(',') if h.strip()]
# Despliegue separado: frontend en Vercel (FRONTEND_URL) y backend en Render.
# Vercel reenvía /api, /catalogo y /uploads al backend; el WebSocket va directo a Render.
FRONTEND_URL = os.getenv('FRONTEND_URL', '').strip().rstrip('/')
ORIGENES_PERMITIDOS = {o.strip().rstrip('/') for o in (FRONTEND_URL + ',' + os.getenv('ALLOWED_ORIGINS', '')).split(',') if o.strip()}
if FRONTEND_URL:
    os.environ.setdefault('PUBLIC_URL', FRONTEND_URL)
if os.getenv('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
    os.environ.setdefault('PUBLIC_URL', 'https://' + os.environ['RENDER_EXTERNAL_HOSTNAME'])
ROOM_IDLE_MINUTES = int(os.getenv('ROOM_IDLE_MINUTES', '60'))
ROOM_MAX_HOURS = int(os.getenv('ROOM_MAX_HOURS', '8'))
ROOM_RETENTION_DAYS = int(os.getenv('ROOM_RETENTION_DAYS', '7'))
CLEANUP_INTERVAL_SECONDS = int(os.getenv('CLEANUP_INTERVAL_SECONDS', '60'))
AUTO_MIGRATE = os.getenv('AUTO_MIGRATE', 'false' if PRODUCCION else 'true').lower() == 'true'
JWT_SECRET = os.getenv('JWT_SECRET', '')
JWT_MINUTES = int(os.getenv('JWT_MINUTES', '120'))
COOKIE_NAME = '__Host-mazahua_sesion' if PRODUCCION else 'mazahua_sesion'
JWT_ISSUER = 'loteria-mazahua'

# En desarrollo conservar la firma entre reinicios sin poner secretos en el código.
if not JWT_SECRET and not PRODUCCION:
    ruta_clave = Path(__file__).resolve().parent / '.jwt-secret'
    try:
        with ruta_clave.open('x', encoding='ascii') as archivo:
            archivo.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
    JWT_SECRET = ruta_clave.read_text(encoding='ascii').strip()
if len(JWT_SECRET.encode()) < 32 or not 5 <= JWT_MINUTES <= 480:
    raise RuntimeError('Configura JWT_SECRET (mínimo 32 bytes) y JWT_MINUTES entre 5 y 480')

if min(ROOM_IDLE_MINUTES, ROOM_MAX_HOURS, ROOM_RETENTION_DAYS, CLEANUP_INTERVAL_SECONDS) <= 0:
    raise RuntimeError('Los tiempos de caducidad y limpieza deben ser positivos')
if PRODUCCION:
    if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
        raise RuntimeError('Configura ALLOWED_HOSTS con el dominio real')
    if os.getenv('DB_USER', 'root') == 'root' or not os.getenv('DB_PASSWORD'):
        raise RuntimeError('Producción requiere un usuario MySQL propio y una contraseña')
    if os.getenv('SERIAL_ENABLED', 'false').lower() in {'true', '1', 'yes'}:
        raise RuntimeError('En la VPS utiliza SERIAL_ENABLED=false; el USB pertenece al navegador')
