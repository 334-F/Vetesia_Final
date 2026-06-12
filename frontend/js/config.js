/**
 * config.js · Configuración global del frontend de VetÉsia
 */
window.VETESIA = window.VETESIA || {};

window.VETESIA.config = {
  // En local apunta a localhost:5000, en producción a Render
  API_BASE_URL: (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:5001/api'
    : 'https://vetesia-backend.onrender.com/api',
  STRIPE_PUBLISHABLE_KEY: 'pk_test_cambia_esto_por_tu_clave',
  APP_NAME: 'VetÉsia',
};