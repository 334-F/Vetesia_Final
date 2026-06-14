/*
 * favoritos.js · Favoritos persistentes en el navegador (localStorage)
 * --------------------------------------------------------------------
 * Guarda los productos marcados con el corazón para que NO se borren
 * al recargar la página. No necesita cambios en las tarjetas: deduce
 * el id del producto a partir del enlace "Ver Más" de cada tarjeta.
 */
(function () {
  const KEY = 'vetesia_favoritos';

  function leer() {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); }
    catch (e) { return []; }
  }
  function guardar(ids) {
    localStorage.setItem(KEY, JSON.stringify(ids));
  }

  // Saca el id del producto de la tarjeta donde está el corazón
  function idDeTarjeta(btn) {
    const card = btn.closest('.product-card') || btn.closest('.card');
    if (!card) return null;
    const link = card.querySelector('a[href*="producto.html?id="]');
    if (!link) return null;
    const m = link.getAttribute('href').match(/id=(\d+)/);
    return m ? Number(m[1]) : null;
  }

  // Marca como activos (corazón relleno) los favoritos guardados
  function aplicar() {
    const favs = leer();
    document.querySelectorAll('.heart-btn').forEach(function (btn) {
      const id = idDeTarjeta(btn);
      if (id != null && favs.includes(id)) btn.classList.add('active');
    });
  }

  // Al pulsar un corazón: el onclick original cambia el color;
  // aquí (después) guardamos o quitamos el favorito en localStorage.
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.heart-btn');
    if (!btn) return;
    const id = idDeTarjeta(btn);
    if (id == null) return;
    const ids = leer();
    const activo = btn.classList.contains('active');
    const i = ids.indexOf(id);
    if (activo && i === -1) ids.push(id);
    if (!activo && i !== -1) ids.splice(i, 1);
    guardar(ids);
  });

  // La tienda carga los productos por AJAX: reaplicamos cuando aparecen
  document.addEventListener('DOMContentLoaded', function () {
    aplicar();
    new MutationObserver(aplicar).observe(document.body, { childList: true, subtree: true });
  });
})();