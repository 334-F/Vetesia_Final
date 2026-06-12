/**
 * ui.js · Utilidades de interfaz comunes
 *
 * Funciones reutilizables en toda la app: toasts de notificación,
 * formateo de precios y fechas, renderizado de estrellas, etc.
 */
(function() {

  window.VETESIA.ui = {

    /** Muestra una notificación tipo toast en la esquina superior derecha. */
    toast(mensaje, tipo = 'success') {
      const wrap = document.getElementById('toast-container') || (() => {
        const c = document.createElement('div');
        c.id = 'toast-container';
        c.className = 'toast-vetesia';
        document.body.appendChild(c);
        return c;
      })();

      const colores = {
        success: 'success',
        error: 'danger',
        info: 'info',
        warning: 'warning',
      };

      const toast = document.createElement('div');
      toast.className = `alert alert-${colores[tipo] || 'info'} alert-dismissible fade show mb-2`;
      toast.innerHTML = `
        ${mensaje}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      `;
      wrap.appendChild(toast);

      setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
      }, 4000);
    },

    /** Formatea un precio en euros con dos decimales. */
    precio(n) {
      const num = parseFloat(n) || 0;
      return num.toFixed(2).replace('.', ',') + ' €';
    },

    /** Convierte una fecha ISO a formato dd/mm/aaaa. */
    fecha(iso) {
      if (!iso) return '-';
      const d = new Date(iso);
      return d.toLocaleDateString('es-ES');
    },

    /** Formatea una fecha ISO incluyendo hora. */
    fechaHora(iso) {
      if (!iso) return '-';
      const d = new Date(iso);
      return d.toLocaleString('es-ES', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      });
    },

    /** Devuelve HTML con estrellas (0 a 5). */
    estrellas(valoracion) {
      const n = Math.round(parseFloat(valoracion) || 0);
      let html = '<span class="estrellas">';
      for (let i = 0; i < 5; i++) {
        html += i < n ? '★' : '☆';
      }
      html += '</span>';
      return html;
    },

    /** Formatea un estado de pedido para mostrar. */
    estadoTag(estado) {
      const labels = {
        pendiente_pago: 'Pendiente de pago',
        pagado: 'Pagado',
        preparando: 'Preparando',
        enviado: 'Enviado',
        entregado: 'Entregado',
        cancelado: 'Cancelado',
        reembolsado: 'Reembolsado',
      };
      return `<span class="estado-tag estado-${estado}">${labels[estado] || estado}</span>`;
    },

    /** Escapa HTML para evitar inyecciones. */
    escapeHtml(text) {
      if (text === null || text === undefined) return '';
      const div = document.createElement('div');
      div.textContent = String(text);
      return div.innerHTML;
    },

    /** Indicador visual del stock disponible. */
    stockInfo(stock) {
      if (stock <= 0) return '<span class="stock-info stock-agotado">Agotado</span>';
      if (stock <= 5) return `<span class="stock-info stock-bajo">¡Solo quedan ${stock}!</span>`;
      return `<span class="stock-info stock-ok">En stock</span>`;
    },

    /** Muestra un spinner mientras se carga contenido en un contenedor. */
    cargando(contenedor) {
      if (typeof contenedor === 'string') {
        contenedor = document.querySelector(contenedor);
      }
      if (contenedor) {
        contenedor.innerHTML = '<div class="text-center py-5"><div class="spinner-vetesia"></div></div>';
      }
    },

    /** Devuelve true si quedan elementos en URL params. */
    queryParam(name) {
      return new URLSearchParams(window.location.search).get(name);
    },

    /** Resuelve y formatea una URL de imagen, soportando absolutas, locales y placeholders. */
    imagen(url) {
      if (!url) return '/img/placeholder.png';
      if (url.startsWith('http://') || url.startsWith('https://')) {
        return url;
      }
      return url.startsWith('/img/') ? url : `/img/${url}`;
    },
  };
})();
