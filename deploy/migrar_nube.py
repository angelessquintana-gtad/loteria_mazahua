"""Copia de MySQL y multimedia hacia servicios nuevos; no modifica la base local.

--revisar: mide y genera el manifiesto de catálogo sin subir datos.
--copiar: exige una base remota vacía; sube archivos y copia datos transaccionalmente.
Las credenciales se leen solo de deploy/.cloud-secrets.json, excluido de Git.
"""
import argparse
import hashlib
import json
import os
import ssl
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
os.environ['AUTO_MIGRATE'] = 'false'
os.environ['SERIAL_ENABLED'] = 'false'


def parametros_remotos():
    return json.loads((RAIZ / 'deploy/.cloud-secrets.json').read_text(encoding='utf-8'))


def motor_remoto():
    from sqlalchemy import URL, create_engine
    secretos = parametros_remotos()
    return create_engine(URL.create('mysql+pymysql', username=secretos['DB_USER'], password=secretos['DB_PASSWORD'],
        host=secretos['DB_HOST'], port=int(secretos['DB_PORT']), database=secretos['DB_NAME'], query={'charset':'utf8mb4'}),
        hide_parameters=True, pool_pre_ping=True, pool_size=1, max_overflow=0,
        connect_args={'connect_timeout':15, 'ssl':ssl.create_default_context()})


def inventario():
    import main
    from sqlalchemy import MetaData, select
    from database import engine
    origen = MetaData()
    origen.reflect(bind=engine)
    datos = {}
    with engine.connect() as conexion:
        for tabla in main.Base.metadata.sorted_tables:
            if tabla.name in origen.tables and tabla.name not in {'sesiones', 'recuperaciones_password'}:
                datos[tabla.name] = [dict(fila) for fila in conexion.execute(select(origen.tables[tabla.name])).mappings()]
    archivos = {}
    for carpeta in (RAIZ / 'catalogo').iterdir():
        if carpeta.is_dir():
            for archivo in carpeta.iterdir():
                if archivo.is_file() and archivo.suffix.lower() in {'.jpg','.jpeg','.png','.webp','.svg','.m4a','.mp3','.wav','.ogg','.webm','.mp4'}:
                    archivos[archivo.relative_to(RAIZ).as_posix()] = archivo
    for archivo_db in datos.get('imagenes', []) + datos.get('audios', []):
        for ruta in (archivo_db.get('ruta'),):
            if ruta and ruta.startswith('/uploads/'):
                archivo = (RAIZ / ruta.lstrip('/')).resolve()
                if not archivo.is_relative_to((RAIZ / 'uploads').resolve()) or not archivo.is_file():
                    raise RuntimeError('Falta un archivo multimedia utilizado por una tarjeta. Revisar antes de migrar.')
                archivos[ruta.lstrip('/')] = archivo
    manifest = main.entradas_catalogo()
    (RAIZ / 'catalogo_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return datos, archivos


def copiar(datos, archivos, confirmar_administrador=False):
    import main
    import almacenamiento
    from sqlalchemy import select, func, insert, update
    secretos = parametros_remotos()
    for clave in ('SUPABASE_URL','SUPABASE_SERVICE_KEY','SUPABASE_BUCKET'):
        os.environ[clave] = secretos[clave]
    destino = motor_remoto()
    try:
        # No ejecutar DROP, TRUNCATE ni DELETE sobre la base del usuario.
        main.Base.metadata.create_all(destino)
        with destino.connect() as conexion:
            for tabla in main.Base.metadata.sorted_tables:
                if conexion.scalar(select(func.count()).select_from(tabla)):
                    raise RuntimeError('La base remota no está vacía. No se reemplazarán sus datos.')
        carpeta_backup = RAIZ / 'deploy/backups'
        carpeta_backup.mkdir(exist_ok=True)
        copia = carpeta_backup / ('pre_nube_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.json')
        copia.write_text(json.dumps(datos, ensure_ascii=False, default=lambda v:v.isoformat()), encoding='utf-8')
        registro_subidas = RAIZ / 'deploy/.cloud-uploaded.json'
        subidos = json.loads(registro_subidas.read_text(encoding='utf-8')) if registro_subidas.exists() else {}
        for numero, (ruta, archivo) in enumerate(archivos.items(), 1):
            contenido = archivo.read_bytes()
            firma = hashlib.sha256(contenido).hexdigest()
            identificador = secretos['SUPABASE_URL'] + '/' + secretos['SUPABASE_BUCKET'] + '/' + ruta
            if subidos.get(identificador) != firma:
                almacenamiento.guardar(ruta, contenido)
                subidos[identificador] = firma
                registro_subidas.write_text(json.dumps(subidos), encoding='utf-8')
            if numero % 25 == 0:
                print(f'Archivos transferidos: {numero}/{len(archivos)}', flush=True)
        with destino.begin() as conexion:
            for tabla in main.Base.metadata.sorted_tables:
                columnas = set(tabla.c.keys())
                for fila in datos.get(tabla.name, []):
                    conexion.execute(insert(tabla).values(**{k:v for k,v in fila.items() if k in columnas}))
        with destino.connect() as conexion:
            conteos = {t.name:conexion.scalar(select(func.count()).select_from(t)) for t in main.Base.metadata.sorted_tables}
        print(json.dumps({'copia_remota_completada':True,'archivos':len(archivos),'filas':conteos}, ensure_ascii=True))
    finally:
        destino.dispose()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revisar', action='store_true')
    parser.add_argument('--copiar', action='store_true')
    parser.add_argument('--primer-docente-administrador', action='store_true')
    args = parser.parse_args()
    datos, archivos = inventario()
    print(json.dumps({'filas_origen':{k:len(v) for k,v in datos.items()}, 'archivos_referenciados_y_catalogo':len(archivos),
                      'multimedia_bytes':sum(p.stat().st_size for p in archivos.values())}, ensure_ascii=True))
    if args.copiar:
        copiar(datos, archivos, args.primer_docente_administrador)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # No mostrar excepciones de drivers que puedan repetir datos de conexión.
        print('No se completó la operación. Tipo de error: ' + type(error).__name__)
        raise SystemExit(1)
