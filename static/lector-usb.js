/* Cada página docente posee su puerto y envía lecturas solo a su propia sala. */
class LectorUSB {
  constructor(onUid, onStatus, onLine = () => {}) {
    this.onUid = onUid; this.onStatus = onStatus;
    this.onLine = onLine;
    this.port = null; this.reader = null; this.running = false; this.done = null;
    this.lastUid = ''; this.lastTime = 0;
    this.heartbeatSeen = false; this.lastHeartbeat = 0; this.heartbeatTimer = null; this.lastHeartbeatLog = 0;
  }
  static extraer(line) {
    // El arranque del ESP32 puede anteponer bytes ilegibles al primer UID.
    // Aceptar ese ruido solo si existe un marcador explícito y un UID completo.
    const marked = line.match(/(?:UID:|Tarjeta detectada:)\s*([0-9a-f]{2}(?:[\s:-]+[0-9a-f]{2})+)\s*$/i);
    const value = marked ? marked[1] : line.trim();
    if (!/^[0-9a-f]{2}(?:[\s:-]+[0-9a-f]{2})+$/i.test(value)) return null;
    const bytes = value.split(/[\s:-]+/);
    return [4, 7, 10].includes(bytes.length) ? bytes.join(' ').toUpperCase() : null;
  }
  async conectar() {
    if (this.port) return;
    if (!window.isSecureContext) throw Error('Abre la página con HTTPS para conectar el lector USB.');
    if (!navigator.serial) throw Error('Para el lector USB utiliza Chrome o Edge en una computadora.');
    const port = await navigator.serial.requestPort();
    try { await port.open({baudRate: 115200}); }
    catch (error) {
      throw Error('El puerto no está disponible. Desconecta el lector en las otras pestañas (docente o administración) y cierra el Monitor Serie o el puente serial. Selecciona USB-SERIAL CH340 o el adaptador USB del ESP32, no un puerto Bluetooth. Detalle: ' + error.message);
    }
    // El CH340 puede dejar las líneas de auto-reset activas al abrir el puerto.
    // Liberarlas permite que el ESP32 ejecute el firmware en vez de quedar detenido.
    try {
      await port.setSignals({dataTerminalReady: false, requestToSend: false});
    } catch {
      // Algunos adaptadores no implementan estas señales; la lectura sigue disponible.
    }
    this.port = port; this.running = true;
    this.lastUid = ''; this.lastTime = 0;
    this.heartbeatSeen = false; this.lastHeartbeat = 0; this.lastHeartbeatLog = 0;
    this.onStatus('Lector conectado. Acerca una tarjeta.', true);
    this.done = this.leer();
  }
  async leer() {
    let fallo = '';
    const port = this.port;
    try {
      while (this.running) {
        const decoder = new TextDecoder(); let buffer = '', interrumpido = false;
        try {
          if (!port.readable) throw Error('El puerto dejó de estar disponible');
          this.reader = port.readable.getReader();
          this.heartbeatTimer = setInterval(() => {
            if (this.running && this.heartbeatSeen && Date.now() - this.lastHeartbeat > 18000) {
              interrumpido = true;
              this.reader?.cancel().catch(() => {});
            }
          }, 3000);
          while (this.running) {
            const {value, done} = await this.reader.read();
            if (done) { interrumpido = true; break; }
            buffer += decoder.decode(value, {stream: true});
            const lines = buffer.split(/\r?\n/); buffer = lines.pop().slice(-512);
            for (const line of lines) {
          if (line.trim() === 'STATUS:RFID OK' || line.startsWith('STATUS:RC522')) {
            this.heartbeatSeen = true; this.lastHeartbeat = Date.now();
            if (line.startsWith('STATUS:RC522') || this.lastHeartbeat - this.lastHeartbeatLog >= 30000) {
              this.lastHeartbeatLog = this.lastHeartbeat;
              try { this.onLine(line); } catch {}
            }
            if (line.startsWith('STATUS:RC522')) this.onStatus('El RC522 no responde; el ESP32 está intentando recuperarlo.', true);
            continue;
          }
          if (line.trim()) {
            try { this.onLine(line); }
            catch (error) { this.onStatus('Datos USB recibidos; falló el diagnóstico del panel: ' + error.message, true); }
          }
          if (line.startsWith('ERROR:')) {
            this.onStatus(`USB conectado, pero el ESP32 informa: ${line.slice(6).trim()}`, true);
          }
          const uid = LectorUSB.extraer(line);
          if (!uid) continue;
          const now = Date.now();
          if (uid === this.lastUid && now - this.lastTime < 1800) continue;
          this.lastUid = uid; this.lastTime = now;
          this.onStatus(`UID recibido: ${uid}`, true);
          // Un error del panel o de la API no debe cerrar el puerto físico.
          try {
            Promise.resolve(this.onUid(uid)).catch(error => {
              this.onStatus(`UID recibido: ${uid}. Error al procesarlo: ${error.message}`, true);
            });
          } catch (error) {
            this.onStatus(`UID recibido: ${uid}. Error al procesarlo: ${error.message}`, true);
          }
            }
          }
        } catch (error) {
          if (this.running) { interrumpido = true; fallo = error.message; }
        } finally {
          clearInterval(this.heartbeatTimer); this.heartbeatTimer = null;
          try { this.reader?.releaseLock(); } catch {}
          this.reader = null;
        }
        if (!this.running || !interrumpido) break;
        this.onStatus('Se interrumpió la lectura. Reconectando el lector automáticamente…', false);
        try { await port.close(); } catch {}
        let reconectado = false;
        for (let intento = 0; this.running && intento < 5; intento++) {
          await new Promise(resolve => setTimeout(resolve, 1000));
          if (!this.running) break;
          try {
            await port.open({baudRate: 115200});
            try { await port.setSignals({dataTerminalReady: false, requestToSend: false}); } catch {}
            reconectado = true; this.heartbeatSeen = false; this.lastHeartbeat = 0;
            this.lastUid = ''; this.lastTime = 0; fallo = '';
            this.onStatus('Lector reconectado automáticamente. Acerca una tarjeta.', true);
            break;
          } catch (error) { fallo = error.message; }
        }
        if (!reconectado) break;
      }
    } finally {
      clearInterval(this.heartbeatTimer); this.heartbeatTimer = null;
      this.reader = null; this.running = false;
      try { await port?.close(); } catch {}
      this.port = null;
      this.onStatus(fallo ? 'No se pudo recuperar el lector USB: ' + fallo + '. Comprueba el cable y vuelve a conectarlo.' : 'Lector desconectado. Puedes volver a conectarlo.', false);
    }
  }
  async desconectar() {
    this.running = false;
    await this.reader?.cancel();
    await this.done;
  }
}
window.LectorUSB = LectorUSB;
