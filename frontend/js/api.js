/**
 * api.js · Cliente HTTP para la API REST de VetÉsia
 *
 * Encapsula todas las llamadas fetch() y añade automáticamente
 * el token JWT en la cabecera Authorization si el usuario está autenticado.
 * Si la respuesta es 401, redirige al login.
 */
(function() {
  const API = window.VETESIA.config.API_BASE_URL;

  async function request(method, endpoint, body = null, extraHeaders = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...extraHeaders,
    };

    const token = localStorage.getItem('vetesia_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const opts = { method, headers };
    if (body !== null) {
      opts.body = JSON.stringify(body);
    }

    let response;
    try {
      response = await fetch(`${API}${endpoint}`, opts);
    } catch (e) {
      throw new Error('No se puede conectar con el servidor. ¿Está corriendo?');
    }

    // 401 → token caducado o no válido
    if (response.status === 401 && token) {
      localStorage.removeItem('vetesia_token');
      localStorage.removeItem('vetesia_user');
      if (!endpoint.includes('/auth/login')) {
        window.location.href = '/pages/login.html?expired=1';
      }
    }

    // Si es un PDF u otro archivo binario
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/pdf') || contentType.includes('octet-stream')) {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.blob();
    }

    let data;
    try {
      data = await response.json();
    } catch (e) {
      data = {};
    }

    if (!response.ok) {
      const err = new Error(data.error || `HTTP ${response.status}`);
      err.status = response.status;
      err.data = data;
      throw err;
    }

    return data;
  }

  window.VETESIA.api = {
    get: (endpoint) => request('GET', endpoint),
    post: (endpoint, body) => request('POST', endpoint, body),
    patch: (endpoint, body) => request('PATCH', endpoint, body),
    put: (endpoint, body) => request('PUT', endpoint, body),
    delete: (endpoint) => request('DELETE', endpoint),

    // Descargar PDF de factura
    descargarFactura: async (pedidoId) => {
      const blob = await request('GET', `/pedidos/${pedidoId}/factura`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `factura_VE-${String(pedidoId).padStart(6, '0')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },
  };
})();
