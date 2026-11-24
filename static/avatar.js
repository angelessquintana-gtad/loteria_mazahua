/* Avatares de animalitos para los alumnos, dibujados en SVG a partir de un código corto:
   n = animal, k = color, e = cara, a = accesorio, f = fondo. Ejemplo: «n6-k0-e1-a5-f2».
   El mismo código se guarda en la base de datos (participantes.avatar). */
(() => {
  const ANIMALES = ['Conejo', 'Gato', 'Perrito', 'Oso', 'Coyote', 'Búho', 'Ajolote', 'Venado'];
  // [color principal, color claro] de cada animal
  const COLORES = [
    [['#F3EFEA', '#FFFFFF'], ['#B9AFA7', '#E9E3DD'], ['#A0714F', '#E7CBAE'], ['#E8D5B5', '#FFF6E6']],
    [['#F2A04E', '#FFE1BE'], ['#9AA0A8', '#E3E6EA'], ['#45434B', '#9C99A3'], ['#F3E3C7', '#FFFFFF']],
    [['#B07A4F', '#F1D7B8'], ['#E2C08F', '#FFF1DC'], ['#5A4A40', '#C2A794'], ['#F2F2F2', '#FFFFFF']],
    [['#8B5A3C', '#D9B08C'], ['#4A3F40', '#9C8D8E'], ['#F2F2F2', '#FFFFFF'], ['#C68A52', '#F3D3A8']],
    [['#C98B4F', '#F6E4CC'], ['#9A8F84', '#EFE8E0'], ['#E07B39', '#FFF0E0'], ['#8A6A4F', '#E6D5C3']],
    [['#9C6B4A', '#F0DDC5'], ['#7B7F8E', '#E6E8EE'], ['#C9A36B', '#FBF0DA'], ['#7A5A96', '#E8DDF3']],
    [['#F7A8C4', '#FFD9E7'], ['#F2C9A0', '#FFE8D2'], ['#9FD6C4', '#DFF5EE'], ['#C7B4F2', '#EDE5FF']],
    [['#B9834F', '#F3E1C9'], ['#A26D45', '#EBD3B8'], ['#D39B62', '#FBEAD5'], ['#8C6A51', '#E9DCCF']],
  ];
  const FONDOS = ['#FDE2EA', '#DFF3EA', '#FFF0CF', '#E2EAFB', '#EFE4FB', '#FFE3D6'];
  const PANUELOS = ['#E94C75', '#2F8B70', '#F2A93B', '#3B5BA9', '#8E4BB3', '#74203D'];
  const CARAS = ['Sonrisa', 'Feliz', 'Sorpresa', 'Guiño'];
  const ACCESORIOS = ['Nada', 'Flor', 'Sombrero', 'Moño', 'Lentes', 'Corona de flores'];
  const NOMBRES = {n: 'Animal', k: 'Color', e: 'Cara', a: 'Accesorio', f: 'Fondo'};
  const ORDEN = ['n', 'k', 'e', 'a', 'f'];
  const TOTAL = {n: ANIMALES.length, k: 4, e: CARAS.length, a: ACCESORIOS.length, f: FONDOS.length};
  const PREDETERMINADO = 'n0-k0-e0-a1-f0';

  function leer(codigo) {
    const v = {};
    for (const parte of String(codigo || '').split('-')) {
      const clave = parte[0], numero = Number(parte.slice(1));
      if (TOTAL[clave] && Number.isInteger(numero)) v[clave] = Math.min(Math.max(numero, 0), TOTAL[clave] - 1);
    }
    // Códigos anteriores (personas) o vacíos: se convierten en un animalito estable.
    if (v.n === undefined) {
      let h = 0; for (const c of String(codigo || 'x')) h = (h * 31 + c.charCodeAt(0)) >>> 0;
      v.n = h % TOTAL.n; v.k ??= (h >> 3) % 4; v.e ??= (h >> 5) % TOTAL.e; v.f ??= (h >> 7) % TOTAL.f; v.a ??= (h >> 9) % TOTAL.a;
    }
    for (const k of ORDEN) v[k] ??= 0;
    return v;
  }
  const escribir = v => ORDEN.map(k => k + v[k]).join('-');
  const aleatorio = () => escribir(Object.fromEntries(ORDEN.map(k => [k, Math.floor(Math.random() * TOTAL[k])])));
  function tono(hex, f) {
    const n = parseInt(hex.slice(1), 16);
    return '#' + [n >> 16, (n >> 8) & 255, n & 255].map(x => Math.round(f < 1 ? x * f : x + (255 - x) * (f - 1))).map(x => Math.min(255, Math.max(0, x)).toString(16).padStart(2, '0')).join('');
  }

  function svg(codigo, tam = 64, etiqueta = '') {
    const v = leer(codigo);
    const [piel, claro] = COLORES[v.n][v.k];
    const borde = tono(piel, .62), rosa = '#F7A1B8', oscuro = '#2B1B22';
    const fondo = FONDOS[v.f], panuelo = PANUELOS[v.f];
    const L = [];
    const linea = `stroke="${borde}" stroke-width="2.2" stroke-linejoin="round"`;
    L.push(`<circle cx="60" cy="60" r="60" fill="${fondo}"/>`,
      `<circle cx="22" cy="24" r="5" fill="#fff" opacity=".55"/><circle cx="98" cy="96" r="7" fill="#fff" opacity=".4"/><circle cx="100" cy="28" r="3" fill="#fff" opacity=".6"/>`);
    // Orejas o adornos de atrás
    const atras = {
      0: `<g ${linea}><ellipse cx="45" cy="24" rx="8" ry="22" fill="${piel}" transform="rotate(-12 45 24)"/><ellipse cx="75" cy="24" rx="8" ry="22" fill="${piel}" transform="rotate(12 75 24)"/></g><ellipse cx="45" cy="25" rx="3.6" ry="15" fill="${rosa}" transform="rotate(-12 45 25)"/><ellipse cx="75" cy="25" rx="3.6" ry="15" fill="${rosa}" transform="rotate(12 75 25)"/>`,
      1: `<g ${linea}><path d="M33 48 L37 17 L56 34 Z" fill="${piel}"/><path d="M87 48 L83 17 L64 34 Z" fill="${piel}"/></g><path d="M38 40 L40 25 L50 34 Z" fill="${rosa}"/><path d="M82 40 L80 25 L70 34 Z" fill="${rosa}"/>`,
      2: '',
      3: `<g ${linea}><circle cx="36" cy="36" r="11" fill="${piel}"/><circle cx="84" cy="36" r="11" fill="${piel}"/></g><circle cx="36" cy="36" r="5.5" fill="${claro}"/><circle cx="84" cy="36" r="5.5" fill="${claro}"/>`,
      4: `<g ${linea}><path d="M31 50 L33 10 L56 32 Z" fill="${piel}"/><path d="M89 50 L87 10 L64 32 Z" fill="${piel}"/></g><path d="M36 42 L37 21 L50 33 Z" fill="${tono(piel, .7)}"/><path d="M84 42 L83 21 L70 33 Z" fill="${tono(piel, .7)}"/>`,
      5: `<g ${linea}><path d="M34 40 L36 16 L52 32 Z" fill="${piel}"/><path d="M86 40 L84 16 L68 32 Z" fill="${piel}"/></g>`,
      6: [[-1, 1], [1, -1]].map(([lado]) => [0, 1, 2].map(i => {
        const x = 60 + lado * 34, y = 44 + i * 13, ang = lado * (-35 + i * 35);
        return `<ellipse cx="${x + lado * 8}" cy="${y}" rx="12" ry="5" fill="${tono(piel, .82)}" transform="rotate(${ang} ${x} ${y})" ${linea}/>`;
      }).join('')).join(''),
      7: `<g stroke="#7A4E2D" stroke-width="4" fill="none" stroke-linecap="round"><path d="M46 32 L40 12 M42 20 L32 16 M41 15 L44 6"/><path d="M74 32 L80 12 M78 20 L88 16 M79 15 L76 6"/></g><g ${linea}><ellipse cx="30" cy="46" rx="13" ry="6.5" fill="${piel}" transform="rotate(-22 30 46)"/><ellipse cx="90" cy="46" rx="13" ry="6.5" fill="${piel}" transform="rotate(22 90 46)"/></g><ellipse cx="31" cy="46" rx="7" ry="3" fill="${rosa}" transform="rotate(-22 31 46)"/><ellipse cx="89" cy="46" rx="7" ry="3" fill="${rosa}" transform="rotate(22 89 46)"/>`,
    }[v.n];
    L.push(atras);
    // Cuerpo con paliacate
    L.push(`<path d="M22 122 Q24 92 60 90 Q96 92 98 122 Z" fill="${piel}" ${linea}/>`,
      `<path d="M30 120 Q34 100 60 98 Q86 100 90 120 Z" fill="${claro}"/>`,
      `<path d="M38 90 Q60 104 82 90 L76 99 Q60 110 44 99 Z" fill="${panuelo}"/><path d="M60 100 L54 112 L66 112 Z" fill="${panuelo}"/>`,
      `<g fill="#fff" opacity=".8"><circle cx="48" cy="97" r="1.6"/><circle cx="60" cy="102" r="1.6"/><circle cx="72" cy="97" r="1.6"/></g>`);
    // Cabeza
    const cabeza = v.n === 6 ? `<ellipse cx="60" cy="60" rx="34" ry="27" fill="${piel}" ${linea}/>`
      : v.n === 5 ? `<ellipse cx="60" cy="60" rx="31" ry="30" fill="${piel}" ${linea}/><ellipse cx="60" cy="62" rx="24" ry="21" fill="${claro}"/>`
        : `<ellipse cx="60" cy="60" rx="30" ry="28" fill="${piel}" ${linea}/>`;
    L.push(cabeza);
    if (v.n === 2) L.push(`<g ${linea}><ellipse cx="32" cy="58" rx="9" ry="19" fill="${tono(piel, .72)}" transform="rotate(18 32 58)"/><ellipse cx="88" cy="58" rx="9" ry="19" fill="${tono(piel, .72)}" transform="rotate(-18 88 58)"/></g>`);
    if (v.n === 7) L.push(`<g fill="${claro}" opacity=".9"><circle cx="52" cy="40" r="2.4"/><circle cx="60" cy="37" r="2.4"/><circle cx="68" cy="40" r="2.4"/></g>`);
    // Hocico
    if ([2, 3, 4, 7].includes(v.n)) L.push(`<ellipse cx="60" cy="71" rx="14" ry="10.5" fill="${claro}"/>`);
    if (v.n === 1 || v.n === 0) L.push(`<ellipse cx="60" cy="70" rx="11" ry="8" fill="${claro}"/>`);
    // Ojos según la cara
    const ojosX = v.n === 6 ? [44, 76] : [48.5, 71.5];
    const y = v.n === 6 ? 56 : 57;
    if (v.n === 5) L.push(`<circle cx="48" cy="56" r="10" fill="#fff" stroke="${borde}" stroke-width="1.6"/><circle cx="72" cy="56" r="10" fill="#fff" stroke="${borde}" stroke-width="1.6"/>`);
    const ojo = (x, cerrado) => cerrado
      ? `<path d="M${x - 4.5} ${y + 1} Q${x} ${y - 4} ${x + 4.5} ${y + 1}" stroke="${oscuro}" stroke-width="2.6" fill="none" stroke-linecap="round"/>`
      : `<ellipse cx="${x}" cy="${y}" rx="${v.e === 2 ? 5 : 4.2}" ry="${v.e === 2 ? 5.6 : 5}" fill="${oscuro}"/><circle cx="${x + 1.6}" cy="${y - 1.8}" r="1.7" fill="#fff"/><circle cx="${x - 1.4}" cy="${y + 1.8}" r=".8" fill="#fff"/>`;
    L.push(ojo(ojosX[0], v.e === 1), ojo(ojosX[1], v.e === 1 || v.e === 3));
    // Cachetes
    L.push(`<ellipse cx="${ojosX[0] - 7}" cy="68" rx="5.5" ry="3.6" fill="#FF8FAB" opacity=".55"/><ellipse cx="${ojosX[1] + 7}" cy="68" rx="5.5" ry="3.6" fill="#FF8FAB" opacity=".55"/>`);
    // Nariz o pico
    if (v.n === 5) L.push(`<path d="M55 63 L65 63 L60 72 Z" fill="#F2A93B" stroke="#C47F1C" stroke-width="1.2" stroke-linejoin="round"/>`);
    else if (v.n !== 6) L.push(`<path d="M56 64.5 Q60 62.5 64 64.5 Q62 69 60 69 Q58 69 56 64.5 Z" fill="${v.n === 0 || v.n === 1 ? '#F07C9B' : oscuro}"/>`);
    // Boca
    const bocaY = v.n === 6 ? 68 : 72;
    L.push([
      `<path d="M53 ${bocaY} Q56.5 ${bocaY + 4} 60 ${bocaY} Q63.5 ${bocaY + 4} 67 ${bocaY}" stroke="${oscuro}" stroke-width="2" fill="none" stroke-linecap="round"/>`,
      `<path d="M52 ${bocaY - 1} Q60 ${bocaY + 11} 68 ${bocaY - 1} Z" fill="#8E2A3B"/><path d="M56 ${bocaY + 4} Q60 ${bocaY + 8} 64 ${bocaY + 4}" fill="#FF8FA8"/>`,
      `<ellipse cx="60" cy="${bocaY + 2}" rx="3.6" ry="4.4" fill="#8E2A3B"/>`,
      `<path d="M53 ${bocaY} Q60 ${bocaY + 6} 67 ${bocaY}" stroke="${oscuro}" stroke-width="2" fill="none" stroke-linecap="round"/>`,
    ][v.e]);
    if (v.n === 0) L.push(`<rect x="57.5" y="${bocaY + 1}" width="5" height="4.5" rx="1" fill="#fff" stroke="${borde}" stroke-width=".8"/>`);
    if (v.n === 1) L.push(`<g stroke="${borde}" stroke-width="1.3" stroke-linecap="round"><path d="M44 68 L32 66 M44 71 L32 73"/><path d="M76 68 L88 66 M76 71 L88 73"/></g>`);
    // Accesorio
    const flor = (x, yy, c = '#E94C75', r = 4.6) => `<g transform="translate(${x} ${yy})">${[0, 72, 144, 216, 288].map(g => `<circle r="${r}" cx="${Math.cos(g * Math.PI / 180) * r * 1.15}" cy="${Math.sin(g * Math.PI / 180) * r * 1.15}" fill="${c}"/>`).join('')}<circle r="${r * .72}" fill="#F7C548"/></g>`;
    L.push({
      0: '',
      1: flor(84, 38),
      2: `<ellipse cx="60" cy="36" rx="34" ry="7" fill="#E3B96A" stroke="#B9873A" stroke-width="1.4"/><path d="M40 36 Q42 14 60 14 Q78 14 80 36 Z" fill="#EDC97E" stroke="#B9873A" stroke-width="1.4"/><path d="M41 31 Q60 37 79 31" stroke="${panuelo}" stroke-width="4" fill="none"/>`,
      3: `<g transform="translate(60 31)"><path d="M0 0 L-14 -8 L-14 8 Z" fill="${panuelo}"/><path d="M0 0 L14 -8 L14 8 Z" fill="${panuelo}"/><circle r="4.2" fill="${tono(panuelo, .75)}"/></g>`,
      4: `<g fill="rgba(255,255,255,.25)" stroke="${oscuro}" stroke-width="2.2"><circle cx="${ojosX[0]}" cy="${y}" r="8.5"/><circle cx="${ojosX[1]}" cy="${y}" r="8.5"/></g><path d="M${ojosX[0] + 8.5} ${y} L${ojosX[1] - 8.5} ${y}" stroke="${oscuro}" stroke-width="2.2"/>`,
      5: flor(40, 36, '#E94C75', 4) + flor(51, 31, '#F2A93B', 4) + flor(62, 30, '#8E4BB3', 4) + flor(73, 32, '#2F8B70', 4) + flor(83, 37, '#E94C75', 4),
    }[v.a]);
    const nombre = String(etiqueta || '').replace(/[<&>"]/g, '');
    const id = 'av' + Math.random().toString(36).slice(2, 8);
    return `<svg class="avatar-svg" viewBox="0 0 120 120" width="${tam}" height="${tam}" role="img" aria-label="${nombre ? 'Avatar de ' + nombre : 'Avatar: ' + ANIMALES[v.n].toLowerCase()}">${nombre ? `<title>${nombre}</title>` : ''}<defs><clipPath id="${id}"><circle cx="60" cy="60" r="60"/></clipPath></defs><g clip-path="url(#${id})">${L.join('')}</g></svg>`;
  }

  function nodo(codigo, tam, etiqueta) {
    const span = document.createElement('span');
    span.className = 'avatar-burbuja';
    span.innerHTML = svg(codigo, tam, etiqueta);
    return span;
  }

  /* Editor interactivo: vista previa grande + pestañas con muestras. */
  function crearEditor(contenedor, inicial, alCambiar) {
    let valores = leer(inicial);
    let pestana = 'n';
    contenedor.classList.add('avatar-editor');
    contenedor.innerHTML = '';
    const vista = document.createElement('div'); vista.className = 'avatar-vista';
    const nombreAnimal = document.createElement('p'); nombreAnimal.className = 'avatar-nombre';
    const azar = document.createElement('button'); azar.type = 'button'; azar.className = 'avatar-azar'; azar.textContent = '🎲 Sorpréndeme';
    const pestanas = document.createElement('div'); pestanas.className = 'avatar-pestanas'; pestanas.setAttribute('role', 'tablist');
    const opciones = document.createElement('div'); opciones.className = 'avatar-opciones'; opciones.setAttribute('role', 'radiogroup');
    const izquierda = document.createElement('div'); izquierda.className = 'avatar-izquierda';
    izquierda.append(vista, nombreAnimal, azar);
    const derecha = document.createElement('div'); derecha.className = 'avatar-derecha';
    derecha.append(pestanas, opciones);
    contenedor.append(izquierda, derecha);

    const etiquetaDe = (k, i) => ({n: ANIMALES, e: CARAS, a: ACCESORIOS}[k]?.[i] || `${NOMBRES[k]} ${i + 1}`);
    function actualizar(animar = true) {
      const codigo = escribir(valores);
      vista.innerHTML = svg(codigo, 132, '');
      nombreAnimal.textContent = ANIMALES[valores.n];
      if (animar) { vista.classList.remove('rebote'); void vista.offsetWidth; vista.classList.add('rebote'); }
      pestanas.replaceChildren(...ORDEN.map(k => {
        const b = document.createElement('button'); b.type = 'button'; b.textContent = NOMBRES[k];
        b.setAttribute('role', 'tab'); b.setAttribute('aria-selected', String(k === pestana));
        b.onclick = () => { pestana = k; actualizar(false); }; return b;
      }));
      opciones.setAttribute('aria-label', NOMBRES[pestana]);
      opciones.replaceChildren(...Array.from({length: TOTAL[pestana]}, (_, i) => {
        const b = document.createElement('button'); b.type = 'button'; b.className = 'avatar-opcion';
        b.setAttribute('role', 'radio'); b.setAttribute('aria-checked', String(valores[pestana] === i));
        const texto = etiquetaDe(pestana, i); b.setAttribute('aria-label', texto); b.title = texto;
        if (pestana === 'f') { b.classList.add('muestra-color'); b.style.setProperty('--muestra', FONDOS[i]); }
        else b.innerHTML = svg(escribir({...valores, [pestana]: i}), 46);
        b.onclick = () => { valores = {...valores, [pestana]: i}; actualizar(); alCambiar?.(escribir(valores)); };
        return b;
      }));
    }
    azar.onclick = () => { valores = leer(aleatorio()); actualizar(); alCambiar?.(escribir(valores)); };
    actualizar(false);
    return {valor: () => escribir(valores)};
  }

  window.Avatar = {svg, nodo, crearEditor, aleatorio, leer, escribir, PREDETERMINADO, ANIMALES};
})();
