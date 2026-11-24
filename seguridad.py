"""Política central de permisos, validada en el servidor para cada petición.

- Público / alumnos: portada, vocabulario, simulador, videos, acceso, y la página
  /estudiante para entrar a una partida con su código (QR). Solo pueden unirse,
  ver su tablero, marcar casillas y cantar lotería.
- Docente (con sesión iniciada): panel, partidas, tarjetas, imágenes, audios y su cuenta.
Cambiar la URL no sirve para saltarse esto: el servidor responde 401/redirige al acceso.
"""
import posixpath
from urllib.parse import unquote

PAGINAS_DOCENTE = {'/panel', '/docente', '/administracion', '/editar', '/cuenta',
                   '/docs', '/redoc', '/openapi.json', '/static/docente.html', '/static/administracion.html'}
AUTH_PUBLICAS = {'/api/auth/login', '/api/auth/registro', '/api/auth/recuperar', '/api/auth/restablecer',
                 '/api/auth/configuracion'}


def ruta_normalizada(path):
    partes = [p.rstrip(' .') if p not in ('.', '..') else p for p in unquote(path).replace('\\', '/').split('/')]
    return '/' + posixpath.normpath('/'.join(partes)).lstrip('/').casefold()


def rol_requerido(path, method):
    """Devuelve 'docente' si la ruta necesita sesión docente, o None si es pública."""
    path = ruta_normalizada(path)
    if path in PAGINAS_DOCENTE:
        return 'docente'
    if path.startswith('/api/auth/'):
        return None if path in AUTH_PUBLICAS else 'docente'
    if path.startswith('/api/catalogo/imagen/') and method in {'GET', 'HEAD'}:
        return None
    if path.startswith(('/api/admin/', '/api/catalogo/', '/api/esp32/', '/api/ultimo-uid', '/api/uid/', '/api/tarjetas', '/api/invitacion/')):
        return 'docente'
    if path == '/api/videos':
        return None if method in {'GET', 'HEAD'} else 'docente'
    if path == '/api/partidas/unirse' or (path.startswith('/api/partidas/') and path.endswith('/publica')):
        return None   # lo único que hace el alumno antes de jugar
    if path == '/api/partidas' or path.startswith('/api/partidas/'):
        return 'docente'
    if path.startswith('/api/juego/') and path.endswith('/anunciar'):
        return 'docente'
    return None
