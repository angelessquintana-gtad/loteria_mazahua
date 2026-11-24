// Editor sencillo: lista las cartas (GET /api/tarjetas) y guarda con POST, PUT y DELETE /api/tarjetas.
// El token CSRF y la sesión los agrega sesion-docente.js automáticamente.
(() => {
  const $ = id => document.getElementById(id);
  let cartas = [], actual = null;
  // Grabaciones con el micrófono, una por idioma (se envían como archivo .webm).
  const grabaciones = {mazahua: null, espanol: null}, grabadoras = {mazahua: null, espanol: null};
  const nodo = (tag, texto, clase) => { const e = document.createElement(tag); if (texto) e.textContent = texto; if (clase) e.className = clase; return e; };
  const normalizar = t => String(t || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const mensaje = (t, ok = true) => { $('edMensaje').textContent = t; $('edMensaje').className = 'ed-mensaje' + (ok ? '' : ' error'); };
  const errorApi = async r => { try { const d = await r.json(); return typeof d.detail === 'string' ? d.detail : (d.detail?.[0]?.msg || 'No se pudo completar la operación.'); } catch { return 'No se pudo completar la operación.'; } };

  function ficha(c) {
    const art = nodo('article', null, 'ed-ficha');
    const img = nodo('img'); img.src = c.miniatura_url || c.imagen_url || ''; img.alt = c.traduccion_espanol; img.loading = 'lazy'; img.decoding = 'async';
    img.onerror = () => {
      if (c.imagen_url && img.getAttribute('src') !== c.imagen_url) { img.src = c.imagen_url; return; }
      img.replaceWith(Object.assign(nodo('div', '🖼 Falta la imagen', 'img-faltante ed-faltante'), {title: 'Falta el archivo ' + c.imagen_url + '. Súbelo de nuevo con Editar.'}));
      art.classList.add('ed-sin-imagen');
      art.querySelector('.ed-estado')?.prepend(nodo('strong', '⚠ Falta el archivo de imagen: pulsa Editar y vuelve a subirla. ', 'ed-alerta'));
    };
    const info = nodo('div', null, 'ed-info');
    info.append(nodo('h2', (c.numero ? c.numero + ' · ' : '') + c.palabra_mazahua), nodo('p', c.traduccion_espanol, 'ed-esp'), nodo('p', c.descripcion || '', 'ed-desc'));
    const estado = nodo('p', `${c.audio_mazahua_url ? '🔊 Mazahua ✓' : '🔇 Sin audio mazahua'} · ${c.audio_espanol_url ? '🔊 Español ✓' : '🔇 Sin audio español'}`, 'ed-estado');
    const botones = nodo('div', null, 'ed-acciones');
    const editar = nodo('button', 'Editar'); editar.type = 'button'; editar.onclick = () => abrir(c);
    const borrar = nodo('button', 'Eliminar', 'danger'); borrar.type = 'button'; borrar.onclick = () => eliminar(c, borrar);
    botones.append(editar, borrar); info.append(estado, botones); art.append(img, info);
    return art;
  }
  function pintar() {
    const q = normalizar($('edBuscar').value.trim());
    const lista = cartas.filter(c => [c.palabra_mazahua, c.traduccion_espanol, c.descripcion, c.uid, c.numero].some(v => normalizar(v).includes(q)));
    $('edLista').replaceChildren(...lista.map(ficha));
    mensaje(lista.length ? `${lista.length} de ${cartas.length} palabras` : 'No hay palabras que coincidan con la búsqueda.');
  }
  async function cargar() {
    const r = await fetch('/api/tarjetas', {cache: 'no-store'});
    if (!r.ok) { mensaje(await errorApi(r), false); return; }
    cartas = await r.json();
    pintar();
  }
  function vista(id, url) { const e = $(id); e.hidden = !url; if (url) e.src = url; else e.removeAttribute('src'); }
  function abrir(c) {
    for (const idioma of ['mazahua', 'espanol']) reiniciarGrabador(idioma);
    actual = c; $('edForm').reset(); $('edError').textContent = '';
    $('edTitulo').textContent = c ? `Editar «${c.palabra_mazahua}»` : 'Agregar tarjeta';
    $('edGuardar').textContent = c ? 'Guardar cambios' : 'Agregar tarjeta';
    $('fNumero').value = c?.numero ?? '';
    $('quitarMazahuaCaja').hidden = !c?.audio_mazahua_url; $('quitarEspanolCaja').hidden = !c?.audio_espanol_url;
    $('fMazahua').value = c?.palabra_mazahua || ''; $('fEspanol').value = c?.traduccion_espanol || '';
    $('fDescripcion').value = c?.descripcion || ''; $('fUid').value = c?.uid || '';
    vista('vImagen', c?.imagen_url); vista('vAudioMazahua', c?.audio_mazahua_url); vista('vAudioEspanol', c?.audio_espanol_url);
    const req = c ? '(solo si quieres cambiarla)' : '*';
    $('reqImagen').textContent = req; $('reqAudioM').textContent = c ? '(solo si quieres cambiarlo)' : '*'; $('reqAudioE').textContent = c ? '(solo si quieres cambiarlo)' : '(opcional)';
    for (const id of ['fImagen', 'fAudioMazahua']) $(id).required = !c;
    $('fAudioEspanol').required = false;
    $('edDialogo').showModal(); $('fMazahua').focus();
  }
  $('fImagen').onchange = e => { const f = e.target.files[0]; if (f) vista('vImagen', URL.createObjectURL(f)); };
  const GRABADOR = {
    mazahua: {boton: 'edGrabarMazahua', estado: 'edGrabarMazahuaEstado', archivo: 'fAudioMazahua', vista: 'vAudioMazahua', quitar: 'fQuitarMazahua', texto: 'en mazahua'},
    espanol: {boton: 'edGrabarEspanol', estado: 'edGrabarEspanolEstado', archivo: 'fAudioEspanol', vista: 'vAudioEspanol', quitar: 'fQuitarEspanol', texto: 'en español'},
  };
  function detenerGrabacion(idioma) { const g = grabadoras[idioma]; if (g && g.state === 'recording') g.stop(); }
  function reiniciarGrabador(idioma) {
    detenerGrabacion(idioma); grabaciones[idioma] = null;
    const c = GRABADOR[idioma]; $(c.estado).textContent = ''; $(c.boton).textContent = `🎙 Grabar ${c.texto} con el micrófono`;
  }
  for (const [idioma, c] of Object.entries(GRABADOR)) {
    $(c.archivo).onchange = e => { const f = e.target.files[0]; if (f) { reiniciarGrabador(idioma); vista(c.vista, URL.createObjectURL(f)); } };
    $(c.boton).onclick = async () => {
      const otro = idioma === 'mazahua' ? 'espanol' : 'mazahua'; detenerGrabacion(otro);
      if (grabadoras[idioma] && grabadoras[idioma].state === 'recording') { grabadoras[idioma].stop(); return; }
      if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) { $(c.estado).textContent = 'Este navegador no permite grabar; sube un archivo.'; return; }
      try {
        const flujo = await navigator.mediaDevices.getUserMedia({audio: true});
        const partes = [], grabadora = new MediaRecorder(flujo); grabadoras[idioma] = grabadora;
        grabadora.ondataavailable = ev => ev.data.size && partes.push(ev.data);
        grabadora.onstop = () => {
          flujo.getTracks().forEach(t => t.stop());
          if (!partes.length) { $(c.estado).textContent = 'No se grabó sonido. Inténtalo de nuevo.'; $(c.boton).textContent = `🎙 Grabar ${c.texto} con el micrófono`; return; }
          grabaciones[idioma] = new Blob(partes, {type: grabadora.mimeType || 'audio/webm'});
          $(c.archivo).value = ''; $(c.archivo).required = false; $(c.quitar).checked = false;
          vista(c.vista, URL.createObjectURL(grabaciones[idioma]));
          $(c.boton).textContent = '🎙 Volver a grabar'; $(c.estado).textContent = '✓ Grabación lista. Escúchala con ▶ y pulsa Guardar.';
        };
        grabadora.start(); $(c.boton).textContent = '⏹ Detener grabación'; $(c.estado).textContent = `Grabando… di la palabra ${c.texto}.`;
      } catch { $(c.estado).textContent = 'No se pudo usar el micrófono. Revisa el permiso del navegador.'; }
    };
  }
  $('edCancelar').onclick = () => { detenerGrabacion('mazahua'); detenerGrabacion('espanol'); $('edDialogo').close(); };
  $('edAgregar').onclick = () => abrir(null);
  $('edBuscar').oninput = pintar;

  $('edForm').onsubmit = async e => {
    e.preventDefault();
    const datos = new FormData($('edForm'));
    // UID y número son opcionales: vacíos se guardan sin valor.
    for (const campo of ['imagen', 'audio_mazahua', 'audio_espanol']) { const f = datos.get(campo); if (!f || !f.name) datos.delete(campo); }
    for (const idioma of ['mazahua', 'espanol']) {
      if (grabaciones[idioma] && !datos.get('audio_' + idioma)) datos.set('audio_' + idioma, grabaciones[idioma], `grabacion_${idioma}.webm`);
    }
    const numero = String(datos.get('numero') || '').trim();
    if (numero && !/^\d{1,4}$/.test(numero)) { $('edError').textContent = 'El número de tarjeta debe ser un número (1, 2, 3…).'; return; }
    if (!actual && !datos.get('imagen')) { $('edError').textContent = 'Para agregar una tarjeta adjunta su imagen.'; return; }
    if (!actual && !datos.get('audio_mazahua')) { $('edError').textContent = 'Falta el audio en mazahua: súbelo o grábalo con el micrófono.'; return; }
    if (!$('fQuitarMazahua').checked) datos.delete('eliminar_audio_mazahua');
    if (!$('fQuitarEspanol').checked) datos.delete('eliminar_audio_espanol');
    const boton = $('edGuardar'); boton.disabled = true; $('edError').textContent = 'Guardando…';
    try {
      const r = await fetch(actual ? `/api/tarjetas/${actual.id}` : '/api/tarjetas', {method: actual ? 'PUT' : 'POST', body: datos});
      if (!r.ok) throw Error(await errorApi(r));
      const resultado = await r.json();
      $('edDialogo').close(); await cargar(); mensaje('✓ ' + (resultado.mensaje || 'Cambios guardados correctamente.'));
    } catch (error) { $('edError').textContent = error.message; }
    finally { boton.disabled = false; }
  };
  async function eliminar(c, boton) {
    if (!confirm(`¿Eliminar «${c.palabra_mazahua}» (${c.traduccion_espanol})? Esta acción no se puede deshacer.`)) return;
    boton.disabled = true;
    const r = await fetch(`/api/tarjetas/${c.id}`, {method: 'DELETE'});
    if (!r.ok) { mensaje(await errorApi(r), false); boton.disabled = false; return; }
    const resultado = await r.json().catch(() => ({}));
    await cargar(); mensaje('✓ ' + (resultado.mensaje || `«${c.palabra_mazahua}» se eliminó.`));
  }
  cargar();
})();
