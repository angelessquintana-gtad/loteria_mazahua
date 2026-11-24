"""Puente USB/Serial: lee el UID del ESP32 (COM13) y lo envía a FastAPI.

El ESP32 no necesita Wi-Fi: solo manda líneas como "UID:C9 72 1A 10" por el
cable USB. Este programa las recibe, las publica en la API y la página del
panel las muestra automáticamente.

Uso:
    python serial_bridge.py
"""

import json
import os
import re
import sys
import time
from getpass import getpass
from http.cookiejar import CookieJar
from threading import Event
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPCookieProcessor

try:
    import serial
    from serial.tools import list_ports
except ImportError:
    print("Falta pyserial. Instálalo con: pip install -r requirements.txt")
    sys.exit(1)

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

PUERTO = os.getenv("SERIAL_PORT", "COM13").strip()
BAUDIOS = int(os.getenv("SERIAL_BAUD", "115200"))
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").strip().rstrip("/")
URL_UID = f"{API_URL}/api/esp32/uid"
URL_HEARTBEAT = f"{API_URL}/api/esp32/heartbeat"
HEARTBEAT_SEGUNDOS = 5.0
HTTP_TIMEOUT = 3.0
http = build_opener(HTTPCookieProcessor(CookieJar()))
csrf_token = ''

def normalizar_uid(valor: str) -> str:
    partes = re.split(r"[\s:\-]+", valor.strip())
    return " ".join(parte.upper() for parte in partes if parte)


def extraer_uid(linea: str) -> str | None:
    # Protocolo actual y mensajes de lectura del firmware anterior.
    valor = linea.strip()
    if valor.upper().startswith("UID:"):
        valor = valor[4:].strip()
    elif valor.lower().startswith("tarjeta detectada:"):
        valor = valor.split(":", 1)[1].strip()
    if re.fullmatch(r"[0-9a-fA-F]{2}(?:[\s:-]+[0-9a-fA-F]{2})+", valor):
        uid = normalizar_uid(valor)
        if len(uid.split()) in {4, 7, 10}:
            return uid
    return None


def enviar_json(url: str, datos: dict, timeout: float = HTTP_TIMEOUT) -> dict:
    cuerpo = json.dumps(datos).encode("utf-8")
    peticion = Request(url, data=cuerpo, headers={"Content-Type": "application/json", 'X-CSRF-Token': csrf_token}, method="POST")
    with http.open(peticion, timeout=timeout) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def autenticar_api():
    global csrf_token
    usuario = input('Usuario docente: ').strip()
    password = getpass('Contraseña docente: ')
    try:
        resultado = enviar_json(f'{API_URL}/api/auth/login', {'usuario': usuario, 'password': password}, timeout=10)
        csrf_token = resultado['csrf_token']
    except (URLError, HTTPError, OSError, ValueError, KeyError):
        raise SystemExit('No se pudo autenticar el puente. Verifica la cuenta y que FastAPI esté activo.')


def enviar_uid(uid: str) -> bool:
    for intento in range(3):
        try:
            respuesta = enviar_json(URL_UID, {"uid": uid})
            detalle = " (ya registrada)" if respuesta.get("registrada") else ""
            print(f"  UID {uid} enviado a la API{detalle}")
            return True
        except (URLError, HTTPError, TimeoutError, OSError, ValueError) as error:
            if intento == 2:
                print(f"  No se pudo enviar el UID {uid}: {error}")
                print(f"  Verifica que FastAPI esté corriendo en {API_URL}")
                return False
            time.sleep(0.5)
    return False


def latido() -> bool:
    try:
        enviar_json(URL_HEARTBEAT, {"puerto": PUERTO}, timeout=1.5)
        return True
    except (URLError, HTTPError, TimeoutError, OSError, ValueError):
        return False


def mostrar_puertos() -> None:
    puertos = list(list_ports.comports())
    if not puertos:
        print("  No se detectó ningún puerto COM. Conecta el ESP32 por USB.")
        return
    print("  Puertos disponibles:")
    for puerto in puertos:
        print(f"    {puerto.device} - {puerto.description}")
    print(f"  Si tu ESP32 usa otro puerto, cambia SERIAL_PORT en .env (actual: {PUERTO}).")


def main(stop_event=None, uid_callback=None, status_callback=None) -> None:
    if uid_callback is None:
        autenticar_api()
    stop_event = stop_event or Event()
    print("Puente USB/Serial RFID -> FastAPI")
    print(f"Puerto: {PUERTO} @ {BAUDIOS} baudios")
    print(f"API:    {API_URL}")
    print("Cierra el Monitor Serie de Arduino para liberar el puerto.")
    print("Pulsa Ctrl+C para detener.\n")

    ultimo_latido = 0.0
    api_estado = None

    while not stop_event.is_set():
        try:
            with serial.Serial(PUERTO, BAUDIOS, timeout=1) as conexion:
                print(f"Conectado a {PUERTO}. Esperando tarjetas...\n")
                ultimo_latido = 0.0

                while not stop_event.is_set():
                    ahora = time.monotonic()
                    if ahora - ultimo_latido >= HEARTBEAT_SEGUNDOS:
                        ultimo_latido = ahora
                        if status_callback:
                            status_callback(True, PUERTO, "Puerto USB abierto")
                            conectado = True
                        else:
                            conectado = latido()
                        if conectado != api_estado:
                            api_estado = conectado
                            if conectado:
                                print("API conectada.")
                            else:
                                print(f"API no responde en {API_URL}; se reintentará al leer una tarjeta.")

                    linea = conexion.readline().decode("utf-8", errors="replace").strip()
                    if not linea:
                        continue

                    if linea.startswith(("READY:", "INFO:", "ERROR:")):
                        print("  " + linea.split(":", 1)[1].strip())
                        continue

                    uid = extraer_uid(linea)
                    if uid:
                        print(f"Tarjeta detectada: {uid}")
                        if uid_callback:
                            uid_callback(uid)
                        else:
                            enviar_uid(uid)
        except serial.SerialException as error:
            if status_callback:
                status_callback(False, PUERTO, f"No se puede abrir {PUERTO}. Cierra el Monitor Serie y verifica el cable USB. {error}")
            print(f"No se pudo abrir {PUERTO}: {error}")
            if isinstance(error.__cause__, PermissionError) or "denegado" in str(error).lower() or "permission" in str(error).lower():
                print("  El puerto está ocupado: cierra el Monitor Serie de Arduino IDE (o cualquier otro programa que use el COM).")
            mostrar_puertos()
            print("Reintentando en 4 segundos... (Ctrl+C para salir)\n")
            stop_event.wait(4)
        except KeyboardInterrupt:
            print("\nLector detenido.")
            return


if __name__ == "__main__":
    main()
