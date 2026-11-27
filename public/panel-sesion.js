(() => {
  const panel = document.querySelector('[data-segundos-sesion]');
  if (!panel) return;
  let temporizador;
  let consultando = false;

  function programar(segundos) {
    clearTimeout(temporizador);
    temporizador = setTimeout(comprobar, (segundos + 1) * 1000);
  }

  async function comprobar() {
    if (consultando) return;
    consultando = true;
    try {
      const respuesta = await fetch(panel.dataset.consultarSesion, {cache: 'no-store'});
      if (!respuesta.ok) throw new Error();
      const estado = await respuesta.json();
      if (estado.destino) {
        programar(estado.segundos_sesion);
      } else {
        window.location.replace(panel.dataset.catalogo);
      }
    } catch {
      programar(30);
    } finally {
      consultando = false;
    }
  }

  programar(Number(panel.dataset.segundosSesion));
  window.addEventListener('pageshow', event => {
    if (event.persisted) comprobar();
  });
})();
