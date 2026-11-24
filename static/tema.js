/* Detalles visuales e interactivos comunes: logo, botones del menú, títulos animados,
   aparición de tarjetas, imágenes de respaldo, ondas en los botones y confeti. */
(() => {
  const movimientoReducido = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ICONOS = {
    '/vocabulario': '📚', '/simulador': '🎲', '/videos': '🎬', '/acceso': '👩‍🏫', '/docente': '🎯',
    '/editar': '🃏', '/cuenta': '👤', '/estudiante': '🙋', '#como-jugar': '💡', '/panel': '🏠',
  };

  /* Imagen que no carga: miniatura → imagen completa → burbuja con la palabra. */
  window.respaldoImagen = (img, carta = {}) => {
    img.addEventListener('error', function fallo() {
      if (carta.imagen_url && !img.dataset.intentoCompleto && img.getAttribute('src') !== carta.imagen_url) {
        img.dataset.intentoCompleto = '1'; img.src = carta.imagen_url; return;
      }
      img.removeEventListener('error', fallo);
      const palabra = carta.palabra_mazahua || img.alt || '';
      const caja = document.createElement('div');
      caja.className = 'img-burbuja ' + (img.className || '');
      caja.setAttribute('role', 'img');
      caja.setAttribute('aria-label', img.alt || palabra);
      caja.title = carta.imagen_url ? 'Falta el archivo de imagen: ' + carta.imagen_url : 'Sin imagen';
      const inicial = document.createElement('b'); inicial.textContent = (palabra.trim()[0] || '✿').toLocaleUpperCase();
      const texto = document.createElement('span'); texto.textContent = palabra;
      caja.append(inicial, texto);
      img.replaceWith(caja);
    });
  };

  /* Confeti (con frijolitos) para celebrar. */
  window.lanzarConfeti = (cantidad = 90) => {
    if (movimientoReducido) return;
    const capa = document.createElement('div'); capa.className = 'confeti-capa'; capa.setAttribute('aria-hidden', 'true');
    const colores = ['#e94c75', '#f2b24d', '#2f8b70', '#74203d', '#3b5ba9', '#fff'];
    for (let i = 0; i < cantidad; i++) {
      const pieza = document.createElement('span');
      pieza.className = 'confeti-pieza' + (i % 7 === 0 ? ' frijol' : '');
      pieza.style.left = Math.random() * 100 + 'vw';
      pieza.style.background = colores[i % colores.length];
      pieza.style.setProperty('--dx', (Math.random() * 200 - 100) + 'px');
      pieza.style.setProperty('--giro', (Math.random() * 900 + 200) + 'deg');
      pieza.style.setProperty('--dur', (2.4 + Math.random() * 1.8) + 's');
      pieza.style.animationDelay = Math.random() * .6 + 's';
      capa.append(pieza);
    }
    document.body.append(capa);
    setTimeout(() => capa.remove(), 5200);
  };

  /* Ajusta el ancho del tablero para que quepa completo en la pantalla (sin desplazarse). */
  window.ajustarTablero = el => {
    if (!el || !el.isConnected || !el.offsetParent) return;
    el.style.width = '';
    for (let intento = 0; intento < 4; intento++) {
      const r = el.getBoundingClientRect();
      if (!r.height) return;
      const arriba = r.top + window.scrollY;
      const contenedor = el.closest('.board-panel');
      const debajo = contenedor ? Math.max(0, contenedor.getBoundingClientRect().bottom - r.bottom) : 0;
      // Si el tablero empieza muy abajo (por ejemplo, en celular debajo de otro panel), se usa la pantalla completa.
      const disponible = (arriba < window.innerHeight * .55 ? window.innerHeight - arriba : window.innerHeight - 70) - debajo - 14;
      if (r.height <= disponible + 2) return;
      el.style.width = Math.max(250, Math.floor(r.width * disponible / r.height)) + 'px';
    }
  };
  let esperaAjuste = null;
  window.addEventListener('resize', () => {
    clearTimeout(esperaAjuste);
    esperaAjuste = setTimeout(() => document.querySelectorAll('.board').forEach(window.ajustarTablero), 120);
  });

  /* Aparición tipo burbuja al entrar en pantalla. */
  const observador = 'IntersectionObserver' in window && !movimientoReducido
    ? new IntersectionObserver(entradas => entradas.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); observador.unobserve(e.target); } }), {rootMargin: '0px 0px -40px 0px'})
    : null;
  window.observarAparicion = elementos => {
    let orden = 0;
    for (const el of elementos) {
      if (!observador) continue;
      el.classList.add('aparece'); el.style.setProperty('--orden', String(orden++ % 8)); observador.observe(el);
    }
  };

  function titulosVivos() {
    for (const h1 of document.querySelectorAll('.hero h1, .home-copy h1')) {
      if (h1.dataset.vivo || h1.closest('[data-role="estudiante"]') && document.body.classList.contains('playing')) continue;
      h1.dataset.vivo = '1';
      h1.setAttribute('aria-label', h1.textContent.replace(/\s+/g, ' ').trim());
      let i = 0;
      const procesar = nodo => {
        for (const hijo of [...nodo.childNodes]) {
          if (hijo.nodeType === Node.TEXT_NODE) {
            const fragmento = document.createDocumentFragment();
            for (const parte of hijo.textContent.split(/(\s+)/)) {
              if (!parte) continue;
              if (/^\s+$/.test(parte)) { fragmento.append(document.createTextNode(' ')); continue; }
              const palabra = document.createElement('span'); palabra.className = 'palabra'; palabra.setAttribute('aria-hidden', 'true');
              for (const letra of parte) {
                const s = document.createElement('span'); s.className = 'letra' + (/[.!¡?¿]/.test(letra) ? ' acento' : '');
                s.textContent = letra; s.style.setProperty('--i', String(i++)); palabra.append(s);
              }
              fragmento.append(palabra);
            }
            hijo.replaceWith(fragmento);
          } else if (hijo.nodeType === Node.ELEMENT_NODE && hijo.tagName !== 'BR') {
            procesar(hijo);
          }
        }
      };
      procesar(h1);
      h1.classList.add('titulo-vivo');
      // Al tocar el título, las letras hacen «la ola».
      h1.addEventListener('click', () => { h1.classList.remove('ola'); void h1.offsetWidth; h1.classList.add('ola'); window.sonidoClic?.(); });
    }
  }

  function decorarMenu() {
    const nav = document.querySelector('.app-nav');
    if (!nav) return;
    const marca = nav.querySelector('.brand');
    if (marca && !marca.querySelector('.brand-logo')) {
      const logo = document.createElement('img');
      logo.className = 'brand-logo'; logo.alt = ''; logo.width = 62; logo.height = 52;
      logo.src = '/static/img/logo-mazahua-160.webp';
      marca.prepend(logo);
    }
    for (const a of nav.querySelectorAll('.nav-catalogo a, .home-nav a')) {
      const ruta = a.getAttribute('href') || '';
      if (!a.querySelector('.icono-nav') && ICONOS[ruta]) {
        const icono = document.createElement('span'); icono.className = 'icono-nav'; icono.setAttribute('aria-hidden', 'true'); icono.textContent = ICONOS[ruta];
        a.prepend(icono);
      }
      if (ruta === location.pathname) a.setAttribute('aria-current', 'page');
    }
  }

  function favicon() {
    if (document.querySelector('link[rel="icon"]')) return;
    const l = document.createElement('link'); l.rel = 'icon'; l.type = 'image/png'; l.href = '/static/img/favicon.png';
    document.head.append(l);
  }

  function logoInicio() {
    const zona = document.querySelector('.home .card-display');
    if (!zona || zona.dataset.logo) return;
    zona.dataset.logo = '1';
    zona.className = 'logo-hero';
    zona.innerHTML = '';
    const img = document.createElement('img');
    img.src = '/static/img/logo-mazahua.webp'; img.alt = 'Lotería Mazahua: niña mazahua con cartas de la lotería'; img.width = 720; img.height = 594;
    img.addEventListener('click', e => chispas(e.clientX, e.clientY));
    zona.append(img);
  }

  function chispas(x, y) {
    window.sonidoClic?.();
    if (movimientoReducido) return;
    const simbolos = ['🌸', '🌽', '✨', '🫘', '💮', '⭐'];
    for (let i = 0; i < 10; i++) {
      const s = document.createElement('span'); s.className = 'chispa'; s.textContent = simbolos[i % simbolos.length];
      const angulo = (Math.PI * 2 * i) / 10;
      s.style.left = x + 'px'; s.style.top = y + 'px'; s.style.position = 'fixed';
      s.style.setProperty('--dx', Math.cos(angulo) * 90 + 'px'); s.style.setProperty('--dy', Math.sin(angulo) * 90 + 'px');
      document.body.append(s); setTimeout(() => s.remove(), 1000);
    }
  }

  /* Onda tipo burbuja al presionar botones. */
  document.addEventListener('pointerdown', e => {
    const b = e.target.closest('button, .home-start, .boton-rol');
    if (!b || b.disabled || movimientoReducido || b.closest('.menu-cuenta-lista')) return;
    const r = b.getBoundingClientRect(), tam = Math.max(r.width, r.height);
    const onda = document.createElement('span'); onda.className = 'burbuja-onda';
    onda.style.width = onda.style.height = tam + 'px';
    onda.style.left = (e.clientX - r.left - tam / 2) + 'px'; onda.style.top = (e.clientY - r.top - tam / 2) + 'px';
    if (getComputedStyle(b).position === 'static') b.style.position = 'relative';
    b.style.overflow = 'hidden';
    b.append(onda); setTimeout(() => onda.remove(), 650);
  }, {passive: true});

  function iniciar() {
    favicon(); decorarMenu(); titulosVivos(); logoInicio();
    const nav = document.querySelector('.app-nav');
    if (nav) new MutationObserver(() => decorarMenu()).observe(nav, {childList: true, subtree: true});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
