/* Registro por orden del catálogo y grabación local del significado en español. */
(() => {
  let leyendo = false, solicitandoMicrofono = false, grabador = null, flujo = null;
  let subiendo = false, finalizando = false, pendiente = null, tarjetaActual = null, vistaUrl = null;
  let temporizador = null, limite = null, inicio = 0;
  const MAX_AUDIO = 12 * 1024 * 1024;
  const ocupado = () => leyendo || solicitandoMicrofono || subiendo || finalizando || (grabador && grabador.state !== 'inactive');
  const estado = texto => { $('estadoGrabacion').textContent = texto; };
  function botones() {
    $('grabarEspanol').disabled = ocupado();
    $('detenerGrabacion').disabled = !grabador || grabador.state !== 'recording';
    $('reintentarGrabacion').hidden = !pendiente?.id || subiendo;
    $('clearBtn').disabled = ocupado() || Boolean(pendiente);
    $('saveBtn').disabled = ocupado();
    $('audioEspanol').disabled = ocupado();
    $('autoCatalogo').disabled = ocupado();
  }
  async function json(url, options) {
    const control = new AbortController();
    const timer = setTimeout(() => control.abort(), 15000);
    try {
      const r = await fetch(url, { ...options, cache: 'no-store', signal: control.signal });
      const d = await r.json();
      if (!r.ok) {
        const error = Error(r.status === 404 && url.startsWith('/api/catalogo/') ? 'El servidor no tiene activo el registro automático. Reinicia iniciar_proyecto.bat y recarga esta página.' : typeof d.detail === 'string' ? d.detail : 'No se pudo completar la solicitud');
        error.status = r.status; throw error;
      }
      return d;
    } catch (e) {
      if (e.name === 'AbortError') throw Error('El servidor tardó demasiado. El lector sigue conectado; vuelve a pasar la tarjeta.');
      throw e;
    } finally { clearTimeout(timer); }
  }
  function mostrarOrden(d) {
    $('catalogoEstado').textContent = `${d.asignadas} de ${d.total} palabras asignadas. ` +
      (d.siguiente ? `Siguiente: ${d.siguiente.traduccion_espanol} · ${d.siguiente.palabra_mazahua}` : 'Catálogo completo. Puedes volver a leer cualquier tarjeta.');
  }
  async function actualizarOrden() {
    try { mostrarOrden(await json('/api/catalogo/estado')); }
    catch (e) { $('catalogoEstado').textContent = e.message; }
  }
  async function leer(uid) {
    uid = uid.trim().toUpperCase().replace(/\s+/g, ' ');
    if (ocupado() || pendiente) {
      showMessage('Termina de grabar o guardar el audio actual y vuelve a pasar la tarjeta.', 'err');
      return;
    }
    leyendo = true; botones(); stopSequence();
    $('simulateUid').value = uid;
    $('scanStatus').textContent = 'Tarjeta detectada: ' + uid;
    setSimMessage('UID recibido: ' + uid + '. Consultando su registro…');
    try {
      // Una tarjeta existente se consulta sin depender de la importación del catálogo.
      let d;
      try { d = { tarjeta: await json('/api/uid/' + encodeURIComponent(uid)), nueva: false }; }
      catch (e) {
        if (e.status !== 404) throw e;
        d = await json('/api/catalogo/registrar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ uid }) });
      }
      tarjetaActual = d.tarjeta;
      await loadCards();
      if (!cards.some(t => t.id === d.tarjeta.id)) cards.push(d.tarjeta);
      await window.editCard(d.tarjeta.id);
      $('uid').readOnly = true;
      $('formTitle').textContent = d.nueva ? 'Tarjeta registrada automáticamente' : 'Tarjeta ya registrada';
      $('scanStatus').textContent = `${uid} · ${d.tarjeta.traduccion_espanol}`;
      $('simulateUid').value = uid;
      showSimulatedCard(d.tarjeta);
      if (d.catalogo) mostrarOrden(d.catalogo);
      else void actualizarOrden();
      await readCard(uid, true);
      estado(`Graba en español: “${d.tarjeta.traduccion_espanol}”.`);
      showMessage(d.nueva ? 'Datos, imagen y audio mazahua guardados en la base de datos. Falta grabar el español.' : 'Registro recuperado. Puedes escuchar o volver a grabar el español.', 'ok');
      $('grabarEspanol').focus();
    } catch (e) { showMessage(e.message, 'err'); setSimMessage('UID leído: ' + uid + '. ' + e.message, 'sim-error'); }
    finally { leyendo = false; botones(); }
  }
  function cerrarMicrofono() {
    clearInterval(temporizador); clearTimeout(limite);
    flujo?.getTracks().forEach(t => t.stop()); flujo = null;
  }
  function detener() {
    if (grabador?.state === 'recording') { finalizando = true; grabador.stop(); botones(); }
  }
  async function guardarPendiente() {
    if (!pendiente?.id || subiendo) return;
    subiendo = true; botones();
    const audio = pendiente;
    estado('Guardando el audio en español…');
    try {
      const body = new FormData(); body.append('audio_espanol', audio.archivo);
      const d = await json(`/api/tarjetas/${audio.id}/audio-espanol`, { method: 'POST', body });
      pendiente = null;
      if (tarjetaActual?.id === d.tarjeta.id) tarjetaActual = d.tarjeta;
      $('audioEspanol').value = '';
      $('currentAudioEspanol').textContent = 'Audio en español guardado en la base de datos.';
      $('previewAudioEspanol').src = d.tarjeta.audio_espanol_url;
      showSimulatedCard(d.tarjeta);
      await loadCards();
      estado(`Audio de “${d.tarjeta.traduccion_espanol}” guardado. Ya puedes pasar la siguiente tarjeta.`);
      showMessage('✓ Grabación guardada en la tarjeta ' + d.tarjeta.uid, 'ok');
    } catch (e) { estado('No se pudo guardar: ' + e.message + '. La grabación se conserva; pulsa Reintentar guardar audio.'); }
    finally { subiendo = false; botones(); }
  }
  $('grabarEspanol').onclick = async () => {
    if (ocupado()) return;
    if (pendiente?.id) { estado('Primero guarda la grabación pendiente.'); return; }
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      estado('El micrófono requiere Chrome o Edge en localhost o HTTPS. También puedes adjuntar un audio.'); return;
    }
    const destinoId = editingId;
    solicitandoMicrofono = true; botones(); stopSequence();
    try {
      flujo = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/mp4'].find(t => MediaRecorder.isTypeSupported(t));
      grabador = new MediaRecorder(flujo, mimeType ? { mimeType } : undefined);
      const partes = []; let bytes = 0, error = false;
      grabador.ondataavailable = e => {
        if (e.data.size) { partes.push(e.data); bytes += e.data.size; }
        if (bytes >= MAX_AUDIO) detener();
      };
      grabador.onerror = () => { error = true; estado('Falló la grabación. Vuelve a intentarlo.'); if (grabador.state !== 'inactive') grabador.stop(); cerrarMicrofono(); };
      grabador.onstop = async () => {
        cerrarMicrofono();
        const tipo = grabador.mimeType || partes[0]?.type || 'audio/webm';
        const blob = new Blob(partes, { type: tipo });
        grabador = null; finalizando = false;
        if (error || !blob.size || blob.size > MAX_AUDIO) {
          estado('No se obtuvo un audio válido de hasta 12 MB. Vuelve a grabar.'); botones(); return;
        }
        const extension = tipo.includes('mp4') ? 'mp4' : tipo.includes('ogg') ? 'ogg' : 'webm';
        const archivo = new File([blob], `espanol.${extension}`, { type: tipo });
        if (vistaUrl) URL.revokeObjectURL(vistaUrl);
        vistaUrl = URL.createObjectURL(blob);
        $('previewAudioEspanol').src = vistaUrl; $('audioEspanolPreview').hidden = false;
        if (destinoId) {
          pendiente = { id: destinoId, archivo }; await guardarPendiente();
        } else {
          const transferencia = new DataTransfer(); transferencia.items.add(archivo);
          $('audioEspanol').files = transferencia.files;
          estado('Grabación lista. Pulsa Guardar tarjeta para crear el registro manual.');
        }
        botones();
      };
      grabador.start(500); inicio = Date.now();
      temporizador = setInterval(() => estado(`Grabando español… ${Math.floor((Date.now() - inicio) / 1000)} s. Pulsa Detener y guardar al terminar.`), 500);
      limite = setTimeout(detener, 120000);
      estado('Grabando español… Habla ahora.');
    } catch (e) {
      cerrarMicrofono(); estado(e.name === 'NotAllowedError' ? 'Permite el acceso al micrófono en el navegador para grabar.' : 'No se pudo iniciar el micrófono: ' + e.message);
    } finally { solicitandoMicrofono = false; botones(); }
  };
  $('detenerGrabacion').onclick = detener;
  $('reintentarGrabacion').onclick = guardarPendiente;
  const editar = window.editCard;
  window.editCard = async id => {
    if ((ocupado() && !leyendo) || pendiente) { showMessage('Termina de guardar la grabación actual antes de cambiar de tarjeta.', 'err'); return; }
    await editar(id);
    tarjetaActual = cards.find(t => t.id === id) || null;
  };
  const eliminar = window.deleteCard;
  window.deleteCard = async id => {
    if (ocupado() || pendiente) { showMessage('Termina de guardar el audio antes de eliminar una tarjeta.', 'err'); return; }
    await eliminar(id); await actualizarOrden();
  };
  const limpiar = clearForm;
  clearForm = () => { if ((ocupado() && !leyendo) || pendiente) return; limpiar(); tarjetaActual = null; estado('Micrófono listo.'); };
  $('clearBtn').onclick = clearForm;
  $('simulateForm').removeEventListener('submit', simulateRead);
  $('simulateForm').addEventListener('submit', async e => {
    e.preventDefault();
    if ($('autoCatalogo').checked) await leer($('simulateUid').value);
    else await simulateRead(e);
  });
  $('simulateBtn').textContent = 'Leer UID';
  $('autoCatalogo').onchange = () => { actualizarOrden(); if (!$('autoCatalogo').checked) estado('Modo manual: puedes editar datos o registrar archivos.'); };
  $('cardForm').addEventListener('submit', e => {
    if (ocupado() || pendiente) { e.preventDefault(); e.stopImmediatePropagation(); showMessage('Espera a que termine de guardarse la grabación.', 'err'); }
  }, true);
  window.addEventListener('beforeunload', e => { if (ocupado() || pendiente) { e.preventDefault(); e.returnValue = ''; } });
  window.registroAutomatico = { activo: () => $('autoCatalogo').checked, leer, actualizarOrden };
  actualizarOrden(); botones();
})();
