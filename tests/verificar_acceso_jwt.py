"""Pruebas aisladas del sistema completo: python -m tests.verificar_acceso_jwt
Usa SQLite en memoria y una carpeta temporal: nunca toca tu MySQL ni tus archivos.

Comprueba: migración desde la estructura anterior (con respaldo), registro, inicio de sesión
con correo, recuperación de contraseña (temporal y de un solo uso), sesiones JWT revocables,
CSRF, permisos de docente y alumno, tarjetas con imágenes y audios, partidas, QR y WebSocket.
"""
import hashlib
import os
import secrets
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

os.environ.update(APP_ENV='development', AUTO_MIGRATE='false', SERIAL_ENABLED='false',
                  JWT_SECRET=secrets.token_urlsafe(48), CLEANUP_INTERVAL_SECONDS='3600')

ESTRUCTURA_ANTERIOR = [
    "CREATE TABLE docentes (id INTEGER PRIMARY KEY, usuario VARCHAR(80) UNIQUE NOT NULL, nombre VARCHAR(100) NOT NULL, password_hash VARCHAR(255) NOT NULL, activo BOOLEAN NOT NULL, rol VARCHAR(20), estado VARCHAR(20), correo VARCHAR(254), creado DATETIME NOT NULL)",
    "CREATE TABLE tarjetas_rfid (id INTEGER PRIMARY KEY, uid VARCHAR(40) UNIQUE NOT NULL, palabra_mazahua VARCHAR(150) NOT NULL, traduccion_espanol VARCHAR(150) NOT NULL, categoria VARCHAR(100), descripcion TEXT, imagen_url VARCHAR(255) NOT NULL, audio_mazahua_url VARCHAR(255), audio_espanol_url VARCHAR(255), created_at DATETIME)",
    "CREATE TABLE catalogo_asignaciones (carpeta VARCHAR(100) PRIMARY KEY, tarjeta_id INTEGER UNIQUE NOT NULL REFERENCES tarjetas_rfid(id))",
    "CREATE TABLE partidas (id INTEGER PRIMARY KEY, codigo VARCHAR(6) UNIQUE NOT NULL, clave VARCHAR(64) NOT NULL, estado VARCHAR(16) NOT NULL, creada DATETIME NOT NULL, iniciada DATETIME, finalizada DATETIME, limite INTEGER NOT NULL, ultima_carta JSON, secuencia INTEGER NOT NULL, ultima_actividad_docente DATETIME, cierre_motivo VARCHAR(30))",
    "CREATE TABLE participantes (id INTEGER PRIMARY KEY, partida_id INTEGER NOT NULL REFERENCES partidas(id), nombre VARCHAR(60) NOT NULL, solicitud VARCHAR(36) NOT NULL, incorporado DATETIME NOT NULL)",
    "CREATE TABLE tableros (id INTEGER PRIMARY KEY, participante_id INTEGER UNIQUE NOT NULL REFERENCES participantes(id), cartas JSON NOT NULL, marcas JSON NOT NULL)",
    "CREATE TABLE anuncios_partida (id INTEGER PRIMARY KEY, partida_id INTEGER NOT NULL REFERENCES partidas(id), tarjeta_id INTEGER NOT NULL REFERENCES tarjetas_rfid(id), contenido JSON NOT NULL)",
    "CREATE TABLE resultados_partida (partida_id INTEGER PRIMARY KEY REFERENCES partidas(id), participante_id INTEGER NOT NULL REFERENCES participantes(id), fecha DATETIME NOT NULL)",
]


def main(produccion=False):
    if produccion:
        os.environ.update(APP_ENV='production', DB_USER='prueba_aislada', DB_PASSWORD='solo-prueba',
                          ALLOWED_HOSTS='testserver,localhost', AUTO_MIGRATE='false')
    base_url = 'https://testserver' if produccion else 'http://testserver'
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, event, inspect, text
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from starlette.websockets import WebSocketDisconnect
    import database

    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)

    @event.listens_for(engine, 'connect')
    def claves_foraneas(conexion, _):
        conexion.execute('PRAGMA foreign_keys=ON')
    database.engine = engine
    database.SessionLocal = sessionmaker(bind=engine, autoflush=False)
    (Path(tempfile.gettempdir()) / 'opencode').mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix='mazahua-', dir=Path(tempfile.gettempdir()) / 'opencode') as carpeta:
        os.environ['UPLOADS_DIR'] = carpeta
        import migracion
        migracion.CARPETA_RESPALDOS = Path(carpeta) / 'respaldos'
        import main as aplicacion
        import autenticacion
        from claves import hash_password

        # ---------- 1. Migración desde la estructura anterior ----------
        ahora = datetime.utcnow()
        with engine.begin() as c:
            for sql in ESTRUCTURA_ANTERIOR:
                c.execute(text(sql))
            c.execute(text("INSERT INTO docentes VALUES (7,'direccion','Dirección escolar',:h,1,'administrador','aprobada','direccion@escuela.mx',:f)"),
                      {'h': hash_password('anterior1'), 'f': ahora})
            for i in range(1, 18):
                c.execute(text("INSERT INTO tarjetas_rfid (id,uid,palabra_mazahua,traduccion_espanol,imagen_url,audio_mazahua_url,audio_espanol_url) "
                               "VALUES (:i,:u,:m,:e,:img,:am,:ae)"),
                          {'i': i, 'u': f'AA {i:02d}', 'm': f'Mazahua {i}', 'e': f'Español {i}',
                           'img': f'/catalogo/{i:04d}_x/imagen.jpg', 'am': f'/catalogo/{i:04d}_x/audio_mazahua.m4a',
                           'ae': '/uploads/audios/es.mp3' if i == 1 else None})
            c.execute(text("INSERT INTO catalogo_asignaciones VALUES ('0003_x', 3)"))
            c.execute(text("INSERT INTO partidas VALUES (1,'OLD123','clave',:e,:f,:f,:f,25,:u,2,:f,'loteria')"),
                      {'e': 'finalizada', 'f': ahora, 'u': '{"id": 2}'})
            c.execute(text("INSERT INTO participantes VALUES (1,1,'Luis','11111111-1111-4111-8111-111111111111',:f)"), {'f': ahora})
            c.execute(text("INSERT INTO tableros VALUES (1,1,:c,:m)"), {'c': '[{"id": 1}, {"id": 2}, {"id": 999}]', 'm': '[2]'})
            c.execute(text("INSERT INTO anuncios_partida VALUES (1,1,2,'{}')"))
            c.execute(text("INSERT INTO resultados_partida VALUES (1,1,:f)"), {'f': ahora})
        aplicacion.inicializar_base()
        tablas = set(inspect(engine).get_table_names())
        assert tablas == {'usuarios', 'tarjetas', 'partidas', 'participantes', 'tableros',
                          'tablero_tarjetas', 'anuncios', 'sesiones', 'recuperaciones_password'}, tablas
        assert [c['name'] for c in inspect(engine).get_columns('tarjetas')][:8] == [
            'id', 'numero', 'nombre_espanol', 'nombre_mazahua', 'descripcion', 'imagen', 'audio_mazahua', 'audio_espanol']
        assert list((Path(carpeta) / 'respaldos').glob('respaldo_antes_de_migrar_*.sql')), 'Falta el respaldo previo'
        with engine.connect() as c:
            assert c.execute(text("SELECT correo FROM usuarios WHERE id=7")).scalar() == 'direccion@escuela.mx'
            assert c.execute(text("SELECT COUNT(*) FROM tarjetas")).scalar() == 17
            assert c.execute(text("SELECT numero FROM tarjetas WHERE id=3")).scalar() == 3
            assert c.execute(text("SELECT COUNT(imagen), COUNT(audio_mazahua), COUNT(audio_espanol) FROM tarjetas")).one() == (17, 17, 1)
            assert c.execute(text("SELECT gano FROM participantes WHERE id=1")).scalar() == 1
            assert c.execute(text("SELECT COUNT(*) FROM tablero_tarjetas")).scalar() == 2  # la carta 999 no existía
            assert c.execute(text("SELECT ultima_tarjeta_id FROM partidas WHERE id=1")).scalar() == 2
            assert c.execute(text("SELECT descripcion FROM tarjetas WHERE id=1")).scalar().startswith('«Mazahua 1»')
        aplicacion.inicializar_base()  # una segunda vez no debe migrar ni fallar
        # Versión intermedia (tarjetas + imagenes + audios) → tabla única.
        prueba = create_engine('sqlite://', poolclass=StaticPool)
        with prueba.begin() as c:
            c.execute(text("CREATE TABLE tarjetas (id INTEGER PRIMARY KEY, numero INTEGER, uid_rfid VARCHAR(40), nombre_espanol VARCHAR(150), nombre_mazahua VARCHAR(150), descripcion TEXT)"))
            c.execute(text("CREATE TABLE imagenes (id INTEGER PRIMARY KEY, tarjeta_id INTEGER, nombre_archivo VARCHAR(255), ruta VARCHAR(255))"))
            c.execute(text("CREATE TABLE audios (id INTEGER PRIMARY KEY, tarjeta_id INTEGER, idioma VARCHAR(10), nombre_archivo VARCHAR(255), ruta VARCHAR(255))"))
            c.execute(text("INSERT INTO tarjetas VALUES (1, 10, 'F9 DB 91 10', 'Gato', 'Mixi', 'd')"))
            c.execute(text("INSERT INTO imagenes VALUES (1, 1, 'i.jpg', '/catalogo/0010_gato/imagen.jpg')"))
            c.execute(text("INSERT INTO audios VALUES (1, 1, 'mazahua', 'm.m4a', '/m.m4a'), (2, 1, 'espanol', 'e.m4a', '/e.m4a')"))
        assert migracion.unificar_tarjetas(prueba) == 1
        assert set(inspect(prueba).get_table_names()) == {'tarjetas'}
        with prueba.connect() as c:
            assert c.execute(text("SELECT nombre_mazahua, imagen, audio_mazahua, audio_espanol, uid_rfid FROM tarjetas")).one() == \
                ('Mixi', '/catalogo/0010_gato/imagen.jpg', '/m.m4a', '/e.m4a', 'F9 DB 91 10')
        assert migracion.unificar_tarjetas(prueba) is None, 'Una sola vez'
        # Material de catalogo/: audios en español grabados y correcciones de nombres.
        with engine.begin() as c:
            c.execute(text("UPDATE tarjetas SET nombre_mazahua='Segi', nombre_espanol='Tortilla' WHERE numero=6"))
        with database.SessionLocal() as db:
            cambios = aplicacion.sincronizar_material_catalogo(db)
            assert cambios['audios_espanol'] == 17 and cambios['nombres'] == 1, cambios
            assert aplicacion.sincronizar_material_catalogo(db) == {'audios_espanol': 0, 'imagenes': 0, 'nombres': 0}, 'Debe ser idempotente'
        with engine.connect() as c:
            assert c.execute(text("SELECT nombre_mazahua FROM tarjetas WHERE numero=6")).scalar() == "T'zeyi"
            assert c.execute(text("SELECT COUNT(*) FROM tarjetas WHERE audio_espanol LIKE '/catalogo/%'")).scalar() == 17

        cliente = TestClient(aplicacion.app, base_url=base_url)
        anonimo = TestClient(aplicacion.app, base_url=base_url)

        # ---------- 2. Cuenta migrada: inicia sesión con su correo ----------
        r = cliente.post('/api/auth/login', json={'correo': 'direccion@escuela.mx', 'password': 'anterior1'})
        assert r.status_code == 200, r.text
        cliente.post('/api/auth/logout', headers={'X-CSRF-Token': r.json()['csrf_token']})

        # ---------- 3. Registro con validaciones ----------
        registro = lambda **d: anonimo.post('/api/auth/registro', json={'nombre': 'Ana López', 'correo': 'ana@escuela.mx',
                                                                       'password': 'abc123', 'confirmacion': 'abc123', **d})
        assert registro(correo='sin-arroba').status_code == 422
        assert registro(password='abc', confirmacion='abc').status_code == 422
        assert registro(confirmacion='otra12').status_code == 422
        assert registro(nombre=' ').status_code == 422
        assert registro().status_code == 201
        assert registro(correo='ANA@escuela.mx').status_code == 409, 'Correo duplicado'
        assert anonimo.post('/api/auth/solicitudes', json={}).status_code in {401, 404, 405}, 'Ya no existen solicitudes'
        assert anonimo.post('/api/auth/invitaciones', json={}).status_code in {401, 404, 405}

        # ---------- 4. Inicio de sesión ----------
        assert anonimo.post('/api/auth/login', json={'correo': 'ana@escuela.mx', 'password': 'malmal'}).status_code == 401
        assert anonimo.post('/api/auth/login', json={'correo': 'nadie@escuela.mx', 'password': 'abc123'}).status_code == 401
        r = cliente.post('/api/auth/login', json={'correo': 'Ana@Escuela.MX', 'password': 'abc123'})
        assert r.status_code == 200 and r.json()['docente']['nombre'] == 'Ana López'
        csrf = r.json()['csrf_token']
        H = {'X-CSRF-Token': csrf}
        assert cliente.get('/api/auth/me').json()['docente']['correo'] == 'ana@escuela.mx'
        with database.SessionLocal() as db:
            usuario = db.query(autenticacion.Usuario).filter_by(correo='ana@escuela.mx').one()
            assert usuario.password_hash.startswith('pbkdf2_sha256$') and 'abc123' not in usuario.password_hash

        # ---------- 5. Permisos: el alumno (sin sesión) no administra nada ----------
        for metodo, ruta in [('get', '/panel'), ('get', '/editar'), ('get', '/docente'), ('get', '/administracion'), ('get', '/cuenta')]:
            r = getattr(anonimo, metodo)(ruta, follow_redirects=False)
            assert r.status_code == 303 and '/acceso' in r.headers['location'], ruta
        assert anonimo.get('/api/tarjetas').status_code == 401
        assert anonimo.post('/api/tarjetas', data={'palabra_mazahua': 'x', 'traduccion_espanol': 'y'}).status_code == 401
        assert anonimo.delete('/api/tarjetas/1').status_code == 401
        assert anonimo.post('/api/partidas', json={'limite': 5}).status_code == 401
        assert anonimo.get('/api/invitacion/ABC234').status_code == 401
        assert anonimo.put('/api/videos', json={'videos': []}).status_code == 401
        assert anonimo.get('/api/vocabulario').status_code == 200
        assert cliente.post('/api/partidas', json={'limite': 5}).status_code == 403, 'Sin CSRF debe rechazarse'

        # ---------- 6. Tarjetas: agregar, editar, subir/eliminar audio, eliminar ----------
        png = b'\x89PNG\r\n\x1a\n' + b'0' * 64
        r = cliente.post('/api/tarjetas', headers=H, data={'palabra_mazahua': 'Mixi', 'traduccion_espanol': 'Gato', 'numero': '50'},
                         files={'imagen': ('g.png', png, 'image/png'), 'audio_mazahua': ('m.mp3', b'ID3' + b'0' * 64, 'audio/mpeg')})
        assert r.status_code == 200, r.text
        nueva = r.json()['tarjeta']
        assert nueva['numero'] == 50 and nueva['uid'] is None and nueva['audio_espanol_url'] is None
        assert nueva['descripcion'].startswith('«Mixi»')
        assert (Path(carpeta) / nueva['imagen_url'].removeprefix('/uploads/')).is_file()
        r = cliente.post('/api/tarjetas', headers=H, data={'palabra_mazahua': 'X', 'traduccion_espanol': 'Y', 'numero': '50'},
                         files={'imagen': ('g.png', png, 'image/png'), 'audio_mazahua': ('m.mp3', b'ID3' + b'0' * 64, 'audio/mpeg')})
        assert r.status_code == 409, 'Número repetido'
        r = cliente.put(f"/api/tarjetas/{nueva['id']}", headers=H, data={'palabra_mazahua': 'Mixi', 'traduccion_espanol': 'Gato', 'descripcion': 'Animal doméstico.'},
                        files={'audio_espanol': ('e.mp3', b'ID3' + b'1' * 64, 'audio/mpeg')})
        assert r.status_code == 200 and r.json()['tarjeta']['audio_espanol_url'] and r.json()['tarjeta']['descripcion'] == 'Animal doméstico.'
        audio_es = Path(carpeta) / r.json()['tarjeta']['audio_espanol_url'].removeprefix('/uploads/')
        assert audio_es.is_file()
        r = cliente.put(f"/api/tarjetas/{nueva['id']}", headers=H, data={'palabra_mazahua': 'Mixi', 'traduccion_espanol': 'Gato', 'eliminar_audio_espanol': 'true'})
        assert r.json()['tarjeta']['audio_espanol_url'] is None and not audio_es.exists(), 'Eliminar audio'
        assert r.json()['tarjeta']['numero'] == 50, 'El número se conserva si no se envía'
        with engine.connect() as c:
            assert c.execute(text("SELECT audio_mazahua IS NOT NULL, audio_espanol IS NULL FROM tarjetas WHERE id=:i"), {'i': nueva['id']}).one() == (1, 1)
        assert [t['id'] for t in cliente.get('/api/tarjetas?buscar=50').json()] == [nueva['id']]
        assert cliente.delete(f"/api/tarjetas/{nueva['id']}", headers=H).status_code == 200
        with engine.connect() as c:
            assert c.execute(text("SELECT COUNT(*) FROM tarjetas WHERE id=:i"), {'i': nueva['id']}).scalar() == 0

        # ---------- 7. Partida, QR, alumnos, límite y juego ----------
        r = cliente.post('/api/partidas', headers=H, json={'limite': 2, 'nombre': 'Grupo 3A'})
        assert r.status_code == 201 and r.json()['nombre'] == 'Grupo 3A' and 'clave' not in r.json()
        codigo = r.json()['codigo']
        assert cliente.get(f'/api/invitacion/{codigo}').json()['url'].endswith(f'/estudiante?codigo={codigo}')
        assert cliente.get(f'/api/invitacion/{codigo}/qr').headers['content-type'].startswith('image/svg')
        publica = anonimo.get(f'/api/partidas/{codigo}/publica').json()
        assert publica == {'codigo': codigo, 'nombre': 'Grupo 3A', 'estado': 'esperando', 'limite': 2, 'lugares_disponibles': 2}
        assert anonimo.get('/api/partidas/ZZZZZZ/publica').status_code == 404
        alumnos = [str(uuid4()) for _ in range(3)]
        r = anonimo.post('/api/partidas/unirse', json={'codigo': codigo, 'nombre': 'Luis', 'solicitud': alumnos[0], 'avatar': 'p1-c0-h0-e0-a1-r0-f0'})
        assert r.status_code == 200 and r.json()['participantes'][0]['avatar'] == 'p1-c0-h0-e0-a1-r0-f0', 'Se guarda el avatar del alumno'
        assert anonimo.post('/api/partidas/unirse', json={'codigo': codigo, 'nombre': 'X', 'solicitud': str(uuid4()), 'avatar': '<script>'}).status_code == 422
        assert anonimo.post('/api/partidas/unirse', json={'codigo': codigo, 'nombre': 'Eva', 'solicitud': alumnos[1]}).status_code == 200
        r = anonimo.post('/api/partidas/unirse', json={'codigo': codigo, 'nombre': 'Sol', 'solicitud': alumnos[2]})
        assert r.status_code == 409 and 'llena' in r.json()['detail']
        assert anonimo.post(f'/api/partidas/{codigo}/iniciar', json={}).status_code == 401, 'El alumno no inicia partidas'
        assert anonimo.post(f'/api/juego/{codigo}/anunciar', json={'uid': '3'}).status_code == 401
        # Otro docente no puede administrar la partida de Ana.
        otro = TestClient(aplicacion.app, base_url=base_url)
        otro.post('/api/auth/registro', json={'nombre': 'Beto', 'correo': 'beto@escuela.mx', 'password': 'beto12', 'confirmacion': 'beto12'})
        csrf_otro = otro.post('/api/auth/login', json={'correo': 'beto@escuela.mx', 'password': 'beto12'}).json()['csrf_token']
        assert otro.post(f'/api/partidas/{codigo}/finalizar', headers={'X-CSRF-Token': csrf_otro}, json={}).status_code == 403
        assert cliente.post(f'/api/partidas/{codigo}/iniciar', headers=H, json={}).json()['estado'] == 'en_curso'
        r = anonimo.post('/api/partidas/unirse', json={'codigo': codigo, 'nombre': 'Tarde', 'solicitud': str(uuid4())})
        assert r.status_code == 409 and 'comenzó' in r.json()['detail']
        with engine.connect() as c:
            assert c.execute(text("SELECT COUNT(*) FROM tablero_tarjetas")).scalar() == 2 + 32
        r = cliente.post(f'/api/juego/{codigo}/anunciar', headers=H, json={'uid': '3'})  # por número de carta
        assert r.status_code == 200 and r.json()['ultima_carta']['numero'] == 3
        assert cliente.post(f'/api/juego/{codigo}/anunciar', headers=H, json={'uid': 'AA 05'}).status_code == 200  # por UID
        with anonimo.websocket_connect(f'/ws/partidas/{codigo}') as ws:
            ws.send_text(alumnos[0])
            datos = ws.receive_json()
            assert len(datos['tablero']['cartas']) == 16 and 'clave' not in datos
            id_carta = next((c['id'] for c in datos['tablero']['cartas'] if c['id'] in datos['anunciadas']), None)
            no_anunciada = next(c['id'] for c in datos['tablero']['cartas'] if c['id'] not in datos['anunciadas'])
            ws.send_text('{"reaccion": "🚫"}')  # emoji no permitido: se ignora
            ws.send_text('{"reaccion": "👏"}')
            reaccion = ws.receive_json()
            assert reaccion == {'tipo': 'reaccion', 'emoji': '👏', 'id': reaccion['id'], 'nombre': 'Luis', 'avatar': 'p1-c0-h0-e0-a1-r0-f0'}, reaccion
        assert anonimo.post(f'/api/juego/{codigo}/marcar', json={'token': alumnos[0], 'tarjeta_id': no_anunciada, 'marcada': True}).status_code == 409
        if id_carta:
            assert id_carta in anonimo.post(f'/api/juego/{codigo}/marcar', json={'token': alumnos[0], 'tarjeta_id': id_carta, 'marcada': True}).json()['marcas']
        with anonimo.websocket_connect(f'/ws/partidas/{codigo}') as ws:
            ws.send_text('docente')  # sin sesión docente: se rechaza
            try:
                ws.receive_json()
                raise AssertionError('Un alumno no debe recibir la vista del docente')
            except WebSocketDisconnect as cierre:
                assert cierre.code == 1008
        esquema_ws = 'wss' if produccion else 'ws'  # la cookie de producción solo viaja por HTTPS/WSS
        with cliente.websocket_connect(f'{esquema_ws}://testserver/ws/partidas/{codigo}') as ws:
            ws.send_text('docente')
            assert ws.receive_json()['nombre'] == 'Grupo 3A'
        assert [p['codigo'] for p in cliente.get('/api/partidas/mias').json()][0] == codigo
        assert cliente.post(f'/api/partidas/{codigo}/finalizar', headers=H, json={}).json()['estado'] == 'finalizada'
        assert anonimo.post('/api/partidas/unirse', json={'codigo': codigo, 'nombre': 'X', 'solicitud': str(uuid4())}).status_code == 409

        # ---------- 8. Perfil y cambio de contraseña ----------
        r = cliente.put('/api/auth/perfil', headers=H, json={'nombre': 'Ana L.', 'correo': 'beto@escuela.mx', 'password': 'abc123'})
        assert r.status_code == 409, 'Correo de otra cuenta'
        assert cliente.put('/api/auth/perfil', headers=H, json={'nombre': 'Ana L.', 'correo': 'ana@escuela.mx', 'password': 'mala12'}).status_code == 403
        assert cliente.put('/api/auth/perfil', headers=H, json={'nombre': 'Ana L.', 'correo': 'ana@escuela.mx', 'password': 'abc123'}).status_code == 200

        # ---------- 9. Recuperación: enlace temporal y de un solo uso ----------
        local = TestClient(aplicacion.app, base_url=base_url, client=('127.0.0.1', 5000))
        r = local.post('/api/auth/recuperar', json={'correo': 'ana@escuela.mx'})
        if produccion:
            assert r.status_code == 202 and 'enlace' not in r.json(), 'En producción nunca se muestra el enlace'
        else:
            assert r.status_code == 202 and r.json()['enlace'].startswith('/acceso#recuperar=')
            token = r.json()['enlace'].split('=', 1)[1]
            with engine.connect() as c:
                guardado = c.execute(text("SELECT token_hash FROM recuperaciones_password")).scalar()
            assert guardado == hashlib.sha256(token.encode()).hexdigest() and token not in guardado, 'Solo se guarda el hash'
            assert anonimo.post('/api/auth/restablecer', json={'token': token, 'nueva': 'abc'}).status_code == 422
            assert anonimo.post('/api/auth/restablecer', json={'token': token, 'nueva': 'nueva1'}).status_code == 200
            assert anonimo.post('/api/auth/restablecer', json={'token': token, 'nueva': 'otra12'}).status_code == 403, 'Un solo uso'
            assert cliente.get('/api/auth/me').status_code == 401, 'Las sesiones anteriores se cierran'
            assert anonimo.post('/api/auth/login', json={'correo': 'ana@escuela.mx', 'password': 'nueva1'}).status_code == 200
            # Enlace vencido
            vencido = secrets.token_urlsafe(32)
            with database.SessionLocal() as db:
                db.add(autenticacion.RecuperacionPassword(token_hash=hashlib.sha256(vencido.encode()).hexdigest(), usuario_id=usuario.id,
                                                          vence=datetime.utcnow() - timedelta(minutes=1)))
                db.commit()
            assert anonimo.post('/api/auth/restablecer', json={'token': vencido, 'nueva': 'nueva2'}).status_code == 403
        remoto = anonimo.post('/api/auth/recuperar', json={'correo': 'ana@escuela.mx'})
        assert remoto.status_code == 202 and 'enlace' not in remoto.json(), 'Desde otro equipo nunca se muestra el enlace'
        assert anonimo.post('/api/auth/recuperar', json={'correo': 'nadie@escuela.mx'}).json()['mensaje'] == remoto.json()['mensaje'], \
            'No revela qué correos existen'

        # ---------- 10. Cerrar sesión revoca el JWT ----------
        r = otro.post('/api/auth/logout', headers={'X-CSRF-Token': csrf_otro})
        assert r.status_code == 200 and otro.get('/api/auth/me').status_code == 401

    print('OK: migración con respaldo (también imagenes/audios → tabla única de tarjetas), material del catálogo (audios en español), registro y validaciones, inicio de sesión con correo, recuperación temporal de un uso, '
          'sesiones revocables, CSRF, permisos de alumno/docente, tarjetas con imágenes y audios, partidas, QR, límite y WebSocket.')


if __name__ == '__main__':
    main()
