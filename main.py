from pathlib import Path
from uuid import uuid4
import os
import time
import asyncio
import logging
import io
import re
import socket
import qrcode
import qrcode.image.svg
from contextlib import suppress
from contextlib import asynccontextmanager
from threading import Event, Thread, Lock

from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.responses import Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import Column, Integer, String, Text, func, text, event
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import Base, SessionLocal, engine
from partidas import router as partidas_router
from configuracion import AUTO_MIGRATE, PRODUCCION, ALLOWED_HOSTS, CLEANUP_INTERVAL_SECONDS
from middleware import ProteccionHTTP
from autenticacion import router as auth_router
from frontend_web import pagina, DIST
import almacenamiento

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = Path(os.getenv('UPLOADS_DIR', str(BASE_DIR / 'uploads'))).resolve()
IMAGE_DIR = UPLOADS_DIR / "imagenes"
AUDIO_DIR = UPLOADS_DIR / "audios"
CATALOGO_DIR = BASE_DIR / "catalogo"
VIDEOS_YOUTUBE = BASE_DIR / "videos_youtube.json"
TIPOS_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}
TIPOS_AUDIO = {".mp3", ".wav", ".ogg", ".m4a", ".webm", ".mp4"}
MAX_IMAGEN = 5 * 1024 * 1024
MAX_AUDIO = 12 * 1024 * 1024
catalogo_lock = Lock()
for folder in (IMAGE_DIR, AUDIO_DIR):
    folder.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app):
    from serial_bridge import main as iniciar_serial
    detener = Event()
    hilo = None
    if os.getenv("SERIAL_ENABLED", "false").lower() in {"true", "1", "yes"}:
        hilo = Thread(target=iniciar_serial, args=(detener, publicar_uid, actualizar_lector), daemon=True)
        hilo.start()
    from partidas import ejecutar_mantenimiento
    async def mantenimiento_periodico():
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            try:
                await asyncio.to_thread(ejecutar_mantenimiento)
            except Exception:
                logging.getLogger('mazahua.partidas').exception('No se pudo ejecutar el mantenimiento')
    await asyncio.to_thread(ejecutar_mantenimiento)
    tarea = asyncio.create_task(mantenimiento_periodico())
    try:
        yield
    finally:
        tarea.cancel()
        with suppress(asyncio.CancelledError):
            await tarea
        detener.set()
        if hilo:
            hilo.join(timeout=5)


app = FastAPI(
    lifespan=lifespan,
    title="Registro de tarjetas RFID · Lotería Mazahua",
    description="Administración y partidas de la lotería bilingüe.",
    docs_url=None if PRODUCCION else '/docs', redoc_url=None if PRODUCCION else '/redoc',
    openapi_url=None if PRODUCCION else '/openapi.json'
)
app.include_router(partidas_router)
app.include_router(auth_router)
app.add_middleware(ProteccionHTTP)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS if PRODUCCION else ['*'])

class Tarjeta(Base):
    """Tabla única de las tarjetas: nombres, descripción, imagen y audios en un solo registro.
    Las imágenes y audios son archivos (catalogo/ o uploads/); aquí se guarda su ruta."""
    __tablename__ = "tarjetas"
    id = Column(Integer, primary_key=True)
    numero = Column(Integer, unique=True, nullable=True)                       # número de la carta (1, 2, 3…)
    traduccion_espanol = Column('nombre_espanol', String(150), nullable=False)  # cómo se escribe en español
    palabra_mazahua = Column('nombre_mazahua', String(150), nullable=False)     # cómo se escribe en mazahua
    descripcion = Column(Text, nullable=True)
    imagen_url = Column('imagen', String(255), nullable=True)                   # ruta de la imagen
    audio_mazahua_url = Column('audio_mazahua', String(255), nullable=True)     # ruta del audio en mazahua
    audio_espanol_url = Column('audio_espanol', String(255), nullable=True)     # ruta del audio en español
    uid = Column('uid_rfid', String(40), unique=True, nullable=True)            # UID de la tarjeta física RFID (opcional)


def descripcion_por_defecto(palabra_mazahua: str, traduccion_espanol: str) -> str:
    """Texto que se guarda cuando el docente deja la descripción vacía."""
    return (f"«{palabra_mazahua.strip()}» es la palabra en lengua mazahua para «{traduccion_espanol.strip().lower()}». "
            "Escucha su pronunciación en mazahua y en español.")


@event.listens_for(Tarjeta, 'before_insert')
def _descripcion_al_registrar(_mapper, _conexion, tarjeta):
    # Toda tarjeta nueva (formulario, lector RFID o catálogo) recibe descripción por defecto.
    if not (tarjeta.descripcion or '').strip():
        tarjeta.descripcion = descripcion_por_defecto(tarjeta.palabra_mazahua, tarjeta.traduccion_espanol)


RENOMBRES_CATALOGO = {'0029_niño': '0029_nino', '0030_niña': '0030_nina', '0044_bañarse': '0044_banarse', '0047_leña': '0047_lena'}


def inicializar_base():
    """Crea las tablas que falten y, si encuentra la estructura anterior, la migra (con respaldo)."""
    import autenticacion  # noqa: F401  (registra usuarios, sesiones y recuperaciones)
    from migracion import asegurar_columnas, migrar_estructura_anterior, unificar_tarjetas
    migrar_estructura_anterior(engine, Base)
    unificar_tarjetas(engine)
    Base.metadata.create_all(bind=engine)
    asegurar_columnas(engine)
    with engine.begin() as conexion:
        # Las carpetas del catálogo con «ñ» se renombraron sin acentos: algunos programas para
        # descomprimir en Windows alteraban esos nombres y las imágenes y audios no aparecían.
        for anterior, nuevo in RENOMBRES_CATALOGO.items():
            for columna in ('imagen', 'audio_mazahua', 'audio_espanol'):
                conexion.execute(text(f"UPDATE tarjetas SET {columna} = REPLACE({columna}, :a, :n) WHERE {columna} LIKE :p"),
                                 {'a': f'/catalogo/{anterior}/', 'n': f'/catalogo/{nuevo}/', 'p': f'/catalogo/{anterior}/%'})
    with engine.begin() as conexion:
        # Descripción por defecto para las tarjetas que no tengan una (no cambia las ya escritas).
        vacias = conexion.execute(text("SELECT id, nombre_mazahua, nombre_espanol FROM tarjetas "
                                       "WHERE descripcion IS NULL OR TRIM(descripcion) = ''")).all()
        for id_, mazahua, espanol in vacias:
            conexion.execute(text('UPDATE tarjetas SET descripcion = :d WHERE id = :i'),
                             {'d': descripcion_por_defecto(mazahua, espanol), 'i': id_})


if AUTO_MIGRATE:
    inicializar_base()

ultimo_uid = ""
ultimo_uid_seq = 0
ultimo_uid_fecha = None
lector_heartbeat = 0.0
lector_puerto = ""
lector_error = "Conecta el lector USB desde el navegador o inicia el puente serial local."
uid_lock = Lock()
LECTOR_TIMEOUT_SEGUNDOS = 15


def lector_activo() -> bool:
    return lector_heartbeat > 0 and (time.monotonic() - lector_heartbeat) <= LECTOR_TIMEOUT_SEGUNDOS


def actualizar_lector(conectado, puerto, mensaje):
    global lector_heartbeat, lector_puerto, lector_error
    lector_heartbeat = time.monotonic() if conectado else 0.0
    lector_puerto = puerto
    lector_error = "" if conectado else mensaje


def publicar_uid(uid):
    global ultimo_uid, ultimo_uid_seq, ultimo_uid_fecha
    with uid_lock:
        ultimo_uid = normalizar_uid(uid)
        ultimo_uid_seq += 1
        ultimo_uid_fecha = time.strftime("%Y-%m-%d %H:%M:%S")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if almacenamiento.remoto():
    @app.get('/uploads/{ruta:path}', include_in_schema=False)
    def archivo_subido_remoto(ruta: str):
        return RedirectResponse(almacenamiento.url_publica('uploads/' + ruta), status_code=307)

    @app.get('/catalogo/{ruta:path}', include_in_schema=False)
    def archivo_catalogo_remoto(ruta: str):
        return RedirectResponse(almacenamiento.url_publica('catalogo/' + ruta), status_code=307)
else:
    app.mount('/uploads', StaticFiles(directory=str(UPLOADS_DIR)), name='uploads')
    app.mount('/catalogo', StaticFiles(directory=str(CATALOGO_DIR)), name='catalogo')
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
# Astro genera los recursos compilados dentro de _astro; las páginas privadas
# siempre pasan por su ruta y por el control de autenticación, nunca por un mount.
if (DIST / '_astro').is_dir():
    app.mount('/_astro', StaticFiles(directory=str(DIST / '_astro')), name='astro')

def url_invitacion(codigo: str, request: Request):
    codigo = codigo.upper()
    if not re.fullmatch(r'[A-Z0-9]{6}', codigo):
        raise HTTPException(422, 'Código de partida inválido.')
    base = (os.getenv('FRONTEND_URL') or str(request.base_url)).rstrip('/')
    local = request.url.hostname in {'localhost', '127.0.0.1', '::1'} and not os.getenv('FRONTEND_URL')
    disponible = True
    if local:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
                conexion.connect(('8.8.8.8', 80))
                direccion = conexion.getsockname()[0]
            if not direccion or direccion.startswith('127.'):
                raise OSError('No se encontró una dirección de red local')
            puerto = request.url.port
            base = f'{request.url.scheme}://{direccion}' + (f':{puerto}' if puerto else '')
        except OSError:
            disponible = False
    return base + '/estudiante?codigo=' + codigo, local, disponible


@app.get('/api/tiempo-real/{codigo}', include_in_schema=False)
def tiempo_real(codigo: str, request: Request):
    """Dirección del WebSocket. Con frontend en Vercel apunta directo a Render (WS_PUBLIC_URL o
    RENDER_EXTERNAL_HOSTNAME); al docente con sesión además le da un ticket breve."""
    from autenticacion import autenticar_solicitud, crear_ticket_ws
    codigo = codigo.upper()
    if not re.fullmatch(r'[A-Z0-9]{6}', codigo):
        raise HTTPException(422, 'Código de partida inválido.')
    base = os.getenv('WS_PUBLIC_URL', '').rstrip('/')
    if not base and os.getenv('FRONTEND_URL') and os.getenv('RENDER_EXTERNAL_HOSTNAME'):
        base = 'wss://' + os.environ['RENDER_EXTERNAL_HOSTNAME']
    docente = autenticar_solicitud(request)
    return JSONResponse({'ws': base, 'ticket': crear_ticket_ws(docente, codigo) if docente else ''},
                        headers={'Cache-Control': 'no-store'})


@app.get('/api/invitacion/{codigo}')
def invitacion(codigo: str, request: Request):
    url, local, disponible = url_invitacion(codigo, request)
    return {'url': url, 'red_local': local, 'disponible': disponible}


@app.get('/api/invitacion/{codigo}/qr')
def invitacion_qr(codigo: str, request: Request):
    url, _, _ = url_invitacion(codigo, request)
    imagen = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, border=4)
    salida = io.BytesIO()
    imagen.save(salida)
    return Response(content=salida.getvalue(), media_type='image/svg+xml', headers={'Cache-Control': 'no-store'})


def entradas_catalogo():
    if almacenamiento.remoto():
        import json
        return json.loads((BASE_DIR / 'catalogo_manifest.json').read_text(encoding='utf-8'))
    entradas = []
    for carpeta in sorted(CATALOGO_DIR.iterdir(), key=lambda p: int(p.name.split("_", 1)[0]) if p.name.split("_", 1)[0].isdigit() else 99999):
        datos = carpeta / "datos.txt"
        if not carpeta.is_dir() or not datos.is_file():
            continue
        valores = dict(linea.split("=", 1) for linea in datos.read_text(encoding="utf-8-sig").splitlines() if "=" in linea)
        valores = {k.strip(): v.strip() for k, v in valores.items()}
        imagen = next((p for p in sorted(carpeta.glob("imagen.*")) if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".svg"}), None)
        audio = carpeta / "audio_mazahua.m4a"
        audio_es = next((p for p in sorted(carpeta.glob("audio_espanol.*")) if p.suffix.lower() in TIPOS_AUDIO), None)
        espanol = valores.get("traduccion_espanol", valores.get("traduccion_español", ""))
        if not valores.get("nombre_mazahua") or not espanol or not audio.is_file():
            raise HTTPException(422, f"El catálogo está incompleto en {carpeta.name}")
        numero = carpeta.name.split("_", 1)[0]
        entradas.append({"carpeta": carpeta.name, "numero": int(numero) if numero.isdigit() else None,
                         "palabra_mazahua": valores["nombre_mazahua"],
                         "traduccion_espanol": espanol,
                         "imagen_url": f"/catalogo/{carpeta.name}/{imagen.name}" if imagen else f"/api/catalogo/imagen/{carpeta.name}",
                         "audio_mazahua_url": f"/catalogo/{carpeta.name}/{audio.name}",
                         "audio_espanol_url": f"/catalogo/{carpeta.name}/{audio_es.name}" if audio_es else None})
    return entradas


# Correcciones del material entregado (carpeta, nombre anterior → nombre correcto).
CORRECCIONES_MATERIAL = {('0006_tortilla', 'Segi'): "T'zeyi"}


def archivo_existe(ruta: str | None) -> bool:
    if not ruta or almacenamiento.remoto():
        return True  # en la nube no se puede comprobar aquí; se conserva
    if ruta.startswith('/catalogo/'):
        return (CATALOGO_DIR / ruta.removeprefix('/catalogo/')).is_file()
    if ruta.startswith('/uploads/'):
        return (UPLOADS_DIR / ruta.removeprefix('/uploads/')).is_file()
    return True


def sincronizar_material_catalogo(db) -> dict:
    """Aplica el material de catalogo/ a las tarjetas que ya existen (por su número de carta):
    - agrega el audio en español grabado cuando la tarjeta no tiene, tiene uno generado
      automáticamente (es_*.wav) o su archivo ya no existe; los audios subidos por el docente se respetan;
    - actualiza la imagen si apuntaba a un archivo del catálogo que ya no existe;
    - aplica las correcciones de nombres del material."""
    cambios = {'audios_espanol': 0, 'imagenes': 0, 'nombres': 0}
    try:
        entradas = {e['numero']: e for e in entradas_catalogo() if e.get('numero')}
    except Exception:
        return cambios
    for tarjeta in db.query(Tarjeta).filter(Tarjeta.numero.in_(list(entradas))):
        e = entradas[tarjeta.numero]
        actual = tarjeta.audio_espanol_url
        generado = bool(actual) and actual.startswith('/uploads/audios/es_')
        if e.get('audio_espanol_url') and actual != e['audio_espanol_url'] and (not actual or generado or not archivo_existe(actual)):
            tarjeta.audio_espanol_url = e['audio_espanol_url']
            cambios['audios_espanol'] += 1
        prefijo = f"/catalogo/{e['carpeta'][:4]}_"  # misma carta (mismo número de carpeta)
        imagen = tarjeta.imagen_url
        if imagen and imagen.startswith(prefijo) and not archivo_existe(imagen) and imagen != e['imagen_url']:
            tarjeta.imagen_url = e['imagen_url']
            cambios['imagenes'] += 1
        audio = tarjeta.audio_mazahua_url
        if e.get('audio_mazahua_url') and audio and audio.startswith(prefijo) and not archivo_existe(audio) and audio != e['audio_mazahua_url']:
            tarjeta.audio_mazahua_url = e['audio_mazahua_url']
        nuevo = CORRECCIONES_MATERIAL.get((e['carpeta'], tarjeta.palabra_mazahua))
        if nuevo:
            if tarjeta.descripcion == descripcion_por_defecto(tarjeta.palabra_mazahua, tarjeta.traduccion_espanol):
                tarjeta.descripcion = descripcion_por_defecto(nuevo, tarjeta.traduccion_espanol)
            tarjeta.palabra_mazahua = nuevo
            cambios['nombres'] += 1
    db.commit()
    if any(cambios.values()):
        print(f"Material del catálogo aplicado: {cambios['audios_espanol']} audios en español, "
              f"{cambios['imagenes']} imágenes y {cambios['nombres']} nombres corregidos.", flush=True)
    return cambios


def estado_catalogo(db):
    """Las cartas del catálogo ya registradas se reconocen por su número (tarjetas.numero)."""
    entradas = entradas_catalogo()
    usados = {n for (n,) in db.query(Tarjeta.numero).filter(Tarjeta.numero.isnot(None))}
    registradas = [e for e in entradas if e.get("numero") in usados]
    return {"total": len(entradas), "asignadas": len(registradas),
            "siguiente": next((e for e in entradas if e.get("numero") not in usados), None)}


@app.get("/api/catalogo/estado")
def consultar_catalogo(db: Session = Depends(get_db)):
    return estado_catalogo(db)


@app.get("/api/catalogo/imagen/{carpeta}")
def imagen_catalogo(carpeta: str):
    colores = {"0048_azul": "#2875dd", "0049_verde": "#269966", "0050_amarillo": "#f4cf38",
               "0051_rojo": "#dc4545", "0052_naranja": "#f49332", "0053_morado": "#8e54bc"}
    if carpeta not in colores:
        raise HTTPException(404, "No se encontró la imagen del catálogo")
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600"><rect width="600" height="600" rx="36" fill="{colores[carpeta]}"/><text x="300" y="330" text-anchor="middle" font-family="sans-serif" font-size="60" fill="#111">{carpeta.split("_", 1)[1].capitalize()}</text></svg>'
    return Response(svg, media_type="image/svg+xml")


@app.post("/api/catalogo/registrar")
def registrar_desde_catalogo(payload: dict, db: Session = Depends(get_db)):
    uid = normalizar_uid(str(payload.get("uid", "")))
    if not uid or len(uid) > 40:
        raise HTTPException(400, "Introduce un UID válido de hasta 40 caracteres")
    with catalogo_lock:
        existente = db.query(Tarjeta).filter(Tarjeta.uid == uid).first()
        if existente:
            return {"ok": True, "nueva": False, "tarjeta": tarjeta_json(existente), "catalogo": estado_catalogo(db)}
        estado = estado_catalogo(db)
        entrada = estado["siguiente"]
        if not entrada:
            raise HTTPException(409, "Ya se asignaron todas las palabras del catálogo")
        tarjeta = Tarjeta(uid=uid, **{k: v for k, v in entrada.items() if k != "carpeta"})
        try:
            db.add(tarjeta)
            db.commit()
            db.refresh(tarjeta)
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Otra lectura acaba de asignar esta tarjeta o palabra. Vuelve a pasar la tarjeta.")
        return {"ok": True, "nueva": True, "tarjeta": tarjeta_json(tarjeta), "catalogo": estado_catalogo(db)}


@app.post("/api/tarjetas/{tarjeta_id}/audio-espanol", tags=['Tarjetas (administración)'])
def guardar_audio_espanol(tarjeta_id: int, audio_espanol: UploadFile = File(...), db: Session = Depends(get_db)):
    tarjeta = db.query(Tarjeta).filter(Tarjeta.id == tarjeta_id).first()
    if not tarjeta:
        raise HTTPException(404, "No se encontró la tarjeta")
    nueva_url = guardar_archivo(audio_espanol, AUDIO_DIR, TIPOS_AUDIO, MAX_AUDIO, True)
    antigua_url = tarjeta.audio_espanol_url
    try:
        tarjeta.audio_espanol_url = nueva_url
        db.commit()
        db.refresh(tarjeta)
    except Exception:
        db.rollback()
        borrar_archivo(nueva_url)
        raise HTTPException(500, "No se pudo guardar el audio en español")
    borrar_archivo(antigua_url)
    return {"ok": True, "tarjeta": tarjeta_json(tarjeta), "mensaje": "Audio en español guardado"}

@app.get("/")
def inicio():
    return pagina()


@app.get("/administracion")
def administracion():
    return pagina('administracion')


@app.get('/panel', include_in_schema=False)
def panel_docente():
    return pagina('panel')


@app.get('/acceso', include_in_schema=False)
def acceso():
    return pagina('acceso')


@app.get('/cuenta', include_in_schema=False)
def cuenta():
    return pagina('cuenta')


@app.get('/vocabulario', include_in_schema=False)
def vocabulario():
    return pagina('vocabulario')


@app.get('/editar', include_in_schema=False)
def editar_vocabulario():
    return pagina('editar')


@app.get('/simulador', include_in_schema=False)
def simulador():
    return pagina('simulador')


@app.get('/videos', include_in_schema=False)
def videos():
    return pagina('videos')


_MINIATURAS_REMOTAS = None


def carpetas_con_miniatura_remota() -> set:
    """En la nube los binarios están en Supabase: el manifiesto dice qué cartas tienen miniatura."""
    global _MINIATURAS_REMOTAS
    if _MINIATURAS_REMOTAS is None:
        import json
        try:
            datos = json.loads((BASE_DIR / 'catalogo_manifest.json').read_text(encoding='utf-8'))
            _MINIATURAS_REMOTAS = {e['carpeta'] for e in datos if e.get('miniatura')}
        except (OSError, ValueError, KeyError):
            _MINIATURAS_REMOTAS = set()
    return _MINIATURAS_REMOTAS


def miniatura_url(imagen_url: str | None) -> str | None:
    """Miniatura ligera (360 px, WEBP) de las imágenes del catálogo; las listas cargan mucho más rápido."""
    if imagen_url and imagen_url.startswith('/catalogo/'):
        partes = imagen_url.split('/')
        if len(partes) == 4 and (partes[2] in carpetas_con_miniatura_remota() if almacenamiento.remoto()
                                 else (CATALOGO_DIR / partes[2] / 'miniatura.webp').is_file()):
            return f'/catalogo/{partes[2]}/miniatura.webp'
    return imagen_url


def tarjeta_json(t: Tarjeta):
    return {
        "id": t.id,
        "numero": t.numero,
        "uid": t.uid,
        "palabra_mazahua": t.palabra_mazahua,
        "traduccion_espanol": t.traduccion_espanol,
        "descripcion": t.descripcion,
        "imagen_url": t.imagen_url,
        "miniatura_url": miniatura_url(t.imagen_url),
        "audio_mazahua_url": t.audio_mazahua_url,
        "audio_espanol_url": t.audio_espanol_url,
    }

@app.get("/api/estado")
def estado():
    return {"ok": True, "servicio": "Registro RFID Mazahua"}


@app.get('/api/ready')
def disponible(db: Session = Depends(get_db)):
    try:
        db.execute(text('SELECT 1'))
        db.query(Tarjeta.id).limit(1).all()
        return {'ok': True}
    except Exception:
        raise HTTPException(503, 'Base de datos no disponible')


@app.get('/api/admin/partidas')
def administrar_partidas(request: Request, db: Session = Depends(get_db)):
    from partidas import Partida, Participante, mantenimiento_partidas
    from configuracion import ROOM_IDLE_MINUTES, ROOM_MAX_HOURS, ROOM_RETENTION_DAYS
    mantenimiento_partidas(db)
    from sqlalchemy import or_
    docente = request.state.docente
    filas = (db.query(Partida, func.count(Participante.id)).outerjoin(Participante, Participante.partida_id == Partida.id)
             .filter(or_(Partida.usuario_id == docente['id'], Partida.usuario_id.is_(None)))
             .group_by(Partida.id).order_by(Partida.id.desc()).limit(100).all())
    return {'politica': {'inactividad_minutos': ROOM_IDLE_MINUTES, 'duracion_maxima_horas': ROOM_MAX_HOURS,
                         'retencion_dias': ROOM_RETENTION_DAYS},
            'partidas': [{'codigo': p.codigo, 'nombre': p.nombre, 'estado': p.estado, 'creada': p.creada, 'iniciada': p.iniciada,
                         'finalizada': p.finalizada, 'ultima_actividad_docente': p.ultima_actividad_docente,
                         'cierre_motivo': p.cierre_motivo, 'participantes': n} for p, n in filas]}


@app.post('/api/admin/partidas/{codigo}/finalizar')
def finalizar_desde_administracion(codigo: str, request: Request, db: Session = Depends(get_db)):
    from datetime import datetime
    from partidas import buscar, exigir_docente
    p = buscar(db, codigo, True)
    exigir_docente(p, request)
    if p.estado != 'finalizada':
        p.estado, p.finalizada, p.cierre_motivo = 'finalizada', datetime.utcnow(), 'docente'
        db.commit()
    return {'ok': True, 'codigo': p.codigo, 'estado': p.estado}


@app.post('/api/admin/mantenimiento')
def mantener_desde_administracion(db: Session = Depends(get_db)):
    from partidas import mantenimiento_partidas
    return {'ok': True, **mantenimiento_partidas(db)}

def filtrar_tarjetas(consulta, buscar: str | None, incluir_uid: bool = False):
    """Búsqueda sin distinguir mayúsculas en mazahua, español y descripción (y número/UID para el docente)."""
    if buscar and buscar.strip():
        texto = buscar.strip().lower()
        patron = f"%{texto}%"
        columnas = [Tarjeta.palabra_mazahua, Tarjeta.traduccion_espanol, Tarjeta.descripcion]
        if incluir_uid:
            columnas.append(Tarjeta.uid)
        from sqlalchemy import or_
        condiciones = [func.lower(c).like(patron) for c in columnas]
        if texto.isdigit():
            condiciones.append(Tarjeta.numero == int(texto))
        consulta = consulta.filter(or_(*condiciones))
    return consulta


def orden_tarjetas():
    # Primero por número de carta; las que no tienen número, al final.
    return (Tarjeta.numero.is_(None), Tarjeta.numero, Tarjeta.id)


@app.get("/api/tarjetas", tags=['Tarjetas (administración)'])
def listar_tarjetas(buscar: str | None = None, db: Session = Depends(get_db)):
    """Lista completa para el docente (incluye número y UID). Opcional: ?buscar=texto"""
    consulta = filtrar_tarjetas(db.query(Tarjeta), buscar, incluir_uid=True)
    return [tarjeta_json(t) for t in consulta.order_by(*orden_tarjetas()).all()]


CAMPOS_PUBLICOS = ('id', 'numero', 'palabra_mazahua', 'traduccion_espanol', 'descripcion',
                   'imagen_url', 'miniatura_url', 'audio_mazahua_url', 'audio_espanol_url')


@app.get('/api/vocabulario', tags=['Vocabulario público'])
def vocabulario_publico(buscar: str | None = None, db: Session = Depends(get_db)):
    """Catálogo de aprendizaje de solo lectura; no expone UID ni funciones administrativas.
    Admite búsqueda: /api/vocabulario?buscar=gato"""
    consulta = filtrar_tarjetas(db.query(Tarjeta), buscar)
    return [{campo: tarjeta_json(t)[campo] for campo in CAMPOS_PUBLICOS}
            for t in consulta.order_by(*orden_tarjetas()).all()]


@app.get('/api/vocabulario/{tarjeta_id}', tags=['Vocabulario público'])
def vocabulario_detalle(tarjeta_id: int, db: Session = Depends(get_db)):
    """Consulta pública de un solo elemento, sin UID."""
    tarjeta = db.query(Tarjeta).filter(Tarjeta.id == tarjeta_id).first()
    if not tarjeta:
        raise HTTPException(404, "No se encontró el elemento del vocabulario")
    return {campo: tarjeta_json(tarjeta)[campo] for campo in CAMPOS_PUBLICOS}


# ---------------------------------------------------------------------------
# Videos de YouTube (evidencias del proyecto)
# Los enlaces se guardan en videos_youtube.json (raíz del proyecto). Se pueden
# editar a mano en ese archivo o desde Administración → "Videos de YouTube".
# ---------------------------------------------------------------------------
import json as _json
videos_lock = Lock()
PATRON_YOUTUBE = re.compile(r'(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/|v/)|youtu\.be/)([A-Za-z0-9_-]{11})')


def id_youtube(url: str) -> str | None:
    url = (url or '').strip()
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', url):
        return url
    coincidencia = PATRON_YOUTUBE.search(url)
    return coincidencia.group(1) if coincidencia else None


def leer_videos() -> list[dict]:
    if not VIDEOS_YOUTUBE.is_file():
        return []
    try:
        datos = _json.loads(VIDEOS_YOUTUBE.read_text(encoding='utf-8-sig'))
    except (ValueError, OSError):
        raise HTTPException(500, 'El archivo videos_youtube.json tiene un error de formato. Revisa comas y comillas.')
    return datos.get('videos', []) if isinstance(datos, dict) else datos


def video_publico(v: dict, indice: int) -> dict:
    url = str(v.get('url', '') or '').strip()
    vid = id_youtube(url)
    return {'orden': indice + 1, 'titulo': str(v.get('titulo', '') or f'Video {indice + 1}'),
            'descripcion': str(v.get('descripcion', '') or ''), 'url': url,
            'youtube_id': vid,
            'enlace': f'https://www.youtube.com/watch?v={vid}' if vid else None,
            'miniatura': f'https://img.youtube.com/vi/{vid}/hqdefault.jpg' if vid else None,
            'pendiente': vid is None}


@app.get('/api/videos', tags=['Videos de YouTube'])
def listar_videos():
    """Videos de evidencia con miniatura y enlace a YouTube (los vacíos aparecen como pendientes)."""
    return [video_publico(v, i) for i, v in enumerate(leer_videos()) if isinstance(v, dict)]


@app.put('/api/videos', tags=['Videos de YouTube'])
def guardar_videos(payload: dict):
    """Solo administrador. Cuerpo: {"videos": [{"titulo": "...", "descripcion": "...", "url": "https://youtu.be/..."}]}"""
    videos = payload.get('videos')
    if not isinstance(videos, list) or len(videos) > 30:
        raise HTTPException(422, 'Envía una lista "videos" con máximo 30 elementos.')
    limpios = []
    for i, v in enumerate(videos):
        if not isinstance(v, dict):
            raise HTTPException(422, f'El video {i + 1} no tiene un formato válido.')
        titulo = str(v.get('titulo', '')).strip()[:150]
        descripcion = str(v.get('descripcion', '')).strip()[:500]
        url = str(v.get('url', '')).strip()[:300]
        if url and not id_youtube(url):
            raise HTTPException(422, f'El enlace del video {i + 1} no parece un enlace válido de YouTube.')
        if not titulo:
            raise HTTPException(422, f'Escribe un título para el video {i + 1}.')
        limpios.append({'titulo': titulo, 'descripcion': descripcion, 'url': url})
    with videos_lock:
        temporal = VIDEOS_YOUTUBE.with_suffix('.json.tmp')
        temporal.write_text(_json.dumps({'videos': limpios}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temporal.replace(VIDEOS_YOUTUBE)
    return {'ok': True, 'mensaje': 'Videos guardados correctamente', 'videos': listar_videos()}

@app.get("/api/tarjetas/{tarjeta_id}", tags=['Tarjetas (administración)'])
def obtener_tarjeta(tarjeta_id: int, db: Session = Depends(get_db)):
    tarjeta = db.query(Tarjeta).filter(Tarjeta.id == tarjeta_id).first()
    if not tarjeta:
        raise HTTPException(status_code=404, detail="No se encontró la tarjeta")
    return tarjeta_json(tarjeta)

@app.get("/api/uid/{uid}", tags=['Tarjetas (administración)'])
def buscar_por_uid(uid: str, db: Session = Depends(get_db)):
    tarjeta = db.query(Tarjeta).filter(Tarjeta.uid == normalizar_uid(uid)).first()
    if not tarjeta:
        raise HTTPException(status_code=404, detail="No existe una tarjeta registrada con ese UID")
    return tarjeta_json(tarjeta)

@app.post("/api/esp32/uid")
def recibir_uid(payload: dict, db: Session = Depends(get_db)):
    """Recibe el UID enviado por serial_bridge.py, por ejemplo: {\"uid\":\"C9 72 1A 10\"}."""
    uid = normalizar_uid(str(payload.get("uid", "")))
    if not uid:
        raise HTTPException(status_code=400, detail="Falta el UID")
    publicar_uid(uid)
    existente = db.query(Tarjeta).filter(Tarjeta.uid == uid).first()
    return {"ok": True, "uid": uid, "seq": ultimo_uid_seq,
            "registrada": existente is not None,
            "tarjeta_id": existente.id if existente else None}

@app.post("/api/esp32/heartbeat")
def latido_lector(payload: dict):
    """serial_bridge.py avisa cada pocos segundos que el puerto COM sigue abierto."""
    actualizar_lector(True, str(payload.get("puerto", "")).strip(), "")
    return {"ok": True, "puerto": lector_puerto}

@app.get("/api/ultimo-uid")
def obtener_ultimo_uid():
    return {
        "uid": ultimo_uid,
        "seq": ultimo_uid_seq,
        "fecha": ultimo_uid_fecha,
        "lector_conectado": lector_activo(),
        "puerto": lector_puerto,
        "error": lector_error,
    }


def normalizar_uid(uid: str) -> str:
    return " ".join(uid.strip().upper().split())


def guardar_archivo(archivo: UploadFile | None, destino: Path, tipos: set[str], max_bytes: int, obligatorio: bool = False):
    if archivo is None or not archivo.filename:
        if obligatorio:
            raise HTTPException(status_code=400, detail="Debes adjuntar todos los archivos solicitados")
        return None
    extension = Path(archivo.filename).suffix.lower()
    if extension not in tipos:
        raise HTTPException(status_code=400, detail=f"Formato no permitido: {extension or 'sin extensión'}")
    contenido = archivo.file.read(max_bytes + 1)
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    if len(contenido) > max_bytes:
        raise HTTPException(status_code=413, detail=f"El archivo {archivo.filename} supera el tamaño máximo permitido")
    nombre = f"{uuid4().hex}{extension}"
    if almacenamiento.remoto():
        return almacenamiento.guardar(f'uploads/{destino.name}/{nombre}', contenido)
    ruta = destino / nombre
    ruta.write_bytes(contenido)
    return f"/uploads/{destino.name}/{nombre}"


def borrar_archivo(url: str | None):
    if not url or not url.startswith("/uploads/"):
        return
    relativo = url.removeprefix("/uploads/")
    if almacenamiento.remoto():
        almacenamiento.borrar('uploads/' + relativo)
        return
    ruta = (UPLOADS_DIR / relativo).resolve()
    if ruta.is_relative_to(UPLOADS_DIR.resolve()) and ruta.exists() and ruta.is_file():
        try:
            ruta.unlink()
        except OSError:
            pass

def uid_opcional(uid: str | None) -> str | None:
    uid = normalizar_uid(uid or '')
    if len(uid) > 40:
        raise HTTPException(422, "El UID puede tener máximo 40 caracteres.")
    return uid or None


def numero_opcional(numero: str | None) -> int | None:
    numero = (numero or '').strip()
    if not numero:
        return None
    if not numero.isdigit() or not 1 <= int(numero) <= 9999:
        raise HTTPException(422, "El número de tarjeta debe ser un número entero (1, 2, 3…).")
    return int(numero)


def validar_unicos(db, uid, numero, excluir_id=None):
    for campo, valor, texto in ((Tarjeta.uid, uid, 'Ese UID ya pertenece a otra tarjeta.'),
                                (Tarjeta.numero, numero, 'Ese número de tarjeta ya está en uso.')):
        if valor is not None:
            consulta = db.query(Tarjeta.id).filter(campo == valor)
            if excluir_id:
                consulta = consulta.filter(Tarjeta.id != excluir_id)
            if consulta.first():
                raise HTTPException(409, texto)


@app.post("/api/tarjetas", tags=['Tarjetas (administración)'])
def registrar_tarjeta(
    palabra_mazahua: str = Form(...),
    traduccion_espanol: str = Form(...),
    descripcion: str = Form("", max_length=4000),
    numero: str | None = Form(None, description="Número de la carta (opcional)"),
    uid: str | None = Form(None, description="UID de la tarjeta RFID (opcional)"),
    imagen: UploadFile | None = File(None),
    audio_mazahua: UploadFile | None = File(None),
    audio_espanol: UploadFile | None = File(None, description="Opcional: también puede generarse o grabarse después"),
    db: Session = Depends(get_db),
):
    """Agregar una tarjeta: nombre en mazahua y español, descripción, imagen y audios."""
    uid, numero = uid_opcional(uid), numero_opcional(numero)
    palabra_mazahua = palabra_mazahua.strip()
    traduccion_espanol = traduccion_espanol.strip()
    if not palabra_mazahua or not traduccion_espanol:
        raise HTTPException(status_code=400, detail="El nombre en mazahua y el nombre en español son obligatorios.")
    validar_unicos(db, uid, numero)
    if not (imagen and imagen.filename) or not (audio_mazahua and audio_mazahua.filename):
        raise HTTPException(status_code=400, detail="Adjunta la imagen y el audio en mazahua.")

    guardados = []
    try:
        imagen_url = guardar_archivo(imagen, IMAGE_DIR, TIPOS_IMAGEN, MAX_IMAGEN, True)
        guardados.append(imagen_url)
        audio_mazahua_url = guardar_archivo(audio_mazahua, AUDIO_DIR, TIPOS_AUDIO, MAX_AUDIO, True)
        guardados.append(audio_mazahua_url)
        audio_espanol_url = guardar_archivo(audio_espanol, AUDIO_DIR, TIPOS_AUDIO, MAX_AUDIO)
        guardados.append(audio_espanol_url)
    except Exception:
        for url in guardados:
            borrar_archivo(url)
        raise

    tarjeta = Tarjeta(uid=uid, numero=numero, palabra_mazahua=palabra_mazahua, traduccion_espanol=traduccion_espanol,
                      descripcion=descripcion.strip() or descripcion_por_defecto(palabra_mazahua, traduccion_espanol),
                      imagen_url=imagen_url, audio_mazahua_url=audio_mazahua_url, audio_espanol_url=audio_espanol_url)
    db.add(tarjeta)
    try:
        db.commit()
        db.refresh(tarjeta)
    except IntegrityError:
        db.rollback()
        for url in guardados: borrar_archivo(url)
        raise HTTPException(status_code=409, detail="Ya existe una tarjeta con ese UID o número.")
    except Exception:
        db.rollback()
        for url in guardados: borrar_archivo(url)
        raise HTTPException(status_code=500, detail="No se pudo guardar el registro en la base de datos")
    return {"ok": True, "mensaje": f"Tarjeta «{palabra_mazahua}» agregada con su imagen y audios.", "tarjeta": tarjeta_json(tarjeta)}


@app.put("/api/tarjetas/{tarjeta_id}", tags=['Tarjetas (administración)'])
def editar_tarjeta(
    tarjeta_id: int,
    palabra_mazahua: str = Form(...),
    traduccion_espanol: str = Form(...),
    descripcion: str = Form("", max_length=4000),
    numero: str | None = Form(None),
    uid: str | None = Form(None),
    imagen: UploadFile | None = File(None),
    audio_mazahua: UploadFile | None = File(None),
    audio_espanol: UploadFile | None = File(None),
    eliminar_audio_mazahua: bool = Form(False),
    eliminar_audio_espanol: bool = Form(False),
    db: Session = Depends(get_db),
):
    """Editar una tarjeta. Los archivos que no se envían se conservan; los audios se pueden eliminar."""
    tarjeta = db.query(Tarjeta).filter(Tarjeta.id == tarjeta_id).first()
    if not tarjeta:
        raise HTTPException(status_code=404, detail="No se encontró la tarjeta que deseas editar")
    if not palabra_mazahua.strip() or not traduccion_espanol.strip():
        raise HTTPException(status_code=400, detail="El nombre en mazahua y el nombre en español son obligatorios.")
    uid = uid_opcional(uid) if uid is not None else tarjeta.uid
    numero = numero_opcional(numero) if numero is not None else tarjeta.numero
    validar_unicos(db, uid, numero, excluir_id=tarjeta_id)

    nuevos = []
    try:
        if imagen and imagen.filename:
            nuevos.append(("imagen_url", guardar_archivo(imagen, IMAGE_DIR, TIPOS_IMAGEN, MAX_IMAGEN)))
        if audio_mazahua and audio_mazahua.filename:
            nuevos.append(("audio_mazahua_url", guardar_archivo(audio_mazahua, AUDIO_DIR, TIPOS_AUDIO, MAX_AUDIO)))
        if audio_espanol and audio_espanol.filename:
            nuevos.append(("audio_espanol_url", guardar_archivo(audio_espanol, AUDIO_DIR, TIPOS_AUDIO, MAX_AUDIO)))
        urls_antiguas = []
        for campo, url in nuevos:
            urls_antiguas.append(getattr(tarjeta, campo))
            setattr(tarjeta, campo, url)
        reemplazados = {campo for campo, _ in nuevos}
        for campo, eliminar in (("audio_mazahua_url", eliminar_audio_mazahua), ("audio_espanol_url", eliminar_audio_espanol)):
            if eliminar and campo not in reemplazados and getattr(tarjeta, campo):
                urls_antiguas.append(getattr(tarjeta, campo))
                setattr(tarjeta, campo, None)
        tarjeta.uid, tarjeta.numero = uid, numero
        tarjeta.palabra_mazahua = palabra_mazahua.strip()
        tarjeta.traduccion_espanol = traduccion_espanol.strip()
        tarjeta.descripcion = descripcion.strip() or descripcion_por_defecto(tarjeta.palabra_mazahua, tarjeta.traduccion_espanol)
        db.commit()
        db.refresh(tarjeta)
        for url in urls_antiguas: borrar_archivo(url)
    except IntegrityError:
        db.rollback()
        for _, url in nuevos: borrar_archivo(url)
        raise HTTPException(status_code=409, detail="Ya existe una tarjeta con ese UID o número.")
    except HTTPException:
        db.rollback()
        for _, url in nuevos: borrar_archivo(url)
        raise
    except Exception:
        db.rollback()
        for _, url in nuevos: borrar_archivo(url)
        raise HTTPException(status_code=500, detail="No se pudieron actualizar los datos de la tarjeta")
    cambios = [texto for campo, texto in (("imagen_url", "la nueva imagen"), ("audio_mazahua_url", "el audio en mazahua"),
                                          ("audio_espanol_url", "el audio en español")) if any(c == campo for c, _ in nuevos)]
    extra = f" Se guardó {' y '.join(cambios)}." if cambios else ""
    return {"ok": True, "mensaje": f"Tarjeta «{tarjeta.palabra_mazahua}» actualizada.{extra}", "tarjeta": tarjeta_json(tarjeta)}


@app.delete("/api/tarjetas/{tarjeta_id}", tags=['Tarjetas (administración)'])
def eliminar_tarjeta(tarjeta_id: int, db: Session = Depends(get_db)):
    from partidas import Anuncio, Partida, Participante, Tablero, TableroTarjeta, mantenimiento_partidas

    mantenimiento_partidas(db)

    tarjeta = db.query(Tarjeta).filter(Tarjeta.id == tarjeta_id).first()
    if not tarjeta:
        raise HTTPException(status_code=404, detail="No se encontró la tarjeta")
    urls = [tarjeta.imagen_url, tarjeta.audio_mazahua_url, tarjeta.audio_espanol_url]
    try:
        # No romper un tablero o los anuncios de una partida que sigue en curso.
        activas = {c for (c,) in db.query(Partida.codigo).join(Anuncio, Anuncio.partida_id == Partida.id)
                   .filter(Partida.estado == "en_curso", Anuncio.tarjeta_id == tarjeta_id)}
        activas.update(c for (c,) in db.query(Partida.codigo)
                       .join(Participante, Participante.partida_id == Partida.id)
                       .join(Tablero, Tablero.participante_id == Participante.id)
                       .join(TableroTarjeta, TableroTarjeta.tablero_id == Tablero.id)
                       .filter(Partida.estado == "en_curso", TableroTarjeta.tarjeta_id == tarjeta_id))
        if activas:
            raise HTTPException(409, "No se puede eliminar esta tarjeta porque se utiliza en las partidas en curso: "
                                + ", ".join(sorted(activas)) + ". Finalízalas y vuelve a eliminarla.")
        # Historial de partidas terminadas que usaron esta carta (sus imagen y audios se borran en cascada).
        db.query(Anuncio).filter(Anuncio.tarjeta_id == tarjeta_id).delete(synchronize_session=False)
        db.query(TableroTarjeta).filter(TableroTarjeta.tarjeta_id == tarjeta_id).delete(synchronize_session=False)
        db.query(Partida).filter(Partida.ultima_tarjeta_id == tarjeta_id).update({'ultima_tarjeta_id': None}, synchronize_session=False)
        db.delete(tarjeta)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "La tarjeta tiene referencias en la base de datos que impiden eliminarla. Finaliza las partidas que la utilizan y vuelve a intentarlo.")
    except Exception:
        db.rollback()
        raise HTTPException(500, "No se pudo eliminar la tarjeta de la base de datos. El registro se ha conservado.")
    for url in urls: borrar_archivo(url)
    return {"ok": True, "mensaje": f"Tarjeta «{tarjeta.palabra_mazahua}» eliminada junto con su imagen y audios."}


def esquema_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from seguridad import rol_requerido
    from configuracion import COOKIE_NAME
    esquema = get_openapi(title=app.title, version='2.0.0', description=app.description, routes=app.routes)
    esquema.setdefault('components', {}).setdefault('securitySchemes', {}).update({
        'SesionDocente': {'type': 'apiKey', 'in': 'cookie', 'name': COOKIE_NAME,
                         'description': 'Iniciar sesión en /acceso (correo y contraseña) o POST /api/auth/login.'},
        'CSRF': {'type': 'apiKey', 'in': 'header', 'name': 'X-CSRF-Token',
                 'description': 'Copiar csrf_token de GET /api/auth/me. Necesario para modificar datos con cookie.'},
        'JWTBearer': {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT'},
    })
    for ruta, metodos in esquema['paths'].items():
        for metodo, operacion in metodos.items():
            if metodo.upper() in {'GET', 'POST', 'PUT', 'DELETE', 'PATCH'} and rol_requerido(ruta, metodo.upper()):
                cookie = {'SesionDocente': []}
                if metodo.upper() not in {'GET', 'HEAD'}:
                    cookie['CSRF'] = []
                operacion['security'] = [cookie, {'JWTBearer': []}]
    app.openapi_schema = esquema
    return esquema


app.openapi = esquema_openapi


def cargar_catalogo_si_vacia(db) -> int:
    """Base de datos nueva (por ejemplo, en la nube): registra las cartas del catálogo para que
    el sistema funcione sin importar ningún archivo SQL."""
    if db.query(Tarjeta.id).first():
        return 0
    entradas = entradas_catalogo()
    for e in entradas:
        nombre = CORRECCIONES_MATERIAL.get((e['carpeta'], e['palabra_mazahua']), e['palabra_mazahua'])
        db.add(Tarjeta(numero=e.get('numero'), palabra_mazahua=nombre, traduccion_espanol=e['traduccion_espanol'],
                       descripcion=descripcion_por_defecto(nombre, e['traduccion_espanol']), imagen_url=e['imagen_url'],
                       audio_mazahua_url=e['audio_mazahua_url'], audio_espanol_url=e.get('audio_espanol_url')))
    db.commit()
    print(f'Base de datos nueva: se registraron {len(entradas)} cartas del catálogo.', flush=True)
    return len(entradas)


if AUTO_MIGRATE:
    # Aplica el material de catalogo/ (audios en español, imágenes y nombres corregidos) a la base existente.
    with SessionLocal() as _db:
        cargar_catalogo_si_vacia(_db)
        sincronizar_material_catalogo(_db)
