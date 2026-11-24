"""Puente temporal de configuración, solo loopback. Nunca imprime secretos.

Se usa durante el despliegue asistido y se cierra con POST /stop.
No se incluye en la imagen de producción ni se publica en la web.
"""
import json
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

RUTA = Path(__file__).with_name('.cloud-secrets.json')
TOKEN = secrets.token_urlsafe(48)
PERMITIDAS = {'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_SSL',
              'SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'SUPABASE_DB_PASSWORD', 'SUPABASE_BUCKET',
              'JWT_SECRET', 'PUBLIC_URL', 'RENDER_EXTERNAL_HOSTNAME', 'BREVO_API_KEY', 'MAIL_FROM'}


def leer():
    return json.loads(RUTA.read_text(encoding='utf-8')) if RUTA.exists() else {}


def guardar(datos):
    temporal = RUTA.with_suffix('.json.tmp')
    temporal.write_text(json.dumps(datos), encoding='utf-8')
    temporal.replace(RUTA)


class Configuracion(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def responder(self, datos, estado=200):
        contenido = json.dumps(datos).encode()
        self.send_response(estado)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def autorizado(self):
        return not self.headers.get('Origin') and secrets.compare_digest(self.headers.get('X-Setup-Token', ''), TOKEN)

    def do_GET(self):
        if self.headers.get('Origin'):
            return self.responder({}, 403)
        if self.path == '/session':
            return self.responder({'token': TOKEN})
        if self.path == '/values' and self.autorizado():
            return self.responder(leer())
        self.responder({}, 404)

    def do_POST(self):
        if not self.autorizado():
            return self.responder({}, 403)
        if self.path == '/stop':
            self.responder({'ok': True})
            import threading
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if self.path != '/values' or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.responder({}, 400)
        try:
            longitud = int(self.headers.get('Content-Length', '0'))
            if not 0 < longitud < 32768:
                raise ValueError()
            nuevos = json.loads(self.rfile.read(longitud))
            if not isinstance(nuevos, dict) or not set(nuevos).issubset(PERMITIDAS) or not all(isinstance(v, str) for v in nuevos.values()):
                raise ValueError()
            guardar({**leer(), **nuevos})
            self.responder({'ok': True, 'guardadas': len(nuevos)})
        except Exception:
            self.responder({'ok': False}, 400)


if __name__ == '__main__':
    datos = leer()
    datos.setdefault('JWT_SECRET', secrets.token_urlsafe(48))
    guardar(datos)
    HTTPServer(('127.0.0.1', 18761), Configuracion).serve_forever()
