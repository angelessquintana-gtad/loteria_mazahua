/* Páginas del docente: la sesión vive en una cookie HttpOnly (el token nunca se guarda en el navegador).
   Este archivo agrega el código CSRF a las peticiones que modifican datos y, si la sesión se cerró
   o venció, lleva a la pantalla de acceso. */
(() => {
  const original = window.fetch.bind(window);
  const privadas = ['/panel', '/docente', '/administracion', '/editar', '/cuenta'];
  const destino = privadas.includes(location.pathname) ? location.pathname : '/panel';
  const acceder = () => location.replace('/acceso?destino=' + encodeURIComponent(destino));
  let csrf = '';
  const lista = original('/api/auth/me', {cache: 'no-store'}).then(async response => {
    if (response.status === 401) { acceder(); throw Error('Inicia sesión.'); }
    if (!response.ok) throw Error('No se pudo verificar tu sesión. Recarga la página.');
    const data = await response.json(); csrf = data.csrf_token; return data.docente;
  });
  window.docenteActual = lista;
  window.fetch = async (input, init = {}) => {
    const url = new URL(input instanceof Request ? input.url : input, location.href);
    const method = (init.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
    const local = url.origin === location.origin && url.pathname.startsWith('/api/');
    if (local && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
      await lista;
      const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
      headers.set('X-CSRF-Token', csrf); init = {...init, headers};
    }
    const response = await original(input, init);
    if (local && response.status === 401 && !url.pathname.startsWith('/api/auth/')) acceder();
    return response;
  };
  // Las pestañas abiertas detectan el cierre de sesión o su vencimiento.
  setInterval(() => original('/api/auth/me', {cache:'no-store'}).then(r => { if (r.status === 401) acceder(); }).catch(() => {}), 60000);
  lista.catch(() => {});
})();
