/* Navegación en todas las pantallas (excepto la del alumno).
   Sin sesión: «Regresar» e «Inicio» (portada).
   Con sesión de docente: solo sus secciones (Partidas, Tarjetas, Vocabulario),
   «Regresar», «Inicio» (su panel) y, en la esquina, el menú de su cuenta
   con «Editar mis datos», «Cambiar contraseña» y «Cerrar sesión». */
(() => {
  const nav = document.querySelector('.app-nav');
  if (!nav || document.body.dataset.role === 'estudiante') return;
  const ruta = location.pathname;
  const crear = (etiqueta, props = {}) => Object.assign(document.createElement(etiqueta), props);
  const caja = crear('div', {className: 'nav-acciones'});
  const inicio = crear('a', {href: '/', className: 'nav-boton', textContent: '⌂ Inicio'});
  const regresar = crear('button', {type: 'button', className: 'nav-boton', textContent: '← Regresar'});
  regresar.onclick = () => { if (history.length > 1 && document.referrer.startsWith(location.origin)) history.back(); else location.href = inicio.href; };
  if (ruta === '/') regresar.hidden = true;
  caja.append(regresar, inicio);
  nav.append(caja);

  fetch('/api/auth/me', {cache: 'no-store'}).then(r => r.ok ? r.json() : null).then(datos => {
    if (!datos) return;
    const docente = datos.docente || {};
    inicio.href = '/panel';
    if (ruta === '/panel') inicio.hidden = true;
    regresar.hidden = ruta === '/panel';

    // El docente solo ve sus secciones (sin Videos, Simulador ni Lector RFID).
    const marca = nav.querySelector('.brand'); if (marca) marca.href = '/panel';
    const enlaces = nav.querySelector('.nav-catalogo, .home-nav');
    if (enlaces) {
      enlaces.className = 'nav-catalogo';
      enlaces.replaceChildren(...[['/docente', 'Partidas'], ['/editar', 'Tarjetas'], ['/vocabulario', 'Vocabulario']].map(([href, texto]) => {
        const a = crear('a', {href, textContent: texto});
        if (ruta === href) a.setAttribute('aria-current', 'page');
        return a;
      }));
    }

    // Menú de la cuenta en la esquina.
    const menu = crear('div', {className: 'menu-cuenta'});
    const nombre = (docente.nombre || 'Docente').trim();
    const boton = crear('button', {type: 'button', className: 'menu-cuenta-boton', title: 'Mi cuenta'});
    boton.setAttribute('aria-haspopup', 'true'); boton.setAttribute('aria-expanded', 'false'); boton.setAttribute('aria-label', 'Mi cuenta: ' + nombre);
    boton.append(crear('span', {className: 'menu-cuenta-inicial', textContent: nombre.charAt(0).toUpperCase()}),
                 crear('span', {className: 'menu-cuenta-nombre', textContent: nombre.split(/\s+/)[0] + ' ▾'}));
    const lista = crear('div', {className: 'menu-cuenta-lista', hidden: true});
    const datosCaja = crear('div', {className: 'menu-cuenta-datos'});
    datosCaja.append(crear('strong', {textContent: nombre}), crear('small', {textContent: docente.correo || ''}));
    const salir = crear('button', {type: 'button', className: 'nav-salir', textContent: 'Cerrar sesión'});
    lista.append(datosCaja,
      crear('a', {href: '/cuenta#misDatos', textContent: '✎ Editar mis datos'}),
      crear('a', {href: '/cuenta#cambiarPassword', textContent: '🔒 Cambiar contraseña'}),
      salir);
    const abrir = (si) => { lista.hidden = !si; boton.setAttribute('aria-expanded', String(si)); };
    boton.onclick = (e) => { e.stopPropagation(); abrir(lista.hidden); };
    document.addEventListener('click', (e) => { if (!menu.contains(e.target)) abrir(false); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !lista.hidden) { abrir(false); boton.focus(); } });
    salir.onclick = async () => {
      salir.disabled = true; salir.textContent = 'Cerrando…';
      try {
        const r = await fetch('/api/auth/logout', {method: 'POST', headers: {'X-CSRF-Token': datos.csrf_token}});
        if (!r.ok && r.status !== 401) throw Error();
        location.replace('/acceso?salida=1');
      } catch { salir.disabled = false; salir.textContent = 'Reintentar cerrar sesión'; }
    };
    menu.append(boton, lista);
    caja.append(menu);
  }).catch(() => {});
})();
