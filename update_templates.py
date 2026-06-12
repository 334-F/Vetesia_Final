import os
import re

templates_dir = os.path.join(os.path.dirname(__file__), 'templates')

def update_asset_paths(content):
    # Reemplazar rutas de CSS e imágenes por rutas estáticas absolutas de Flask
    content = re.sub(r'href="\./css/([^"]+)"', r'href="/static/css/\1"', content)
    content = re.sub(r'href="css/([^"]+)"', r'href="/static/css/\1"', content)
    content = re.sub(r'src="\./fotos/([^"]+)"', r'src="/static/fotos/\1"', content)
    content = re.sub(r'src="fotos/([^"]+)"', r'src="/static/fotos/\1"', content)
    
    # Reemplazar enlaces HTML locales por rutas relativas del servidor
    content = re.sub(r'href="\./index\.html"', r'href="/"', content)
    content = re.sub(r'href="index\.html"', r'href="/"', content)
    content = re.sub(r'href="\./([^"]+\.html)"', r'href="/\1"', content)
    content = re.sub(r'href="(?!\/)([^"]+\.html)"', r'href="/\1"', content)
    
    return content

def add_flash_messages(content):
    # Añadir contenedor de mensajes flash justo después de <body>
    flash_block = """
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="container mt-3">
          {% for category, message in messages %}
            <div class="alert alert-{{ category if category != 'error' else 'danger' }} alert-dismissible fade show" role="alert">
              {{ message }}
              <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}
    """
    
    # Evitar duplicaciones
    if "{% with messages = get_flashed_messages" not in content:
        content = re.sub(r'(<body>)', r'\1' + flash_block, content)
    return content

def update_navbar_icons(content):
    # Encontrar la sección de header-icons e inyectar el menú dinámico del carrito y cuenta
    old_icons_pattern = r'<div class="header-icons d-flex align-items-center">.*?</a>\s*</div>'
    
    new_icons = """<div class="header-icons d-flex align-items-center">
                <div class="search-box">
                    <input type="text" class="search-input" placeholder="Buscar...">
                    <button class="search-btn" onclick="event.preventDefault(); this.previousElementSibling.focus();">
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-search nav-icon-search nav-svg-icon" viewBox="0 0 16 16">
                            <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
                        </svg>
                    </button>
                </div>
                <a href="/carrito.html" class="icon-link ms-3 position-relative" title="Carrito de Compras">
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" fill="currentColor" class="bi bi-cart3 nav-icon cart-icon-svg" viewBox="0 0 16 16">
                        <path d="M0 1.5A.5.5 0 0 1 .5 1H2a.5.5 0 0 1 .485.379L2.89 3H14.5a.5.5 0 0 1 .49.598l-1 5a.5.5 0 0 1-.465.401l-9.397.472L4.415 11H13a.5.5 0 0 1 0 1H4a.5.5 0 0 1-.491-.408L2.01 3.607 1.61 2H.5a.5.5 0 0 1-.5-.5zM3.102 4l.84 4.479 9.144-.459L13.89 4H3.102zM5 12a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm7 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-7 1a1 1 0 1 1 0 2 1 1 0 0 1 0-2zm7 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
                    </svg>
                    {% if cart_count > 0 %}
                    <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger" style="font-size: 0.65rem;">
                        {{ cart_count }}
                    </span>
                    {% endif %}
                </a>
                <a href="/cuenta.html" class="icon-link ms-3 d-flex align-items-center text-decoration-none" title="{% if logged_in %}Sesión iniciada como {{ user_name }}{% else %}Mi Cuenta{% endif %}" style="color: inherit;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" fill="currentColor" class="bi bi-person-circle nav-icon nav-svg-icon" viewBox="0 0 16 16">
                        <path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0z"/>
                        <path fill-rule="evenodd" d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1z"/>
                    </svg>
                    {% if logged_in %}
                    <span class="ms-1 d-none d-lg-inline" style="font-size: 0.95rem; color: #3eb3a0; font-weight: 500; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        {{ user_name }}
                    </span>
                    {% if session.get('user_email') == 'admin@vetesia.com' %}
                    <a href="/admin.html" class="ms-2 text-success" title="Panel de Administración">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-shield-lock-fill" viewBox="0 0 16 16">
                            <path fill-rule="evenodd" d="M8 0c-.69 0-1.843.265-2.928.56-1.11.3-2.229.655-2.887.87a1.54 1.54 0 0 0-1.044 1.262c-.596 4.477.787 7.795 2.465 9.99a11.8 11.8 0 0 0 2.517 2.453c.386.273.744.482 1.048.625.28.132.581.24.829.24s.548-.108.829-.24c.3-.143.662-.352 1.048-.625a11.8 11.8 0 0 0 2.517-2.453c1.678-2.195 3.061-5.513 2.465-9.99a1.54 1.54 0 0 0-1.044-1.263 63 63 0 0 0-2.887-.87C9.843.266 8.69 0 8 0m0 5a1.5 1.5 0 0 1 .5 2.915l.385 1.99a.5.5 0 0 1-.97.185l-.15-.75-.15.75a.5.5 0 0 1-.97-.186l.385-1.99A1.5 1.5 0 0 1 8 5"/>
                        </svg>
                    </a>
                    {% endif %}
                    <a href="/logout" class="ms-2 text-danger" title="Cerrar Sesión">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" class="bi bi-box-arrow-right" viewBox="0 0 16 16">
                            <path fill-rule="evenodd" d="M10 12.5a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-9a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v2a.5.5 0 0 0 1 0v-2A1.5 1.5 0 0 0 9.5 2h-8A1.5 1.5 0 0 0 0 3.5v9A1.5 1.5 0 0 0 1.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-2a.5.5 0 0 0-1 0z"/>
                            <path fill-rule="evenodd" d="M15.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 0 0-.708.708L14.293 7.5H5.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708z"/>
                        </svg>
                    </a>
                    {% endif %}
                </a>
            </div>"""
            
    content = re.sub(old_icons_pattern, new_icons, content, flags=re.DOTALL)
    return content

def process_index():
    file_path = os.path.join(templates_dir, 'index.html')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = update_asset_paths(content)
    content = add_flash_messages(content)
    content = update_navbar_icons(content)
    
    # Reemplazar sección de productos estrella por la lista dinámica
    products_section_pattern = r'<!-- PRODUCTOS SECTION -->.*?<!-- FOOTER -->'
    
    dynamic_products_section = """<!-- PRODUCTOS SECTION -->
    <section id="productos" class="container mt-5 mb-5 pt-3">
        <h2 class="text-center mb-5" style="font-size: 3rem; color: #7ed957;">NUESTROS PRODUCTOS ESTRELLA</h2>
        <div class="row justify-content-center">
            {% for producto in productos %}
            <div class="col-md-4 col-sm-6 mb-4">
                <div class="card product-card text-center position-relative h-100 d-flex flex-column justify-content-between">
                    <div>
                        <img src="/static/fotos/{{ producto.imagen_url }}" class="card-img-top product-img" alt="{{ producto.nombre }}">
                        <div class="card-body pb-0">
                            <h5 class="product-title">{{ producto.nombre }}</h5>
                            <p class="card-text text-muted mb-1" style="font-family: 'Smooch Sans', sans-serif; font-size: 1.4rem;">{{ producto.categoria }}</p>
                            <h4 class="mb-3 fw-bold" style="color: #4a4a4a;">{{ "{:,.2f}".format(producto.precio).replace(",", "X").replace(".", ",").replace("X", ".") }} €</h4>
                        </div>
                    </div>
                    <div class="card-body pt-0 pb-4">
                        <div class="d-flex justify-content-center gap-2 px-2">
                            <a href="/{{ producto.slug }}.html" class="btn btn-outline-secondary w-50 m-0" style="border-radius: 10px; font-weight: 500; font-size: 1.1rem !important; padding: 6px 0; display: flex; align-items: center; justify-content: center;">Ver Más</a>
                            <form action="/cart/add" method="POST" class="w-50 m-0">
                                <input type="hidden" name="product_id" value="{{ producto.id }}">
                                <input type="hidden" name="cantidad" value="1">
                                <button type="submit" class="btn btn-1 text-white w-100 m-0 d-flex align-items-center justify-content-center gap-1" style="font-size: 1.1rem; padding: 6px 0; height: 100%;"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M0 1.5A.5.5 0 0 1 .5 1H2a.5.5 0 0 1 .485.379L2.89 3H14.5a.5.5 0 0 1 .49.598l-1 5a.5.5 0 0 1-.465.401l-9.397.472L4.415 11H13a.5.5 0 0 1 0 1H4a.5.5 0 0 1-.491-.408L2.01 3.607 1.61 2H.5a.5.5 0 0 1-.5-.5zM3.102 4l.84 4.479 9.144-.459L13.89 4H3.102zM5 12a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm7 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-7 1a1 1 0 1 1 0 2 1 1 0 0 1 0-2zm7 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/></svg> Compra</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </section>

    <!-- FOOTER -->"""
    
    content = re.sub(products_section_pattern, dynamic_products_section, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("index.html actualizado.")

def process_tienda():
    file_path = os.path.join(templates_dir, 'tienda.html')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = update_asset_paths(content)
    content = add_flash_messages(content)
    content = update_navbar_icons(content)
    
    # Reemplazar sección de catálogo estrella por la lista dinámica
    products_section_pattern = r'<!-- PRODUCTOS SECTION -->.*?<!-- FOOTER -->'
    
    dynamic_products_section = """<!-- PRODUCTOS SECTION -->
        <section id="productos" class="container mt-5 mb-5 pt-3">
            <h2 class="text-center mb-5" style="font-size: 3rem; color: #7ed957;">MAQUINARIA VETERINARIA</h2>
            <div class="row justify-content-center">
                {% for producto in productos %}
                <div class="col-md-4 col-sm-6 mb-4">
                    <div class="card product-card text-center position-relative h-100 d-flex flex-column justify-content-between">
                        <div>
                            <button class="btn btn-light rounded-circle shadow-sm position-absolute top-0 end-0 m-3 heart-btn" onclick="this.classList.toggle('active'); event.preventDefault();">
                                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor" class="bi bi-heart-fill" viewBox="0 0 16 16">
                                    <path fill-rule="evenodd" d="M8 1.314C12.438-3.248 23.534 4.735 8 15-7.534 4.736 3.562-3.248 8 1.314z"/>
                                </svg>
                            </button>
                            <img src="/static/fotos/{{ producto.imagen_url }}" class="card-img-top product-img" alt="{{ producto.nombre }}">
                            <div class="card-body pb-0">
                                <h5 class="product-title">{{ producto.nombre }}</h5>
                                <p class="card-text text-muted mb-1" style="font-family: 'Smooch Sans', sans-serif; font-size: 1.4rem;">{{ producto.categoria }}</p>
                                <h4 class="mb-3 fw-bold" style="color: #4a4a4a;">{{ "{:,.2f}".format(producto.precio).replace(",", "X").replace(".", ",").replace("X", ".") }} €</h4>
                            </div>
                        </div>
                        <div class="card-body pt-0 pb-4">
                            <div class="d-flex justify-content-center gap-2 px-2">
                                <a href="/{{ producto.slug }}.html" class="btn btn-outline-secondary w-50 m-0" style="border-radius: 10px; font-weight: 500; font-size: 1.1rem !important; padding: 6px 0; display: flex; align-items: center; justify-content: center;">Ver Más</a>
                                <form action="/cart/add" method="POST" class="w-50 m-0">
                                    <input type="hidden" name="product_id" value="{{ producto.id }}">
                                    <input type="hidden" name="cantidad" value="1">
                                    <button type="submit" class="btn btn-1 text-white w-100 m-0 d-flex align-items-center justify-content-center gap-1" style="font-size: 1.1rem; padding: 6px 0; height: 100%;"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M0 1.5A.5.5 0 0 1 .5 1H2a.5.5 0 0 1 .485.379L2.89 3H14.5a.5.5 0 0 1 .49.598l-1 5a.5.5 0 0 1-.465.401l-9.397.472L4.415 11H13a.5.5 0 0 1 0 1H4a.5.5 0 0 1-.491-.408L2.01 3.607 1.61 2H.5a.5.5 0 0 1-.5-.5zM3.102 4l.84 4.479 9.144-.459L13.89 4H3.102zM5 12a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm7 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm-7 1a1 1 0 1 1 0 2 1 1 0 0 1 0-2zm7 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/></svg> Compra</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </section>
    </div>

    <!-- FOOTER -->"""
    
    content = re.sub(products_section_pattern, dynamic_products_section, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("tienda.html actualizado.")

def process_product_details(filename):
    file_path = os.path.join(templates_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = update_asset_paths(content)
    content = add_flash_messages(content)
    content = update_navbar_icons(content)
    
    # Reemplazar formulario estático de Añadir al carrito
    old_form_pattern = r'<div class="d-flex align-items-center mt-5 p-4" style="background: rgba\(62, 179, 160, 0\.05\);.*?</button>\s*</div>\s*</div>'
    
    new_form = """<form action="/cart/add" method="POST" class="d-flex align-items-center mt-5 p-4" style="background: rgba(62, 179, 160, 0.05); border-radius: 15px; border: 1px solid rgba(62, 179, 160, 0.2);">
                    <input type="hidden" name="product_id" value="{{ producto.id }}">
                    <div class="me-3" style="width: 100px;">
                        <label for="cantidad" class="form-label small text-muted mb-1">Cantidad</label>
                        <input type="number" name="cantidad" id="cantidad" class="form-control form-control-lg" value="1" min="1" style="text-align: center; border-radius: 10px;">
                    </div>
                    <div class="flex-grow-1 align-self-end">
                        <button type="submit" class="btn btn-custom w-100 btn-lg shadow-sm" style="border-radius: 10px; font-weight: 500;">
                            <i class="bi bi-cart-plus me-2"></i> Añadir al Carrito
                        </button>
                    </div>
                </form>"""
                
    content = re.sub(old_form_pattern, new_form, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"{filename} actualizado.")

def process_carrito():
    file_path = os.path.join(templates_dir, 'carrito.html')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = update_asset_paths(content)
    content = add_flash_messages(content)
    content = update_navbar_icons(content)
    
    # Reemplazar sección del carrito entera
    cart_section_pattern = r'<!-- CART SECTION -->.*?<!-- FOOTER -->'
    
    dynamic_cart_section = """<!-- CART SECTION -->
    <div class="container mt-5 mb-5" style="min-height: 50vh;">
        <h2 class="cart-title mb-4">Tu Carrito</h2>
        
        {% if not cart_items %}
        <div class="text-center py-5 shadow-sm border-0 bg-white" style="border-radius: 15px; padding: 40px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" fill="currentColor" class="bi bi-cart-x text-muted mb-3" viewBox="0 0 16 16">
                <path d="M7.354 5.646a.5.5 0 1 0-.708.708L7.793 7.5 6.646 8.646a.5.5 0 1 0 .708.708L8.5 8.207l1.146 1.147a.5.5 0 0 0 .708-.708L9.207 7.5l1.147-1.146a.5.5 0 0 0-.708-.708L8.5 6.793z"/>
                <path d="M.5 1a.5.5 0 0 0 0 1h1.11l.401 1.607 1.498 7.985A.5.5 0 0 0 4 12h1a2 2 0 1 0 0 4 2 2 0 0 0 0-4h7a2 2 0 1 0 0 4 2 2 0 0 0 0-4h1a.5.5 0 0 0 .491-.408l1.5-8A.5.5 0 0 0 14.5 3H2.89l-.405-1.621A.5.5 0 0 0 2 1zm3.915 10L3.102 4h10.796l-1.313 7zM6 14a1 1 0 1 1-2 0 1 1 0 0 1 2 0m7 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0"/>
            </svg>
            <h3 class="mb-4" style="color: #4a4a4a;">Tu carrito está vacío</h3>
            <a href="/tienda.html" class="btn btn-custom px-5 py-3 fs-5" style="border-radius: 30px;">Ir a la Tienda</a>
        </div>
        {% else %}
        <div class="row">
            <div class="col-lg-8">
                <!-- Cart Items -->
                <div class="card shadow-sm border-0 mb-4" style="border-radius: 15px;">
                    <div class="card-body">
                        {% for item in cart_items %}
                        <div class="d-flex align-items-center py-3 {% if not loop.last %}border-bottom{% endif %}">
                            <img src="/static/fotos/{{ item.producto.imagen_url }}" alt="{{ item.producto.nombre }}" class="cart-item-img me-3" style="width: 80px; height: 80px; object-fit: contain;">
                            <div class="flex-grow-1">
                                <h5 class="mb-1" style="font-size: 1.5rem; color: #3eb3a0;">{{ item.producto.nombre }}</h5>
                                <p class="mb-0 text-muted" style="font-family: 'Smooch Sans', sans-serif; font-size: 1.2rem;">{{ item.producto.categoria }}</p>
                            </div>
                            <div class="d-flex align-items-center me-4">
                                <form action="/cart/update" method="POST" class="m-0">
                                    <input type="hidden" name="product_id" value="{{ item.producto.id }}">
                                    <input type="hidden" name="action" value="decrease">
                                    <button type="submit" class="quantity-btn">-</button>
                                </form>
                                <span class="mx-3 fs-5" style="min-width: 20px; text-align: center;">{{ item.cantidad }}</span>
                                <form action="/cart/update" method="POST" class="m-0">
                                    <input type="hidden" name="product_id" value="{{ item.producto.id }}">
                                    <input type="hidden" name="action" value="increase">
                                    <button type="submit" class="quantity-btn">+</button>
                                </form>
                            </div>
                            <div class="text-end" style="width: 120px;">
                                <span class="fs-4 fw-bold">{{ "{:,.2f}".format(item.total_price).replace(",", "X").replace(".", ",").replace("X", ".") }}€</span>
                            </div>
                            <form action="/cart/delete" method="POST" class="m-0">
                                <input type="hidden" name="product_id" value="{{ item.producto.id }}">
                                <button type="submit" class="btn btn-link text-danger ms-3 p-0 text-decoration-none" title="Eliminar">
                                    <span class="fs-4">✖</span>
                                </button>
                            </form>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <div class="col-lg-4">
                <!-- Summary -->
                <div class="checkout-summary">
                    <h4 class="mb-4" style="color: #3eb3a0;">Resumen del Pedido</h4>
                    <div class="d-flex justify-content-between mb-3 fs-5" style="font-family: 'Smooch Sans', sans-serif;">
                        <span>Subtotal</span>
                        <span>{{ totals.subtotal }}€</span>
                    </div>
                    <div class="d-flex justify-content-between mb-3 fs-5" style="font-family: 'Smooch Sans', sans-serif;">
                        <span>Envío Asegurado B2B</span>
                        <span>{{ totals.envio }}€</span>
                    </div>
                    <div class="d-flex justify-content-between mb-3 fs-5 text-muted" style="font-family: 'Smooch Sans', sans-serif;">
                        <span>IVA (21%)</span>
                        <span>{{ totals.iva }}€</span>
                    </div>
                    <hr>
                    <div class="d-flex justify-content-between mb-4 mt-3">
                        <span class="fs-3 fw-bold">Total con IVA</span>
                        <span class="fs-3 fw-bold" style="color: #7ed957;">{{ totals.total }}€</span>
                    </div>
                    <a href="/pago.html" class="btn btn-custom w-100 mb-3 text-center d-block py-2 fs-5" style="border-radius: 30px; text-decoration: none;">Proceder al Pago</a>
                    <a href="/tienda.html" class="btn btn-outline-secondary w-100 py-2" style="border-radius: 30px; font-size: 1.2rem;">Seguir Comprando</a>
                </div>
            </div>
        </div>
        {% endif %}
    </div>

    <!-- FOOTER -->"""
    
    content = re.sub(cart_section_pattern, dynamic_cart_section, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("carrito.html actualizado.")

def process_cuenta():
    file_path = os.path.join(templates_dir, 'cuenta.html')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = update_asset_paths(content)
    content = add_flash_messages(content)
    content = update_navbar_icons(content)
    
    # Reemplazar el contenedor principal para manejar condicionalmente la cuenta de usuario / login
    account_section_pattern = r'<!-- MAIN ACCOUNT SECTION -->.*?<!-- FOOTER -->'
    
    dynamic_account_section = """<!-- MAIN ACCOUNT SECTION -->
    <div class="container" style="min-height: 60vh; margin-top: 50px; margin-bottom: 50px;">
        {% if logged_in %}
        <div class="row justify-content-center">
            <div class="col-md-10">
                <div class="card shadow-sm border-0 p-4" style="border-radius: 20px;">
                    <div class="d-flex justify-content-between align-items-center border-bottom pb-3 mb-4">
                        <div>
                            <h2 style="color: #3eb3a0; font-weight: 700;" class="mb-0">Panel de Control de {{ user_name }}</h2>
                            <p class="text-muted mb-0">Gestión de cuenta B2B y pedidos veterinarios</p>
                        </div>
                        <a href="/logout" class="btn btn-outline-danger px-4 py-2" style="border-radius: 20px;">Cerrar Sesión</a>
                    </div>
                    
                    {% if session.get('user_email') == 'admin@vetesia.com' %}
                    <!-- VISTA EXCLUSIVA DEL ADMINISTRADOR -->
                    <div class="row mt-4 justify-content-center py-4">
                        <div class="col-md-8 text-center">
                            <div class="p-5 bg-light shadow-sm" style="border-radius: 20px; border-top: 5px solid #3eb3a0;">
                                <i class="bi bi-shield-lock-fill text-success" style="font-size: 5rem;"></i>
                                <h3 class="fw-bold mt-3" style="color: #4a4a4a;">Acceso de Administrador Autorizado</h3>
                                <p class="text-muted fs-5">Tienes permisos totales para gestionar clientes, monitorizar pedidos y exportar reportes oficiales.</p>
                                <hr class="my-4">
                                <a href="/admin.html" class="btn btn-success px-5 py-3 fs-5" style="border-radius: 30px; font-weight: 600;">
                                    <i class="bi bi-speedometer2 me-2"></i>Ir al Panel de Administración
                                </a>
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <!-- VISTA GENERAL DEL CLIENTE B2B -->
                    <div class="row mt-4">
                        <div class="col-lg-4 mb-4">
                            <div class="p-3 bg-light" style="border-radius: 15px; border-left: 5px solid #7ed957;">
                                <h5 class="fw-bold" style="color: #4a4a4a;">Datos de Empresa</h5>
                                <hr>
                                <p class="mb-1"><strong>Empresa:</strong> {{ user_name }}</p>
                                <p class="mb-3"><strong>Correo:</strong> {{ session.get('user_email', '') }}</p>
                                <small class="text-muted">ID Cliente: #{{ session.get('user_id', '') }}</small>
                            </div>
                        </div>
                        
                        <div class="col-lg-8">
                            <h4 class="fw-bold mb-4" style="color: #3eb3a0;"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-box-seam me-2" viewBox="0 0 16 16"><path d="M8.186 1.113a.5.5 0 0 0-.372 0L1.846 3.5l2.404.962L10.404 2zm3.564 1.426L5.596 5 8 5.961 14.154 3.5zm3.25 1.7-6.5 2.6v7.922l6.5-2.6V4.24zM7.5 14.762V6.838L1 4.24v7.922zm.25-9.8L1.75 3.5 8 1 14.25 3.5z"/></svg>Historial de Pedidos</h4>
                            {% if not pedidos %}
                            <div class="text-center py-4 bg-light" style="border-radius: 15px;">
                                <p class="text-muted mb-0">Aún no has tramitado ningún pedido con nosotros.</p>
                                <a href="/tienda.html" class="btn btn-custom btn-sm mt-3 px-4">Ir a la Tienda</a>
                            </div>
                            {% else %}
                                {% for pedido in pedidos %}
                                <div class="card mb-4 border-0 shadow-sm" style="border-radius: 15px; overflow: hidden;">
                                    <div class="card-header bg-light d-flex justify-content-between align-items-center py-3 border-0">
                                        <div>
                                            <span class="fw-bold" style="color: #3eb3a0;">Pedido #{{ pedido.id }}</span>
                                            <span class="text-muted ms-3">{{ pedido.fecha }}</span>
                                        </div>
                                        <span class="badge bg-warning text-dark py-2 px-3" style="border-radius: 10px; font-weight: 500;">
                                            {{ pedido.estado | upper }}
                                        </span>
                                    </div>
                                    <div class="card-body">
                                        <div class="row">
                                            <div class="col-md-7">
                                                {% for item in pedido.articulos %}
                                                <div class="d-flex align-items-center mb-3">
                                                    <img src="/static/fotos/{{ item.imagen_url }}" alt="{{ item.nombre }}" class="me-3" style="width: 50px; height: 50px; object-fit: contain;">
                                                    <div>
                                                        <h6 class="mb-0 fw-bold">{{ item.nombre }}</h6>
                                                        <small class="text-muted">{{ item.cantidad }} x {{ "{:,.2f}".format(item.precio_unitario).replace(",", "X").replace(".", ",").replace("X", ".") }}€</small>
                                                    </div>
                                                </div>
                                                {% endfor %}
                                            </div>
                                            <div class="col-md-5 text-end border-start">
                                                <small class="text-muted d-block">CIF Facturación: {{ pedido.cif }}</small>
                                                <span class="fs-4 fw-bold mt-2 d-block" style="color: #7ed957;">{{ "{:,.2f}".format(pedido.total).replace(",", "X").replace(".", ",").replace("X", ".") }}€</span>
                                                <a href="/factura/{{ pedido.id }}.pdf" class="btn btn-outline-success btn-sm mt-3 px-3 py-1 d-inline-flex align-items-center gap-1" style="border-radius: 15px;">
                                                    <i class="bi bi-file-earmark-pdf"></i> Descargar Factura
                                                </a>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                {% endfor %}
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
        {% else %}
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-5">
                <div class="card form-card shadow-sm" style="border-radius: 20px; padding: 35px; background: white;">
                    <h2 class="login-title mb-4">Inicia Sesión</h2>
                    <form action="/cuenta.html" method="POST">
                        <div class="mb-3">
                            <input type="text" name="empresa" class="form-control form-control-custom" placeholder="Nombre de la Empresa o Correo" required style="border-radius: 10px;">
                        </div>
                        <div class="mb-4">
                            <input type="password" name="password" class="form-control form-control-custom" placeholder="Contraseña" required style="border-radius: 10px;">
                        </div>
                        <div class="d-flex justify-content-between align-items-center mb-4 px-2" style="font-family: 'Smooch Sans', sans-serif; font-size: 1.2rem;">
                            <div>
                                <input type="checkbox" id="rememberMe">
                                <label for="rememberMe" class="ms-1">Recuérdame</label>
                            </div>
                            <a href="/olvido.html" style="color: #3eb3a0; text-decoration: none;">¿Olvidaste tu contraseña?</a>
                        </div>
                        <button type="submit" class="btn btn-custom w-100 fs-4 py-2 mb-2" style="border-radius: 30px;">Entrar</button>
                        
                        <a href="/tienda.html" class="btn btn-outline-secondary w-100 fs-4 py-2 mb-3" style="border-radius: 30px; font-family: 'Smooch Sans', sans-serif;">Navegar como Invitado</a>
                        
                        <div class="text-center mt-3 pt-3 border-top" style="font-family: 'Smooch Sans', sans-serif; font-size: 1.3rem;">
                            ¿Aún no tienes cuenta? <a href="/registro.html" style="color: #7ed957; font-weight: bold; text-decoration: none;">Regístrate</a>
                        </div>
                        
                        <div class="text-center mt-3 p-3 bg-light rounded" style="font-family: 'Smooch Sans', sans-serif; font-size: 1.15rem; line-height: 1.3;">
                            <span class="d-block fw-bold text-muted mb-2">Accesos de Demostración:</span>
                            <div class="mb-1">🔑 <strong>Admin:</strong> <code>admin@vetesia.com</code> / <code>admin123</code></div>
                            <div>👤 <strong>Invitado B2B:</strong> <code>invitado@vetesia.com</code> / <code>invitado123</code></div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        {% endif %}
    </div>
```

    <!-- FOOTER -->"""
    
    content = re.sub(account_section_pattern, dynamic_account_section, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("cuenta.html actualizado.")

def process_registro():
    file_path = os.path.join(templates_dir, 'registro.html')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = update_asset_paths(content)
    content = add_flash_messages(content)
    content = update_navbar_icons(content)
    
    # Reemplazar el contenedor principal del registro
    register_section_pattern = r'<!-- MAIN ACCOUNT SECTION -->.*?<!-- FOOTER -->'
    
    dynamic_register_section = """<!-- MAIN ACCOUNT SECTION -->
    <div class="container" style="min-height: 50vh; margin-top: 50px; margin-bottom: 50px;">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-5">
                <div class="card form-card shadow-sm" style="border-radius: 20px; padding: 35px; background: white;">
                    <h2 class="login-title mb-4">Crear Cuenta B2B</h2>
                    <form action="/registro.html" method="POST">
                        <div class="mb-3">
                            <input type="text" name="empresa" class="form-control form-control-custom" placeholder="Nombre de la Empresa" required style="border-radius: 10px;">
                        </div>
                        <div class="mb-3">
                            <input type="email" name="email" class="form-control form-control-custom" placeholder="Correo Electrónico" required style="border-radius: 10px;">
                        </div>
                        <div class="mb-3">
                            <input type="password" name="password" class="form-control form-control-custom" placeholder="Contraseña" required style="border-radius: 10px;">
                        </div>
                        <div class="mb-4">
                            <input type="password" name="confirm_password" class="form-control form-control-custom" placeholder="Confirmar Contraseña" required style="border-radius: 10px;">
                        </div>
                        
                        <button type="submit" class="btn btn-custom w-100 fs-4 py-2" style="border-radius: 30px;">Registrarse</button>
                        
                        <div class="text-center mt-4 pt-3 border-top" style="font-family: 'Smooch Sans', sans-serif; font-size: 1.3rem;">
                            ¿Ya tienes cuenta? <a href="/cuenta.html" style="color: #7ed957; font-weight: bold; text-decoration: none;">Inicia Sesión</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- FOOTER -->"""
    
    content = re.sub(register_section_pattern, dynamic_register_section, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("registro.html actualizado.")

def process_pago():
    file_path = os.path.join(templates_dir, 'pago.html')
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = update_asset_paths(content)
    content = add_flash_messages(content)
    content = update_navbar_icons(content)
    
    # Adaptar inputs duplicados (name="cp") en pago.html y poner el action
    # Primero cambiar el action del formulario
    content = re.sub(r'<form action="post" method="get" class="was-validated">', r'<form action="/submit_order" method="POST" class="was-validated">', content)
    
    # Reemplazar el input de dirección
    old_direccion = """<div class=" mt-3">
                <label for="text" class="form-label">Dirección:</label>
                <input type="text" name="cp" id="cp" class="form-control" placeholder="introduzca su dirección"
                    required>"""
    new_direccion = """<div class=" mt-3">
                <label for="direccion" class="form-label">Dirección:</label>
                <input type="text" name="direccion" id="direccion" class="form-control" placeholder="Introduzca su dirección de entrega"
                    required>"""
    content = content.replace(old_direccion, new_direccion)
    
    # Reemplazar el input de código postal
    old_cp = """<div class=" mt-3 ">
                <label for="text" class="form-label">Código postal (5 números):</label>
                <input type="text" name="cp" id="cp" class="form-control" placeholder="introduzca su código postal"
                    required pattern="[0-9]{5}">"""
    new_cp = """<div class=" mt-3 ">
                <label for="codigo_postal" class="form-label">Código postal (5 números):</label>
                <input type="text" name="codigo_postal" id="codigo_postal" class="form-control" placeholder="Introduzca su código postal"
                    required pattern="[0-9]{5}">"""
    content = content.replace(old_cp, new_cp)
    
    # Rellenar campos predeterminados de sesión si está logueado
    content = content.replace('placeholder="Introduzca el nombre de la empresa"\n                    required>', 'placeholder="Introduzca el nombre de la empresa"\n                    required value="{{ session.get(\'user_name\', \'\') }}">')
    content = content.replace('placeholder="introduzca su correo electrónico" required', 'placeholder="introduzca su correo electrónico" required value="{{ session.get(\'user_email\', \'\') }}"')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("pago.html actualizado.")

def process_generic_page(filename):
    file_path = os.path.join(templates_dir, filename)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    content = update_asset_paths(content)
    content = add_flash_messages(content)
    content = update_navbar_icons(content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"{filename} actualizado.")

def run_updates():
    process_index()
    process_tienda()
    process_product_details('veta5plus.html')
    process_product_details('wato20.html')
    process_product_details('circuito.html')
    process_carrito()
    process_cuenta()
    process_registro()
    process_pago()
    
    # Páginas genéricas que no requieren lógica de backend específica
    for page in ['servicios.html', 'informacion.html', 'olvido.html']:
        process_generic_page(page)

if __name__ == '__main__':
    run_updates()
