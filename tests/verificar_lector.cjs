// Ejecutar desde la raíz: node tests/verificar_lector.cjs.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const chunks = ['READY:ok\nUID:C9 72', ' 1A 10\r\nUID:C9 72 1A 10\n', 'UID:01:02:03:04:05:06:07\nERROR:ruido\n'];
const received = [], statuses = [];
let released = false, closed = false;
let aperturas = 0;
const fakePort = {
  async open(options) { assert.equal(options.baudRate, 115200); if (++aperturas > 1) throw Error('Cable desconectado'); },
  async setSignals(options) { assert.equal(options.dataTerminalReady, false); assert.equal(options.requestToSend, false); },
  async close() { closed = true; },
  readable: {getReader() { return {
    async read() { return chunks.length ? {value:new TextEncoder().encode(chunks.shift()), done:false} : {done:true}; },
    releaseLock() { released = true; }, async cancel() {},
  }; }},
};
const ctx = vm.createContext({window:{isSecureContext:true}, navigator:{serial:{async requestPort() { return fakePort; }}}, TextDecoder, Date,
  setInterval, clearInterval, setTimeout(fn) { return setTimeout(fn, 0); }});
vm.runInContext(fs.readFileSync('static/lector-usb.js','utf8'),ctx);
const Reader = ctx.window.LectorUSB;
assert.equal(Reader.extraer('UID:C9-72-1a-10'),'C9 72 1A 10');
assert.equal(Reader.extraer('Tarjeta detectada: 01 02 03 04'),'01 02 03 04');
assert.equal(Reader.extraer('}�!�UID:A9 DD 25 10'),'A9 DD 25 10');
for (const value of ['ERROR:fallo','UID:FF','UID:01 02 03','UID:zz 22 33 44']) assert.equal(Reader.extraer(value),null);
(async () => {
  const reader = new Reader(uid=>received.push(uid),(text,connected)=>statuses.push(connected));
  await reader.conectar(); await reader.done;
  assert.deepEqual(received,['C9 72 1A 10','01 02 03 04 05 06 07']);
  assert.deepEqual(statuses,[true,true,true,true,false,false]);
  assert.equal(aperturas, 6, 'Se intenta reconectar cinco veces después de desconectar el cable');
  assert.ok(released && closed && !reader.port);
  ctx.window.isSecureContext = false;
  await assert.rejects(()=>reader.conectar(),/HTTPS/);
  console.log('OK: líneas USB fragmentadas, UID normalizado, antirrebote, cierre de puerto y HTTPS.');
})().catch(error=>{console.error(error);process.exitCode=1;});
