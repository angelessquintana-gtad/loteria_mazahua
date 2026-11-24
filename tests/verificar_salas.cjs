// Ejecutar desde la raíz: node tests/verificar_salas.cjs.
// Regresión: una respuesta del backend anterior debe informar, no romper la página.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
function element() {
  return {textContent: '', hidden: false, style: {}, classList: {toggle() {}, add() {}},
    after() {}, append() {}, replaceChildren() {}, setAttribute() {},
    querySelector() { return {textContent: ''}; }, showModal() { this.open = true; }, close() { this.open = false; }};
}
const elements = new Map();
const context = vm.createContext({
  document: {body: {dataset: {role: 'estudiante'}, classList: {toggle() {}}}, createElement: element,
    getElementById(id) { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); }},
  sessionStorage: {getItem() { return null; }},
  location: {search: '', origin: 'http://localhost:8000'},
  URLSearchParams, window: {addEventListener() {}},
});
vm.runInContext(fs.readFileSync('static/salas.js', 'utf8'), context);
assert.equal(vm.runInContext("render({codigo:'ABC234', estado:'en_curso', participantes:[], limite:25})", context), false);
assert.match(elements.get('message').textContent, /versión anterior/);
assert.equal(vm.runInContext("render({codigo:'ABC234', estado:'esperando', participantes:[], anunciadas:[], limite:25})", context), true);
assert.equal(vm.runInContext("render({codigo:'ABC234', estado:'en_curso', participantes:[], anunciadas:[], limite:25, tablero:{cartas:[]}})", context), false);
console.log('OK: respuestas antiguas/incompletas y sala válida sin error de length.');

// El docente renueva su sesión y solo confirma el cierre después del éxito HTTP.
(async () => {
  const nodos = new Map(), intervalos = [], reintentos = [], solicitudes = [];
  let fallarCierre = true;
  const sala = {codigo:'ABC234', nombre:'Grupo de prueba', estado:'esperando', participantes:[], anunciadas:[], limite:25};
  const docente = vm.createContext({
    document: {body: {dataset: {role:'docente'}, classList:{toggle(){}}}, createElement:element,
      getElementById(id) {if(!nodos.has(id))nodos.set(id,element());return nodos.get(id);}},
    sessionStorage:{getItem(){return null;},setItem(){}},
    location:{origin:'http://localhost:8000',hostname:'localhost',protocol:'http:',host:'localhost:8000'},
    URL, URLSearchParams,
    navigator:{clipboard:{writeText:async()=>{}}},
    window:{addEventListener(){},LectorUSB:class{},SecuenciaAudio:class{detener(){} async habilitar(){}}},
    WebSocket:class{close(){}}, confirm:()=>true,
    setInterval(fn,ms){intervalos.push({fn,ms});}, clearTimeout(){},
    setTimeout(fn,ms){reintentos.push({fn,ms});},
    fetch:async(path,options)=>{
      const datos=JSON.parse(options.body); solicitudes.push({path,datos});
      if(path.endsWith('/latido'))return {ok:true,json:async()=>({estado:sala.estado})};
      if(path.endsWith('/finalizar')){
        if(fallarCierre)return {ok:false,json:async()=>({detail:'Error de conexión con la base'})};
        sala.estado='finalizada';return {ok:true,json:async()=>({...sala})};
      }
      return {ok:true,json:async()=>({...sala})};
    },
  });
  vm.runInContext(fs.readFileSync('static/salas.js','utf8'),docente);
  assert.equal(intervalos[0].ms,30000);
  docente.document.getElementById('capacity').value='25'; docente.document.getElementById('roomName').value='Grupo de prueba';
  nodos.get('createForm').onsubmit({preventDefault(){}});
  await new Promise(resolve=>setImmediate(resolve));
  await intervalos[0].fn();
  assert.equal(solicitudes.at(-1).path,'/api/partidas/ABC234/latido');
  assert.equal(solicitudes[0].datos.nombre,'Grupo de prueba');
  assert.equal(solicitudes.at(-1).datos.clave,undefined,'El docente se identifica con su sesión, no con una clave');
  nodos.get('finish').onclick(); await new Promise(resolve=>setImmediate(resolve));
  assert.match(nodos.get('message').textContent,/Error de conexión/);
  assert.equal(vm.runInContext('currentRoom.estado',docente),'esperando');
  fallarCierre=false;
  nodos.get('finish').onclick(); await new Promise(resolve=>setImmediate(resolve));
  assert.equal(vm.runInContext('currentRoom.estado',docente),'finalizada');
  assert.match(nodos.get('connection').textContent,/cierre guardado/);
  vm.runInContext('socket.onclose({code:1000})',docente);
  assert.equal(reintentos.length,0,'Una partida finalizada no debe reconectar indefinidamente');
  const antes=solicitudes.length; await intervalos[0].fn();
  assert.equal(solicitudes.length,antes,'No renovar una partida finalizada');
  console.log('OK: latido docente, error de cierre visible, cierre confirmado e interrupción de latidos/reconexiones.');
})().catch(error=>{console.error(error);process.exitCode=1;});
