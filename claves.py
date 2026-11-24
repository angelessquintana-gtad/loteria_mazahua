"""Funciones de contraseña independientes de la configuración del servidor."""
import hashlib
import hmac
import secrets
import re


def formato_hash_valido(encoded):
    if not re.fullmatch(r'pbkdf2_sha256\$\d+\$[0-9a-f]{32}\$[0-9a-f]{64}', encoded):
        return False
    return 100_000 <= int(encoded.split('$')[1]) <= 2_000_000


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600_000).hex()
    return f'pbkdf2_sha256$600000${salt}${digest}'


def verificar_password(password, encoded):
    try:
        algoritmo, iterations, salt, digest = encoded.split('$')
        if algoritmo != 'pbkdf2_sha256' or not 100_000 <= int(iterations) <= 2_000_000:
            return False
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(iterations)).hex()
        return hmac.compare_digest(actual, digest)
    except (ValueError, TypeError):
        return False
