"""Recuperación administrativa desde un equipo autorizado, sin tocar MySQL local."""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


if __name__ == '__main__':
    datos = json.loads((RAIZ / 'deploy/.cloud-secrets.json').read_text(encoding='utf-8'))
    for clave in ('DB_HOST','DB_PORT','DB_NAME','DB_USER','DB_PASSWORD','JWT_SECRET'):
        os.environ[clave] = datos[clave]
    os.environ.update(DB_SSL='true', AUTO_MIGRATE='false', SERIAL_ENABLED='false')
    from configurar_admin import main
    try:
        main()
    except Exception:
        print('No se pudo actualizar la cuenta remota. Revisa los datos y la conexión. No se modificó la base local.')
        raise SystemExit(1)
