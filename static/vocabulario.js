(() => {
  const id = name => document.getElementById(name);
  let palabras = [];
  const normalizar = texto => String(texto || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
  function nodo(tag, texto, clase) { const elemento = document.createElement(tag); if (texto) elemento.textContent = texto; if (clase) elemento.className = clase; return elemento; }
  const reproductor = new Audio();
  let botonSonando = null;
  function marcarSonando(boton) { botonSonando?.classList.remove('sonando'); botonSonando = boton; boton?.classList.add('sonando'); }
  function detener() { reproductor.pause(); window.callarEspanol?.(); marcarSonando(null); }
  function tocar(url, boton) {
    detener(); reproductor.src = url; marcarSonando(boton);
    reproductor.play().catch(() => marcarSonando(null));
  }
  reproductor.addEventListener('ended', () => marcarSonando(null));
  function dibujar() {
    const busqueda = normalizar(id('buscarPalabra').value.trim());
    const filtradas = palabras.filter(p => [p.palabra_mazahua, p.traduccion_espanol, p.categoria, p.descripcion].some(v => normalizar(v).includes(busqueda)));
    const tarjetas = filtradas.map(palabra => {
      const tarjeta = nodo('article', null, 'vocabulario-card');
      const imagen = nodo('img'); window.respaldoImagen?.(imagen, palabra); imagen.src = palabra.miniatura_url || palabra.imagen_url; imagen.decoding = 'async';
      imagen.alt = palabra.traduccion_espanol; imagen.loading = 'lazy'; imagen.width = imagen.height = 400;
      const cuerpo = nodo('div', null, 'vocabulario-content');
      cuerpo.append(nodo('h2', palabra.palabra_mazahua), nodo('p', palabra.traduccion_espanol, 'vocabulario-espanol'));
      cuerpo.append(nodo('p', palabra.descripcion || `«${palabra.palabra_mazahua}» es la palabra en lengua mazahua para «${String(palabra.traduccion_espanol).toLocaleLowerCase()}».`, 'vocabulario-descripcion'));
      // Burbujas de audio: mazahua y español (si no hay archivo en español, se usa la voz del navegador).
      const botones = nodo('div', null, 'burbujas-audio');
      const crearBoton = (texto, clase, accion) => { const b = nodo('button', texto, 'burbuja-audio ' + clase); b.type = 'button'; b.onclick = () => accion(b); return b; };
      if (palabra.audio_mazahua_url) botones.append(crearBoton('🔊 Mazahua', 'mazahua', b => tocar(palabra.audio_mazahua_url, b)));
      if (palabra.audio_espanol_url) botones.append(crearBoton('🔊 Español', 'espanol', b => tocar(palabra.audio_espanol_url, b)));
      else if (window.hablarEspanol) botones.append(crearBoton('🔊 Español', 'espanol', b => { detener(); marcarSonando(b); hablarEspanol(palabra.traduccion_espanol); setTimeout(() => marcarSonando(null), 1500); }));
      cuerpo.append(botones);
      // Tocar la imagen reproduce la palabra en mazahua.
      imagen.addEventListener('click', () => { const b = botones.querySelector('.mazahua'); if (b) b.click(); tarjeta.animate([{transform:'scale(1)'},{transform:'scale(1.04) rotate(-1deg)'},{transform:'scale(1)'}], {duration: 450, easing: 'cubic-bezier(.34,1.56,.64,1)'}); });
      imagen.style.cursor = 'pointer'; imagen.title = 'Toca para escuchar en mazahua';
      tarjeta.append(imagen, cuerpo); return tarjeta;
    });
    id('galeriaVocabulario').replaceChildren(...tarjetas);
    window.observarAparicion?.(tarjetas);
    id('totalPalabras').textContent = `${filtradas.length} de ${palabras.length} palabras`;
    id('mensajeCatalogo').textContent = !palabras.length ? 'El docente todavía no ha registrado palabras.' : !filtradas.length ? 'No hay palabras que coincidan con tu búsqueda.' : '';
  }
  async function cargar() {
    id('reintentarCatalogo').hidden = true; id('galeriaVocabulario').setAttribute('aria-busy', 'true');
    try {
      const response = await fetch('/api/vocabulario', {cache:'no-store'});
      if (!response.ok) throw Error('No se pudo cargar el vocabulario. Intenta de nuevo.');
      palabras = await response.json(); dibujar();
    } catch (error) { id('mensajeCatalogo').textContent = error.message; id('totalPalabras').textContent = 'Catálogo sin conexión'; id('reintentarCatalogo').hidden = false; }
    finally { id('galeriaVocabulario').setAttribute('aria-busy', 'false'); }
  }
  id('buscarPalabra').addEventListener('input', dibujar); id('reintentarCatalogo').onclick = cargar; cargar();
})();
