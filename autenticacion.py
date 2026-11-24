"""Cuentas de docentes: registro libre, inicio de sesión con correo y recuperación de contraseña.

- Las contraseñas se guardan con hash PBKDF2-SHA256 (nunca en texto plano).
- La sesión es un JWT firmado en una cookie HttpOnly; cada sesión se registra en la tabla
  `sesiones` para poder cerrarla (logout) o invalidarla al cambiar la contraseña.
- La recuperación usa un enlace temporal (30 min) y de un solo uso; en la base solo se
  guarda el hash del código del enlace.
"""
import hashlib
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.exc import IntegrityError

from claves import hash_password, verificar_password
from configuracion import COOKIE_NAME, JWT_ISSUER, JWT_MINUTES, JWT_SECRET, PRODUCCION
from database import Base, SessionLocal
from correo import correo_disponible, enviar_recuperacion

router = APIRouter(prefix='/api/auth', tags=['Cuenta docente'])
logger = logging.getLogger('mazahua.cuentas')
MINIMO_PASSWORD = 6


class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(254), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, nullable=False, default=datetime.utcnow)


class Sesion(Base):
    __tablename__ = 'sesiones'
    jti = Column(String(64), primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True)
    vence = Column(DateTime, nullable=False, index=True)


class RecuperacionPassword(Base):
    __tablename__ = 'recuperaciones_password'
    token_hash = Column(String(64), primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True)
    creada = Column(DateTime, nullable=False, default=datetime.utcnow)
    vence = Column(DateTime, nullable=False, index=True)


# ---------------------------------------------------------------- validaciones
class Registro(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: str = Field(min_length=1, max_length=100)
    correo: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)
    confirmacion: str = Field(min_length=1, max_length=128)


class Credenciales(BaseModel):
    model_config = ConfigDict(extra='forbid')
    correo: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class CorreoSolicitud(BaseModel):
    model_config = ConfigDict(extra='forbid')
    correo: str = Field(min_length=1, max_length=254)


class CambioPassword(BaseModel):
    model_config = ConfigDict(extra='forbid')
    actual: str = Field(min_length=1, max_length=128)
    nueva: str = Field(min_length=1, max_length=128)


class Perfil(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: str = Field(min_length=1, max_length=100)
    correo: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class Restablecer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    token: str = Field(min_length=32, max_length=128)
    nueva: str = Field(min_length=1, max_length=128)


def correo_normalizado(valor):
    valor = (valor or '').strip().lower()
    if len(valor) > 254 or not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z]{2,63}", valor):
        raise HTTPException(422, 'Escribe un correo electrónico válido, por ejemplo nombre@escuela.mx.')
    return valor


def nombre_normalizado(valor):
    nombre = ' '.join((valor or '').split())
    if len(nombre) < 2 or any(ord(c) < 32 for c in nombre):
        raise HTTPException(422, 'Escribe tu nombre completo.')
    return nombre


def validar_password(password):
    if len(password) < MINIMO_PASSWORD or not password.strip():
        raise HTTPException(422, f'La contraseña debe tener al menos {MINIMO_PASSWORD} caracteres.')


def resumen(usuario):
    # 'rol' se conserva para compatibilidad con las páginas: todo docente tiene los mismos permisos.
    return {'id': usuario.id, 'nombre': usuario.nombre, 'correo': usuario.correo, 'rol': 'docente',
            'fecha_registro': usuario.fecha_registro.isoformat() if usuario.fecha_registro else None}


# ---------------------------------------------------------------- sesiones
def emitir_sesion(db, usuario, response):
    ahora = datetime.now(timezone.utc)
    vence = ahora + timedelta(minutes=JWT_MINUTES)
    jti, csrf = secrets.token_hex(32), secrets.token_urlsafe(32)
    token = jwt.encode({'sub': str(usuario.id), 'jti': jti, 'csrf': csrf, 'role': 'docente',
                        'iss': JWT_ISSUER, 'aud': JWT_ISSUER, 'iat': ahora, 'nbf': ahora, 'exp': vence},
                       JWT_SECRET, algorithm='HS256')
    db.query(Sesion).filter(Sesion.vence <= datetime.utcnow()).delete(synchronize_session=False)
    db.add(Sesion(jti=jti, usuario_id=usuario.id, vence=vence.replace(tzinfo=None)))
    db.commit()
    response.set_cookie(COOKIE_NAME, token, max_age=JWT_MINUTES * 60, httponly=True,
                        secure=PRODUCCION, samesite='strict', path='/')
    response.headers['Cache-Control'] = 'no-store'
    return {'docente': resumen(usuario), 'csrf_token': csrf, 'vence': vence.isoformat()}


def autenticar_solicitud(request):
    """Devuelve los datos del docente si la cookie (o Bearer) es una sesión vigente; si no, None."""
    header = request.headers.get('authorization', '')
    if header:
        esquema, _, token = header.partition(' ')
        if esquema.lower() != 'bearer':
            return None
    else:
        token = request.cookies.get(COOKIE_NAME, '')
    if not token or len(token) > 4096:
        return None
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=['HS256'], issuer=JWT_ISSUER, audience=JWT_ISSUER,
                            options={'require': ['sub', 'jti', 'exp', 'iat', 'nbf', 'iss', 'aud', 'csrf']})
        with SessionLocal() as db:
            sesion = db.get(Sesion, claims['jti'])
            if not sesion or sesion.vence <= datetime.utcnow() or str(sesion.usuario_id) != claims['sub']:
                return None
            usuario = db.get(Usuario, sesion.usuario_id)
            if not usuario:
                return None
            return {**resumen(usuario), 'jti': claims['jti'], 'csrf': claims['csrf'], 'bearer': bool(header)}
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        return None


def crear_ticket_ws(docente, codigo):
    """Ticket firmado y breve para abrir el WebSocket de una partida desde otro dominio."""
    ahora = datetime.now(timezone.utc)
    return jwt.encode({'sub': str(docente['id']), 'jti': docente['jti'], 'sala': codigo, 'typ': 'ws',
                       'iat': ahora, 'exp': ahora + timedelta(minutes=2), 'iss': JWT_ISSUER, 'aud': JWT_ISSUER + '-ws'},
                      JWT_SECRET, algorithm='HS256')


def docente_por_ticket(ticket, codigo):
    try:
        claims = jwt.decode(ticket, JWT_SECRET, algorithms=['HS256'], issuer=JWT_ISSUER, audience=JWT_ISSUER + '-ws',
                            options={'require': ['sub', 'jti', 'exp', 'sala', 'typ']})
        if claims['typ'] != 'ws' or claims['sala'] != codigo:
            return None
        with SessionLocal() as db:
            sesion = db.get(Sesion, claims['jti'])
            if not sesion or sesion.vence <= datetime.utcnow() or str(sesion.usuario_id) != claims['sub']:
                return None
            usuario = db.get(Usuario, sesion.usuario_id)
            return {**resumen(usuario), 'jti': claims['jti'], 'csrf': '', 'bearer': False} if usuario else None
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        return None


def docente_actual(request):
    docente = getattr(request.state, 'docente', None)
    if not docente:
        raise HTTPException(401, 'Inicia sesión con tu cuenta docente.', headers={'WWW-Authenticate': 'Bearer'})
    return docente


# Una comprobación falsa tiene el mismo coste que una real: no revela qué correos existen.
_HASH_FICTICIO = hash_password(secrets.token_urlsafe(32))


# ---------------------------------------------------------------- rutas
@router.post('/registro', status_code=201)
def registrar(datos: Registro):
    """Crear cuenta de docente: sin solicitudes ni aprobaciones."""
    nombre = nombre_normalizado(datos.nombre)
    correo = correo_normalizado(datos.correo)
    validar_password(datos.password)
    if datos.password != datos.confirmacion:
        raise HTTPException(422, 'Las contraseñas no coinciden.')
    with SessionLocal() as db:
        if db.query(Usuario.id).filter_by(correo=correo).first():
            raise HTTPException(409, 'Ya existe una cuenta con ese correo. Inicia sesión o recupera tu contraseña.')
        db.add(Usuario(nombre=nombre, correo=correo, password_hash=hash_password(datos.password)))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Ya existe una cuenta con ese correo. Inicia sesión o recupera tu contraseña.')
    return {'ok': True, 'correo': correo, 'mensaje': '¡Cuenta creada! Ya puedes iniciar sesión con tu correo y contraseña.'}


@router.post('/login')
def login(datos: Credenciales, response: Response):
    correo = (datos.correo or '').strip().lower()
    with SessionLocal() as db:
        usuario = db.query(Usuario).filter_by(correo=correo).first()
        valido = verificar_password(datos.password, usuario.password_hash if usuario else _HASH_FICTICIO)
        if not valido or not usuario:
            raise HTTPException(401, 'Correo o contraseña incorrectos.')
        resultado = emitir_sesion(db, usuario, response)
        resultado['mensaje'] = f'¡Bienvenido(a), {usuario.nombre}!'
        return resultado


@router.get('/me')
def me(request: Request):
    docente = docente_actual(request)
    return {'docente': {k: docente[k] for k in ('id', 'nombre', 'correo', 'rol', 'fecha_registro')},
            'csrf_token': docente['csrf']}


@router.post('/logout')
def logout(request: Request, response: Response):
    docente = docente_actual(request)
    with SessionLocal() as db:
        db.query(Sesion).filter_by(jti=docente['jti']).delete()
        db.commit()
    response.delete_cookie(COOKIE_NAME, path='/', secure=PRODUCCION, httponly=True, samesite='strict')
    return {'ok': True, 'mensaje': 'Sesión cerrada.'}


@router.put('/perfil')
def actualizar_perfil(datos: Perfil, request: Request):
    """Cambiar nombre y correo (pide la contraseña actual)."""
    actual = docente_actual(request)
    nombre, correo = nombre_normalizado(datos.nombre), correo_normalizado(datos.correo)
    with SessionLocal() as db:
        usuario = db.query(Usuario).filter_by(id=actual['id']).with_for_update().one()
        if not verificar_password(datos.password, usuario.password_hash):
            raise HTTPException(403, 'La contraseña actual no es correcta.')
        usuario.nombre, usuario.correo = nombre, correo
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Ese correo ya pertenece a otra cuenta.')
    return {'ok': True, 'mensaje': 'Tus datos se actualizaron.'}


@router.post('/password')
def cambiar_password(datos: CambioPassword, request: Request, response: Response):
    actual = docente_actual(request)
    validar_password(datos.nueva)
    with SessionLocal() as db:
        usuario = db.query(Usuario).filter_by(id=actual['id']).with_for_update().one()
        if not verificar_password(datos.actual, usuario.password_hash):
            raise HTTPException(403, 'La contraseña actual no es correcta.')
        usuario.password_hash = hash_password(datos.nueva)
        db.query(Sesion).filter_by(usuario_id=usuario.id).delete()
        db.query(RecuperacionPassword).filter_by(usuario_id=usuario.id).delete()
        db.commit()
    response.delete_cookie(COOKIE_NAME, path='/', secure=PRODUCCION, httponly=True, samesite='strict')
    return {'ok': True, 'mensaje': 'Contraseña actualizada. Inicia sesión de nuevo con tu nueva contraseña.'}


@router.get('/configuracion')
def opciones_acceso():
    return {'recuperacion_por_correo': correo_disponible(), 'minimo_password': MINIMO_PASSWORD}


def es_equipo_local(request):
    host = request.client.host if request.client else ''
    return host in {'127.0.0.1', '::1', 'localhost'}


@router.post('/recuperar', status_code=202)
def recuperar(datos: CorreoSolicitud, request: Request, background_tasks: BackgroundTasks):
    """Envía un enlace de recuperación (válido 30 minutos y de un solo uso)."""
    correo = correo_normalizado(datos.correo)
    mensaje = ('Si el correo está registrado, te enviamos un enlace para crear una nueva contraseña. '
               'Es válido por 30 minutos. Revisa también la carpeta de correo no deseado.')
    enlace_local = None
    with SessionLocal() as db:
        usuario = db.query(Usuario).filter_by(correo=correo).with_for_update().first()
        if usuario:
            reciente = db.query(RecuperacionPassword).filter(RecuperacionPassword.usuario_id == usuario.id,
                RecuperacionPassword.creada > datetime.utcnow() - timedelta(minutes=1)).first()
            if not reciente:
                token = secrets.token_urlsafe(32)
                db.query(RecuperacionPassword).filter_by(usuario_id=usuario.id).delete()
                db.add(RecuperacionPassword(token_hash=hashlib.sha256(token.encode()).hexdigest(), usuario_id=usuario.id,
                                            vence=datetime.utcnow() + timedelta(minutes=30)))
                db.commit()
                if correo_disponible():
                    background_tasks.add_task(enviar_recuperacion, correo, token)
                elif not PRODUCCION:
                    # Sin servidor de correo configurado (uso local): el enlace se muestra en la
                    # ventana del servidor y, si la petición viene de esta misma computadora, en pantalla.
                    ruta = '/acceso#recuperar=' + token
                    print(f'\n[Recuperación de contraseña] {correo}: abre http://127.0.0.1:8000{ruta}\n', flush=True)
                    if es_equipo_local(request):
                        enlace_local = ruta
    if enlace_local:
        return {'mensaje': 'El correo electrónico aún no está configurado en este equipo, así que aquí tienes '
                           'tu enlace de recuperación (válido 30 minutos, un solo uso).', 'enlace': enlace_local}
    return {'mensaje': mensaje}


@router.post('/restablecer')
def restablecer(datos: Restablecer):
    validar_password(datos.nueva)
    token_hash = hashlib.sha256(datos.token.encode()).hexdigest()
    with SessionLocal() as db:
        recuperacion = db.get(RecuperacionPassword, token_hash)
        if not recuperacion:
            raise HTTPException(403, 'El enlace no es válido, ya fue utilizado o venció. Solicita otro.')
        usuario = db.query(Usuario).filter_by(id=recuperacion.usuario_id).with_for_update().one()
        # Consumir el enlace de forma condicional impide usarlo dos veces al mismo tiempo.
        usada = db.query(RecuperacionPassword).filter(RecuperacionPassword.token_hash == token_hash,
            RecuperacionPassword.vence > datetime.utcnow()).delete(synchronize_session=False)
        if usada != 1:
            db.commit()
            raise HTTPException(403, 'El enlace no es válido, ya fue utilizado o venció. Solicita otro.')
        usuario.password_hash = hash_password(datos.nueva)
        db.query(Sesion).filter_by(usuario_id=usuario.id).delete()
        db.query(RecuperacionPassword).filter_by(usuario_id=usuario.id).delete(synchronize_session=False)
        db.commit()
        correo = usuario.correo
    return {'ok': True, 'correo': correo,
            'mensaje': '¡Contraseña actualizada! Ya puedes iniciar sesión con tu nueva contraseña.'}
