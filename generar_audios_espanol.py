"""Genera el audio en ESPAÑOL de las tarjetas que no lo tienen, con la voz de Windows.

Uso: doble clic en 5_GENERAR_AUDIOS_ESPANOL.bat  (MySQL debe estar encendido).

- Solo crea audio para las tarjetas SIN audio en español; nunca reemplaza los que
  ya grabaste o subiste.
- Usa una voz en español instalada en Windows (de preferencia México, p. ej. "Sabina").
- Los archivos se guardan en uploads/audios/ y la ruta se registra en MySQL.
- Si después quieres una grabación propia, reemplázala en /editar (subir o grabar).
"""
import sys
import uuid
from pathlib import Path

PREFERENCIAS = ('es-mx', 'es_mx', 'mexico', 'méxico', 'sabina', 'raul', 'raúl', 'dalia', 'jorge')


def es_espanol(voz) -> bool:
    texto = ' '.join(str(x) for x in (voz.id, voz.name, *(getattr(voz, 'languages', None) or []))).lower()
    return any(c in texto for c in ('spanish', 'español', 'espanol', 'es-', 'es_', '\\es', '/es', "b'\\x05es")) or texto.endswith(' es')


def elegir_voz(motor):
    voces = motor.getProperty('voices') or []
    espanol = [v for v in voces if es_espanol(v)]
    if not espanol:
        return None, voces
    preferida = next((v for v in espanol if any(p in f'{v.id} {v.name}'.lower() for p in PREFERENCIAS)), espanol[0])
    return preferida, voces


def main():
    try:
        import pyttsx3
    except ImportError:
        print('Falta la librería de voz. Ejecuta primero 1_INSTALAR.bat (o: .venv\\Scripts\\python.exe -m pip install pyttsx3).')
        sys.exit(1)
    import main as aplicacion
    from main import SessionLocal, Tarjeta, AUDIO_DIR

    motor = pyttsx3.init()
    voz, voces = elegir_voz(motor)
    if not voz:
        print('No se encontró una voz en español instalada en Windows.')
        print('Instálala en: Configuración → Hora e idioma → Idioma → Agregar idioma → Español (México),')
        print('marcando "Texto a voz". Después vuelve a ejecutar este archivo.')
        print('Voces disponibles:', ', '.join(v.name for v in voces) or 'ninguna')
        sys.exit(1)
    motor.setProperty('voice', voz.id)
    motor.setProperty('rate', 140)  # un poco más lento que lo normal, para aprender
    print(f'Voz utilizada: {voz.name}')

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    try:
        pendientes = db.query(Tarjeta).filter((Tarjeta.audio_espanol_url.is_(None)) | (Tarjeta.audio_espanol_url == '')).order_by(Tarjeta.id).all()
        if not pendientes:
            print('Todas las tarjetas ya tienen audio en español. No hay nada que hacer.')
            return
        print(f'Generando {len(pendientes)} audios en español…')
        archivos = []
        hechos = 0
        for tarjeta in pendientes:
            nombre = f'es_{uuid.uuid4().hex}.wav'
            ruta = AUDIO_DIR / nombre
            motor.save_to_file(tarjeta.traduccion_espanol.strip(), str(ruta))
            motor.runAndWait()  # uno por uno: así cada palabra queda en su propio archivo
            archivos.append((tarjeta, nombre))
            if ruta.is_file() and ruta.stat().st_size > 1000:
                tarjeta.audio_espanol_url = f'/uploads/audios/{nombre}'
                hechos += 1
                print(f'  ✓ {tarjeta.traduccion_espanol}')
            else:
                ruta.unlink(missing_ok=True)
                print(f'  ✗ No se pudo generar: {tarjeta.traduccion_espanol}')
        db.commit()
        print(f'\nListo: {hechos} de {len(archivos)} tarjetas ahora tienen audio en español.')
    except Exception as error:
        db.rollback()
        print('No se pudieron generar los audios:', str(error).splitlines()[0][:200])
        print('Revisa que MySQL esté encendido en XAMPP.')
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
