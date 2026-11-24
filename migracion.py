"""Migración de la estructura anterior de la base de datos a la nueva (se ejecuta sola al iniciar).

Estructura anterior                          →  Estructura nueva
--------------------------------------------    -------------------------------------------------
docentes (usuario, rol, estado, activo…)     →  usuarios (nombre, correo, password_hash, fecha_registro)
sesiones_docentes                            →  sesiones (se vuelve a iniciar sesión)
invitaciones_docentes                        →  (se elimina: ya no hay invitaciones)
recuperaciones_password (docente_id)         →  recuperaciones_password (usuario_id)
tarjetas_rfid (con rutas de archivos)        →  tarjetas (tabla única: nombres, descripción, imagen y audios)
imagenes + audios (versión intermedia)       →  columnas imagen, audio_mazahua y audio_espanol de tarjetas
catalogo_asignaciones                        →  tarjetas.numero (número de la carta)
partidas (clave, ultima_carta JSON)          →  partidas (nombre, usuario_id, ultima_tarjeta_id)
participantes (solicitud)                    →  participantes (dispositivo, gano)
resultados_partida                           →  participantes.gano
tableros (cartas y marcas en JSON)           →  tableros + tablero_tarjetas
anuncios_partida (copia JSON de la carta)    →  anuncios (solo la relación con la tarjeta)

Antes de cambiar nada se escribe un respaldo completo en sql/respaldos/. Si algo falla,
las tablas anteriores se restauran y no se pierde información.
"""
import json
import logging
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import inspect, text

logger = logging.getLogger('mazahua.migracion')
CARPETA_RESPALDOS = Path(__file__).resolve().parent / 'sql' / 'respaldos'
PREFIJO = '_antigua_'
ANTIGUAS = ['tarjetas_rfid', 'catalogo_asignaciones', 'docentes', 'sesiones_docentes', 'invitaciones_docentes',
            'recuperaciones_password', 'partidas', 'participantes', 'tableros', 'anuncios_partida', 'resultados_partida']
# Tablas que existen en ambas versiones con el mismo nombre: se reconocen por una columna antigua.
FIRMA_ANTIGUA = {'partidas': 'clave', 'participantes': 'solicitud', 'tableros': 'cartas', 'recuperaciones_password': 'docente_id'}


def tablas_antiguas(insp):
    existentes = set(insp.get_table_names())
    encontradas = []
    for tabla in ANTIGUAS:
        if tabla not in existentes:
            continue
        firma = FIRMA_ANTIGUA.get(tabla)
        if firma and firma not in {c['name'] for c in insp.get_columns(tabla)}:
            continue  # ya tiene la estructura nueva
        encontradas.append(tabla)
    return encontradas


def literal(valor):
    if valor is None:
        return 'NULL'
    if isinstance(valor, bool):
        return '1' if valor else '0'
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, (datetime, date)):
        return "'" + valor.strftime('%Y-%m-%d %H:%M:%S' if isinstance(valor, datetime) else '%Y-%m-%d') + "'"
    if isinstance(valor, (bytes, bytearray)):
        return "0x" + bytes(valor).hex() if valor else "''"
    if not isinstance(valor, str):
        valor = json.dumps(valor, ensure_ascii=False)
    escapado = (valor.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
                .replace('\r', '\\r').replace('\x00', '\\0'))
    return f"'{escapado}'"


def escribir_respaldo(conexion, tablas, mysql):
    CARPETA_RESPALDOS.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA_RESPALDOS / f"respaldo_antes_de_migrar_{datetime.now():%Y%m%d_%H%M%S}.sql"
    lineas = ['-- Respaldo automático de la base de datos ANTES de migrar a la nueva estructura.',
              '-- Para volver a la versión anterior: importa este archivo en phpMyAdmin en una base vacía.',
              'SET FOREIGN_KEY_CHECKS = 0;', '']
    for tabla in tablas:
        if mysql:
            crear = conexion.execute(text(f'SHOW CREATE TABLE `{tabla}`')).fetchone()[1]
            lineas += [f'DROP TABLE IF EXISTS `{tabla}`;', crear + ';']
        resultado = conexion.execute(text(f'SELECT * FROM {tabla}'))
        columnas = list(resultado.keys())
        for fila in resultado:
            valores = ', '.join(literal(v) for v in fila)
            lineas.append(f"INSERT INTO `{tabla}` (`{'`, `'.join(columnas)}`) VALUES ({valores});")
        lineas.append('')
    lineas.append('SET FOREIGN_KEY_CHECKS = 1;')
    ruta.write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    return ruta


def claves_foraneas(conexion, activar, mysql):
    if mysql:
        conexion.execute(text(f'SET FOREIGN_KEY_CHECKS = {1 if activar else 0}'))
    else:
        conexion.execute(text(f'PRAGMA foreign_keys = {"ON" if activar else "OFF"}'))


def numero_desde_ruta(ruta):
    """'/catalogo/0010_gato/imagen.jpg' → 10"""
    if ruta and ruta.startswith('/catalogo/'):
        prefijo = ruta.split('/')[2].split('_', 1)[0]
        if prefijo.isdigit():
            return int(prefijo)
    return None


def como_json(valor, defecto):
    if valor is None:
        return defecto
    if isinstance(valor, (list, dict)):
        return valor
    try:
        return json.loads(valor)
    except (TypeError, ValueError):
        return defecto


def filas(conexion, tabla, existentes):
    if tabla not in existentes:
        return []
    return [dict(f._mapping) for f in conexion.execute(text(f'SELECT * FROM {PREFIJO}{tabla}'))]


def copiar_datos(conexion, existentes):
    ahora = datetime.utcnow()
    ins = lambda tabla, datos: datos and conexion.execute(text(
        f"INSERT INTO {tabla} ({', '.join(datos[0])}) VALUES ({', '.join(':' + c for c in datos[0])})"), datos)

    # Usuarios (docentes). El inicio de sesión ahora es con correo.
    usuarios, correos = [], set()
    for d in filas(conexion, 'docentes', existentes):
        correo = (d.get('correo') or '').strip().lower() or f"{d['usuario']}@sin-correo.local"
        if correo in correos:
            correo = f"{d['usuario']}.{d['id']}@sin-correo.local"
        correos.add(correo)
        usuarios.append({'id': d['id'], 'nombre': d['nombre'], 'correo': correo, 'password_hash': d['password_hash'],
                         'fecha_registro': d.get('creado') or ahora})
    ins('usuarios', usuarios)

    # Tarjetas: una sola tabla con nombres, descripción, imagen y audios.
    asignadas = {a['tarjeta_id']: a['carpeta'] for a in filas(conexion, 'catalogo_asignaciones', existentes)}
    tarjetas, numeros = [], set()
    for t in filas(conexion, 'tarjetas_rfid', existentes):
        carpeta = asignadas.get(t['id'], '')
        numero = int(carpeta.split('_', 1)[0]) if carpeta[:4].isdigit() else numero_desde_ruta(t.get('imagen_url'))
        if numero in numeros:
            numero = None
        numeros.add(numero)
        tarjetas.append({'id': t['id'], 'numero': numero, 'nombre_espanol': t['traduccion_espanol'],
                         'nombre_mazahua': t['palabra_mazahua'], 'descripcion': t.get('descripcion'),
                         'imagen': t.get('imagen_url') or None, 'audio_mazahua': t.get('audio_mazahua_url') or None,
                         'audio_espanol': t.get('audio_espanol_url') or None, 'uid_rfid': t['uid'] or None})
    ins('tarjetas', tarjetas)
    ids_tarjetas = {t['id'] for t in tarjetas}

    # Partidas y su historial.
    partidas = []
    for p in filas(conexion, 'partidas', existentes):
        ultima = como_json(p.get('ultima_carta'), {}) or {}
        ultima_id = ultima.get('id') if isinstance(ultima, dict) else None
        partidas.append({'id': p['id'], 'codigo': p['codigo'], 'nombre': f"Partida {p['codigo']}", 'usuario_id': None,
                         'limite': p.get('limite') or 25, 'estado': p['estado'], 'fecha_creacion': p['creada'],
                         'iniciada': p.get('iniciada'), 'finalizada': p.get('finalizada'),
                         'ultima_tarjeta_id': ultima_id if ultima_id in ids_tarjetas else None,
                         'secuencia': p.get('secuencia') or 0, 'ultima_actividad_docente': p.get('ultima_actividad_docente'),
                         'cierre_motivo': p.get('cierre_motivo')})
    ins('partidas', partidas)
    ganadores = {r['participante_id'] for r in filas(conexion, 'resultados_partida', existentes)}
    ins('participantes', [{'id': a['id'], 'partida_id': a['partida_id'], 'nombre': a['nombre'], 'dispositivo': a['solicitud'],
                           'fecha_ingreso': a['incorporado'], 'gano': a['id'] in ganadores}
                          for a in filas(conexion, 'participantes', existentes)])
    tableros, casillas = [], []
    for t in filas(conexion, 'tableros', existentes):
        tableros.append({'id': t['id'], 'participante_id': t['participante_id'], 'creado': ahora})
        marcas = set(como_json(t.get('marcas'), []))
        for posicion, carta in enumerate(como_json(t.get('cartas'), [])):
            tarjeta_id = carta.get('id') if isinstance(carta, dict) else carta
            if tarjeta_id in ids_tarjetas:
                casillas.append({'tablero_id': t['id'], 'posicion': posicion, 'tarjeta_id': tarjeta_id, 'marcada': tarjeta_id in marcas})
    ins('tableros', tableros)
    ins('tablero_tarjetas', casillas)
    ins('anuncios', [{'id': a['id'], 'partida_id': a['partida_id'], 'tarjeta_id': a['tarjeta_id'], 'fecha': ahora}
                     for a in filas(conexion, 'anuncios_partida', existentes) if a['tarjeta_id'] in ids_tarjetas])
    return {'usuarios': len(usuarios), 'tarjetas': len(tarjetas), 'partidas': len(partidas), 'tableros': len(tableros)}


def migrar_estructura_anterior(engine, Base):
    insp = inspect(engine)
    antiguas = tablas_antiguas(insp)
    if not antiguas:
        return None
    mysql = engine.dialect.name in {'mysql', 'mariadb'}
    print('Actualizando la base de datos a la nueva estructura (se hace una sola vez)…', flush=True)
    with engine.begin() as conexion:
        respaldo = escribir_respaldo(conexion, antiguas, mysql)
    print(f'  Respaldo guardado en: {respaldo}', flush=True)

    # 1) Apartar las tablas anteriores con otro nombre.
    with engine.begin() as conexion:
        claves_foraneas(conexion, False, mysql)
        for tabla in antiguas:
            conexion.execute(text(f'ALTER TABLE {tabla} RENAME TO {PREFIJO}{tabla}'))
        claves_foraneas(conexion, True, mysql)
    nuevas_creadas = []
    try:
        # 2) Crear las tablas nuevas y copiar la información.
        existentes_antes = set(inspect(engine).get_table_names())
        Base.metadata.create_all(bind=engine)
        nuevas_creadas = [t for t in inspect(engine).get_table_names() if t not in existentes_antes]
        with engine.begin() as conexion:
            resumen = copiar_datos(conexion, set(antiguas))
        # 3) Eliminar las tablas anteriores (ya están respaldadas en el archivo .sql).
        with engine.begin() as conexion:
            claves_foraneas(conexion, False, mysql)
            for tabla in antiguas:
                conexion.execute(text(f'DROP TABLE {PREFIJO}{tabla}'))
            claves_foraneas(conexion, True, mysql)
    except Exception:
        logger.exception('La migración falló; se restauran las tablas anteriores')
        with engine.begin() as conexion:
            claves_foraneas(conexion, False, mysql)
            for tabla in nuevas_creadas:
                conexion.execute(text(f'DROP TABLE IF EXISTS {tabla}'))
            for tabla in antiguas:
                conexion.execute(text(f'ALTER TABLE {PREFIJO}{tabla} RENAME TO {tabla}'))
            claves_foraneas(conexion, True, mysql)
        raise
    print('  Migración terminada: ' + ', '.join(f'{v} {k}' for k, v in resumen.items()), flush=True)
    return resumen


def unificar_tarjetas(engine):
    """Versión intermedia → tabla única: pasa las rutas de `imagenes` y `audios` a las columnas
    imagen, audio_mazahua y audio_espanol de `tarjetas`, y elimina esas dos tablas (con respaldo previo)."""
    insp = inspect(engine)
    tablas = set(insp.get_table_names())
    if 'tarjetas' not in tablas or not tablas & {'imagenes', 'audios'}:
        return None
    columnas = {c['name'] for c in insp.get_columns('tarjetas')}
    mysql = engine.dialect.name in {'mysql', 'mariadb'}
    print('Uniendo imágenes y audios en la tabla tarjetas (se hace una sola vez)…', flush=True)
    with engine.begin() as conexion:
        respaldo = escribir_respaldo(conexion, [t for t in ('tarjetas', 'imagenes', 'audios') if t in tablas], mysql)
    print(f'  Respaldo guardado en: {respaldo}', flush=True)
    anterior = 'descripcion'
    with engine.begin() as conexion:
        for columna in ('imagen', 'audio_mazahua', 'audio_espanol'):
            if columna not in columnas:
                despues = f' AFTER {anterior}' if mysql else ''
                conexion.execute(text(f'ALTER TABLE tarjetas ADD COLUMN {columna} VARCHAR(255) NULL{despues}'))
            anterior = columna
        if 'imagenes' in tablas:
            conexion.execute(text('UPDATE tarjetas SET imagen = (SELECT i.ruta FROM imagenes i WHERE i.tarjeta_id = tarjetas.id) '
                                  'WHERE imagen IS NULL'))
        if 'audios' in tablas:
            for idioma in ('mazahua', 'espanol'):
                conexion.execute(text(f"UPDATE tarjetas SET audio_{idioma} = (SELECT a.ruta FROM audios a WHERE "
                                      f"a.tarjeta_id = tarjetas.id AND a.idioma = '{idioma}') WHERE audio_{idioma} IS NULL"))
        if mysql and 'uid_rfid' in columnas:
            conexion.execute(text('ALTER TABLE tarjetas MODIFY COLUMN uid_rfid VARCHAR(40) NULL AFTER audio_espanol'))
        claves_foraneas(conexion, False, mysql)
        for tabla in ('audios', 'imagenes'):
            if tabla in tablas:
                conexion.execute(text(f'DROP TABLE {tabla}'))
        claves_foraneas(conexion, True, mysql)
    with engine.connect() as conexion:
        total = conexion.execute(text('SELECT COUNT(*) FROM tarjetas')).scalar()
    print(f'  Listo: {total} tarjetas con su imagen y audios en una sola tabla.', flush=True)
    return total


def asegurar_columnas(engine):
    """Agrega columnas nuevas a tablas ya existentes (sin tocar sus datos)."""
    insp = inspect(engine)
    if 'participantes' in insp.get_table_names():
        columnas = {c['name'] for c in insp.get_columns('participantes')}
        if 'avatar' not in columnas:
            with engine.begin() as conexion:
                conexion.execute(text('ALTER TABLE participantes ADD COLUMN avatar VARCHAR(60) NULL'))
            print('Listo: se agregó la columna avatar a participantes.')
    if 'partidas' in insp.get_table_names():
        if 'anfitrion' not in {c['name'] for c in insp.get_columns('partidas')}:
            with engine.begin() as conexion:
                conexion.execute(text('ALTER TABLE partidas ADD COLUMN anfitrion VARCHAR(64) NULL'))
            print('Listo: se agregó la columna anfitrion a partidas (partidas entre amigos).')
