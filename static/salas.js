'use strict';
const $ = id => document.getElementById(id);
const teacher = document.body.dataset.role === 'docente';
const storageKey = teacher ? 'mazahua-docente' : 'mazahua-estudiante';
let session = null, socket, retry, stopped = false, currentRoom = null;
let audioKey = null, audioDone = null, processing = false, queueVersion = 0;
let heartbeatBusy = false;
let highlightedAnnouncement = null;
let shownEnd = null;
const pendingScans = [];
const game = $('game');
const narration = teacher ? new window.SecuenciaAudio(text => { $('audioStatus').textContent = text; }) : null;
try { session = JSON.parse(sessionStorage.getItem(storageKey)); } catch {}
// Partidas creadas con la versión anterior guardaban una clave; ahora el docente se identifica con su sesión.
if (teacher && session?.codigo && session.token !== 'docente') session.token = 'docente';
if (!teacher) {
  const scannedCode = new URLSearchParams(location.search).get('codigo')?.toUpperCase();
  if (scannedCode && session?.codigo && scannedCode !== session.codigo) session = null;
}

function node(tag, text, cls) {
  const n = document.createElement(tag); if (text) n.textContent = text; if (cls) n.className = cls; return n;
}
function avatarDe(persona, tam = 32) {
  if (window.Avatar) return window.Avatar.nodo(persona?.avatar || window.Avatar.PREDETERMINADO, tam, persona?.nombre || '');
  return node('span', (persona?.nombre || '?').slice(0, 1).toLocaleUpperCase(), 'avatar');
}
let ultimaCartaVista = null, recienMarcada = null;
const vistosEnSala = new Set();
function mostrarReaccion(datos) {
  let capa = document.querySelector('.capa-reacciones');
  if (!capa) { capa = node('div', null, 'capa-reacciones'); capa.setAttribute('aria-hidden', 'true'); document.body.append(capa); }
  const burbuja = node('div', null, 'reaccion-flotante');
  burbuja.style.left = (8 + Math.random() * 78) + '%';
  burbuja.style.setProperty('--deriva', (Math.random() * 80 - 40) + 'px');
  burbuja.append(avatarDe(datos, 34), node('span', datos.emoji, 'emoji'), node('span', datos.nombre));
  capa.append(burbuja); setTimeout(() => burbuja.remove(), 4300);
}
function enviarReaccion(emoji, boton) {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;
  socket.send(JSON.stringify({reaccion: emoji}));
  document.querySelectorAll('.barra-reacciones button').forEach(b => { b.disabled = true; });
  setTimeout(() => document.querySelectorAll('.barra-reacciones button').forEach(b => { b.disabled = false; }), 1200);
  boton?.animate?.([{transform:'scale(1.4)'},{transform:'scale(1)'}], {duration:300});
}
function proyectar(activar) {
  document.body.classList.toggle('proyector', activar);
  if (activar && !document.fullscreenElement) document.documentElement.requestFullscreen?.().catch(() => {});
  if (!activar && document.fullscreenElement) document.exitFullscreen?.().catch(() => {});
  if (activar && !document.querySelector('.salir-proyector')) {
    const salir = node('button', '✕ Salir del modo proyector', 'salir-proyector'); salir.type = 'button';
    salir.onclick = () => proyectar(false); document.body.append(salir);
  }
}
document.addEventListener?.('fullscreenchange', () => { if (!document.fullscreenElement) document.body.classList.remove('proyector'); });
document.addEventListener?.('keydown', e => { if (e.key === 'Escape') document.body.classList.remove('proyector'); });
function message(text, success = false) { $('message').textContent = text; $('message').classList.toggle('success', success); }
function showNotice(title, description, buttonText = 'Entendido', avatar = null) {
  let dialog = $('gameNotice');
  if (!dialog) {
    dialog = node('dialog', null, 'game-notice'); dialog.id = 'gameNotice';
    dialog.setAttribute('aria-labelledby', 'noticeTitle');
    dialog.setAttribute('aria-describedby', 'noticeDescription');
    const icon = node('span', '✿', 'notice-icon'); icon.setAttribute('aria-hidden', 'true');
    const heading = node('h2'); heading.id = 'noticeTitle';
    const text = node('p'); text.id = 'noticeDescription';
    const button = node('button', buttonText, 'notice-button'); button.type = 'button';
    button.onclick = () => dialog.close();
    dialog.append(icon, heading, text, button); document.body.append(dialog);
  }
  $('noticeTitle').textContent = title; $('noticeDescription').textContent = description;
  dialog.querySelector('.avatar-burbuja')?.remove?.();
  if (avatar) dialog.querySelector('.notice-icon').after(avatarDe({avatar}, 96));
  dialog.querySelector('button').textContent = buttonText;
  if (!dialog.open) dialog.showModal();
}
function save() { sessionStorage.setItem(storageKey, JSON.stringify(session)); }
async function heartbeat() {
  if (!teacher || !session?.codigo || heartbeatBusy || currentRoom?.estado === 'finalizada') return;
  heartbeatBusy = true;
  try {
    const result = await request(`/api/partidas/${session.codigo}/latido`, {});
    if (result.estado === 'finalizada' && currentRoom) render({...currentRoom, estado: 'finalizada', cierre_motivo: result.cierre_motivo});
  } catch (error) { $('connection').textContent = 'No se pudo renovar la sesión docente: ' + error.message; }
  finally { heartbeatBusy = false; }
}
async function request(path, data) {
  let response;
  try { response = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)}); }
  catch { throw Error('No se pudo conectar con el servidor. Revisa tu conexión e intenta de nuevo.'); }
  let result;
  try { result = await response.json(); } catch { throw Error('El servidor no respondió correctamente. Intenta de nuevo.'); }
  if (!response.ok) throw Error(typeof result.detail === 'string' ? result.detail : 'Revisa los datos e intenta de nuevo.');
  return result;
}
async function busy(button, operation) {
  button.disabled = true; message('');
  try { await operation(); } catch (e) { message(e.message); }
  finally { button.disabled = false; }
}

function announcedCard(room) {
  const panel = node('article', null, 'announced-panel');
  const card = room.ultima_carta;
  if (!card) {
    const empty = node('div', null, 'empty-card'); empty.append(node('span', '✳'), node('h3', 'La primera carta está por llegar'), node('p', 'El docente la anunciará con su lector.', 'note')); panel.append(empty); return panel;
  }
  const img = node('img', null, 'announced-image'); window.respaldoImagen?.(img, card); img.src = card.imagen_url; img.alt = card.traduccion_espanol;
  const claveCarta = `${room.codigo}:${room.secuencia ?? room.anunciadas.length}`;
  if (claveCarta !== ultimaCartaVista) { ultimaCartaVista = claveCarta; panel.classList.add('carta-nueva'); }
  const words = node('div');
  words.append(node('p', 'Carta anunciada', 'announced-label'), node('h3', card.palabra_mazahua), node('p', card.traduccion_espanol, 'translation'));
  words.append(node('p', teacher ? 'La imagen se comparte con todo el grupo. El audio se reproduce en esta computadora.' : '¿La tienes? Toca esa carta en tu tablero para poner tu ficha.', 'note'));
  words.append(node('p', `${room.anunciadas.length} ${room.anunciadas.length === 1 ? 'carta anunciada' : 'cartas anunciadas'}`, 'announced-total'));
  if (teacher) {
    const proyector = node('button', '📽 Proyectar en pantalla completa', 'boton-proyector'); proyector.type = 'button';
    proyector.onclick = () => proyectar(!document.body.classList.contains('proyector')); words.append(proyector);
  }
  if (!teacher) {
    // El alumno puede escuchar la pronunciación en su propio dispositivo (mazahua y luego español).
    const listen = node('button', '🔊 Escuchar pronunciación', 'secondary listen-button'); listen.type = 'button';
    listen.onclick = () => playCard(card); words.append(listen);
  }
  panel.append(img, words); return panel;
}
let studentAudio = null;
function playCard(card) {
  studentAudio?.pause(); window.callarEspanol?.();
  const spanish = () => card.audio_espanol_url ? new Audio(card.audio_espanol_url).play().catch(() => {}) : window.hablarEspanol?.(card.traduccion_espanol);
  if (!card.audio_mazahua_url) { spanish(); return; }
  studentAudio = new Audio(card.audio_mazahua_url);
  studentAudio.onended = () => setTimeout(spanish, 400);
  studentAudio.play().catch(() => message('Toca de nuevo el botón para escuchar.'));
}
function celebrateWinner(room) {
  if (!room.ganador) return;
  const key = `mazahua-celebracion:${room.codigo}:${room.ganador.id}`;
  try { if (sessionStorage.getItem(key)) return; sessionStorage.setItem(key, '1'); } catch {}
  window.sonidoVictoria?.();
  window.lanzarConfeti?.(120);
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const celebration = node('div', null, 'celebration');
  celebration.setAttribute('aria-hidden', 'true');
  for (let i = 0; i < 24; i++) {
    const piece = node('span', null, 'confetti');
    piece.style.setProperty('--x', `${(i * 37) % 100}%`);
    piece.style.setProperty('--delay', `${(i % 8) * 0.09}s`);
    piece.style.setProperty('--color', ['#e94c75', '#f2b24d', '#2f8b70', '#8b294e'][i % 4]);
    celebration.append(piece);
  }
  const dialog = $('gameNotice');
  (dialog?.open ? dialog : document.body).append(celebration);
  setTimeout(() => celebration.remove(), 4000);
}
function renderGame(room) {
  game.hidden = room.estado === 'esperando'; if (game.hidden) return;
  const content = [];
  if (room.ganador) {
    const winner = node('div', null, 'winner');
    winner.setAttribute('role', 'status');
    winner.append(avatarDe(room.ganador, 56), node('span', '¡Lotería!', 'winner-title'), node('span', 'Ganó '), node('strong', room.ganador.nombre, 'winner-name'));
    winner.style.gridColumn = '1 / -1'; content.push(winner);
  }
  content.push(announcedCard(room));
  if (teacher) {
    game.classList.add('teacher-game');
    const key = `${room.codigo}:${room.secuencia ?? room.anunciadas.length}`;
    if (room.estado !== 'en_curso') cancelQueue();
    else if (room.ultima_carta && audioKey !== key) {
      audioKey = key;
      const done = audioDone;
      narration.programar(room.ultima_carta, 250, () => { if (audioDone === done) audioDone = null; done?.(); });
    }
  } else if (room.tablero) {
    const panel = node('section', null, 'board-panel'), heading = node('div', null, 'board-heading');
    const titles = node('div'); titles.append(node('h2', 'Mi tablero'), node('p', 'Coloca un frijol en las cartas de tu tablero que ya fueron anunciadas.'));
    const contador = node('span', null, 'contador-frijoles');
    const frijol = node('img'); frijol.src = '/static/frijol.svg'; frijol.alt = '';
    contador.append(frijol, document.createTextNode(`${room.tablero.marcas.length} / 16`));
    contador.setAttribute('aria-label', `${room.tablero.marcas.length} de 16 frijoles colocados`);
    heading.append(titles, contador);
    const grid = node('div', null, 'board');
    const latestId = room.ultima_carta?.id;
    const announcementKey = latestId != null ? `${room.codigo}:${room.secuencia ?? latestId}` : null;
    const isNewAnnouncement = announcementKey !== null && announcementKey !== highlightedAnnouncement;
    for (const card of room.tablero.cartas) {
      const marked = room.tablero.marcas.includes(card.id);
      const announced = room.anunciadas.includes(card.id);
      const latest = card.id === latestId;
      const button = node('button', null, `tile${marked ? ' marked' : ''}${marked && card.id === recienMarcada ? ' recien' : ''}${latest ? ' latest-announcement' : ''}${latest && isNewAnnouncement ? ' announcement-flash' : ''}`);
      button.type = 'button'; button.setAttribute('aria-pressed', String(marked)); button.disabled = room.estado !== 'en_curso' || (!announced && !marked);
      button.setAttribute('aria-label', `${card.traduccion_espanol}: ${marked ? 'frijol colocado' : announced ? 'carta anunciada, puedes colocar un frijol' : 'aún no anunciada'}`);
      const img = node('img'); window.respaldoImagen?.(img, card); img.src = card.miniatura_url || card.imagen_url; img.decoding = 'async'; img.alt = card.traduccion_espanol;
      button.title = `${card.palabra_mazahua} · ${card.traduccion_espanol}`;
      button.append(img, node('span', card.palabra_mazahua), node('small', card.traduccion_espanol));
      button.onclick = () => busy(button, async () => {
        const result = await request(`/api/juego/${session.codigo}/marcar`, {token:session.token, tarjeta_id:card.id, marcada:!marked});
        recienMarcada = marked ? null : card.id;
        if (!marked) window.sonidoClic?.();
        if (currentRoom?.tablero && currentRoom.estado === 'en_curso') { currentRoom.tablero.marcas = result.marcas; renderGame(currentRoom); }
        recienMarcada = null;
      }); grid.append(button);
    }
    highlightedAnnouncement = announcementKey;
    const announced = room.tablero.cartas.filter(c => room.anunciadas.includes(c.id)).length;
    const progress = node('progress'); progress.max = 16; progress.value = room.tablero.marcas.length; progress.setAttribute('aria-label','Casillas marcadas');
    panel.append(heading, grid, node('p', `${room.tablero.marcas.length} de 16 cartas marcadas · ${announced} de tu tablero anunciadas`, 'board-progress'), progress, node('p', 'Ganas al marcar todo tu tablero, siempre que sus 16 cartas hayan sido anunciadas.', 'note'));
    if (room.estado === 'en_curso') {
      const barra = node('div', null, 'barra-reacciones'); barra.setAttribute('aria-label', 'Enviar una reacción al grupo');
      for (const [emoji, texto] of [['👏', 'Aplausos'], ['😄', 'Feliz'], ['🌽', 'Maíz'], ['❤️', 'Me encanta'], ['🎉', 'Fiesta'], ['🤔', 'Pensando']]) {
        const b = node('button', emoji); b.type = 'button'; b.title = texto; b.setAttribute('aria-label', 'Reacción: ' + texto);
        b.onclick = () => enviarReaccion(emoji, b); barra.append(b);
      }
      panel.append(barra);
    }
    if (room.estado === 'en_curso' && room.tablero.marcas.length === 16 && announced === 16) {
      const claim = node('button', '¡LOTERÍA!', 'claim claim-ready'); claim.type = 'button';
      claim.setAttribute('aria-label', '¡Lotería! Reclamar victoria');
      claim.onclick = () => busy(claim, async () => { const result = await request(`/api/juego/${session.codigo}/loteria`, {token:session.token}); render({...result, tablero:currentRoom.tablero}); }); panel.append(claim);
    }
    content.push(panel);
  }
  const anchoAnterior = game.querySelector?.('.board')?.style?.width;
  game.replaceChildren(...content);
  const tablero = game.querySelector?.('.board');
  if (tablero?.style) { if (anchoAnterior) tablero.style.width = anchoAnterior; else requestAnimationFrame(() => window.ajustarTablero?.(tablero)); }
}
const labels = {esperando:'Esperando', en_curso:'En curso', finalizada:'Finalizada'};
function render(room) {
  if (!room || !Array.isArray(room.participantes) || !Array.isArray(room.anunciadas)) { message('El servidor está ejecutando una versión anterior o envió datos incompletos. Reinicia el servidor y recarga la página.'); return false; }
  if (room.tablero && (!Array.isArray(room.tablero.cartas) || !Array.isArray(room.tablero.marcas))) { message('No se pudo cargar el tablero completo. Recarga la página.'); return false; }
  currentRoom = room;
  $('room').hidden = false; if (teacher) $('code').textContent = room.codigo;
  if ($('roomTitle') && room.nombre) $('roomTitle').textContent = room.nombre; $('state').textContent = labels[room.estado] || room.estado;
  $('count').textContent = `${room.participantes.length} / ${room.limite}`;
  $('people').replaceChildren(...room.participantes.map((p, i) => {
    const li = node('li', null, vistosEnSala.has(p.id) ? '' : 'nuevo'); vistosEnSala.add(p.id);
    li.style.setProperty('--i', String(i)); li.append(avatarDe(p, teacher ? 58 : 30), node('span', p.nombre)); return li;
  }));
  if (teacher) {
    let fila = document.querySelector?.('.fila-proyector');
    if (!fila && document.querySelector) { fila = node('div', null, 'fila-proyector'); fila.setAttribute('aria-hidden', 'true'); document.body.append(fila); }
    fila?.replaceChildren(...room.participantes.map(p => avatarDe(p, 54)));
  } else if (session) {
    let mio = document.getElementById('miAvatar');
    if (!mio) { mio = node('span', null, 'mi-avatar'); mio.id = 'miAvatar'; document.querySelector?.('#room .heading')?.prepend(mio); }
    if (mio.dataset && mio.dataset.codigo !== (session.avatar || '') + session.nombre) {
      mio.dataset.codigo = (session.avatar || '') + session.nombre;
      mio.replaceChildren(avatarDe({avatar: session.avatar, nombre: session.nombre}, 40));
      mio.title = session.nombre || '';
    }
  }
  $('phase').textContent = room.estado === 'esperando' ? (teacher ? 'Comparte el código. Inicia cuando tu grupo esté listo.' : 'Ya estás dentro. Espera a que tu docente inicie la partida.') : room.estado === 'en_curso' ? 'Partida en curso. Escucha las cartas y completa tu tablero.' : ['inactividad_docente','duracion_maxima'].includes(room.cierre_motivo) ? 'La partida caducó automáticamente. Pide al docente un código nuevo.' : 'La partida ha finalizado.';
  document.body.classList.toggle('playing', room.estado !== 'esperando');
  renderGame(room);
  if (room.estado === 'finalizada' && shownEnd !== room.codigo) {
    shownEnd = room.codigo;
    if (room.ganador) showNotice('¡Lotería!', `¡${room.ganador.nombre} ganó la partida!`, 'Ver resultado', room.ganador.avatar || window.Avatar?.PREDETERMINADO);
    else showNotice('Partida finalizada', ['inactividad_docente','duracion_maxima'].includes(room.cierre_motivo) ? 'Esta partida caducó. Pide al docente una nueva invitación para volver a jugar.' : 'La partida terminó. Gracias por jugar y compartir la lengua mazahua.', 'Entendido');
  }
  celebrateWinner(room);
  if (teacher) {
    $('invitationPanel').hidden = room.estado !== 'esperando';
    $('createForm').hidden = room.estado !== 'finalizada'; $('empty').hidden = room.participantes.length > 0;
    $('start').hidden = room.estado !== 'esperando'; $('start').disabled = !room.participantes.length;
    $('finish').hidden = room.estado === 'finalizada'; updateLink(room.codigo);
  } else { $('joinPanel').hidden = true; $('leave').hidden = room.estado !== 'finalizada'; }
  return true;
}
async function connect() {
  clearTimeout(retry); if (socket) { socket.onclose = null; socket.close(); }
  $('connection').textContent = 'Conectando con la partida…';
  // Con el frontend en Vercel, el WebSocket va directo al backend (Render); el docente usa un ticket breve.
  let base = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}`, primero = session.token;
  try {
    const r = await fetch(`/api/tiempo-real/${encodeURIComponent(session.codigo)}`, {cache:'no-store'});
    if (r.ok) { const d = await r.json(); if (d.ws) base = d.ws; if (teacher && d.ticket) primero = 'ticket:' + d.ticket; }
  } catch {}
  if (stopped) return;
  socket = new WebSocket(`${base}/ws/partidas/${encodeURIComponent(session.codigo)}`);
  socket.onopen = () => socket.send(primero);
  socket.onmessage = event => {
    try {
      const datos = JSON.parse(event.data);
      if (datos.tipo === 'reaccion') { mostrarReaccion(datos); return; }
      if (render(datos)) $('connection').textContent = 'Conectado · Recibiendo anuncios en vivo';
    } catch { message('No se pudo interpretar la actualización. Recarga la página.'); }
  };
  socket.onerror = () => { $('connection').textContent = 'No se pudo conectar con la partida.'; };
  socket.onclose = event => {
    if (stopped) return;
    if (currentRoom?.estado === 'finalizada') { $('connection').textContent = 'Partida finalizada · cierre guardado'; return; }
    if (event.code === 1008) { message('No se pudo recuperar esta partida. Vuelve a ingresar.'); sessionStorage.removeItem(storageKey); if (!teacher) $('resetSession').hidden = false; return; }
    $('connection').textContent = 'Conexión interrumpida. Reintentando…'; retry = setTimeout(connect,3000);
  };
}
let invitationCode = null;
async function updateLink(code) {
  if (!code) { invitationCode = null; $('invitationDetails').hidden = true; $('qrPlaceholder').hidden = false; return; }
  if (invitationCode === code) return;
  invitationCode = code;
  $('invitationDetails').hidden = true; $('qrPlaceholder').hidden = false;
  $('qrPlaceholder').textContent = 'Preparando invitación…';
  try {
    const response = await fetch(`/api/invitacion/${encodeURIComponent(code)}`, {cache:'no-store'});
    if (!response.ok) throw Error('No se pudo preparar la invitación.');
    const invitation = await response.json();
    if (invitationCode !== code) return;
    $('studentLink').value = invitation.url;
    $('studentQr').src = `/api/invitacion/${encodeURIComponent(code)}/qr`;
    $('invitationDetails').hidden = false; $('qrPlaceholder').hidden = true;
    $('localWarning').textContent = !invitation.disponible ? 'No se pudo detectar la IP local. Abre el panel con una dirección accesible para tu grupo.' : invitation.red_local ? 'Para esta prueba, los estudiantes deben estar en la misma red Wi-Fi que esta computadora.' : '';
  } catch (error) {
    if (invitationCode !== code) return;
    invitationCode = null;
    $('qrPlaceholder').textContent = 'No se pudo generar la invitación. Reinicia el servidor e intenta de nuevo.';
  }
}
function updateQueue() {
  if (!teacher) return;
  $('queueStatus').textContent = pendingScans.length ? `${pendingScans.length} ${pendingScans.length === 1 ? 'tarjeta leída está esperando' : 'tarjetas leídas están esperando'}. Se anunciarán en orden después del audio actual.` : '';
  $('clearQueue').hidden = pendingScans.length === 0;
}
function cancelQueue() {
  if (!teacher) return;
  queueVersion++; pendingScans.length = 0; narration.detener(); narration.carta = null;
  const done = audioDone; audioDone = null; done?.(); updateQueue();
}
async function announceUid(uid) {
  if (!currentRoom || currentRoom.estado !== 'en_curso') { message('Inicia una partida antes de pasar las tarjetas.'); return; }
  if (pendingScans.length >= 54) { message('Hay muchas lecturas pendientes. Espera a que termine el audio.'); return; }
  pendingScans.push({uid, codigo:session.codigo}); updateQueue();
  await drainQueue();
}
async function drainQueue() {
  if (processing) return;
  processing = true; const version = queueVersion;
  try {
    while (pendingScans.length && version === queueVersion && currentRoom?.estado === 'en_curso') {
      const next = pendingScans.shift(); updateQueue();
      if (next.codigo !== session.codigo) continue;
      // La siguiente lectura no se publica hasta terminar ambos audios.
      const finished = new Promise(resolve => { audioDone = resolve; });
      try {
        const result = await request(`/api/juego/${next.codigo}/anunciar`, {uid:next.uid});
        if (version !== queueVersion) break;
        message(''); render(result); await finished;
      } catch (error) { const done = audioDone; audioDone = null; done?.(); message(`Tarjeta ${next.uid}: ${error.message}`); }
    }
  } finally { processing = false; updateQueue(); if (pendingScans.length) void drainQueue(); }
}
if (teacher) {
  updateLink(session?.codigo);
  const lector = new window.LectorUSB(uid => { void announceUid(uid); }, (text, connected) => {
    $('usbStatus').textContent = text; $('usbBadge').textContent = connected ? 'Conectado' : 'Sin conectar';
    $('connectUsb').hidden = connected; $('disconnectUsb').hidden = !connected;
  }, line => {
    const log = $('serialLog');
    const previous = log.dataset.received ? log.textContent.split('\n') : [];
    log.dataset.received = 'true';
    log.textContent = [...previous, line].slice(-30).join('\n');
  });
  $('connectUsb').onclick = () => busy($('connectUsb'), async () => {
    try { await lector.conectar(); } catch (error) { if (error.name !== 'NotFoundError') throw Error(`No se pudo conectar el lector. ${error.message}`); }
  });
  $('disconnectUsb').onclick = () => busy($('disconnectUsb'), () => lector.desconectar());
  $('enableAudio').onclick = () => busy($('enableAudio'), async () => { await narration.habilitar(); $('enableAudio').textContent = 'Sonido activado'; });
  $('replayAudio').onclick = () => narration.repetir();
  $('skipAudio').onclick = () => { narration.detener(); const done = audioDone; audioDone = null; done?.(); $('audioStatus').textContent = 'Audio omitido.'; };
  $('clearQueue').onclick = () => { pendingScans.length = 0; updateQueue(); message('Se descartaron las lecturas pendientes. La carta actual no se modificó.', true); };
  $('createForm').onsubmit = event => { event.preventDefault(); busy($('create'), async () => {
    const limite = Number($('capacity').value);
    if (!Number.isInteger(limite) || limite < 1 || limite > 100) throw Error('El límite de alumnos debe ser un número entre 1 y 100.');
    const room = await request('/api/partidas',{limite, nombre:$('roomName').value.trim()});
    // El panel docente se identifica con su sesión (cookie); ya no se usa una clave de partida.
    cancelQueue(); audioKey = null; session = {codigo:room.codigo,token:'docente'}; save(); render(room); connect();
    message(room.mensaje || 'Partida creada.', true);
  }); };
  $('start').onclick = () => busy($('start'), async () => {
    try { await narration.habilitar(); $('enableAudio').textContent = 'Sonido activado'; } catch { message('La partida puede iniciar; pulsa Activar sonido para habilitar los audios.'); }
    render(await request(`/api/partidas/${session.codigo}/iniciar`,{}));
    message('¡La partida comenzó! Pasa las tarjetas por el lector o anúncialas por número.', true);
  });
  $('finish').onclick = () => { if (!confirm('¿Finalizar esta partida?')) return; const partida = {...session}; busy($('finish'), async () => { const result = await request(`/api/partidas/${partida.codigo}/finalizar`,{}); if(result.estado!=='finalizada')throw Error('El servidor no confirmó el cierre. Vuelve a intentarlo.'); render(result); $('connection').textContent='Partida finalizada · cierre guardado'; }); };
  $('manualForm').onsubmit = event => { event.preventDefault(); void announceUid($('manualUid').value.trim()); };
  $('copy').onclick = () => busy($('copy'), async () => {
    const value = $('studentLink').value;
    if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(value);
    else { $('studentLink').select(); if (!document.execCommand('copy')) throw Error('Selecciona y copia el enlace manualmente.'); }
    message('Enlace copiado.', true);
  });
} else {
  const scannedCode = (new URLSearchParams(location.search).get('codigo') || '').toUpperCase();
  if (/^[A-Z0-9]{6}$/.test(scannedCode)) {
    $('joinCode').value = scannedCode;
    $('codeField').hidden = true;
    $('joinHint').textContent = 'Escribe tu nombre para ingresar a la partida.';
    // Validar desde el QR que la partida exista, esté abierta y tenga lugares.
    fetch(`/api/partidas/${scannedCode}/publica`, {cache:'no-store'}).then(async r => {
      const p = await r.json().catch(() => ({}));
      if (!r.ok) { $('joinHint').textContent = p.detail || 'No se encontró la partida.'; $('codeField').hidden = false; return; }
      if (p.estado !== 'esperando') { $('joinHint').textContent = p.estado === 'en_curso' ? `«${p.nombre}» ya comenzó; ya no se pueden unir alumnos.` : `«${p.nombre}» está cerrada. Pide un código nuevo a tu docente.`; $('join').disabled = true; return; }
      if (p.lugares_disponibles <= 0) { $('joinHint').textContent = `«${p.nombre}» está llena (${p.limite} alumnos).`; $('join').disabled = true; return; }
      $('joinHint').textContent = `Vas a entrar a «${p.nombre}» · ${p.lugares_disponibles} ${p.lugares_disponibles === 1 ? 'lugar disponible' : 'lugares disponibles'}. Escribe tu nombre.`;
    }).catch(() => {});
  }
  let miAvatar = null;
  try { miAvatar = localStorage.getItem('mazahua-avatar'); } catch {}
  if (!miAvatar && window.Avatar) miAvatar = window.Avatar.aleatorio();
  if ($('editorAvatar') && window.Avatar) {
    window.Avatar.crearEditor($('editorAvatar'), miAvatar, codigo => { miAvatar = codigo; try { localStorage.setItem('mazahua-avatar', codigo); } catch {} });
  }
  let pending = null;
  $('joinForm').onsubmit = event => { event.preventDefault(); busy($('join'), async () => {
    const codigo = $('joinCode').value.trim().toUpperCase(), nombre = $('name').value.trim();
    if (!pending || pending.codigo !== codigo || pending.nombre !== nombre) {
      const bytes = crypto.getRandomValues(new Uint8Array(16)); bytes[6] = (bytes[6]&15)|64; bytes[8] = (bytes[8]&63)|128;
      const hex = Array.from(bytes,x=>x.toString(16).padStart(2,'0')).join('');
      pending = {codigo,nombre,solicitud:`${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`};
    }
    pending.avatar = miAvatar || undefined;
    try { localStorage.setItem('mazahua-avatar', miAvatar || ''); } catch {}
    let room;
    try { room = await request('/api/partidas/unirse',pending); }
    catch (error) {
      if (/partida está llena/i.test(error.message)) { showNotice('¡La partida está llena!', 'El grupo alcanzó el máximo de jugadores. Pide al docente una nueva partida.'); return; }
      if (/partida está cerrada|partida finaliz/i.test(error.message)) { showNotice('Partida cerrada', 'Esta partida ya terminó. Pide al docente un nuevo código o enlace.'); return; }
      if (/ya comenzó/i.test(error.message)) { showNotice('La partida ya comenzó', 'Ya no se pueden unir más alumnos a esta partida. Pide al docente un nuevo código.'); return; }
      throw error;
    }
    session = {codigo, token:pending.solicitud, nombre, avatar: miAvatar}; save(); render(room); connect();
    window.lanzarConfeti?.(40);
    message(room.mensaje || '¡Entraste a la partida!', true);
  }); };
  const leave = () => { sessionStorage.removeItem(storageKey); stopped = true; clearTimeout(retry); socket?.close(); location.href = '/estudiante'; };
  $('leave').onclick = leave; $('resetSession').onclick = leave;
}
if (session?.codigo && session?.token) { $('room').hidden = false; if (!teacher) $('joinPanel').hidden = true; connect(); }
if (teacher) { void heartbeat(); setInterval(heartbeat, 30000); }
window.addEventListener('pagehide', () => { stopped = true; clearTimeout(retry); socket?.close(); if (teacher) cancelQueue(); });
