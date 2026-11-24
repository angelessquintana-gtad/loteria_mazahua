// Acceso docente: iniciar sesión, crear cuenta, recuperar y restablecer contraseña.
(() => {
  const $ = id => document.getElementById(id);
  const parametros = new URLSearchParams(location.search);
  const privadas = ['/panel', '/docente', '/administracion', '/editar', '/cuenta'];
  const destino = privadas.includes(parametros.get('destino')) ? parametros.get('destino') : '/panel';
  const correoValido = v => /^[^\s@]+@[^\s@]+\.[a-z]{2,63}$/i.test(v.trim());
  let token = new URLSearchParams(location.hash.slice(1)).get('recuperar') || '';
  if (token) history.replaceState(null, '', location.pathname);

  const ok = t => { $('avisoOk').textContent = t; $('avisoError').textContent = ''; };
  const error = t => { $('avisoError').textContent = t; $('avisoOk').textContent = ''; };
  const limpiar = () => { $('avisoOk').textContent = ''; $('avisoError').textContent = ''; };
  async function enviar(ruta, datos) {
    const r = await fetch('/api/auth/' + ruta, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(datos)});
    let resultado = {}; try { resultado = await r.json(); } catch {}
    if (!r.ok) throw Error(typeof resultado.detail === 'string' ? resultado.detail : 'Revisa los datos e intenta de nuevo.');
    return resultado;
  }
  async function ocupado(boton, tarea) { boton.disabled = true; try { await tarea(); } catch (e) { error(e.message); } finally { boton.disabled = false; } }

  function modo(nombre) {
    for (const f of ['loginForm', 'registroForm', 'recuperarForm', 'restablecerForm']) $(f).hidden = true;
    $(nombre + 'Form').hidden = false;
    $('tabLogin').setAttribute('aria-selected', nombre === 'login'); $('tabRegistro').setAttribute('aria-selected', nombre === 'registro');
    $('accesoTitulo').textContent = {login: 'Iniciar sesión como docente', registro: 'Crear cuenta de docente',
      recuperar: '¿Olvidaste tu contraseña?', restablecer: 'Elige una nueva contraseña'}[nombre];
    document.querySelector('.pestanas').hidden = !['login', 'registro'].includes(nombre);
  }
  $('tabLogin').onclick = () => { limpiar(); modo('login'); $('loginCorreo').focus(); };
  $('tabRegistro').onclick = () => { limpiar(); modo('registro'); $('regNombre').focus(); };
  $('olvide').onclick = () => { limpiar(); $('recCorreo').value = $('loginCorreo').value; modo('recuperar'); $('recCorreo').focus(); };
  $('volverLogin1').onclick = $('volverLogin2').onclick = () => { limpiar(); modo('login'); };

  $('loginForm').onsubmit = e => { e.preventDefault(); ocupado($('loginEnviar'), async () => {
    const correo = $('loginCorreo').value.trim(), password = $('loginPassword').value;
    if (!correoValido(correo)) throw Error('Escribe un correo electrónico válido.');
    if (!password) throw Error('Escribe tu contraseña.');
    const r = await enviar('login', {correo, password});
    ok(r.mensaje + ' Entrando a tu panel…');
    setTimeout(() => location.replace(destino), 700);
  }); };

  $('registroForm').onsubmit = e => { e.preventDefault(); ocupado($('regEnviar'), async () => {
    const datos = {nombre: $('regNombre').value.trim(), correo: $('regCorreo').value.trim(),
                   password: $('regPassword').value, confirmacion: $('regConfirmacion').value};
    if (datos.nombre.length < 2) throw Error('Escribe tu nombre completo.');
    if (!correoValido(datos.correo)) throw Error('Escribe un correo electrónico válido, por ejemplo nombre@escuela.mx.');
    if (datos.password.length < 6) throw Error('La contraseña debe tener al menos 6 caracteres.');
    if (datos.password !== datos.confirmacion) throw Error('Las contraseñas no coinciden.');
    const r = await enviar('registro', datos);
    $('registroForm').reset(); modo('login'); $('loginCorreo').value = r.correo; $('loginPassword').focus();
    ok(r.mensaje);
  }); };

  $('recuperarForm').onsubmit = e => { e.preventDefault(); ocupado($('recEnviar'), async () => {
    const correo = $('recCorreo').value.trim();
    if (!correoValido(correo)) throw Error('Escribe un correo electrónico válido.');
    const r = await enviar('recuperar', {correo});
    ok(r.mensaje);
    if (r.enlace) {
      const a = Object.assign(document.createElement('a'), {href: r.enlace, textContent: 'Abrir enlace para crear mi nueva contraseña →'});
      a.onclick = ev => { ev.preventDefault(); token = new URLSearchParams(r.enlace.split('#')[1]).get('recuperar'); limpiar(); modo('restablecer'); $('nuevaPassword').focus(); };
      $('enlaceLocal').replaceChildren(a); $('enlaceLocal').hidden = false;
    }
  }); };

  $('restablecerForm').onsubmit = e => { e.preventDefault(); ocupado($('resEnviar'), async () => {
    const nueva = $('nuevaPassword').value;
    if (nueva.length < 6) throw Error('La contraseña debe tener al menos 6 caracteres.');
    if (nueva !== $('nuevaConfirmacion').value) throw Error('Las contraseñas no coinciden.');
    const r = await enviar('restablecer', {token, nueva});
    token = ''; $('restablecerForm').reset(); modo('login'); $('loginCorreo').value = r.correo || ''; $('loginPassword').focus();
    ok(r.mensaje);
  }); };

  window.addEventListener('hashchange', () => {
    const nuevo = new URLSearchParams(location.hash.slice(1)).get('recuperar');
    if (nuevo) { token = nuevo; history.replaceState(null, '', location.pathname); limpiar(); modo('restablecer'); }
  });
  if (token) modo('restablecer');
  else if (parametros.get('modo') === 'registro') modo('registro');
  else modo('login');
  if (parametros.get('salida')) ok('Cerraste sesión correctamente.');
  if (parametros.get('destino')) error('Inicia sesión para continuar.');
})();
