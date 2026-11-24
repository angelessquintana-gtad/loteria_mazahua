// Mi cuenta: editar nombre y correo, y cambiar la contraseña.
(() => {
  const $ = id => document.getElementById(id);
  const mensaje = (id, texto, bien) => { $(id).textContent = texto; $(id).className = bien ? 'aviso-ok' : 'aviso-error'; };
  async function enviar(ruta, datos, metodo) {
    const r = await fetch(ruta, {method: metodo, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(datos)});
    let d = {}; try { d = await r.json(); } catch {}
    if (!r.ok) throw Error(typeof d.detail === 'string' ? d.detail : 'Revisa los datos e intenta de nuevo.');
    return d;
  }
  window.docenteActual.then(d => {
    $('perfilNombre').value = d.nombre; $('perfilCorreo').value = d.correo;
    const fecha = d.fecha_registro ? new Date(d.fecha_registro + 'Z').toLocaleDateString('es-MX', {dateStyle: 'long'}) : '';
    $('resumenCuenta').textContent = `${d.nombre} · ${d.correo}` + (fecha ? ` · Cuenta creada el ${fecha}` : '');
  }).catch(() => {});
  $('perfilForm').onsubmit = async e => {
    e.preventDefault(); const b = $('perfilGuardar'); b.disabled = true;
    try {
      if (!/^[^\s@]+@[^\s@]+\.[a-z]{2,63}$/i.test($('perfilCorreo').value.trim())) throw Error('Escribe un correo electrónico válido.');
      const r = await enviar('/api/auth/perfil', {nombre: $('perfilNombre').value, correo: $('perfilCorreo').value, password: $('perfilPassword').value}, 'PUT');
      $('perfilPassword').value = ''; mensaje('mensajePerfil', '✓ ' + r.mensaje, true);
      $('resumenCuenta').textContent = `${$('perfilNombre').value.trim()} · ${$('perfilCorreo').value.trim().toLowerCase()}`;
    } catch (err) { mensaje('mensajePerfil', err.message, false); } finally { b.disabled = false; }
  };
  $('passwordForm').onsubmit = async e => {
    e.preventDefault(); const b = $('passwordGuardar'); b.disabled = true;
    try {
      if ($('nueva').value.length < 6) throw Error('La nueva contraseña debe tener al menos 6 caracteres.');
      if ($('nueva').value !== $('repetida').value) throw Error('Las contraseñas no coinciden.');
      const r = await enviar('/api/auth/password', {actual: $('actual').value, nueva: $('nueva').value}, 'POST');
      mensaje('mensajePassword', '✓ ' + r.mensaje, true);
      setTimeout(() => location.replace('/acceso'), 1800);
    } catch (err) { mensaje('mensajePassword', err.message, false); b.disabled = false; }
  };
})();
