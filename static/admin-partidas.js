(() => {
  let cargando = false;
  async function cargar() {
    if (cargando) return;
    cargando = true;
    try {
      const datos = await respuestaApi(await fetch('/api/admin/partidas', {cache: 'no-store'}));
      const p = datos.politica;
      $('adminRoomsPolicy').textContent = `Cierre tras ${p.inactividad_minutos} min sin docente o ${p.duracion_maxima_horas} h de duración. Historial: ${p.retencion_dias} días. Últimas 100 partidas.`;
      $('adminRoomsBody').innerHTML = datos.partidas.map(p => `<tr><td><strong>${esc(p.codigo)}</strong></td><td>${esc(p.estado)}</td><td>${esc(p.creada || '')}</td><td>${p.participantes}</td><td>${p.estado === 'finalizada' ? esc(p.cierre_motivo || 'Finalizada') : `<button type="button" class="secondary" data-finalizar="${esc(p.codigo)}">Finalizar</button>`}</td></tr>`).join('') || '<tr><td colspan="5">No hay partidas guardadas.</td></tr>';
    } catch (e) { $('adminRoomsMessage').textContent = e.message; }
    finally { cargando = false; }
  }
  $('refreshRooms').onclick = cargar;
  $('adminRoomsBody').onclick = async e => {
    const boton = e.target.closest('[data-finalizar]');
    if (!boton || !confirm(`¿Finalizar la partida ${boton.dataset.finalizar}?`)) return;
    boton.disabled = true;
    try {
      const d = await respuestaApi(await fetch(`/api/admin/partidas/${encodeURIComponent(boton.dataset.finalizar)}/finalizar`, {method: 'POST'}));
      $('adminRoomsMessage').textContent = `Partida ${d.codigo} finalizada y guardada en la base de datos.`;
      await cargar();
    } catch (error) { $('adminRoomsMessage').textContent = error.message; }
    finally { boton.disabled = false; }
  };
  void cargar(); setInterval(cargar, 30000);
})();
