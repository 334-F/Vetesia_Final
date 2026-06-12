/**
 * auth.js · Gestión de la sesión del usuario
 *
 * Guarda y recupera el token JWT y los datos del usuario en localStorage.
 * Expone funciones para login, logout y consulta del usuario actual.
 */
(function() {
  const STORAGE_TOKEN = 'vetesia_token';
  const STORAGE_USER = 'vetesia_user';

  window.VETESIA.auth = {

    isLoggedIn() {
      return !!localStorage.getItem(STORAGE_TOKEN);
    },

    getUser() {
      const raw = localStorage.getItem(STORAGE_USER);
      try {
        return raw ? JSON.parse(raw) : null;
      } catch (e) {
        return null;
      }
    },

    isAdmin() {
      const user = this.getUser();
      return user && user.rol === 'admin';
    },

    async login(email, password) {
      const data = await window.VETESIA.api.post('/auth/login', { email, password });
      localStorage.setItem(STORAGE_TOKEN, data.access_token);
      localStorage.setItem(STORAGE_USER, JSON.stringify(data.usuario));
      return data.usuario;
    },

    async register(datosUsuario) {
      const data = await window.VETESIA.api.post('/auth/register', datosUsuario);
      localStorage.setItem(STORAGE_TOKEN, data.access_token);
      localStorage.setItem(STORAGE_USER, JSON.stringify(data.usuario));
      return data.usuario;
    },

    logout() {
      localStorage.removeItem(STORAGE_TOKEN);
      localStorage.removeItem(STORAGE_USER);
      // Mantener el carrito si no quieres que se pierda al cerrar sesión
      window.location.href = '/';
    },

    /**
     * Comprueba que el usuario está autenticado. Si no, redirige al login.
     * Llamar al principio de páginas privadas (cuenta, checkout, admin).
     */
    requireAuth() {
      if (!this.isLoggedIn()) {
        const url = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `/pages/login.html?next=${url}`;
        return false;
      }
      return true;
    },

    requireAdmin() {
      if (!this.requireAuth()) return false;
      if (!this.isAdmin()) {
        alert('Acceso restringido a administradores');
        window.location.href = '/';
        return false;
      }
      return true;
    },
  };
})();
