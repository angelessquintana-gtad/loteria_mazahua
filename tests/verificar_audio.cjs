// Ejecutar desde la raíz: node tests/verificar_audio.cjs.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
let timerId = 0;
const timers = new Map(), played = [], messages = [];
class AudioFake {
  pause() {}
  load() {}
  removeAttribute() { this.src = ''; }
  getAttribute() { return this.src || null; }
  play() { played.push(this.src); return Promise.resolve(); }
}
const ctx = vm.createContext({window: {}, Audio: AudioFake, setInterval, clearInterval,
  setTimeout(fn, ms) { timers.set(++timerId, {fn, ms}); return timerId; },
  clearTimeout(id) { timers.delete(id); }});
vm.runInContext(fs.readFileSync('static/audio-secuencia.js', 'utf8'), ctx);
const player = new ctx.window.SecuenciaAudio(text => messages.push(text));
async function run() {
  player.programar({audio_mazahua_url: '/mazahua.mp3', audio_espanol_url: '/espanol.mp3'});
  assert.equal(played.length, 0);
  const first = timers.get(timerId); assert.equal(first.ms, 1500);
  await first.fn();
  assert.deepEqual(played, ['/mazahua.mp3']);
  await player.mazahua.onended();
  assert.deepEqual(played, ['/mazahua.mp3', '/espanol.mp3']);
  player.programar({audio_mazahua_url: '/viejo.mp3'});
  const oldTimer = timers.get(timerId);
  player.programar({audio_mazahua_url: '/nuevo.mp3'});
  await oldTimer.fn(); assert.equal(played.length, 2);
  await timers.get(timerId).fn(); assert.equal(played.at(-1), '/nuevo.mp3');
  const ended = player.mazahua.onended; player.detener(); await ended();
  assert.equal(played.length, 3);
  player.programar({}); player.repetir();
  assert.equal(played.length, 3);
  player.programar({audio_mazahua_url: '/bloqueado.mp3'});
  player.mazahua.play = () => Promise.reject(Object.assign(new Error(), {name: 'NotAllowedError'}));
  await player.reproducir(player.version, 0);
  assert.match(messages.at(-1), /navegador bloqueó/);
  console.log('OK: demora 1500 ms, orden por fin de audio, cancelación, sin audios y bloqueo del navegador.');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
