// Respaldo: si una carta aún no tiene archivo de audio en español, se pronuncia con la voz
// en español del navegador/Windows (de preferencia México). Uso: hablarEspanol('Gato').
(() => {
  const sintesis = window.speechSynthesis;
  let voz = null;
  function elegir() {
    const voces = sintesis ? sintesis.getVoices() : [];
    const es = voces.filter(v => /^es([-_]|$)/i.test(v.lang));
    voz = es.find(v => /mx|mexico|méxico/i.test(v.lang + v.name)) || es.find(v => /419|us/i.test(v.lang)) || es[0] || null;
  }
  if (sintesis) { elegir(); sintesis.addEventListener?.('voiceschanged', elegir); }
  window.vozEspanolDisponible = () => !!sintesis;
  window.hablarEspanol = texto => new Promise(resolve => {
    if (!sintesis || !texto) return resolve(false);
    sintesis.cancel();
    const frase = new SpeechSynthesisUtterance(String(texto));
    frase.lang = voz?.lang || 'es-MX'; if (voz) frase.voice = voz; frase.rate = 0.9;
    frase.onend = () => resolve(true); frase.onerror = () => resolve(false);
    sintesis.speak(frase);
  });
  window.callarEspanol = () => sintesis && sintesis.cancel();
})();
