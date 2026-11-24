/* Un pequeño sonido de confirmación, generado localmente al interactuar. */
(() => {
  let audio;
  window.sonidoVictoria = () => {
    if (!audio || audio.state !== 'running') return;
    try {
      const start = audio.currentTime;
      [523.25, 659.25, 783.99, 1046.5].forEach((frequency, index) => {
        const tone = audio.createOscillator(), gain = audio.createGain();
        const time = start + index * 0.13;
        tone.type = 'triangle'; tone.frequency.setValueAtTime(frequency, time);
        gain.gain.setValueAtTime(0.0001, time);
        gain.gain.exponentialRampToValueAtTime(0.08, time + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, time + 0.25);
        tone.connect(gain); gain.connect(audio.destination);
        tone.start(time); tone.stop(time + 0.26);
      });
    } catch (_) { /* La celebración visual funciona aun sin audio. */ }
  };
  document.addEventListener('click', (event) => {
    if (!(event.target instanceof Element)) return;
    const control = event.target.closest('button, a[href], summary');
    if (!control || control.matches(':disabled') || control.getAttribute('aria-disabled') === 'true') return;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    try {
      audio ||= new AudioContext();
      if (audio.state === 'suspended') audio.resume().catch(() => {});
      const now = audio.currentTime;
      const oscillator = audio.createOscillator();
      const volume = audio.createGain();
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(500, now);
      oscillator.frequency.exponentialRampToValueAtTime(760, now + 0.06);
      volume.gain.setValueAtTime(0.0001, now);
      volume.gain.exponentialRampToValueAtTime(0.055, now + 0.012);
      volume.gain.exponentialRampToValueAtTime(0.0001, now + 0.13);
      oscillator.connect(volume);
      volume.connect(audio.destination);
      oscillator.start(now);
      oscillator.stop(now + 0.14);
    } catch (_) {
      // La interacción sigue funcionando si el navegador no permite audio.
    }
  });
})();
