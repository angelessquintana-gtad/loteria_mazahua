"""Salas persistentes; cada lector del navegador anuncia en su propia partida."""
import asyncio
import json
import time
import secrets
import hashlib
import hmac
import logging
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, or_, insert
from sqlalchemy.exc import IntegrityError

from database import Base, SessionLocal, es_tidb
from configuracion import ORIGENES_PERMITIDOS, ROOM_IDLE_MINUTES, ROOM_MAX_HOURS, ROOM_RETENTION_DAYS
from frontend_web import pagina

router = APIRouter()
STATIC = Path(__file__).resolve().parent / "static"
logger = logging.getLogger('mazahua.partidas')


class Partida(Base):
    __tablename__ = "partidas"
    id = Column(Integer, primary_key=True)
    codigo = Column(String(6), unique=True, nullable=False)          # código de acceso que va en el QR
    nombre = Column(String(100), nullable=False, default='Partida')
    usuario_id = Column(Integer, ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True, index=True)  # docente que la creó
    limite = Column(Integer, nullable=False, default=25, server_default="25")
    estado = Column(String(16), nullable=False, default="esperando")  # esperando · en_curso · finalizada
    creada = Column('fecha_creacion', DateTime, nullable=False, default=datetime.utcnow)
    iniciada = Column(DateTime)
    finalizada = Column(DateTime)
    ultima_tarjeta_id = Column(Integer, ForeignKey('tarjetas.id', ondelete='SET NULL'), nullable=True)
    secuencia = Column(Integer, nullable=False, default=0, server_default="0")
    ultima_actividad_docente = Column(DateTime, nullable=True)
    cierre_motivo = Column(String(30), nullable=True)
    # Partida entre amigos (sin cuenta docente): hash de la clave del anfitrión.
    anfitrion = Column(String(64), nullable=True)


def motivo_caducidad(p, ahora=None):
    if p.estado == 'finalizada':
        return None
    ahora = ahora or datetime.utcnow()
    if p.creada <= ahora - timedelta(hours=ROOM_MAX_HOURS):
        return 'duracion_maxima'
    if (p.ultima_actividad_docente or p.iniciada or p.creada) <= ahora - timedelta(minutes=ROOM_IDLE_MINUTES):
        return 'inactividad_docente'
    return None


def mantenimiento_partidas(db, ahora=None):
    """Caduca sesiones abandonadas y purga historial antiguo en lotes acotados."""
    ahora = ahora or datetime.utcnow()
    ultima = func.coalesce(Partida.ultima_actividad_docente, Partida.iniciada, Partida.creada)
    candidatas = (db.query(Partida).filter(Partida.estado != 'finalizada',
                   or_(Partida.creada <= ahora - timedelta(hours=ROOM_MAX_HOURS),
                       ultima <= ahora - timedelta(minutes=ROOM_IDLE_MINUTES)))
                   .order_by(Partida.id).limit(100).with_for_update().all())
    for p in candidatas:
        p.cierre_motivo = motivo_caducidad(p, ahora)
        p.estado, p.finalizada = 'finalizada', ahora
    # Caducadas se conservan durante la retención; no borrar recién cerradas.
    db.flush()
    antiguas = [p.id for p in db.query(Partida).filter(Partida.estado == 'finalizada',
                  Partida.finalizada < ahora - timedelta(days=ROOM_RETENTION_DAYS))
                  .order_by(Partida.id).limit(100).with_for_update().all()]
    if antiguas:
        alumnos = db.query(Participante.id).filter(Participante.partida_id.in_(antiguas))
        tableros = db.query(Tablero.id).filter(Tablero.participante_id.in_(alumnos))
        db.query(Anuncio).filter(Anuncio.partida_id.in_(antiguas)).delete(synchronize_session=False)
        db.query(TableroTarjeta).filter(TableroTarjeta.tablero_id.in_(tableros)).delete(synchronize_session=False)
        db.query(Tablero).filter(Tablero.participante_id.in_(alumnos)).delete(synchronize_session=False)
        db.query(Participante).filter(Participante.partida_id.in_(antiguas)).delete(synchronize_session=False)
        db.query(Partida).filter(Partida.id.in_(antiguas)).delete(synchronize_session=False)
    db.commit()
    return {'caducadas': len(candidatas), 'purgadas': len(antiguas)}


def ejecutar_mantenimiento():
    with SessionLocal() as db:
        resultado = mantenimiento_partidas(db)
        if any(resultado.values()):
            logger.info('Mantenimiento de partidas: %s', resultado)
        return resultado


class NuevaPartida(BaseModel):
    limite: int = Field(default=25, ge=1, le=100, strict=True)
    nombre: str = Field(default='', max_length=100)


class Participante(Base):
    __tablename__ = "participantes"
    __table_args__ = (UniqueConstraint("partida_id", "dispositivo", name='ux_participante_dispositivo'),)
    id = Column(Integer, primary_key=True)
    partida_id = Column(Integer, ForeignKey("partidas.id", ondelete='CASCADE'), nullable=False, index=True)
    nombre = Column(String(60), nullable=False)
    # Identificador aleatorio del navegador del alumno: le permite recargar la página sin perder su tablero.
    solicitud = Column('dispositivo', String(36), nullable=False)
    incorporado = Column('fecha_ingreso', DateTime, nullable=False, default=datetime.utcnow)
    gano = Column(Boolean, nullable=False, default=False, server_default='0')
    # Avatar que el alumno arma al entrar (código corto, por ejemplo «p2-c1-h3-r4-a1-f2»).
    avatar = Column(String(60), nullable=True)


class Ingreso(BaseModel):
    codigo: str = Field(min_length=6, max_length=6, pattern=r"^[A-Za-z0-9]{6}$")
    nombre: str = Field(min_length=1, max_length=60)
    solicitud: UUID
    avatar: str | None = Field(default=None, max_length=60, pattern=r"^[a-z0-9-]*$")


class Tablero(Base):
    __tablename__ = "tableros"
    id = Column(Integer, primary_key=True)
    participante_id = Column(Integer, ForeignKey("participantes.id", ondelete='CASCADE'), unique=True, nullable=False)
    creado = Column(DateTime, nullable=False, default=datetime.utcnow)


class TableroTarjeta(Base):
    """Las 16 cartas de cada tablero (relación con tarjetas) y si el alumno ya la marcó."""
    __tablename__ = "tablero_tarjetas"
    tablero_id = Column(Integer, ForeignKey("tableros.id", ondelete='CASCADE'), primary_key=True)
    posicion = Column(Integer, primary_key=True)
    tarjeta_id = Column(Integer, ForeignKey("tarjetas.id"), nullable=False, index=True)
    marcada = Column(Boolean, nullable=False, default=False, server_default='0')


class Anuncio(Base):
    """Cartas que el docente ya cantó en una partida."""
    __tablename__ = "anuncios"
    __table_args__ = (UniqueConstraint("partida_id", "tarjeta_id", name='ux_anuncio_partida_tarjeta'),)
    id = Column(Integer, primary_key=True)
    partida_id = Column(Integer, ForeignKey("partidas.id", ondelete='CASCADE'), nullable=False, index=True)
    tarjeta_id = Column(Integer, ForeignKey("tarjetas.id"), nullable=False)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)


class Marca(BaseModel):
    token: UUID
    tarjeta_id: int = Field(gt=0)
    marcada: bool


class Reclamo(BaseModel):
    token: UUID


class CartaAnunciada(BaseModel):
    uid: str = Field(min_length=1, max_length=40)   # UID RFID o número de la carta
    clave: str | None = Field(default=None, max_length=64)  # compatibilidad: ya no se usa


def cartas_tablero(db, tablero_id):
    """Devuelve (cartas, marcas) de un tablero con los datos actuales de cada tarjeta."""
    from main import Tarjeta, tarjeta_json
    filas = (db.query(TableroTarjeta, Tarjeta).join(Tarjeta, Tarjeta.id == TableroTarjeta.tarjeta_id)
             .filter(TableroTarjeta.tablero_id == tablero_id).order_by(TableroTarjeta.posicion).all())
    return [tarjeta_json(t) for _, t in filas], sorted(tt.tarjeta_id for tt, _ in filas if tt.marcada)


def preparar_tableros(db, p):
    from main import Tarjeta
    ids = [i for (i,) in db.query(Tarjeta.id).order_by(Tarjeta.id)]
    if len(ids) < 16:
        raise HTTPException(409, f"Necesitas al menos 16 cartas registradas. Actualmente hay {len(ids)}.")
    usados = set()
    for alumno in db.query(Participante).filter_by(partida_id=p.id).order_by(Participante.id):
        # Con más de 16 cartas se distingue el conjunto, no solo la disposición.
        for _ in range(100):
            seleccion = secrets.SystemRandom().sample(ids, 16)
            firma = tuple(sorted(seleccion)) if len(ids) > 16 else tuple(seleccion)
            if firma not in usados:
                usados.add(firma)
                break
        else:
            raise HTTPException(503, "No se pudieron generar tableros diferentes. Intenta de nuevo.")
        tablero = Tablero(participante_id=alumno.id)
        db.add(tablero)
        db.flush()
        db.execute(insert(TableroTarjeta), [{'tablero_id': tablero.id, 'posicion': n, 'tarjeta_id': t, 'marcada': False}
                                            for n, t in enumerate(seleccion)])


class Control(BaseModel):
    clave: str | None = Field(default=None, max_length=64)  # compatibilidad: ya no se usa


def buscar(db, codigo, bloquear=False):
    q = db.query(Partida).filter(Partida.codigo == codigo.upper())
    # Al marcar, varios alumnos leen la sala a la vez (bloqueo compartido); TiDB no lo admite y usa uno normal.
    bloqueada = q.with_for_update(read=bloquear == 'compartido' and not es_tidb()) if bloquear else q
    p = bloqueada.first()
    if p is None:
        raise HTTPException(404, "El código no existe. Revisa los seis caracteres.")
    motivo = motivo_caducidad(p)
    if motivo:
        # Actualización condicional: no cerrar una sesión cuyo docente acaba de renovar.
        ahora = datetime.utcnow()
        ultima = func.coalesce(Partida.ultima_actividad_docente, Partida.iniciada, Partida.creada)
        db.query(Partida).filter(Partida.id == p.id, Partida.estado != 'finalizada',
            or_(Partida.creada <= ahora - timedelta(hours=ROOM_MAX_HOURS),
                ultima <= ahora - timedelta(minutes=ROOM_IDLE_MINUTES))).update(
                    {'estado': 'finalizada', 'finalizada': ahora, 'cierre_motivo': motivo}, synchronize_session=False)
        db.commit()
        # Un commit libera FOR UPDATE; retomar el bloqueo para la operación solicitada.
        p = bloqueada.populate_existing().first()
    return p


def es_del_docente(p, docente):
    """El docente que creó la partida la administra (las partidas antiguas sin dueño, cualquier docente)."""
    return bool(docente) and (p.usuario_id is None or p.usuario_id == docente['id'])


def exigir_docente(p, request):
    docente = getattr(request.state, 'docente', None)
    if not es_del_docente(p, docente):
        raise HTTPException(403, "Solo el docente que creó esta partida puede administrarla.")
    return docente


def snapshot(db, p):
    from main import Tarjeta, tarjeta_json
    anunciadas = [t for (t,) in db.query(Anuncio.tarjeta_id).filter_by(partida_id=p.id).order_by(Anuncio.id)]
    ganador = db.query(Participante).filter_by(partida_id=p.id, gano=True).first()
    ultima_id = p.ultima_tarjeta_id or (anunciadas[-1] if anunciadas else None)
    ultima = db.get(Tarjeta, ultima_id) if ultima_id else None
    return {"id": p.id, "codigo": p.codigo, "nombre": p.nombre, "estado": p.estado, "limite": p.limite,
            "cierre_motivo": p.cierre_motivo,
            "secuencia": p.secuencia,
            "amigos": bool(p.anfitrion),
            "anunciadas": anunciadas,
            "ultima_carta": tarjeta_json(ultima) if ultima else None,
            "ganador": {"id": ganador.id, "nombre": ganador.nombre, "avatar": ganador.avatar} if ganador else None,
            "participantes": [{"id": x.id, "nombre": x.nombre, "avatar": x.avatar} for x in
                              db.query(Participante).filter_by(partida_id=p.id).order_by(Participante.id)]}


@router.get("/docente")
def docente():
    return pagina('docente')


@router.get("/estudiante")
def estudiante():
    return pagina('estudiante')


@router.post("/api/partidas", status_code=201)
def crear(request: Request, datos: NuevaPartida = NuevaPartida()):
    docente = getattr(request.state, 'docente', None)
    nombre = " ".join(datos.nombre.split()) or f"Partida del {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    with SessionLocal() as db:
        if db.query(Partida).filter(Partida.estado != 'finalizada').count() >= 100:
            raise HTTPException(429, 'Hay demasiadas partidas abiertas. Finaliza las anteriores desde tu panel.')
        for _ in range(10):
            p = Partida(codigo="".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6)),
                        nombre=nombre, usuario_id=docente['id'] if docente else None,
                        limite=datos.limite, ultima_actividad_docente=datetime.utcnow())
            db.add(p)
            try:
                db.commit()
                return {**snapshot(db, p), "mensaje": f"Partida «{nombre}» creada. Comparte el código {p.codigo} o el QR."}
            except IntegrityError:
                db.rollback()
        raise HTTPException(503, "No se pudo generar un código. Intenta de nuevo.")


@router.get("/api/partidas/mias")
def mis_partidas(request: Request):
    """Partidas del docente con sesión iniciada (más recientes primero)."""
    docente = getattr(request.state, 'docente', None)
    with SessionLocal() as db:
        filas = (db.query(Partida, func.count(Participante.id)).outerjoin(Participante, Participante.partida_id == Partida.id)
                 .filter(or_(Partida.usuario_id == docente['id'], (Partida.usuario_id.is_(None) & Partida.anfitrion.is_(None))))
                 .group_by(Partida.id).order_by(Partida.id.desc()).limit(50).all())
        return [{'codigo': p.codigo, 'nombre': p.nombre, 'estado': p.estado, 'limite': p.limite,
                 'participantes': n, 'creada': p.creada.isoformat() if p.creada else None} for p, n in filas]


@router.get("/api/partidas/{codigo}/publica")
def partida_publica(codigo: str):
    """Lo mínimo que necesita la pantalla del alumno antes de entrar (sin datos privados)."""
    with SessionLocal() as db:
        p = buscar(db, codigo)
        ocupados = db.query(Participante).filter_by(partida_id=p.id).count()
        return {'codigo': p.codigo, 'nombre': p.nombre, 'estado': p.estado, 'limite': p.limite,
                'lugares_disponibles': max(p.limite - ocupados, 0)}


@router.post("/api/partidas/unirse")
def unirse(datos: Ingreso):
    nombre = " ".join(datos.nombre.split())
    if not nombre or any(ord(c) < 32 for c in nombre):
        raise HTTPException(422, "Escribe un nombre válido.")
    with SessionLocal() as db:
        p = buscar(db, datos.codigo, True)
        token = str(datos.solicitud)
        existente = db.query(Participante).filter_by(partida_id=p.id, solicitud=token).first()
        if existente:
            if datos.avatar and existente.avatar != datos.avatar:
                existente.avatar = datos.avatar
                db.commit()
            return snapshot(db, p)
        if p.estado != "esperando":
            raise HTTPException(409, "La partida ya comenzó; ya no se pueden unir más alumnos." if p.estado == "en_curso"
                                else "La partida está cerrada.")
        if db.query(Participante).filter_by(partida_id=p.id).count() >= p.limite:
            raise HTTPException(409, f"La partida está llena: el máximo es de {p.limite} alumnos.")
        db.add(Participante(partida_id=p.id, nombre=nombre, solicitud=token, avatar=datos.avatar or None))
        db.commit()
        resumen = snapshot(db, p)
        resumen['mensaje'] = f"¡Listo, {nombre}! Entraste a «{p.nombre}». Espera a que {'el anfitrión' if p.anfitrion else 'tu docente'} inicie el juego."
        return resumen


class NuevaPartidaAmigos(BaseModel):
    nombre: str = Field(min_length=1, max_length=60)
    solicitud: UUID
    avatar: str | None = Field(default=None, max_length=60, pattern=r"^[a-z0-9-]*$")


def hash_clave(clave: str) -> str:
    return hashlib.sha256(clave.encode()).hexdigest()


def exigir_anfitrion(p, request: Request):
    clave = request.headers.get('x-anfitrion', '')
    if not p.anfitrion or not clave or not hmac.compare_digest(hash_clave(clave), p.anfitrion):
        raise HTTPException(403, 'Solo quien creó la partida puede controlarla.')


@router.post("/api/amigos", status_code=201)
def crear_con_amigos(datos: NuevaPartidaAmigos):
    """Partida para jugar con amigos sin cuenta: quien la crea es el anfitrión, juega con su
    propio tablero y saca las cartas (al azar); los demás entran con el enlace o el QR."""
    nombre = " ".join(datos.nombre.split())
    if not nombre or any(ord(c) < 32 for c in nombre):
        raise HTTPException(422, "Escribe un nombre válido.")
    clave = secrets.token_urlsafe(24)
    with SessionLocal() as db:
        if db.query(Partida).filter(Partida.estado != 'finalizada').count() >= 100:
            raise HTTPException(429, 'Hay demasiadas partidas abiertas. Intenta más tarde.')
        for _ in range(10):
            p = Partida(codigo="".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6)),
                        nombre=f"Partida de {nombre}"[:100], limite=30, anfitrion=hash_clave(clave),
                        ultima_actividad_docente=datetime.utcnow())
            db.add(p)
            try:
                db.flush()
                db.add(Participante(partida_id=p.id, nombre=nombre, solicitud=str(datos.solicitud), avatar=datos.avatar or None))
                db.commit()
                return {**snapshot(db, p), 'clave_anfitrion': clave,
                        'mensaje': f'¡Partida creada! Comparte el enlace o el QR con tus amigos. Código: {p.codigo}'}
            except IntegrityError:
                db.rollback()
        raise HTTPException(503, "No se pudo generar un código. Intenta de nuevo.")


@router.post("/api/amigos/{codigo}/{accion}")
def controlar_amigos(codigo: str, accion: str, request: Request):
    from main import Tarjeta
    with SessionLocal() as db:
        p = buscar(db, codigo, True)
        exigir_anfitrion(p, request)
        if accion == 'iniciar':
            if p.estado != 'esperando':
                raise HTTPException(409, 'La partida no está en espera.')
            preparar_tableros(db, p)
            p.estado, p.iniciada = 'en_curso', datetime.utcnow()
        elif accion == 'sacar':
            if p.estado != 'en_curso':
                raise HTTPException(409, 'La partida no está en curso.')
            salieron = {t for (t,) in db.query(Anuncio.tarjeta_id).filter_by(partida_id=p.id)}
            disponibles = [t for (t,) in db.query(Tarjeta.id) if t not in salieron]
            if not disponibles:
                raise HTTPException(409, 'Ya salieron todas las cartas.')
            carta_id = secrets.choice(disponibles)
            db.add(Anuncio(partida_id=p.id, tarjeta_id=carta_id))
            p.ultima_tarjeta_id = carta_id
            p.secuencia += 1
        elif accion == 'finalizar':
            if p.estado != 'finalizada':
                p.estado, p.finalizada, p.cierre_motivo = 'finalizada', datetime.utcnow(), 'anfitrion'
        else:
            raise HTTPException(404, 'Acción desconocida.')
        p.ultima_actividad_docente = datetime.utcnow()
        db.commit()
        return snapshot(db, p)


@router.post("/api/partidas/{codigo}/{accion}")
def controlar(codigo: str, accion: str, request: Request, datos: Control = Control()):
    with SessionLocal() as db:
        p = buscar(db, codigo, True)
        exigir_docente(p, request)
        if accion == "iniciar":
            if p.estado != "esperando":
                raise HTTPException(409, "La partida no está en espera.")
            if not db.query(Participante).filter_by(partida_id=p.id).count():
                raise HTTPException(409, "Espera a que se una al menos un alumno.")
            preparar_tableros(db, p)
            p.estado, p.iniciada = "en_curso", datetime.utcnow()
        elif accion == "finalizar":
            if p.estado == "finalizada":
                return snapshot(db, p)
            p.estado, p.finalizada, p.cierre_motivo = "finalizada", datetime.utcnow(), 'docente'
        elif accion == 'latido':
            if p.estado == 'finalizada':
                return {'estado': p.estado, 'cierre_motivo': p.cierre_motivo}
        else:
            raise HTTPException(404, "Acción desconocida.")
        p.ultima_actividad_docente = datetime.utcnow()
        db.commit()
        if accion == 'latido':
            return {'estado': p.estado}
        return snapshot(db, p)


def alumno_tablero(db, p, token, bloquear=False):
    if p.estado != 'en_curso':
        raise HTTPException(409, 'La partida no está en curso.')
    alumno = db.query(Participante).filter_by(partida_id=p.id, solicitud=str(token)).first()
    if not alumno:
        raise HTTPException(403, 'No perteneces a esta partida.')
    consulta = db.query(Tablero).filter_by(participante_id=alumno.id)
    tablero = (consulta.with_for_update() if bloquear else consulta).first()
    if not tablero:
        raise HTTPException(409, 'Esta partida no tiene tableros. Pide al docente crear una nueva partida.')
    return alumno, tablero


@router.post('/api/juego/{codigo}/marcar')
def marcar(codigo: str, datos: Marca):
    with SessionLocal() as db:
        # Bloqueo compartido de sala: varios alumnos marcan en paralelo, mientras
        # finalizar/anunciar conservan exclusión. Solo el tablero propio se bloquea.
        p = buscar(db, codigo, 'compartido')
        _, tablero = alumno_tablero(db, p, datos.token, bloquear=True)
        casilla = db.query(TableroTarjeta).filter_by(tablero_id=tablero.id, tarjeta_id=datos.tarjeta_id).first()
        if not casilla:
            raise HTTPException(422, 'Esta carta no está en tu tablero.')
        if datos.marcada and not db.query(Anuncio).filter_by(partida_id=p.id, tarjeta_id=datos.tarjeta_id).first():
            raise HTTPException(409, 'Esta carta todavía no ha sido anunciada.')
        casilla.marcada = datos.marcada
        db.commit()
        return {"marcas": cartas_tablero(db, tablero.id)[1]}


@router.post('/api/juego/{codigo}/anunciar')
def anunciar(codigo: str, datos: CartaAnunciada, request: Request):
    from main import Tarjeta, normalizar_uid
    with SessionLocal() as db:
        p = buscar(db, codigo, True)
        exigir_docente(p, request)
        if p.estado != 'en_curso':
            raise HTTPException(409, 'La partida no está en curso.')
        valor = normalizar_uid(datos.uid)
        carta = db.query(Tarjeta).filter_by(uid=valor).first()
        if not carta and valor.isdigit():
            carta = db.query(Tarjeta).filter_by(numero=int(valor)).first()  # también se puede anunciar por número
        if not carta:
            raise HTTPException(404, 'No hay una tarjeta registrada con ese UID o número.')
        if not db.query(Anuncio).filter_by(partida_id=p.id, tarjeta_id=carta.id).first():
            db.add(Anuncio(partida_id=p.id, tarjeta_id=carta.id))
        p.ultima_tarjeta_id = carta.id
        p.secuencia += 1
        p.ultima_actividad_docente = datetime.utcnow()
        db.commit()
        return snapshot(db, p)


@router.post('/api/juego/{codigo}/loteria')
def reclamar(codigo: str, datos: Reclamo):
    with SessionLocal() as db:
        p = buscar(db, codigo, True)
        alumno, tablero = alumno_tablero(db, p, datos.token)
        casillas = db.query(TableroTarjeta).filter_by(tablero_id=tablero.id).all()
        cartas = {c.tarjeta_id for c in casillas}
        anunciadas = {a.tarjeta_id for a in db.query(Anuncio).filter_by(partida_id=p.id)}
        if len(cartas) != 16:
            raise HTTPException(409, 'Tu tablero no contiene 16 cartas distintas. Pide al docente crear una nueva partida.')
        marcadas = {c.tarjeta_id for c in casillas if c.marcada}
        if marcadas != cartas:
            raise HTTPException(409, f'Tienes {len(marcadas)} de 16 casillas marcadas. Completa las {16 - len(marcadas)} restantes para reclamar lotería.')
        pendientes = cartas - anunciadas
        if pendientes:
            raise HTTPException(409, f'Tus 16 casillas están marcadas, pero faltan {len(pendientes)} cartas de tu tablero por anunciar. Espera a que salgan para reclamar lotería.')
        alumno.gano = True
        p.estado, p.finalizada = 'finalizada', datetime.utcnow()
        p.cierre_motivo = 'loteria'
        db.commit()
        return snapshot(db, p)


def paquete_en_vivo(codigo):
    """Una consulta agrupada por sala, no una ronda SQL por cada alumno."""
    from autenticacion import Sesion
    with SessionLocal() as db:
        p = buscar(db, codigo)
        comun = snapshot(db, p)
        alumnos = {}
        for alumno, tablero in (db.query(Participante, Tablero).outerjoin(Tablero, Tablero.participante_id == Participante.id)
                                .filter(Participante.partida_id == p.id).all()):
            if tablero:
                cartas, marcas = cartas_tablero(db, tablero.id)
                alumnos[alumno.solicitud] = {'cartas': cartas, 'marcas': marcas}
            else:
                alumnos[alumno.solicitud] = None
        sesiones = {s.jti for s in db.query(Sesion).filter(Sesion.vence > datetime.utcnow())}
        return p.usuario_id, comun, alumnos, sesiones


REACCIONES = {'👏', '😄', '🌽', '❤️', '🎉', '🤔'}


def datos_alumno(codigo, token):
    with SessionLocal() as db:
        p = db.query(Partida).filter_by(codigo=codigo).first()
        alumno = p and db.query(Participante).filter_by(partida_id=p.id, solicitud=token).first()
        return {'id': alumno.id, 'nombre': alumno.nombre, 'avatar': alumno.avatar} if alumno else None


class CanalPartida:
    def __init__(self, codigo):
        self.codigo = codigo
        self.clientes = {}
        self.tarea = None

    async def emitir(self, ws, cliente, paquete):
        usuario_id, comun, alumnos, sesiones = paquete
        try:
            docente = cliente['docente']
            if cliente['token'] == 'docente':
                # El panel docente se identifica con su sesión iniciada (cookie), no con claves.
                if not docente or docente['jti'] not in sesiones or (usuario_id is not None and usuario_id != docente['id']):
                    await ws.close(code=1008)
                    return
                actual = comun
            elif cliente['token'] in alumnos:
                # Cada alumno recibe solamente su tablero, nunca datos de otros alumnos.
                actual = {**comun, 'tablero':alumnos[cliente['token']]}
            else:
                await ws.close(code=1008)
                return
            if actual != cliente['anterior']:
                await asyncio.wait_for(ws.send_json(actual), timeout=10)
                cliente['anterior'] = actual
            if comun['estado'] == 'finalizada':
                await ws.close(code=1000)
        except (WebSocketDisconnect, RuntimeError, TimeoutError):
            self.clientes.pop(ws, None)

    async def reaccion(self, ws, mensaje):
        """Un alumno manda una reacción (emoji): se reenvía a todos los de la sala, máximo 1 por segundo."""
        cliente = self.clientes.get(ws)
        try:
            emoji = json.loads(mensaje).get('reaccion')
        except (ValueError, AttributeError):
            return
        ahora = time.monotonic()
        if not cliente or emoji not in REACCIONES or ahora - cliente.get('ultima_reaccion', 0) < 1.0:
            return
        cliente['ultima_reaccion'] = ahora
        if 'alumno' not in cliente:
            cliente['alumno'] = await asyncio.to_thread(datos_alumno, self.codigo, cliente['token'])
        if not cliente['alumno']:
            return
        aviso = {'tipo': 'reaccion', 'emoji': emoji, **cliente['alumno']}
        await asyncio.gather(*(asyncio.wait_for(otro.send_json(aviso), timeout=5) for otro in list(self.clientes)),
                             return_exceptions=True)

    async def publicar(self):
        try:
            while self.clientes:
                paquete = await asyncio.to_thread(paquete_en_vivo, self.codigo)
                await asyncio.gather(*(self.emitir(ws, c, paquete) for ws,c in list(self.clientes.items())))
                if paquete[1]['estado'] == 'finalizada':
                    return
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception('No se pudo actualizar una sala en vivo')
            await asyncio.gather(*(ws.close(code=1011) for ws in list(self.clientes)), return_exceptions=True)


canales_en_vivo = {}


@router.websocket('/ws/partidas/{codigo}')
async def actualizaciones(ws: WebSocket, codigo: str):
    origin = ws.headers.get('origin')
    if origin and origin.split('://', 1)[-1] != ws.headers.get('host') and origin.rstrip('/') not in ORIGENES_PERMITIDOS:
        await ws.close(code=1008)
        return
    await ws.accept()
    canal = None
    try:
        token = await asyncio.wait_for(ws.receive_text(), timeout=10)
        if not token or len(token) > 1024:
            await ws.close(code=1008)
            return
        from autenticacion import autenticar_solicitud, docente_por_ticket
        if token.startswith('ticket:'):
            # Frontend en otro dominio (Vercel): la cookie no llega a Render, así que el
            # panel manda un ticket firmado de 2 minutos obtenido con su sesión.
            docente = await asyncio.to_thread(docente_por_ticket, token[7:], codigo.upper())
            token = 'docente'
        else:
            docente = await asyncio.to_thread(autenticar_solicitud, ws) if token == 'docente' else None
        codigo = codigo.upper()
        canal = canales_en_vivo.setdefault(codigo, CanalPartida(codigo))
        canal.clientes[ws] = {'token':token, 'docente':docente, 'anterior':None}
        if canal.tarea is None or canal.tarea.done():
            canal.tarea = asyncio.create_task(canal.publicar())
        while True:
            mensaje = await ws.receive_text()
            if token != 'docente' and len(mensaje) < 200:
                await canal.reaccion(ws, mensaje)
    except (WebSocketDisconnect, RuntimeError, TimeoutError):
        pass
    finally:
        if canal:
            canal.clientes.pop(ws, None)
            if not canal.clientes:
                if canales_en_vivo.get(codigo) is canal:
                    canales_en_vivo.pop(codigo, None)
                if canal.tarea and not canal.tarea.done():
                    canal.tarea.cancel()
                    with suppress(asyncio.CancelledError):
                        await canal.tarea
