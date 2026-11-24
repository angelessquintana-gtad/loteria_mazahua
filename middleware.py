import asyncio
import logging
import time

from starlette.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import secrets
from configuracion import ORIGENES_PERMITIDOS, PRODUCCION
from seguridad import rol_requerido, ruta_normalizada
from autenticacion import autenticar_solicitud

logger = logging.getLogger('mazahua.http')


class ProteccionHTTP(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.ventanas = {}
        self.fallos_admin = {}

    def excedido(self, ip, grupo, limite):
        ventana = int(time.monotonic() // 60)
        clave = (ip, grupo)
        anterior, cuenta = self.ventanas.get(clave, (ventana, 0))
        cuenta = cuenta + 1 if anterior == ventana else 1
        if len(self.ventanas) >= 10000 and clave not in self.ventanas:
            self.ventanas = {k: v for k, v in self.ventanas.items() if v[0] == ventana}
            if len(self.ventanas) >= 10000:
                self.ventanas.pop(next(iter(self.ventanas)))
        self.ventanas[clave] = (ventana, cuenta)
        return cuenta > limite

    async def dispatch(self, request, call_next):
        ip = request.client.host if request.client else 'desconocido'
        path = request.url.path
        if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
            origin = request.headers.get('origin')
            if origin and origin != f'{request.url.scheme}://{request.url.netloc}' and origin.rstrip('/') not in ORIGENES_PERMITIDOS:
                return JSONResponse({'detail': 'Origen de solicitud no permitido'}, status_code=403)
            if request.headers.get('sec-fetch-site') == 'cross-site':
                return JSONResponse({'detail': 'Solicitud de otro sitio no permitida'}, status_code=403)
        try:
            if int(request.headers.get('content-length', '0')) > 30 * 1024 * 1024:
                return JSONResponse({'detail': 'La solicitud supera 30 MB'}, status_code=413)
        except ValueError:
            return JSONResponse({'detail': 'Tamaño de solicitud inválido'}, status_code=400)
        if PRODUCCION:
            if path.startswith('/api/') and request.method not in {'GET', 'HEAD', 'OPTIONS'} and self.excedido(ip, 'escrituras', 2400):
                return JSONResponse({'detail': 'Demasiadas operaciones. Espera un minuto.'}, status_code=429, headers={'Retry-After': '60'})
            limite = 240 if path == '/api/partidas/unirse' else 30 if path == '/api/partidas' else 10 if path == '/api/amigos' else None
            if limite and self.excedido(ip, path, limite):
                return JSONResponse({'detail': 'Demasiadas solicitudes. Espera un minuto.'}, status_code=429, headers={'Retry-After': '60'})
        normal = ruta_normalizada(path)
        if PRODUCCION and request.url.scheme != 'https' and (normal.startswith('/api/auth/') or rol_requerido(path, request.method)):
            return JSONResponse({'detail': 'El acceso docente requiere HTTPS.'}, status_code=403)
        if normal in {'/api/auth/login', '/api/auth/registro', '/api/auth/recuperar', '/api/auth/restablecer'} and request.method == 'POST':
            if self.excedido(ip, 'autenticacion', 30):
                return JSONResponse({'detail': 'Demasiados intentos. Espera un minuto.'}, status_code=429, headers={'Retry-After': '60'})
        if rol_requerido(path, request.method):
            docente = await asyncio.to_thread(autenticar_solicitud, request)
            if not docente:
                if request.method == 'GET' and normal in {'/panel', '/docente', '/administracion', '/editar', '/cuenta'}:
                    return RedirectResponse('/acceso?destino=' + normal, status_code=303, headers={'Cache-Control': 'no-store'})
                return JSONResponse({'detail': 'Inicia sesión con tu cuenta docente.'}, status_code=401,
                                    headers={'WWW-Authenticate': 'Bearer', 'Cache-Control': 'no-store'})
            if request.method not in {'GET', 'HEAD', 'OPTIONS'} and not docente['bearer']:
                csrf = request.headers.get('x-csrf-token', '')
                if not secrets.compare_digest(csrf, docente['csrf']):
                    return JSONResponse({'detail': 'Sesión de seguridad inválida. Recarga la página.'}, status_code=403)
            request.state.docente = docente
        originales = {'/static/docente.html': '/docente', '/static/administracion.html': '/administracion',
                      '/static/estudiante.html': '/estudiante', '/static/inicio.html': '/'}
        if normal in originales and request.method in {'GET', 'HEAD'}:
            return RedirectResponse(originales[normal], status_code=303, headers={'Cache-Control': 'no-store'})
        try:
            response = await call_next(request)
        except Exception:
            logger.exception('Error no controlado en %s %s', request.method, path)
            return JSONResponse({'detail': 'Error interno del servidor. Consulta los registros del servicio.'}, status_code=500)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'same-origin'
        if path.startswith('/api/') or path in {'/panel', '/administracion', '/docente', '/editar', '/cuenta', '/acceso'}:
            response.headers['Cache-Control'] = 'no-store'
        elif response.status_code == 200 and path.startswith(('/catalogo/', '/uploads/')):
            # Imágenes y audios no cambian de contenido (los subidos tienen nombre aleatorio): el navegador los guarda 7 días.
            response.headers['Cache-Control'] = 'public, max-age=604800'
        elif path.startswith('/static/') or path.startswith('/_astro/'):
            response.headers.setdefault('Cache-Control', 'no-cache')  # revalida con ETag: rápido y siempre actualizado
        return response
