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

  const modal = document.getElementById('acceso-modal');
  if (!modal || !modal.showModal) return;
  const abrir = document.getElementById('abrir-acceso');
  const error = document.getElementById('acceso-error');
  const enviar = form.querySelector('[type=submit]');
  const url = new URL(form.action);
  url.searchParams.set('modal', '1');
  let apertura = 0;

  async function consultar(opciones) {
    const turno = apertura;
    enviar.disabled = true;
    error.hidden = true;
    try {
      const respuesta = await fetch(url, {cache: 'no-store', ...opciones});
      const datos = await respuesta.json();
      if (!modal.open || turno !== apertura) return;
      if (datos.destino) {
        modal.close();
        window.location.assign(datos.destino);
        return;
      }
      if (datos.csrf) form.elements.csrf.value = datos.csrf;
      if (!respuesta.ok || datos.error) throw new Error(datos.error || 'Vuelve a intentarlo.');
    } catch (fallo) {
      if (!modal.open || turno !== apertura) return;
      error.textContent = fallo instanceof TypeError || fallo instanceof SyntaxError
        ? 'No se pudo conectar. Revisa tu conexión y vuelve a intentarlo.' : fallo.message;
      error.hidden = false;
    } finally {
      if (turno === apertura) enviar.disabled = false;
    }
  }

  abrir.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    apertura++;
    modal.showModal();
    form.elements.usuario.focus();
    consultar();
  });
  document.getElementById('cerrar-acceso').addEventListener('click', () => modal.close());
  modal.addEventListener('close', () => {
    apertura++;
    form.reset();
    mostrarClave(false);
    error.hidden = true;
    const destino = abrir.getClientRects().length ? abrir : document.getElementById('menu');
    destino.focus();
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (enviar.disabled) return;
    if (!form.elements.csrf.value) {
      await consultar();
      if (!modal.open || !form.elements.csrf.value) return;
    }
    await consultar({method: 'POST', body: new FormData(form)});
  });
})();
