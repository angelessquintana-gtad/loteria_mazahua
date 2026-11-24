"""Comprueba páginas y una muestra de multimedia sin credenciales ni descargas completas."""
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, quote
from urllib.request import Request, urlopen

BASE = 'https://loteria-mazahua-escuela.onrender.com'


def comprobar(ruta):
    with urlopen(Request(urljoin(BASE, quote(ruta, safe='/:?=&%')), headers={'Range':'bytes=0-63'}), timeout=90) as respuesta:
        datos = respuesta.read(64)
        return {'ruta':ruta, 'estado':respuesta.status, 'tipo':respuesta.headers.get('Content-Type'), 'muestra_bytes':len(datos)}


def main():
    with urlopen(BASE + '/api/vocabulario', timeout=90) as respuesta:
        tarjetas = json.load(respuesta)
    candidatos = [t[c] for t in tarjetas for c in ('imagen_url','audio_mazahua_url','audio_espanol_url') if t.get(c)]
    muestras = list(dict.fromkeys(candidatos[:9] + [r for r in candidatos if not r.isascii()][:6] +
                                 [r for r in candidatos if r.startswith('/uploads/')][:6]))
    with ThreadPoolExecutor(max_workers=4) as grupo:
        archivos = list(grupo.map(comprobar, muestras))
    paginas = [comprobar(r) for r in ('/', '/acceso', '/vocabulario', '/estudiante', '/api/ready')]
    resultado = {'tarjetas_publicas':len(tarjetas), 'multimedia_correcta':all(r['estado'] in (200,206) and r['muestra_bytes'] for r in archivos),
                 'archivos_comprobados':len(archivos), 'muestras':archivos, 'paginas':paginas}
    print(json.dumps(resultado, ensure_ascii=True))


if __name__ == '__main__':
    main()
