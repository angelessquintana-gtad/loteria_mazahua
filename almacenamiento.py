"""Objetos multimedia persistentes. Las claves privadas solo se usan en el servidor."""
import json
import hashlib
import logging
import mimetypes
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

from fastapi import HTTPException

logger = logging.getLogger('mazahua.archivos')


def remoto():
    return os.getenv('STORAGE_BACKEND', 'local') == 'supabase'


def configuracion():
    origen = os.getenv('SUPABASE_URL', '').rstrip('/')
    bucket = os.getenv('SUPABASE_BUCKET', 'loteria-media')
    clave = os.getenv('SUPABASE_SERVICE_KEY', '')
    if not re.fullmatch(r'https://[a-z0-9-]+\.supabase\.co', origen) or not re.fullmatch(r'[a-z0-9-]{1,63}', bucket) or not clave:
        raise RuntimeError('Configura el almacenamiento Supabase y su clave privada en el servidor.')
    return origen, bucket, clave


def ruta_valida(ruta):
    if not ruta.startswith(('uploads/', 'catalogo/')) or any(p in {'', '.', '..'} for p in ruta.split('/')) or '\\' in ruta or len(ruta) > 1000:
        raise HTTPException(404, 'Archivo no encontrado.')
    return ruta


def url_publica(ruta):
    origen, bucket, _ = configuracion()
    return f'{origen}/storage/v1/object/public/{bucket}/' + quote(clave_objeto(ruta), safe='/')


def clave_objeto(ruta):
    ruta_valida(ruta)
    if re.fullmatch(r'[A-Za-z0-9/._-]+', ruta):
        return ruta
    # Storage limita caracteres de las claves. Las rutas públicas originales
    # (incluyendo niña, leña o nombres con espacios) se mantienen en MySQL.
    extension = ruta.rsplit('.', 1)[-1].lower()
    if not re.fullmatch(r'[a-z0-9]{1,8}', extension):
        raise HTTPException(404, 'Archivo no encontrado.')
    return ruta.split('/')[0] + '/especiales/' + hashlib.sha256(ruta.encode()).hexdigest() + '.' + extension


def solicitar(metodo, ruta, contenido=None, tipo=None, json_datos=None):
    origen, _, clave = configuracion()
    headers = {'apikey': clave, 'Authorization': 'Bearer ' + clave}
    if tipo:
        headers['Content-Type'] = tipo
    if json_datos is not None:
        contenido = json.dumps(json_datos).encode()
        headers['Content-Type'] = 'application/json'
    if metodo == 'POST' and ruta.startswith('object/'):
        headers['x-upsert'] = 'true'
    try:
        with urlopen(Request(origen + '/storage/v1/' + ruta, data=contenido, headers=headers, method=metodo), timeout=45) as respuesta:
            return respuesta.read()
    except HTTPError as error:
        detalle = error.read(4096).decode('utf-8', errors='replace').lower()
        categoria = next((c for c in ('duplicate', 'mime', 'size', 'bucket', 'invalidkey', 'invalid key', 'signature', 'jwt', 'not found', 'unauthorized') if c in detalle), 'otra')
        logger.error('El almacenamiento rechazó una operación (HTTP %s; categoría %s).', error.code, categoria)
        raise HTTPException(503, 'No se pudo guardar o consultar el archivo en la nube. Intenta de nuevo.') from None
    except (URLError, TimeoutError, OSError):
        logger.error('Falló una operación con el almacenamiento remoto. Revisar disponibilidad y cuota.')
        raise HTTPException(503, 'No se pudo guardar o consultar el archivo en la nube. Intenta de nuevo.') from None


def guardar(ruta, contenido):
    _, bucket, _ = configuracion()
    tipo = mimetypes.guess_type(ruta)[0] or 'application/octet-stream'
    solicitar('POST', 'object/' + bucket + '/' + quote(clave_objeto(ruta), safe='/'), contenido, tipo)
    return '/' + ruta


def borrar(ruta):
    # No eliminar el catálogo original mediante operaciones de tarjetas.
    if not ruta.startswith('uploads/'):
        return
    _, bucket, _ = configuracion()
    ruta_valida(ruta)
    try:
        solicitar('DELETE', 'object/' + bucket, json_datos={'prefixes': [clave_objeto(ruta)]})
    except HTTPException:
        # Un fallo al limpiar no debe ocultar el resultado de la transacción de la tarjeta.
        logger.error('Quedó un archivo pendiente de limpieza en el almacenamiento remoto.')
