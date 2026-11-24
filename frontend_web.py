"""Entrega la compilación Astro bajo el mismo origen que la API y WebSocket."""
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse

DIST = Path(__file__).resolve().parent / 'frontend' / 'dist'


def pagina(nombre='index'):
    ruta = DIST / ('index.html' if nombre == 'index' else f'{nombre}/index.html')
    if not ruta.is_file():
        raise HTTPException(503, 'Falta compilar Astro: ejecuta npm ci y npm run build dentro de frontend/.')
    return FileResponse(ruta, headers={'Cache-Control': 'no-store'})
