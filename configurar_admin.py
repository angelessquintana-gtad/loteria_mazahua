"""Crear una cuenta docente o cambiarle la contraseña desde la computadora del servidor.

Normalmente NO hace falta: el docente crea su cuenta en /acceso y recupera su contraseña con
"¿Olvidaste tu contraseña?". Este programa es un respaldo para cuando no hay correo configurado.
Uso: doble clic en 3_CREAR_O_RECUPERAR_CUENTA.bat
"""
import time
from getpass import getpass

TEXTO_AUTOMATICO = ('conda ', 'activate', 'source ', '& ', 'cd ', '.venv', 'call ')


def vaciar_teclado():
    """Descarta lo que la terminal haya escrito sola (p. ej. 'conda activate base' en VS Code)."""
    time.sleep(0.8)
    try:
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getwch()
    except ImportError:
        pass


def preguntar(texto, convertir, oculto=False):
    while True:
        valor = (getpass if oculto else input)(texto)
        if not oculto and valor.strip().lower().startswith(TEXTO_AUTOMATICO):
            print('  (Se ignoró un texto que escribió la terminal automáticamente. Escribe tu respuesta.)')
            continue
        try:
            return convertir(valor)
        except Exception as error:
            print('  ✗', getattr(error, 'detail', None) or error, '— inténtalo de nuevo.')


def main():
    print('Cuenta docente · crear una cuenta o cambiar su contraseña.')
    import main as aplicacion  # noqa: F401  (crea/actualiza las tablas)
    from autenticacion import Usuario, Sesion, RecuperacionPassword, nombre_normalizado, correo_normalizado, validar_password
    from claves import hash_password
    from database import SessionLocal

    vaciar_teclado()
    print('\nEscribe cada dato y presiona Enter.')
    correo = preguntar('Correo del docente: ', correo_normalizado)
    with SessionLocal() as db:
        usuario = db.query(Usuario).filter_by(correo=correo).with_for_update().first()
        if usuario:
            print(f'Cuenta encontrada: {usuario.nombre}. Se le asignará una contraseña nueva.')
        else:
            print('No existe una cuenta con ese correo: se creará una nueva.')
            nombre = preguntar('Nombre completo: ', nombre_normalizado)

        def password_valida(valor):
            validar_password(valor)
            return valor
        while True:
            password = preguntar('Contraseña (mínimo 6 caracteres, no se muestra al escribir): ', password_valida, oculto=True)
            if password == getpass('Repite la contraseña: '):
                break
            print('  ✗ Las contraseñas no coinciden — inténtalo de nuevo.')
        if not usuario:
            usuario = Usuario(nombre=nombre, correo=correo, password_hash=hash_password(password))
            db.add(usuario)
            db.flush()
        else:
            usuario.password_hash = hash_password(password)
            db.query(Sesion).filter_by(usuario_id=usuario.id).delete()
            db.query(RecuperacionPassword).filter_by(usuario_id=usuario.id).delete()
        db.commit()
    print(f'\n✓ Cuenta lista. Abre http://127.0.0.1:8000/acceso e inicia sesión con {correo}.')


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\nOperación cancelada.')
        raise SystemExit(1)
    except Exception as error:
        detalle = getattr(error, 'detail', None) or str(error).splitlines()[0][:200]
        print('No se pudo guardar. No se hicieron cambios.')
        print('Motivo:', detalle)
        print('Revisa que MySQL esté encendido en XAMPP.')
        raise SystemExit(1)
