/**
 * layout.js · Inyecta el navbar y el footer premium de Página en todas las páginas
 * 
 * Centraliza la navegación y pie de página de forma que los cambios se apliquen 
 * globalmente, manteniendo la tipografía, barra de búsqueda y logos originales.
 */
(function() {

  function renderNavbar() {
    const user = window.VETESIA.auth.getUser();
    const isAdmin = window.VETESIA.auth.isAdmin();
    const path = window.location.pathname;
    
    const isHome = path === '/' || path.endsWith('/index.html') || path.endsWith('/');
    const isTienda = path.includes('/catalogo.html') || path.includes('/producto.html');
    const isServicios = path.includes('/servicios.html');

    // Estado del login y menú de usuario
    let userDisplay = '';
    let logoutButton = '';
    let adminLink = '';
    let userTitle = 'Mi Cuenta';
    let userHref = '/pages/mi-cuenta.html';

    if (user) {
      userDisplay = `
        <span class="ms-1 d-none d-lg-inline" style="font-size: 0.95rem; color: #3eb3a0; font-weight: 500; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
          ${window.VETESIA.ui.escapeHtml(user.nombre)}
        </span>
      `;
      userTitle = `Sesión iniciada como ${user.nombre}`;
      
      if (isAdmin) {
        adminLink = `
          <a href="/pages/admin.html" class="ms-2 text-success" title="Panel de Administración">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-shield-lock-fill" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M8 0c-.69 0-1.843.265-2.928.56-1.11.3-2.229.655-2.887.87a1.54 1.54 0 0 0-1.044 1.262c-.596 4.477.787 7.795 2.465 9.99a11.8 11.8 0 0 0 2.517 2.453c.386.273.744.482 1.048.625.28.132.581.24.829.24s.548-.108.829-.24c.3-.143.662-.352 1.048-.625a11.8 11.8 0 0 0 2.517-2.453c1.678-2.195 3.061-5.513 2.465-9.99a1.54 1.54 0 0 0-1.044-1.263 63 63 0 0 0-2.887-.87C9.843.266 8.69 0 8 0m0 5a1.5 1.5 0 0 1 .5 2.915l.385 1.99a.5.5 0 0 1-.97.185l-.15-.75-.15.75a.5.5 0 0 1-.97-.186l.385-1.99A1.5 1.5 0 0 1 8 5"/>
            </svg>
          </a>
        `;
      }

      logoutButton = `
        <a href="#" onclick="window.VETESIA.auth.logout(); return false;" class="ms-2 text-danger" title="Cerrar Sesión">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-box-arrow-right" viewBox="0 0 16 16">
            <path fill-rule="evenodd" d="M10 12.5a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-9a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v2a.5.5 0 0 0 1 0v-2A1.5 1.5 0 0 0 9.5 2h-8A1.5 1.5 0 0 0 0 3.5v9A1.5 1.5 0 0 0 1.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-2a.5.5 0 0 0-1 0z"/>
            <path fill-rule="evenodd" d="M15.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 0 0-.708.708L14.293 7.5H5.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708z"/>
          </svg>
        </a>
      `;
    }

    return `
      <div class="container-1 d-flex justify-content-between align-items-center px-4">
        <a href="/index.html"><img src="/img/logo.webp" alt="Logo VetÉsia" class="logo-1"></a>
        
        <div class="d-flex align-items-center">
          <ul class="nav mb-0 me-4">
            <li class="nav-item">
              <a href="/index.html" class="nav-link ${isHome ? 'active' : ''}">Home</a>
            </li>
            <li class="nav-item">
              <a href="/pages/catalogo.html" class="nav-link ${isTienda ? 'active' : ''}">Tienda</a>
            </li>
            <li class="nav-item">
              <a href="/pages/servicios.html" class="nav-link ${isServicios ? 'active' : ''}">Servicios que ofrecemos</a>
            </li>
          </ul>

          <div class="header-icons d-flex align-items-center">
            <div class="search-box">
              <input type="text" class="search-input" id="nav-search-input" placeholder="Buscar...">
              <button class="search-btn" onclick="event.preventDefault(); document.getElementById('nav-search-input').focus();">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-search nav-icon-search nav-svg-icon" viewBox="0 0 16 16">
                  <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
                </svg>
              </button>
            </div>
            <a href="/pages/carrito.html" class="icon-link ms-3 position-relative" title="Carrito de Compras">
              <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" fill="currentColor" class="bi bi-cart3 nav-icon cart-icon-svg" viewBox="0 0 16 16">
                <path d="M0 1.5A.5.5 0 0 1 .5 1H2a.5.5 0 0 1 .485.379L2.89 3H14.5a.5.5 0 0 1 .49.598l-1 5a.5.5 0 0 1-.465.401l-9.397.472L4.415 11H13a.5.5 0 0 1 0 1H4a.5.5 0 0 1-.491-.408L2.01 3.607 1.61 2H.5a.5.5 0 0 1-.5-.5zM3.102 4l.84 4.479 9.144-.459L13.89 4H3.102zM5 12a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm7 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-7 1a1 1 0 1 1 0 2 1 1 0 0 1 0-2zm7 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
              </svg>
              <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger badge-cart" style="font-size: 0.65rem; display:none">
                0
              </span>
            </a>
            <a href="${userHref}" class="icon-link ms-3 d-flex align-items-center text-decoration-none" title="${userTitle}" style="color: inherit;">
              <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" fill="currentColor" class="bi bi-person-circle nav-icon nav-svg-icon" viewBox="0 0 16 16">
                <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0z"/>
                <path fill-rule="evenodd" d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1z"/>
              </svg>
              ${userDisplay}
            </a>
            ${adminLink}
            ${logoutButton}
          </div>
        </div>
      </div>
    `;
  }

  function renderFooter() {
    return `
      <footer class="gradient-footer text-white text-center">
        <div class="container d-flex justify-content-between align-items-center w-100">
          <img src="/img/logo.webp" alt="Logo VetÉsia" class="logo mb-2">

          <div class="contact-info mt-3" style="color: black;">
            <p class="mb-1" style="color: black;"><strong>Dirección:</strong> Calle de Don Ramón de la Cruz 41, Madrid, España</p>
            <p class="mb-1" style="color: black;"><strong>Correo:</strong> <a href="mailto:info@vetesia.com" style="color: black; text-decoration: none;">info@vetesia.com</a></p>
          </div>

          <p class="mt-3 mb-0" style="color: black;">&copy; 2026 VetÉsia - Todos los derechos reservados</p>

          <div class="social-icons">
            <a href="https://www.instagram.com/nazth09?igsh=MWoxYXZ6N2pyczA1Ng%3D%3D&utm_source=qr" target="_blank" class="mx-2">
              <img src="/img/Instagram.png" alt="Instagram" class="social-logo">
            </a>
            <a href="https://x.com/nathansmf?s=11&t=5QyMTIlgbGhRkPTGuh2HUg" target="_blank" class="mx-2">
              <img src="/img/pixelcut-export.png" alt="Twitter" class="social-logo">
            </a>
            <a href="https://wa.me/691019799" target="_blank" class="whatsapp">
              <img src="/img/Whatsapp.png" alt="WhatsApp" class="social-logo">
            </a>
          </div>
        </div>
      </footer>
    `;
  }

  function init() {
    const navHolder = document.getElementById('navbar-holder');
    if (navHolder) navHolder.innerHTML = renderNavbar();

    const footerHolder = document.getElementById('footer-holder');
    if (footerHolder) footerHolder.innerHTML = renderFooter();

    window.VETESIA.cart.inicializarBadge();
    
    // Configurar búsqueda desde el navbar
    const searchInput = document.getElementById('nav-search-input');
    if (searchInput) {
      searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && searchInput.value.trim() !== '') {
          window.location.href = `/pages/catalogo.html?q=${encodeURIComponent(searchInput.value.trim())}`;
        }
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
