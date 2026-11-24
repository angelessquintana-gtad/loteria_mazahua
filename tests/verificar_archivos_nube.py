"""Pruebas sin red ni credenciales reales para Storage y rutas multimedia."""
import io
import json
import os
from urllib.error import HTTPError
from unittest.mock import patch, MagicMock

from fastapi import HTTPException
import almacenamiento as storage


def main():
    entorno = {'SUPABASE_URL':'https://prueba.supabase.co', 'SUPABASE_BUCKET':'loteria-media',
               'SUPABASE_SERVICE_KEY':'clave-ficticia', 'STORAGE_BACKEND':'supabase'}
    with patch.dict(os.environ, entorno):
        assert storage.url_publica('uploads/imagenes/abc.png').endswith('/loteria-media/uploads/imagenes/abc.png')
        especial = storage.clave_objeto('catalogo/0030_niña/imagen.jpg')
        assert especial.isascii() and especial == storage.clave_objeto('catalogo/0030_niña/imagen.jpg')
        assert especial in storage.url_publica('catalogo/0030_niña/imagen.jpg')
        for ruta in ['uploads/../secreto.env','otra/archivo.png','uploads//archivo.png','uploads/\\archivo.png']:
            try:
                storage.url_publica(ruta)
                raise AssertionError('Ruta aceptada: ' + ruta)
            except HTTPException as error:
                assert error.status_code == 404
        with patch('almacenamiento.urlopen') as abrir:
            abrir.return_value.__enter__.return_value.read.return_value = b'{}'
            assert storage.guardar('uploads/imagenes/abc.png', b'contenido') == '/uploads/imagenes/abc.png'
            peticion = abrir.call_args.args[0]
            assert peticion.get_header('X-upsert') == 'true'
            assert peticion.get_header('Content-type') == 'image/png'
            assert peticion.get_header('Authorization') == 'Bearer clave-ficticia'
            storage.borrar('catalogo/0001_uno/imagen.jpg')
            assert abrir.call_count == 1
            storage.borrar('uploads/imagenes/abc.png')
            assert abrir.call_args.args[0].method == 'DELETE'
            assert json.loads(abrir.call_args.args[0].data) == {'prefixes':['uploads/imagenes/abc.png']}
        fallo = HTTPError('https://prueba.supabase.co', 400, 'error', {}, io.BytesIO(b'{"error":"Duplicate"}'))
        with patch('almacenamiento.urlopen', side_effect=fallo):
            try:
                storage.guardar('uploads/imagenes/abc.png', b'contenido')
                raise AssertionError('No se notificó fallo')
            except HTTPException as error:
                assert error.status_code == 503 and 'clave-ficticia' not in error.detail
    print('OK: almacenamiento persistente, nombres con acentos, upsert, tipos de archivo, rutas seguras y fallos sin secretos.')


if __name__ == '__main__':
    main()
