/**
 * cart.js · Carrito de compra persistente en localStorage
 *
 * El carrito se guarda en el navegador (no en el backend) hasta que se
 * confirma el pedido. Esto permite añadir productos sin estar logueado;
 * el login solo se exige al hacer checkout.
 *
 * Estructura: array de líneas
 *   { producto_id, nombre, imagen_url, precio_base, cantidad,
 *     tipo_servicio_id, tipo_servicio_nombre, precio_extra_servicio,
 *     personalizacion, archivo_diseno_url }
 */
(function() {
  const STORAGE_KEY = 'vetesia_carrito';

  function load() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch (e) {
      return [];
    }
  }

  function save(carrito) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(carrito));
    actualizarBadge();
    document.dispatchEvent(new CustomEvent('carrito:cambio', { detail: carrito }));
  }

  function actualizarBadge() {
    const carrito = load();
    const total = carrito.reduce((sum, l) => sum + l.cantidad, 0);
    document.querySelectorAll('.badge-cart').forEach(el => {
      el.textContent = total;
      el.style.display = total > 0 ? 'inline-block' : 'none';
    });
  }

  window.VETESIA.cart = {
    obtener() {
      return load();
    },

    contar() {
      return load().reduce((sum, l) => sum + l.cantidad, 0);
    },

    agregar(linea) {
      const carrito = load();
      // Si el producto ya está en el carrito y no es personalizable, suma cantidad
      const existente = carrito.find(l =>
        l.producto_id === linea.producto_id &&
        !l.tipo_servicio_id &&
        !linea.tipo_servicio_id
      );
      if (existente) {
        existente.cantidad += linea.cantidad;
      } else {
        carrito.push(linea);
      }
      save(carrito);
    },

    actualizarCantidad(index, cantidad) {
      const carrito = load();
      if (carrito[index]) {
        if (cantidad <= 0) {
          carrito.splice(index, 1);
        } else {
          carrito[index].cantidad = cantidad;
        }
        save(carrito);
      }
    },

    eliminar(index) {
      const carrito = load();
      carrito.splice(index, 1);
      save(carrito);
    },

    vaciar() {
      save([]);
    },

    calcularSubtotal() {
      return load().reduce((sum, l) => {
        const precio = l.precio_base + (l.precio_extra_servicio || 0);
        return sum + precio * l.cantidad;
      }, 0);
    },

    inicializarBadge() {
      actualizarBadge();
    },
  };

  // Inicializar el badge al cargar
  document.addEventListener('DOMContentLoaded', actualizarBadge);
})();
