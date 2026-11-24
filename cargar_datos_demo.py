"""Carga el catálogo de la carpeta catalogo/ en MySQL con UID de demostración.

Uso (desde la carpeta del proyecto):
    .venv\\Scripts\\python.exe cargar_datos_demo.py

- Sirve para probar el sistema en una computadora SIN lector RFID.
- Solo agrega las palabras del catálogo que todavía no están registradas;
  nunca modifica ni borra las tarjetas que ya existen.
- Cada tarjeta recibe un UID como "DEMO 0001". Cuando tengas la tarjeta física,
  cambia ese UID desde Administración → Editar.
"""
import sys

import main
from main import SessionLocal, Tarjeta, entradas_catalogo


def cargar():
    db = SessionLocal()
    try:
        numeros = {n for (n,) in db.query(Tarjeta.numero).filter(Tarjeta.numero.isnot(None))}
        palabras_existentes = {(t.palabra_mazahua.strip().lower(), t.traduccion_espanol.strip().lower())
                               for t in db.query(Tarjeta).all()}
        nuevas = 0
        for entrada in entradas_catalogo():
            clave = (entrada['palabra_mazahua'].strip().lower(), entrada['traduccion_espanol'].strip().lower())
            if entrada.get('numero') in numeros or clave in palabras_existentes:
                continue
            uid = f"DEMO {entrada['carpeta'].split('_', 1)[0]}"
            if db.query(Tarjeta).filter(Tarjeta.uid == uid).first():
                uid = None
            db.add(Tarjeta(uid=uid, **{k: v for k, v in entrada.items() if k != 'carpeta'}))
            nuevas += 1
        db.commit()
        total = db.query(Tarjeta).count()
        print(f'Listo: se agregaron {nuevas} palabras. Total en la base de datos: {total}.')
        if total < 16:
            print('Aviso: la lotería necesita al menos 16 tarjetas para iniciar una partida.')
    except Exception as error:  # Mensaje claro para el usuario final.
        db.rollback()
        print('No se pudo cargar el catálogo:', error)
        print('Revisa que MySQL esté encendido y que el archivo .env tenga los datos correctos.')
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    if not main.AUTO_MIGRATE:
        main.inicializar_base()
    cargar()
