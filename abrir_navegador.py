"""Abre el navegador solo cuando el servidor ya responde (evita la pantalla de error al iniciar)."""
import sys
import time
import urllib.request
import webbrowser

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000'
for _ in range(120):  # hasta 60 segundos
    try:
        with urllib.request.urlopen(URL + '/api/estado', timeout=1) as respuesta:
            if respuesta.status == 200:
                webbrowser.open(URL)
                break
    except Exception:
        time.sleep(0.5)
