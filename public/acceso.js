(() => {
  const form = document.getElementById('acceso-form');
  if (!form) return;
  const clave = form.elements.password;
  const ojo = document.getElementById('acceso-ojo');
  function mostrarClave(visible) {
    clave.type = visible ? 'text' : 'password';
    ojo.title = visible ? 'Ocultar contraseña' : 'Mostrar contraseña';
    ojo.setAttribute('aria-label', ojo.title);
    ojo.querySelector('use').setAttribute('href', visible ? '#i-eye-off' : '#i-eye');
  }
  ojo.hidden = false;
  ojo.addEventListener('click', () => mostrarClave(clave.type === 'password'));

  const popup = document.getElementById('acceso-popup');
  if (!popup) return;
  const abrir = document.getElementById('abrir-acceso');
  const error = document.getElementById('acceso-error');
  const enviar = form.querySelector('[type=submit]');
  const url = new URL(form.action);
  url.searchParams.set('modal', '1');
  let apertura = 0;

  function mostrarFormulario() {
    if (!popup.hidden) return;
    popup.hidden = false;
    abrir.setAttribute('aria-expanded', 'true');
    form.elements.usuario.focus({preventScroll: true});
  }

  async function consultar(opciones) {
    const turno = apertura;
    enviar.disabled = true;
    error.hidden = true;
    try {
      const respuesta = await fetch(url, {cache: 'no-store', ...opciones});
      const datos = await respuesta.json();
      if (turno !== apertura) return;
      if (datos.destino) {
        cerrar();
        window.location.assign(datos.destino);
        return;
      }
      if (datos.csrf) form.elements.csrf.value = datos.csrf;
      if (!respuesta.ok || datos.error) throw new Error(datos.error || 'Vuelve a intentarlo.');
      mostrarFormulario();
    } catch (fallo) {
      if (turno !== apertura) return;
      mostrarFormulario();
      error.textContent = fallo instanceof TypeError || fallo instanceof SyntaxError
        ? 'No se pudo conectar. Revisa tu conexión y vuelve a intentarlo.' : fallo.message;
      error.hidden = false;
    } finally {
      if (turno === apertura) {
        abrir.removeAttribute('aria-busy');
        enviar.disabled = false;
      }
    }
  }

  function cerrar(devolverFoco = false) {
    if (popup.hidden && !abrir.hasAttribute('aria-busy')) return;
    apertura++;
    abrir.removeAttribute('aria-busy');
    popup.hidden = true;
    abrir.setAttribute('aria-expanded', 'false');
    form.reset();
    mostrarClave(false);
    error.hidden = true;
    if (devolverFoco) abrir.focus();
  }

  abrir.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (!popup.hidden || abrir.hasAttribute('aria-busy')) {
      cerrar(true);
      return;
    }
    apertura++;
    abrir.setAttribute('aria-busy', 'true');
    consultar();
  });
  document.getElementById('cerrar-acceso').addEventListener('click', () => cerrar(true));
  const ancla = abrir.parentElement;
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && (!popup.hidden || abrir.hasAttribute('aria-busy'))) {
      event.preventDefault();
      event.stopPropagation();
      cerrar(true);
    }
  }, true);
  function cerrarDesdeFuera(event) {
    if (!ancla.contains(event.target)) cerrar();
  }
  document.addEventListener('click', cerrarDesdeFuera);
  document.addEventListener('focusin', cerrarDesdeFuera);
  matchMedia('(min-width: 768px)').addEventListener('change', () => cerrar());
  window.addEventListener('pagehide', () => cerrar());
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (enviar.disabled) return;
    if (!form.elements.csrf.value) {
      await consultar();
      if (popup.hidden || !form.elements.csrf.value) return;
    }
    await consultar({method: 'POST', body: new FormData(form)});
  });
})();
