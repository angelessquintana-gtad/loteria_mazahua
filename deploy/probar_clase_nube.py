"""Prueba acotada de 25 alumnos en la instalación propia; limpia solo sus datos.

Usa una sesión administrativa temporal firmada con la configuración privada.
No cambia contraseñas ni cuentas. No es un monitor ni genera tráfico permanente.
"""
import asyncio
import json
import secrets
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from deploy.migrar_nube import motor_remoto, parametros_remotos
from sqlalchemy import text
import jwt

BASE = 'https://loteria-mazahua-escuela.onrender.com'


def peticion(ruta, datos=None, token=None):
    headers = {'Content-Type':'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    inicio = time.monotonic()
    with urlopen(Request(BASE + ruta, headers=headers, data=json.dumps(datos).encode() if datos is not None else None), timeout=90) as respuesta:
        return json.load(respuesta), round(time.monotonic() - inicio, 3)


async def conexiones(codigo, alumnos, clave, token, uid, tarjeta_id):
    import websockets
    conexiones_abiertas = []
    async def abrir(alumno):
        inicio = time.monotonic()
        ws = await websockets.connect(BASE.replace('https://', 'wss://') + '/ws/partidas/' + codigo,
                                      origin=BASE, open_timeout=60, ping_interval=20, max_size=1048576)
        conexiones_abiertas.append(ws)
        await ws.send(alumno['solicitud'])
        estado = json.loads(await asyncio.wait_for(ws.recv(), 90))
        assert len(estado['tablero']['cartas']) == 16
        return ws, alumno, estado, round(time.monotonic() - inicio, 3)
    try:
        abiertos = await asyncio.gather(*(abrir(a) for a in alumnos))
        _, anunciar_segundos = await asyncio.to_thread(peticion, f'/api/juego/{codigo}/anunciar', {'clave':clave,'uid':uid}, token)
        inicio_evento = time.monotonic()
        async def recibir(fila):
            ws, alumno, estado, _ = fila
            while estado['secuencia'] < 1:
                estado = json.loads(await asyncio.wait_for(ws.recv(), 90))
            return round(time.monotonic() - inicio_evento, 3)
        latencias = await asyncio.gather(*(recibir(f) for f in abiertos))
        con_carta = [a for _,a,estado,_ in abiertos if tarjeta_id in {c['id'] for c in estado['tablero']['cartas']}]
        async def marcar(alumno):
            resultado, segundos = await asyncio.to_thread(peticion, f'/api/juego/{codigo}/marcar',
                {'token':alumno['solicitud'],'tarjeta_id':tarjeta_id,'marcada':True})
            assert tarjeta_id in resultado['marcas']
            return segundos
        marcas = await asyncio.gather(*(marcar(a) for a in con_carta))
        ws_propio, alumno_propio, estado_propio, _ = abiertos[0]
        otras = estado_propio['tablero']['cartas'][:2]
        for carta in otras:
            await asyncio.to_thread(peticion, f'/api/juego/{codigo}/anunciar', {'clave':clave,'uid':carta['uid']}, token)
        async def marcar_propia(carta):
            return await asyncio.to_thread(peticion, f'/api/juego/{codigo}/marcar',
                {'token':alumno_propio['solicitud'],'tarjeta_id':carta['id'],'marcada':True})
        await asyncio.gather(*(marcar_propia(c) for c in otras))
        esperadas = {c['id'] for c in otras}
        limite = time.monotonic() + 90
        while time.monotonic() < limite:
            estado_actual = json.loads(await asyncio.wait_for(ws_propio.recv(), 90))
            if esperadas.issubset(estado_actual['tablero']['marcas']):
                break
        else:
            raise AssertionError('Se perdió una marca simultánea del mismo alumno')
        return {'websockets_conectados':len(abiertos), 'cartas_por_tablero':16,
                'conexion_y_tablero_max_segundos':max(f[3] for f in abiertos),
                'anunciar_segundos':anunciar_segundos, 'recepcion_anuncio_max_segundos':max(latencias),
                'alumnos_que_marcaron':len(marcas), 'marcar_max_segundos':max(marcas, default=0),
                'marcas_concurrentes_mismo_alumno':True}
    finally:
        await asyncio.gather(*(ws.close() for ws in conexiones_abiertas), return_exceptions=True)


def main():
    motor = motor_remoto()
    jti = secrets.token_hex(32)
    codigo = None
    reporte = {'url':BASE, 'fecha_utc':datetime.now(timezone.utc).isoformat(), 'alumnos':25}
    try:
        with motor.begin() as db:
            docente = db.execute(text("SELECT id FROM docentes WHERE rol='administrador' AND activo=1 AND estado='aprobada' ORDER BY id LIMIT 1")).scalar_one()
            db.execute(text('INSERT INTO sesiones_docentes (jti,docente_id,vence) VALUES (:jti,:id,:vence)'),
                {'jti':jti,'id':docente,'vence':datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(minutes=15)})
        ahora = datetime.now(timezone.utc)
        token = jwt.encode({'sub':str(docente),'jti':jti,'csrf':secrets.token_urlsafe(32),'role':'administrador',
                            'iss':'loteria-mazahua','aud':'loteria-mazahua','iat':ahora,'nbf':ahora,'exp':ahora+timedelta(minutes=15)},
                           parametros_remotos()['JWT_SECRET'], algorithm='HS256')
        reporte['etapa'] = 'consultar_catalogo'
        tarjetas, _ = peticion('/api/tarjetas', token=token)
        assert len(tarjetas) == 54
        reporte['etapa'] = 'crear_partida'
        sala, _ = peticion('/api/partidas', {'limite':25}, token)
        codigo, clave = sala['codigo'], sala['clave']
        alumnos = [{'codigo':codigo,'nombre':f'Prueba técnica {i+1}','solicitud':str(uuid4())} for i in range(25)]
        inicio = time.monotonic()
        reporte['etapa'] = 'ingreso_25_alumnos'
        with ThreadPoolExecutor(max_workers=25) as grupo:
            resultados = list(grupo.map(lambda a:peticion('/api/partidas/unirse', a), alumnos))
        reporte['ingresos_correctos'] = len(resultados)
        reporte['ingreso_total_segundos'] = round(time.monotonic() - inicio, 3)
        reporte['ingreso_max_segundos'] = max(t for _,t in resultados)
        reporte['etapa'] = 'iniciar'
        _, reporte['iniciar_segundos'] = peticion(f'/api/partidas/{codigo}/iniciar', {'clave':clave}, token)
        primera = tarjetas[0]
        reporte['etapa'] = 'websocket_y_marcas'
        reporte.update(asyncio.run(conexiones(codigo, alumnos, clave, token, primera['uid'], primera['id'])))
        with motor.connect() as db:
            reporte['base_datos_indices_bytes_durante_clase'] = int(db.execute(text('SELECT SUM(DATA_LENGTH+INDEX_LENGTH) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE()')).scalar() or 0)
        peticion(f'/api/partidas/{codigo}/finalizar', {'clave':clave}, token)
        reporte['ok'] = True
        reporte['etapa'] = 'completada'
    except Exception as error:
        reporte.update(ok=False, error_tipo=type(error).__name__)
        if isinstance(error, HTTPError):
            reporte['error_http'] = error.code
    finally:
        with motor.begin() as db:
            if codigo:
                partida = db.execute(text('SELECT id FROM partidas WHERE codigo=:codigo'), {'codigo':codigo}).scalar()
                if partida:
                    db.execute(text('DELETE t FROM tableros t INNER JOIN participantes p ON t.participante_id=p.id WHERE p.partida_id=:id'), {'id':partida})
                    for tabla in ('resultados_partida','anuncios_partida','participantes'):
                        db.execute(text(f'DELETE FROM {tabla} WHERE partida_id=:id'), {'id':partida})
                    db.execute(text('DELETE FROM partidas WHERE id=:id AND codigo=:codigo'), {'id':partida,'codigo':codigo})
            db.execute(text('DELETE FROM sesiones_docentes WHERE jti=:jti'), {'jti':jti})
        motor.dispose()
    (RAIZ / 'docs/PRUEBA_NUBE.json').write_text(json.dumps(reporte, indent=2), encoding='utf-8')
    print(json.dumps(reporte, ensure_ascii=True))
    return 0 if reporte.get('ok') else 1


if __name__ == '__main__':
    raise SystemExit(main())
