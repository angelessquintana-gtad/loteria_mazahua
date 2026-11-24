/* Reproductor persistente: las actualizaciones de la sala no interrumpen el audio. */
class SecuenciaAudio {
  static async habilitarElementos(audios) {
    // Una muestra silenciosa válida permite activar ambos elementos durante el clic.
    const buffer = new ArrayBuffer(844), view = new DataView(buffer);
    const texto = (pos, valor) => [...valor].forEach((c, i) => view.setUint8(pos + i, c.charCodeAt(0)));
    texto(0, 'RIFF'); view.setUint32(4, 836, true); texto(8, 'WAVE'); texto(12, 'fmt ');
    view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
    view.setUint32(24, 8000, true); view.setUint32(28, 16000, true);
    view.setUint16(32, 2, true); view.setUint16(34, 16, true); texto(36, 'data'); view.setUint32(40, 800, true);
    const url = URL.createObjectURL(new Blob([buffer], {type: 'audio/wav'}));
    const anteriores = audios.map(audio => audio.getAttribute('src'));
    try {
      // Ambas llamadas a play ocurren antes del primer await: gesto del usuario.
      const intentos = audios.map(audio => {
        audio.pause(); audio.src = url;
        return audio.play();
      });
      const resultados = await Promise.allSettled(intentos);
      const fallo = resultados.find(r => r.status === 'rejected');
      if (fallo) throw fallo.reason;
    } finally {
      audios.forEach((audio, i) => {
        audio.pause(); audio.currentTime = 0; audio.removeAttribute('src');
        if (anteriores[i]) audio.src = anteriores[i];
        audio.load();
      });
      URL.revokeObjectURL(url);
    }
  }
  async habilitar() {
    this.detener();
    await SecuenciaAudio.habilitarElementos([this.mazahua, this.espanol]);
    this.notificar('Sonido activado. Las siguientes lecturas se reproducirán automáticamente si el navegador lo permite.');
    if (this.carta) this.programar(this.carta, 1500, this.alTerminar);
  }
  constructor(notificar = () => {}) {
    this.notificar = notificar;
    this.mazahua = new Audio();
    this.espanol = new Audio();
    this.version = 0;
    this.timer = null;
    this.watchdog = null;
    this.carta = null;
  }
  detener() {
    this.version++;
    globalThis.callarEspanol?.();
    clearTimeout(this.timer);
    clearInterval(this.watchdog);
    this.watchdog = null;
    for (const audio of [this.mazahua, this.espanol]) {
      audio.onended = null;
      audio.onerror = null;
      audio.pause();
      audio.currentTime = 0;
    }
  }
  programar(carta, demora = 1500, alTerminar = () => {}) {
    this.detener();
    this.alTerminar = alTerminar;
    this.carta = carta;
    for (const [audio, url] of [[this.mazahua, carta?.audio_mazahua_url], [this.espanol, carta?.audio_espanol_url]]) {
      audio.removeAttribute('src');
      if (url) { audio.src = url; audio.preload = 'auto'; audio.load(); }
    }
    if (!carta?.audio_mazahua_url && !carta?.audio_espanol_url) {
      this.notificar('Esta carta no tiene audios registrados.');
      this.alTerminar();
      return;
    }
    const version = this.version;
    this.notificar(demora ? 'El audio comenzará en 1.5 segundos…' : 'Iniciando audio…');
    this.timer = setTimeout(() => this.reproducir(version, 0), demora);
  }
  async reproducir(version, indice) {
    if (version !== this.version) return;
    const audio = [this.mazahua, this.espanol][indice];
    if (!audio) { this.notificar('Reproducción terminada.'); this.alTerminar?.(); return; }
    if (!audio.getAttribute('src')) {
      // Sin archivo en español: se pronuncia con la voz en español del navegador (voz-espanol.js).
      if (indice === 1 && this.carta?.traduccion_espanol && globalThis.hablarEspanol) {
        this.notificar('Pronunciando en español…');
        await globalThis.hablarEspanol(this.carta.traduccion_espanol);
        if (version === this.version) { this.notificar('Reproducción terminada.'); this.alTerminar?.(); }
        return;
      }
      this.notificar(indice === 0 ? 'No hay audio mazahua para esta carta.' : 'No hay audio español para esta carta.');
      if (indice === 0) await this.reproducir(version, 1);
      else this.alTerminar?.();
      return;
    }
    let terminado = false, ultimaPosicion = -1, sinAvance = 0;
    const limpiar = () => {
      clearInterval(this.watchdog); this.watchdog = null;
      audio.onended = null; audio.onerror = null;
    };
    const siguiente = () => {
      if (terminado || version !== this.version) return;
      terminado = true; limpiar();
      this.reproducir(version, indice + 1);
    };
    clearInterval(this.watchdog);
    this.watchdog = setInterval(() => {
      if (version !== this.version || terminado) return;
      if (audio.currentTime > ultimaPosicion + 0.01) { ultimaPosicion = audio.currentTime; sinAvance = 0; }
      else if (++sinAvance >= 15) {
        this.notificar('El audio dejó de avanzar. Se continuará con las siguientes lecturas.');
        audio.pause(); siguiente();
      }
    }, 1000);
    audio.onended = siguiente;
    audio.onerror = () => {
      if (version !== this.version) return;
      this.notificar(`No se pudo cargar el audio ${indice === 0 ? 'mazahua' : 'español'}. Revisa el archivo registrado.`);
      siguiente();
    };
    try {
      await audio.play();
      if (version === this.version && !terminado) this.notificar(indice === 0 ? 'Reproduciendo en mazahua…' : 'Reproduciendo en español…');
    } catch (error) {
      if (version !== this.version) return;
      if (terminado) return;
      if (error.name === 'NotAllowedError') {
        terminado = true; limpiar();
        this.notificar('El navegador bloqueó el audio. Pulsa «Activar sonido»; las siguientes lecturas seguirán procesándose.');
        this.alTerminar?.();
      } else {
        this.notificar('No se pudo reproducir el audio. Revisa el archivo registrado.');
        siguiente();
      }
    }
  }
  repetir() {
    // play() se invoca dentro del clic para conservar la activación del usuario.
    if (!this.carta) return;
    this.detener();
    this.reproducir(this.version, 0);
  }
}
window.SecuenciaAudio = SecuenciaAudio;
