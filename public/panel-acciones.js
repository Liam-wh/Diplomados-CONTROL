const visor = document.getElementById('visor-recibo');
const contenido = document.getElementById('contenido-recibo');
const confirmar = document.getElementById('confirmar-eliminar');
const formulario = document.getElementById('form-eliminar');

document.querySelector('.records').addEventListener('click', event => {
  const ver = event.target.closest('[data-recibo]');
  if (ver) {
    event.preventDefault();
    const titulo = 'Recibo de ' + ver.dataset.estudiante;
    document.getElementById('titulo-recibo').textContent = titulo;
    const imagen = ver.dataset.recibo === 'imagen';
    const elemento = document.createElement(imagen ? 'img' : 'iframe');
    if (imagen) {
      elemento.alt = titulo;
      elemento.addEventListener('error', () => {
        contenido.textContent = 'No se pudo cargar el recibo. Cierra esta vista y vuelve a intentarlo.';
      }, {once: true});
    } else {
      elemento.title = titulo;
      elemento.setAttribute('sandbox', 'allow-scripts');
      elemento.referrerPolicy = 'no-referrer';
      document.getElementById('original-recibo').href = ver.href;
    }
    document.getElementById('alternativa-recibo').hidden = imagen;
    elemento.src = ver.href;
    contenido.replaceChildren(elemento);
    visor.showModal();
    return;
  }
  const borrar = event.target.closest('[data-eliminar]');
  if (borrar) {
    formulario.action = borrar.dataset.eliminar;
    document.getElementById('detalle-eliminar').textContent =
      'Se eliminará la inscripción de ' + borrar.dataset.estudiante + ' en ' + borrar.dataset.programa +
      ', junto con cualquier comprobante adjunto. Esta acción es permanente.';
    confirmar.showModal();
  }
});

visor.addEventListener('close', () => contenido.replaceChildren());
document.getElementById('cancelar-eliminar').addEventListener('click', () => confirmar.close());
