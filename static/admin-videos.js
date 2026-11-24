// Editor de enlaces de YouTube (Administración). Guarda con PUT /api/videos,
// que escribe el archivo videos_youtube.json de la raíz del proyecto.
(() => {
  const $ = id => document.getElementById(id);
  const lista = $('listaVideosAdmin');
  if (!lista) return;
  const mensaje = (texto, error = false) => { $('mensajeVideosAdmin').textContent = texto; $('mensajeVideosAdmin').style.color = error ? 'var(--red)' : 'var(--mint)'; };
  function fila(video = {titulo: '', descripcion: '', url: ''}) {
    const caja = document.createElement('div');
    caja.className = 'fieldgroup video-fila';
    caja.innerHTML = '<div class="grid2"><div><label>Título del video</label><input class="v-titulo" maxlength="150" placeholder="Ej. Backend con FastAPI"></div><div><label>Enlace de YouTube</label><input class="v-url" maxlength="300" placeholder="https://www.youtube.com/watch?v=..."></div></div><label>Descripción (opcional)</label><input class="v-descripcion" maxlength="500" placeholder="Qué se muestra en el video"><div class="actions" style="margin-top:10px"><button type="button" class="danger v-quitar">Quitar este video</button></div>';
    caja.querySelector('.v-titulo').value = video.titulo || '';
    caja.querySelector('.v-url').value = video.url || '';
    caja.querySelector('.v-descripcion').value = video.descripcion || '';
    caja.querySelector('.v-quitar').onclick = () => caja.remove();
    return caja;
  }
  async function cargar() {
    try {
      const r = await fetch('/api/videos', {cache: 'no-store'}); const datos = await r.json();
      if (!r.ok) throw Error(datos.detail || 'No se pudieron cargar los videos.');
      lista.replaceChildren(...datos.map(fila));
      if (!datos.length) lista.append(fila());
    } catch (e) { mensaje(e.message, true); }
  }
  $('agregarVideo').onclick = () => lista.append(fila());
  $('guardarVideos').onclick = async () => {
    const boton = $('guardarVideos'); boton.disabled = true; mensaje('Guardando…');
    const videos = [...lista.querySelectorAll('.video-fila')].map(c => ({
      titulo: c.querySelector('.v-titulo').value.trim(), url: c.querySelector('.v-url').value.trim(),
      descripcion: c.querySelector('.v-descripcion').value.trim()}));
    try {
      const r = await fetch('/api/videos', {method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({videos})});
      const datos = await r.json();
      if (!r.ok) throw Error(typeof datos.detail === 'string' ? datos.detail : 'No se pudieron guardar los videos.');
      mensaje('✓ ' + datos.mensaje + '. Revisa la página /videos.');
    } catch (e) { mensaje(e.message, true); }
    finally { boton.disabled = false; }
  };
  cargar();
})();
