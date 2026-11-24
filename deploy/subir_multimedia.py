"""Sube a Supabase Storage los archivos de catalogo/ que falten o hayan cambiado
(audios en español nuevos, la imagen corregida de la tortilla, miniaturas .webp, etc.)
y actualiza catalogo_manifest.json. No toca la base de datos.

Uso (desde la carpeta del proyecto, con internet):
    python deploy/subir_multimedia.py            -> solo muestra qué falta subir
    python deploy/subir_multimedia.py --subir    -> lo sube

Lee SUPABASE_URL, SUPABASE_SERVICE_KEY y SUPABASE_BUCKET de deploy/.cloud-secrets.json
(o de variables de entorno). Ese archivo no se sube a GitHub.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ['AUTO_MIGRATE'] = 'false'
os.environ['SERIAL_ENABLED'] = 'false'
EXTENSIONES = {'.jpg', '.jpeg', '.png', '.webp', '.svg', '.m4a', '.mp3', '.wav', '.ogg', '.webm'}


def credenciales():
    ruta = RAIZ / 'deploy/.cloud-secrets.json'
    datos = json.loads(ruta.read_text(encoding='utf-8')) if ruta.exists() else {}
    for clave in ('SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'SUPABASE_BUCKET'):
        valor = os.getenv(clave) or datos.get(clave)
        if not valor:
            raise SystemExit(f'Falta {clave} (en deploy/.cloud-secrets.json o como variable de entorno).')
        os.environ[clave] = valor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subir', action='store_true')
    args = parser.parse_args()
    credenciales()
    import main as aplicacion  # entradas_catalogo() lee la carpeta local catalogo/
    import almacenamiento
    os.environ['STORAGE_BACKEND'] = 'local'
    manifiesto = aplicacion.entradas_catalogo()
    for entrada in manifiesto:
        entrada['miniatura'] = (RAIZ / 'catalogo' / entrada['carpeta'] / 'miniatura.webp').is_file()
    (RAIZ / 'catalogo_manifest.json').write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding='utf-8')

    registro = RAIZ / 'deploy/.cloud-uploaded.json'
    subidos = json.loads(registro.read_text(encoding='utf-8')) if registro.exists() else {}
    prefijo = os.environ['SUPABASE_URL'] + '/' + os.environ['SUPABASE_BUCKET'] + '/'
    pendientes = []
    for archivo in sorted((RAIZ / 'catalogo').rglob('*')):
        if archivo.is_file() and archivo.suffix.lower() in EXTENSIONES:
            ruta = archivo.relative_to(RAIZ).as_posix()
            firma = hashlib.sha256(archivo.read_bytes()).hexdigest()
            if subidos.get(prefijo + ruta) != firma:
                pendientes.append((ruta, archivo, firma))
    print(f'Manifiesto actualizado ({len(manifiesto)} cartas). Archivos por subir: {len(pendientes)}')
    if not args.subir:
        for ruta, _, _ in pendientes[:15]:
            print('  ', ruta)
        print('Para subirlos: python deploy/subir_multimedia.py --subir')
        return
    for numero, (ruta, archivo, firma) in enumerate(pendientes, 1):
        almacenamiento.guardar(ruta, archivo.read_bytes())
        subidos[prefijo + ruta] = firma
        registro.write_text(json.dumps(subidos), encoding='utf-8')
        if numero % 10 == 0 or numero == len(pendientes):
            print(f'Subidos {numero}/{len(pendientes)}', flush=True)
    print('Listo. Sube también a GitHub el catalogo_manifest.json actualizado.')


if __name__ == '__main__':
    main()
