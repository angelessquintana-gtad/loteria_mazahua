// Copia los recursos de static/ (CSS, JS, fuentes, SVG) dentro de frontend/dist/static
// para que Vercel los sirva junto con las páginas compiladas de Astro.
// Las páginas .html originales de static/ no se copian: Astro ya las incluye.
import { cpSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const raiz = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const destino = join(raiz, 'frontend', 'dist', 'static');
if (!existsSync(join(raiz, 'frontend', 'dist', 'index.html'))) throw new Error('Primero ejecuta npm run build en frontend/.');
cpSync(join(raiz, 'static'), destino, { recursive: true, filter: (ruta) => !ruta.endsWith('.html') });
console.log('Recursos de static/ copiados a frontend/dist/static');
