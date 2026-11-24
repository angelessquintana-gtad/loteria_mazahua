/* Lectura administrativa: UID visible, registro automático y diagnóstico serial. */
(() => {
  const button = document.createElement('button');
  button.type = 'button'; button.className = 'secondary'; button.textContent = 'Conectar lector USB';
  document.querySelector('.scan').append(button);
  const lector = new window.LectorUSB(async uid => {
    $('ultimoUidAdmin').textContent = uid;
    $('scanStatus').textContent = 'Tarjeta detectada: ' + uid;
    $('scanStatus').style.color = 'var(--mint)';
    await procesarLectura(uid);
  }, (text, connected) => {
    window.adminLectorConectado = connected;
    button.textContent = connected ? 'Desconectar lector USB' : 'Conectar lector USB';
    setReaderStatus(text, connected ? 'var(--mint)' : 'var(--red)');
  }, line => {
    const log = $('adminSerialLog');
    log.textContent = [...(log.dataset.received ? log.textContent.split('\n') : []), line].slice(-20).join('\n');
    log.dataset.received = 'true';
  });
  button.onclick = async () => {
    button.disabled = true;
    try {
      if (window.adminLectorConectado) await lector.desconectar(); else await lector.conectar();
    } catch (error) {
      if (error.name !== 'NotFoundError') setReaderStatus('No se pudo conectar. Cierra Arduino o el puente serial. ' + error.message, 'var(--red)');
    } finally { button.disabled = false; }
  };
})();
