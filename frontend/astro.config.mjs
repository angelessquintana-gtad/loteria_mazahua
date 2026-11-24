import { defineConfig } from 'astro/config';

// Backend FastAPI. En "npm run dev" (puerto 4321) estas rutas se reenvían a FastAPI,
// así el frontend se puede editar con recarga automática mientras el backend corre en 8000.
const BACKEND = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
const reenviar = { target: BACKEND, changeOrigin: false };

export default defineConfig({
  output: 'static',
  trailingSlash: 'never',
  build: { format: 'directory' },
  vite: {
    server: {
      proxy: {
        '/api': { ...reenviar, ws: true },
        '/static': reenviar,
        '/catalogo': reenviar,
        '/uploads': reenviar,
        '/docs': reenviar,
        '/openapi.json': reenviar,
      },
    },
  },
});
