// Dinámica básica de la lotería en el navegador. Consume GET /api/vocabulario.
(() => {
  const $ = id => document.getElementById(id);
  const TAM = 16;
  let cartas = [], mazo = [], salidas = [], tablero = [], marcadas = new Set(), terminado = false, temporizador = null, recien = null;
  const barajar = lista => { const a = [...lista]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
  const nodo = (tag, texto, clase) => { const e = document.createElement(tag); if (texto) e.textContent = texto; if (clase) e.className = clase; return e; };
  const mensaje = (texto, error = false) => { $('mensajeSim').textContent = texto; $('mensajeSim').className = 'sim-mensaje' + (error ? ' error' : ''); };

  function detenerAudio() { window.callarEspanol?.(); for (const id of ['audioMazahua', 'audioEspanol']) { const a = $(id); a.pause(); a.onended = null; } }
  function reproducir(carta) {
    detenerAudio();
    const maz = $('audioMazahua'), esp = $('audioEspanol');
    const tocar = (audio, url) => { if (!url) return Promise.reject(); audio.src = url; audio.currentTime = 0; return audio.play(); };
    // Si no hay archivo en español, se usa la voz en español del navegador.
    const espanol = () => carta.audio_espanol_url ? tocar(esp, carta.audio_espanol_url).catch(() => {}) : window.hablarEspanol?.(carta.traduccion_espanol);
    if (carta.audio_mazahua_url) { maz.onended = () => setTimeout(espanol, 400); tocar(maz, carta.audio_mazahua_url).catch(() => mensaje('El navegador bloqueó el audio. Pulsa “Repetir audio”.', true)); }
    else espanol();
  }

  function dibujarCarta(carta) {
    const caja = $('cartaActual');
    const img = nodo('img'); window.respaldoImagen?.(img, carta); img.src = carta.imagen_url; img.alt = carta.traduccion_espanol;
    caja.replaceChildren(img, nodo('p', carta.palabra_mazahua, 'sim-mazahua'), nodo('p', carta.traduccion_espanol, 'sim-espanol'));
    caja.classList.remove('volteo'); void caja.offsetWidth; caja.classList.add('volteo');
  }
  function dibujarTablero() {
    $('tablero').replaceChildren(...tablero.map(carta => {
      const salio = salidas.some(x => x.id === carta.id), marcada = marcadas.has(carta.id);
      const b = nodo('button', null, 'sim-casilla' + (marcada ? ' marcada' : '') + (recien === carta.id ? ' recien' : '') + (salio && !marcada ? ' disponible' : ''));
      // Solo se puede tocar una carta que ya salió (se pinta de verde) o quitar un frijol ya puesto.
      b.disabled = terminado || (!salio && !marcada);
      b.type = 'button'; b.setAttribute('aria-pressed', marcadas.has(carta.id)); b.title = `${carta.palabra_mazahua} · ${carta.traduccion_espanol}`; b.setAttribute('aria-label', `${carta.palabra_mazahua} (${carta.traduccion_espanol})`);
      const img = nodo('img'); window.respaldoImagen?.(img, carta); img.src = carta.miniatura_url || carta.imagen_url; img.alt = carta.palabra_mazahua; img.decoding = 'async';
      b.append(img, nodo('span', carta.palabra_mazahua), nodo('small', carta.traduccion_espanol));
      b.onclick = () => marcar(carta, b);
      return b;
    }));
    $('tablero').setAttribute('aria-busy', 'false');
    if (!$('tablero').style.width && innerWidth > 860) requestAnimationFrame(ajustar);
  }
  // El tablero se achica para caber en la pantalla y el conjunto (panel + tablero) queda centrado.
  function ajustar() {
    const capa = document.querySelector('.sim-layout'), t = $('tablero');
    if (!capa || !window.ajustarTablero) return;
    capa.style.maxWidth = '';
    // En celular el tablero ocupa todo el ancho y la carta cantada queda fija arriba al desplazarse.
    if (innerWidth <= 860) { t.style.width = ''; return; }
    window.ajustarTablero(t);
    if (t.style.width && innerWidth > 860) {
      const panel = document.querySelector('.sim-panel').getBoundingClientRect().width;
      capa.style.maxWidth = Math.ceil(panel + 26 + t.getBoundingClientRect().width) + 'px';
      capa.style.marginInline = 'auto';
    }
  }
  let espera = null;
  window.addEventListener('resize', () => { clearTimeout(espera); espera = setTimeout(ajustar, 150); });
  function actualizarContador() { $('contadorCartas').textContent = `Cartas cantadas: ${salidas.length} de ${mazo.length + salidas.length} · Marcadas: ${marcadas.size} de ${tablero.length}`; }

  function marcar(carta, boton) {
    if (terminado) return;
    if (marcadas.has(carta.id)) { marcadas.delete(carta.id); dibujarTablero(); actualizarContador(); return; }
    if (!salidas.some(s => s.id === carta.id)) {
      boton.classList.remove('error'); void boton.offsetWidth; boton.classList.add('error');
      mensaje(`“${carta.palabra_mazahua}” todavía no ha salido.`, true); return;
    }
    marcadas.add(carta.id); recien = carta.id; dibujarTablero(); recien = null; actualizarContador(); mensaje(`Marcaste “${carta.palabra_mazahua}” (${carta.traduccion_espanol}).`);
    if (marcadas.size === tablero.length) {
      terminado = true; detenerAuto(); $('avisoGanaste').hidden = false; $('btnSacar').disabled = true;
      mensaje(`¡Lotería! Ganaste con ${salidas.length} cartas cantadas.`);
      window.sonidoVictoria?.(); window.lanzarConfeti?.(140);
    }
  }
  function sacar() {
    if (terminado) return;
    if (!mazo.length) { mensaje('Ya salieron todas las cartas.'); detenerAuto(); $('btnSacar').disabled = true; return; }
    const carta = mazo.shift(); salidas.push(carta);
    dibujarCarta(carta); dibujarTablero(); $('btnRepetir').disabled = false;
    const mini = nodo('img'); window.respaldoImagen?.(mini, carta); mini.src = carta.miniatura_url || carta.imagen_url; mini.alt = carta.traduccion_espanol; mini.title = `${carta.palabra_mazahua} · ${carta.traduccion_espanol}`;
    $('historial').prepend(mini);
    actualizarContador();
    if (mazo[0]) new Image().src = mazo[0].imagen_url; // precarga la siguiente carta para que aparezca al instante
    mensaje(tablero.some(c => c.id === carta.id) ? '¡Esta carta está en tu tablero! Márcala.' : 'Esta carta no está en tu tablero.');
    if ($('optAudio').checked) reproducir(carta);
  }
  function detenerAuto() { clearInterval(temporizador); temporizador = null; $('optAuto').checked = false; }
  function nueva() {
    detenerAuto(); detenerAudio();
    tablero = barajar(cartas).slice(0, TAM); mazo = barajar(cartas); salidas = []; marcadas = new Set(); terminado = false;
    $('historial').replaceChildren(); $('avisoGanaste').hidden = true; $('btnSacar').disabled = false; $('btnRepetir').disabled = true;
    $('cartaActual').replaceChildren(nodo('p', 'Pulsa “Sacar carta” para comenzar.', 'sim-vacia'));
    dibujarTablero(); actualizarContador(); mensaje('');
  }
  async function cargar() {
    try {
      const r = await fetch('/api/vocabulario', {cache: 'no-store'});
      if (!r.ok) throw Error('No se pudieron cargar las cartas desde la API.');
      cartas = (await r.json()).filter(c => c.imagen_url);
      if (cartas.length < TAM) { $('contadorCartas').textContent = `Se necesitan al menos ${TAM} cartas registradas; hay ${cartas.length}.`; mensaje('Registra más cartas en Administración o ejecuta cargar_datos_demo.py.', true); return; }
      $('btnNueva').disabled = false; nueva();
      if (mazo[0]) new Image().src = mazo[0].imagen_url;
    } catch (error) { $('contadorCartas').textContent = error.message; }
  }
  $('btnSacar').onclick = sacar;
  $('btnNueva').onclick = nueva;
  $('btnRepetir').onclick = () => { const c = salidas[salidas.length - 1]; if (c) reproducir(c); };
  $('optAuto').onchange = e => { clearInterval(temporizador); temporizador = null; if (e.target.checked && !terminado) { sacar(); temporizador = setInterval(sacar, 8000); } };
  cargar();
})();
