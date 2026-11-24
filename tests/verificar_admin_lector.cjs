/* Ejecutar desde la raíz: node tests/verificar_admin_lector.cjs.
   Regresión: USB real de la clase compartida + callbacks del administrador.
   No requiere dispositivo físico ni modifica la base de datos. */
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const tick = () => new Promise(resolve => setTimeout(resolve, 25));
function portFake() {
  let resolver, abierto = false;
  const cola = [];
  return {
    getInfo: () => ({usbVendorId: 123, usbProductId: 456}),
    async open() { if (abierto) throw Error('Puerto ocupado'); abierto = true; },
    async setSignals() {}, async close() { abierto = false; },
    enviar(texto) { const value = new TextEncoder().encode(texto); if (resolver) { const r = resolver; resolver = null; r({value, done: false}); } else cola.push({value, done: false}); },
    readable: {getReader() { return {
      read() { return cola.length ? Promise.resolve(cola.shift()) : new Promise(resolve => { resolver = resolve; }); },
      async cancel() { if (resolver) { const r = resolver; resolver = null; r({done: true}); } }, releaseLock() {},
    }; }},
  };
}
function contextoPuerto(puerto) {
  const ctx = vm.createContext({window: {isSecureContext: true},
    navigator: {serial: {requestPort: async () => puerto}}, TextDecoder, Date, Promise, setTimeout, clearTimeout, setInterval, clearInterval});
  vm.runInContext(fs.readFileSync('static/lector-usb.js', 'utf8'), ctx);
  return ctx;
}
async function probarPuertoExclusivo() {
  const puerto = portFake(), a = contextoPuerto(puerto), b = contextoPuerto(puerto);
  const lecturasA = [], lecturasB = [];
  const docente = new a.window.LectorUSB(uid => lecturasA.push(uid), () => {});
  const admin = new b.window.LectorUSB(uid => lecturasB.push(uid), () => {});
  await docente.conectar();
  await assert.rejects(() => admin.conectar(), /puerto no está disponible/);
  assert.ok(docente.running, 'Administración no debe desconectar la lectura docente');
  assert.equal(admin.port, null);
  puerto.enviar('UID:01 02 03 04\n'); await tick();
  assert.deepEqual(lecturasA, ['01 02 03 04']); assert.deepEqual(lecturasB, []);
  await docente.desconectar();
  await admin.conectar();
  puerto.enviar('UID:01 02 03 04\n'); await tick();
  assert.deepEqual(lecturasB, ['01 02 03 04']);
  await admin.desconectar();
  await admin.conectar();
  puerto.enviar('UID:01 02 03 04\n'); await tick();
  assert.equal(lecturasB.length, 2, 'Reconectar debe permitir releer el mismo UID inmediatamente');
  await admin.desconectar();
}
async function probarErroresCallback() {
  const puerto = portFake(), ctx = contextoPuerto(puerto), vistos = [], estados = [];
  const lector = new ctx.window.LectorUSB(uid => {
    vistos.push(uid);
    if (vistos.length === 1) throw Error('Error síncrono del panel');
    if (vistos.length === 2) return Promise.reject(Error('Error asíncrono del panel'));
  }, texto => estados.push(texto));
  await lector.conectar();
  puerto.enviar('UID:01 02 03 04\nUID:05 06 07 08\nUID:09 10 11 12\n'); await tick();
  assert.equal(vistos.length, 3); assert.ok(lector.running, 'Un error de la interfaz no debe desconectar el USB');
  assert.equal(estados.filter(t => t.includes('Error al procesarlo')).length, 2);
  await lector.desconectar();
}
async function probarAdministrador() {
  const puerto = portFake(), ctx = contextoPuerto(puerto), elementos = new Map(), creados = [], guardadas = [];
  let falloRegistro = false;
  const elemento = id => {
    if (!elementos.has(id)) elementos.set(id, {textContent: '', value: '', checked: id === 'autoCatalogo', style: {}, dataset: {},
      addEventListener() {}, removeEventListener() {}, append() {}, focus() {}});
    return elementos.get(id);
  };
  Object.assign(ctx, {AbortController, FormData, URL,
    $: elemento,
    document: {createElement() { const e = elemento('boton-' + creados.length); creados.push(e); return e; }, querySelector: () => ({append() {}})},
    fetch: async (url, options = {}) => {
      let status = 200, data;
      if (url === '/api/catalogo/estado') data = {total: 54, asignadas: guardadas.length, siguiente: {traduccion_espanol: 'Siguiente', palabra_mazahua: 'Palabra'}};
      else if (url.startsWith('/api/uid/')) { data = guardadas.find(t => t.uid === decodeURIComponent(url.slice('/api/uid/'.length))); if (!data) { status = 404; data = {detail: 'No registrada'}; } }
      else if (url === '/api/catalogo/registrar') {
        if (falloRegistro) { status = 503; data = {detail: 'Base de datos no disponible'}; }
        else {
          const {uid} = JSON.parse(options.body);
          const tarjeta = {id: guardadas.length + 1, uid, palabra_mazahua: 'Mazahua', traduccion_espanol: 'Palabra ' + (guardadas.length + 1), audio_espanol_url: null};
          guardadas.push(tarjeta); data = {tarjeta, nueva: true};
        }
      } else throw Error('Ruta inesperada: ' + url);
      return {ok: status === 200, status, json: async () => data};
    },
  });
  ctx.window.addEventListener = () => {};
  vm.runInContext(`let cards=[], editingId=null; const reproducciones=[];
    function showMessage(text){$('message').textContent=text}
    function setSimMessage(text){$('simulateMessage').textContent=text}
    function setReaderStatus(text){$('readerStatus').textContent=text}
    function stopSequence(){} function showSimulatedCard(t){$('simulatedWord').textContent=t.palabra_mazahua}
    async function readCard(uid,automatic){reproducciones.push({uid,automatic})}
    async function loadCards(){} function clearForm(){} function simulateRead(){}
    window.editCard=async id=>{editingId=id}; window.deleteCard=async()=>{};
    async function procesarLectura(uid){await window.registroAutomatico.leer(uid)};`, ctx);
  vm.runInContext(fs.readFileSync('static/registro-automatico.js', 'utf8'), ctx);
  vm.runInContext(fs.readFileSync('static/admin-usb.js', 'utf8'), ctx);
  await creados[0].onclick();
  puerto.enviar('READY:RFID USB 115200\nUID:01 02'); puerto.enviar(' 03 04\r\n'); await tick();
  assert.equal(elemento('ultimoUidAdmin').textContent, '01 02 03 04');
  assert.equal(guardadas.length, 1);
  assert.match(elemento('adminSerialLog').textContent, /UID:01 02 03 04/);
  puerto.enviar('UID:05 06 07 08\n'); await tick();
  assert.equal(guardadas.length, 2, 'La falta de español anterior no debe bloquear la lectura siguiente');
  puerto.enviar('UID:01 02 03 04\n'); await tick();
  assert.equal(guardadas.length, 2, 'Consultar una existente no debe importar otra palabra');
  assert.ok(vm.runInContext('reproducciones.every(r=>r.automatic)', ctx));
  falloRegistro = true;
  puerto.enviar('UID:09 10 11 12\n'); await tick();
  assert.equal(elemento('ultimoUidAdmin').textContent, '09 10 11 12');
  assert.match(elemento('simulateMessage').textContent, /UID leído.*Base de datos no disponible/);
  assert.ok(ctx.window.adminLectorConectado, 'Una falla de base de datos no debe cerrar el puerto');
  await creados[0].onclick();
}
(async () => {
  const html = fs.readFileSync('static/administracion.html', 'utf8');
  const parser = vm.runInNewContext(html.match(/^async function respuestaApi.*$/m)[0] + '; respuestaApi');
  await assert.rejects(() => parser(new Response('Internal Server Error', {status: 500})), /HTTP 500/);
  await assert.rejects(() => parser(new Response(JSON.stringify({detail:'Finaliza la partida ABC123'}), {status: 409})), /Finaliza la partida ABC123/);
  assert.equal((await parser(new Response(JSON.stringify({ok:true})))).ok, true);
  await probarPuertoExclusivo(); await probarErroresCallback(); await probarAdministrador();
  console.log('OK: puerto exclusivo sin desconectar otras pestañas, reconexión, errores sin desconectar USB, UID fragmentado visible, registro sucesivo, consulta existente, reproducción y errores de API visibles.');
})().catch(e => {console.error(e); process.exitCode = 1;});
