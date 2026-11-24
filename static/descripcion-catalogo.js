// Añade descripción conservando el registro automático y la grabación ya probados.
(() => {
  const editar = window.editCard;
  window.editCard = async id => {
    await editar(id);
    if (editingId === id) document.getElementById('descripcion').value = cards.find(tarjeta => tarjeta.id === id)?.descripcion || '';
  };
})();
