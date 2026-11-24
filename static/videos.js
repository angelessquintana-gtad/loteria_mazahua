// Muestra los videos de /api/videos como miniaturas que abren YouTube en otra pestaña.
(() => {
  const $ = id => document.getElementById(id);
  const nodo = (tag, texto, clase) => { const e = document.createElement(tag); if (texto) e.textContent = texto; if (clase) e.className = clase; return e; };
  function tarjeta(video) {
    const pendiente = !video.enlace;
    const card = nodo(pendiente ? 'article' : 'a', null, 'video-card' + (pendiente ? ' video-pendiente' : ''));
    if (!pendiente) { card.href = video.enlace; card.target = '_blank'; card.rel = 'noopener noreferrer'; card.setAttribute('aria-label', 'Ver en YouTube: ' + video.titulo); }
    const mini = nodo('div', null, 'video-miniatura');
    if (video.miniatura) { const img = nodo('img'); img.src = video.miniatura; img.alt = ''; img.loading = 'lazy'; img.onerror = () => img.remove(); mini.append(img); }
    mini.append(nodo('span', null, 'video-play'));
    const info = nodo('div', null, 'video-info');
    info.append(nodo('h2', video.titulo));
    if (video.descripcion) info.append(nodo('p', video.descripcion));
    info.append(nodo('span', pendiente ? 'Enlace pendiente de agregar' : 'Ver en YouTube ↗', 'video-estado'));
    card.append(mini, info);
    return card;
  }
  async function cargar() {
    try {
      const r = await fetch('/api/videos', {cache: 'no-store'});
      const datos = await r.json();
      if (!r.ok) throw Error(datos.detail || 'No se pudieron cargar los videos.');
      $('listaVideos').replaceChildren(...datos.map(tarjeta));
      const pendientes = datos.filter(v => !v.enlace).length;
      $('mensajeVideos').textContent = !datos.length ? 'Todavía no hay videos registrados.' : `${datos.length - pendientes} de ${datos.length} videos publicados.`;
      $('notaVideos').hidden = pendientes === 0 && datos.length > 0;
    } catch (error) { $('mensajeVideos').textContent = error.message; }
    finally { $('listaVideos').setAttribute('aria-busy', 'false'); }
  }
  cargar();
})();
