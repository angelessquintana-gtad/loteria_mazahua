// Panel del docente: saludo y lista de sus partidas recientes.
(() => {
  const $ = id => document.getElementById(id);
  const estados = {esperando: 'En espera de alumnos', en_curso: 'En curso', finalizada: 'Finalizada'};
  window.docenteActual.then(d => { $('saludo').textContent = `Hola, ${d.nombre.split(' ')[0]}.`; }).catch(() => {});
  fetch('/api/partidas/mias', {cache: 'no-store'}).then(r => r.ok ? r.json() : Promise.reject()).then(lista => {
    if (!lista.length) { $('mensajePartidas').textContent = 'Todavía no has creado partidas. Pulsa «Crear e iniciar partidas».'; return; }
    $('mensajePartidas').textContent = '';
    const cuerpo = $('tablaPartidas').querySelector('tbody');
    cuerpo.replaceChildren(...lista.map(p => {
      const fila = document.createElement('tr');
      const fecha = p.creada ? new Date(p.creada + 'Z').toLocaleString('es-MX', {dateStyle: 'short', timeStyle: 'short'}) : '';
      for (const valor of [p.nombre, p.codigo, estados[p.estado] || p.estado, `${p.participantes} / ${p.limite}`, fecha]) {
        const celda = document.createElement('td'); celda.textContent = valor; fila.append(celda);
      }
      return fila;
    }));
    $('tablaPartidas').hidden = false;
  }).catch(() => { $('mensajePartidas').textContent = 'No se pudieron cargar tus partidas.'; });
})();
