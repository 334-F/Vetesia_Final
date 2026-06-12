from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from pdf_generator import generar_factura_pdf, generar_reporte_clientes_pdf

app = Flask(__name__)
app.secret_key = 'vetesia_secret_key_for_session_management'

def get_db_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def run_migrations():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(usuarios)")
            columns = [row['name'] for row in cursor.fetchall()]
            
            new_cols = {
                "cif": "TEXT",
                "contacto": "TEXT",
                "telefono": "TEXT",
                "direccion": "TEXT",
                "codigo_postal": "TEXT",
                "municipio": "TEXT",
                "zona": "TEXT",
                "banco": "TEXT",
                "iban": "TEXT"
            }
            
            for col, col_type in new_cols.items():
                if col not in columns:
                    cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {col} {col_type}")
                    print(f"Added column {col} to usuarios table.")
                    
        # Crear la tabla favoritos si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favoritos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos (id) ON DELETE CASCADE,
                UNIQUE(usuario_id, producto_id)
            )
        ''')
        conn.commit()
        conn.close()

run_migrations()

# Inyectar el número de items del carrito y estado de login en todas las plantillas
@app.context_processor
def inject_global_data():
    cart = session.get('cart', {})
    cart_count = sum(cart.values())
    
    logged_in = 'user_id' in session
    user_name = session.get('user_name', '')
    
    def get_image_url(url):
        if not url:
            return '/static/fotos/logo.webp'
        if '://' in url or url.startswith('/') or url.startswith('data:'):
            return url
        return f'/static/fotos/{url}'
        
    return dict(cart_count=cart_count, logged_in=logged_in, user_name=user_name, get_image_url=get_image_url)

# --- RUTAS DE NAVEGACIÓN GENERAL ---

@app.route('/')
@app.route('/index.html')
def index():
    conn = get_db_connection()
    productos = conn.execute('SELECT * FROM productos LIMIT 3').fetchall()
    conn.close()
    return render_template('index.html', productos=productos)

@app.route('/tienda.html')
def tienda():
    conn = get_db_connection()
    productos = conn.execute('SELECT * FROM productos').fetchall()

    favoritos = []

    if 'user_id' in session:
        favoritos_db = conn.execute(
            'SELECT producto_id FROM favoritos WHERE usuario_id = ?',
            (session['user_id'],)
        ).fetchall()

        favoritos = [f['producto_id'] for f in favoritos_db]

    conn.close()

    return render_template(
        'tienda.html',
        productos=productos,
        favoritos=favoritos
    )

@app.route('/servicios.html')
def servicios():
    return render_template('servicios.html')

@app.route('/informacion.html')
def informacion():
    return render_template('informacion.html')

# --- RUTAS DE PRODUCTO ---

# --- RUTA DINÁMICA DE DETALLE DE PRODUCTO Y COMENTARIOS ---

@app.route('/<slug>.html')
def producto_detalle(slug):
    conn = get_db_connection()
    producto = conn.execute('SELECT * FROM productos WHERE slug = ?', (slug,)).fetchone()
    
    if not producto:
        conn.close()
        return "Producto no encontrado", 404
        
    especificaciones = json.loads(producto['especificaciones_json']) if producto['especificaciones_json'] else {}
    
    # Cargar comentarios verificados del producto
    resenas = conn.execute('''
        SELECT r.*, u.nombre_empresa AS usuario_nombre 
        FROM resenas r 
        LEFT JOIN usuarios u ON r.usuario_id = u.id 
        WHERE r.producto_id = ? AND r.verificada = 1
        ORDER BY r.fecha DESC
    ''', (producto['id'],)).fetchall()
    
    # Calcular promedio de estrellas
    promedio_rating = conn.execute('SELECT AVG(valoracion) FROM resenas WHERE producto_id = ? AND verificada = 1', (producto['id'],)).fetchone()[0] or 0.0
    promedio_rating = round(promedio_rating, 1)
    
    conn.close()
    
    # Si es uno de los 3 productos con plantilla específica:
    if slug in ('veta5plus', 'wato20', 'circuito'):
        return render_template(f'{slug}.html', producto=producto, especificaciones=especificaciones, resenas=resenas, promedio_rating=promedio_rating)
    else:
        return render_template('producto_generico.html', producto=producto, especificaciones=especificaciones, resenas=resenas, promedio_rating=promedio_rating)

@app.route('/producto/<int:producto_id>/resena/crear', methods=['POST'])
def producto_resena_crear(producto_id):
    if 'user_id' not in session:
        flash("Inicia sesión para dejar una valoración.", "danger")
        return redirect(url_for('cuenta'))
        
    valoracion = request.form.get('valoracion')
    texto = request.form.get('texto')
    
    if valoracion and texto:
        conn = get_db_connection()
        producto = conn.execute("SELECT slug FROM productos WHERE id = ?", (producto_id,)).fetchone()
        if not producto:
            conn.close()
            return "Producto no encontrado", 404
            
        conn.execute('''
            INSERT INTO resenas (usuario_id, producto_id, valoracion, texto, verificada)
            VALUES (?, ?, ?, ?, 0)
        ''', (session['user_id'], producto_id, int(valoracion), texto))
        conn.commit()
        conn.close()
        flash("Tu valoración ha sido enviada con éxito. Aparecerá una vez sea verificada por un administrador.", "success")
        return redirect(url_for('producto_detalle', slug=producto['slug']))
    else:
        flash("Datos de valoración incompletos.", "warning")
        return redirect(url_for('index'))

# --- RUTAS DE AUTENTICACIÓN ---

@app.route('/registro.html', methods=['GET', 'POST'])
def registro():
    if 'user_id' in session:
        return redirect(url_for('cuenta'))
        
    if request.method == 'POST':
        nombre_empresa = request.form.get('empresa')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Campos de empresa B2B
        cif = request.form.get('cif')
        contacto = request.form.get('contacto')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        codigo_postal = request.form.get('codigo_postal')
        municipio = request.form.get('municipio')
        zona = request.form.get('zona')
        banco = request.form.get('banco')
        iban = request.form.get('iban')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('registro.html')
            
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        
        if user:
            flash('El correo electrónico ya está registrado.', 'danger')
            conn.close()
            return render_template('registro.html')
            
        password_hash = generate_password_hash(password)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO usuarios (
                nombre_empresa, email, password_hash, cif, contacto, telefono, 
                direccion, codigo_postal, municipio, zona, banco, iban
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (nombre_empresa, email, password_hash, cif, contacto, telefono,
             direccion, codigo_postal, municipio, zona, banco, iban)
        )
        conn.commit()
        
        # Iniciar sesión automáticamente después de registrarse
        new_user_id = cursor.lastrowid
        session['user_id'] = new_user_id
        session['user_name'] = nombre_empresa
        session['user_email'] = email
        
        conn.close()
        flash('Cuenta de empresa creada con éxito.', 'success')
        return redirect(url_for('cuenta'))
        
    return render_template('registro.html')

@app.route('/cuenta.html', methods=['GET', 'POST'])
def cuenta():
    if request.method == 'POST':
        nombre_empresa = request.form.get('empresa')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE nombre_empresa = ? OR email = ?', (nombre_empresa, nombre_empresa)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['nombre_empresa']
            session['user_email'] = user['email']
            conn.close()
            flash('Sesión iniciada correctamente.', 'success')
            return redirect(url_for('cuenta'))
        else:
            flash('Credenciales incorrectas.', 'danger')
            conn.close()
            
    # Si ya está logueado, mostrar datos de la empresa e historial de pedidos
    if 'user_id' in session:
        conn = get_db_connection()
        pedidos_db = conn.execute(
            'SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY fecha DESC',
            (session['user_id'],)
        ).fetchall()
        
        pedidos = []
        for p in pedidos_db:
            items = conn.execute('''
                SELECT dp.*, prod.nombre, prod.imagen_url 
                FROM detalles_pedido dp 
                JOIN productos prod ON dp.producto_id = prod.id 
                WHERE dp.pedido_id = ?
            ''', (p['id'],)).fetchall()
            
            pedidos.append({
                'id': p['id'],
                'cif': p['cif'],
                'fecha': p['fecha'],
                'total': p['total'],
                'estado': p['estado'],
                'articulos': items
            })
            
        conn.close()
        return render_template('cuenta.html', pedidos=pedidos)
        
    return render_template('cuenta.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    flash('Has cerrado sesión.', 'success')
    return redirect(url_for('cuenta'))

@app.route('/olvido.html')
def olvido():
    return render_template('olvido.html')

# --- RUTAS DEL CARRITO ---

@app.route('/carrito.html')
def carrito():
    cart = session.get('cart', {})
    conn = get_db_connection()
    
    cart_items = []
    subtotal_all = 0.0
    
    for prod_id_str, qty in list(cart.items()):
        product = conn.execute('SELECT * FROM productos WHERE id = ?', (int(prod_id_str),)).fetchone()
        if product:
            total_price = product['precio'] * qty
            subtotal_all += total_price
            cart_items.append({
                'producto': product,
                'cantidad': qty,
                'total_price': total_price
            })
        else:
            # Eliminar del carrito si no existe en la base de datos
            cart.pop(prod_id_str, None)
            session['cart'] = cart
            session.modified = True
            
    conn.close()
    
    envio = 45.00 if subtotal_all > 0 else 0.0
    iva = subtotal_all * 0.21
    total = subtotal_all + envio + iva
    
    # Formatear números para visualización
    totals = {
        'subtotal': f"{subtotal_all:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        'envio': f"{envio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        'iva': f"{iva:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        'total': f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    }
    
    return render_template('carrito.html', cart_items=cart_items, totals=totals)

@app.route('/cart/add', methods=['POST'])
def cart_add():
    product_id = request.form.get('product_id', type=int)
    cantidad = request.form.get('cantidad', default=1, type=int)
    
    if product_id:
        cart = session.get('cart', {})
        # Las claves en la sesión JSON de Flask se guardan como strings
        prod_id_str = str(product_id)
        if prod_id_str in cart:
            cart[prod_id_str] += cantidad
        else:
            cart[prod_id_str] = cantidad
        session['cart'] = cart
        session.modified = True
        
    return redirect(url_for('carrito'))

@app.route('/cart/update', methods=['POST'])
def cart_update():
    product_id = request.form.get('product_id')
    action = request.form.get('action') # 'increase' o 'decrease'
    
    if product_id:
        cart = session.get('cart', {})
        prod_id_str = str(product_id)
        if prod_id_str in cart:
            if action == 'increase':
                cart[prod_id_str] += 1
            elif action == 'decrease':
                cart[prod_id_str] -= 1
                if cart[prod_id_str] <= 0:
                    cart.pop(prod_id_str)
            session['cart'] = cart
            session.modified = True
            
    return redirect(url_for('carrito'))

@app.route('/cart/delete', methods=['POST'])
def cart_delete():
    product_id = request.form.get('product_id')
    
    if product_id:
        cart = session.get('cart', {})
        prod_id_str = str(product_id)
        cart.pop(prod_id_str, None)
        session['cart'] = cart
        session.modified = True
        
    return redirect(url_for('carrito'))

# --- RUTAS DE PEDIDO / CHECKOUT ---

@app.route('/pago.html')
def pago():
    cart = session.get('cart', {})
    if not cart:
        flash("El carrito está vacío.", "warning")
        return redirect(url_for('tienda'))
    
    user_data = None
    if 'user_id' in session:
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        
    return render_template('pago.html', user_data=user_data)

@app.route('/submit_order', methods=['POST'])
def submit_order():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('tienda'))
        
    # Obtener datos del formulario
    empresa = request.form.get('empresa')
    contacto = request.form.get('contacto')
    cif = request.form.get('cif')
    email = request.form.get('email')
    telefono = request.form.get('telef')
    zona_val = request.form.get('country')
    municipio = request.form.get('ct')
    direccion = request.form.get('direccion') 
    codigo_postal = request.form.get('codigo_postal') 
    
    
    titular_cuenta = request.form.get('titular_cuenta')
    iban = request.form.get('iban')
    banco = request.form.get('banco')
    
    # Traducir zona
    zona_map = {"PI": "Península Ibérica", "IB": "Islas Baleares", "IC": "Islas Canarias"}
    zona_val = zona_map.get(zona_val, zona_val)
    
    # Calcular precios en el servidor
    conn = get_db_connection()
    subtotal_all = 0.0
    items_to_save = []
    
    for prod_id_str, qty in cart.items():
        product = conn.execute('SELECT * FROM productos WHERE id = ?', (int(prod_id_str),)).fetchone()
        if product:
            price = product['precio']
            subtotal_all += price * qty
            items_to_save.append({
                'producto_id': product['id'],
                'cantidad': qty,
                'precio_unitario': price
            })
            
    envio = 45.00 if subtotal_all > 0 else 0.0
    iva = subtotal_all * 0.21
    total = subtotal_all + envio + iva
    
    # Guardar en base de datos
    cursor = conn.cursor()
    usuario_id = session.get('user_id') # Puede ser None si compra como invitado
    
    cursor.execute('''
        INSERT INTO pedidos (
            usuario_id, empresa, email, cif, contacto, telefono, zona, municipio, direccion, codigo_postal, 
            titular_cuenta, iban, banco, subtotal, iva, total
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        usuario_id, empresa, email, cif, contacto, telefono, zona_val, municipio, direccion, codigo_postal,
        titular_cuenta, iban, banco, subtotal_all, iva, total
    ))
    
    pedido_id = cursor.lastrowid
    
    for item in items_to_save:
        cursor.execute('''
            INSERT INTO detalles_pedido (pedido_id, producto_id, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
        ''', (pedido_id, item['producto_id'], item['cantidad'], item['precio_unitario']))
        
    conn.commit()
    conn.close()
    
    # Vaciar carrito de la sesión
    session.pop('cart', None)
    
    # Guardar ID del último pedido en la sesión para mostrarlo en la confirmación
    session['last_order_id'] = pedido_id
    
    return redirect(url_for('confirmacion'))

@app.route('/confirmacion')
def confirmacion():
    order_id = session.get('last_order_id')
    if not order_id:
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    pedido = conn.execute('SELECT * FROM pedidos WHERE id = ?', (order_id,)).fetchone()
    if not pedido:
        conn.close()
        return redirect(url_for('index'))
        
    items = conn.execute('''
        SELECT dp.*, p.nombre, p.imagen_url 
        FROM detalles_pedido dp 
        JOIN productos p ON dp.producto_id = p.id 
        WHERE dp.pedido_id = ?
    ''', (order_id,)).fetchall()
    conn.close()
    
    # Formatear números
    totals = {
        'subtotal': f"{pedido['subtotal']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        'envio': f"{pedido['envio'] if 'envio' in pedido.keys() else 45.00:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), # fallback
        'iva': f"{pedido['iva']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        'total': f"{pedido['total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    }
    # En SQLite, la columna de envío se calcula o almacena. Espera, en la tabla no pusimos envío como columna explícita, sino subtotal, iva, total.
    # El envío es simplemente: total - subtotal - iva.
    envio_calc = pedido['total'] - pedido['subtotal'] - pedido['iva']
    totals['envio'] = f"{envio_calc:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    return render_template('confirmacion.html', pedido=pedido, items=items, totals=totals)

@app.route('/factura/<int:pedido_id>.pdf')
def descargar_factura(pedido_id):
    conn = get_db_connection()
    pedido = conn.execute('SELECT * FROM pedidos WHERE id = ?', (pedido_id,)).fetchone()
    
    if not pedido:
        conn.close()
        return "Factura no encontrada", 404
        
    es_autorizado = False
    if 'user_id' in session and session['user_id'] == pedido['usuario_id']:
        es_autorizado = True
    elif session.get('last_order_id') == pedido_id:
        es_autorizado = True
        
    if not es_autorizado:
        conn.close()
        return "No tienes permiso para ver esta factura", 403
        
    items = conn.execute('''
        SELECT dp.*, p.nombre, p.imagen_url 
        FROM detalles_pedido dp 
        JOIN productos p ON dp.producto_id = p.id 
        WHERE dp.pedido_id = ?
    ''', (pedido_id,)).fetchall()
    conn.close()
    print(dict(pedido))
    
    pdf_buffer = generar_factura_pdf(pedido, items)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'factura_vetesia_{pedido_id}.pdf'
    )

@app.route('/admin.html')
def admin():
    if 'user_id' not in session:
        flash("Acceso restringido. Por favor inicia sesión.", "danger")
        return redirect(url_for('cuenta'))
        
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM usuarios WHERE id = ?", (session['user_id'],)).fetchone()
    
    if not user or user['rol'] not in ('admin', 'trabajador'):
        conn.close()
        flash("Acceso restringido. No tienes permisos para acceder a esta área.", "danger")
        return redirect(url_for('cuenta'))
        
    user_rol = user['rol']
    
    # Estadísticas básicas B2B
    total_clientes = conn.execute("SELECT count(*) FROM usuarios WHERE email != 'admin@vetesia.com'").fetchone()[0]
    total_pedidos = conn.execute("SELECT count(*) FROM pedidos").fetchone()[0]
    
    # Ventas, Compras y Balance Neto
    total_ventas = conn.execute("SELECT sum(total) FROM pedidos WHERE estado IN ('pagado', 'procesando', 'enviado', 'entregado')").fetchone()[0] or 0.0
    total_compras = conn.execute("SELECT sum(monto) FROM compras").fetchone()[0] or 0.0
    balance_neto = total_ventas - total_compras
    
    ventas_formateadas = f"{total_ventas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    compras_formateadas = f"{total_compras:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    balance_formateado = f"{balance_neto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    # Consultar todos los clientes registrados consolidando sus datos de facturación
    clientes_registrados = conn.execute('''
        SELECT u.id, u.nombre_empresa, u.email, p.cif, p.contacto, p.telefono, p.banco, p.iban, p.municipio, p.zona, p.direccion, p.codigo_postal
        FROM usuarios u
        LEFT JOIN (
            SELECT usuario_id, cif, contacto, telefono, banco, iban, municipio, zona, direccion, codigo_postal, max(fecha) 
            FROM pedidos 
            GROUP BY usuario_id
        ) p ON u.id = p.usuario_id
        WHERE u.email != 'admin@vetesia.com'
        ORDER BY u.id ASC
    ''').fetchall()
    
    # Consultar clientes invitados únicos
    clientes_invitados = conn.execute('''
        SELECT NULL as id, empresa as nombre_empresa, email, cif, contacto, telefono, banco, iban, municipio, zona, direccion, codigo_postal
        FROM pedidos
        WHERE usuario_id IS NULL
        GROUP BY cif
    ''').fetchall()
    
    todos_clientes = list(clientes_registrados) + list(clientes_invitados)
    
    # Consultar usuarios
    usuarios = conn.execute("SELECT * FROM usuarios ORDER BY id ASC").fetchall()
    
    # Consultar pedidos
    pedidos_raw = conn.execute('SELECT * FROM pedidos ORDER BY fecha DESC').fetchall()
    pedidos = []
    for p in pedidos_raw:
        items = conn.execute('''
            SELECT dp.*, prod.nombre 
            FROM detalles_pedido dp 
            JOIN productos prod ON dp.producto_id = prod.id 
            WHERE dp.pedido_id = ?
        ''', (p['id'],)).fetchall()
        pedidos.append({
            'id': p['id'],
            'empresa': p['contacto'],
            'cif': p['cif'],
            'total': p['total'],
            'fecha': p['fecha'],
            'estado': p['estado'],
            'articulos': items
        })
        
    # Consultar todos los productos
    productos = conn.execute('SELECT * FROM productos ORDER BY id ASC').fetchall()
    
    # Consultar categorías
    categorias = conn.execute('SELECT * FROM categorias ORDER BY id ASC').fetchall()
    
    # Consultar reseñas pendientes
    resenas_pendientes = conn.execute('''
        SELECT r.*, u.nombre_empresa AS usuario_nombre, p.nombre AS producto_nombre
        FROM resenas r
        JOIN usuarios u ON r.usuario_id = u.id
        JOIN productos p ON r.producto_id = p.id
        WHERE r.verificada = 0
        ORDER BY r.fecha DESC
    ''').fetchall()
    
    # Consultar proveedores
    proveedores = conn.execute('SELECT * FROM proveedores ORDER BY id ASC').fetchall()
    
    # Consultar compras (gastos de proveedores)
    compras = conn.execute('''
        SELECT c.*, p.nombre AS proveedor_nombre
        FROM compras c
        LEFT JOIN proveedores p ON c.proveedor_id = p.id
        ORDER BY c.fecha DESC
    ''').fetchall()
    
    # Informes
    informe_stock = conn.execute('''
        SELECT id, nombre, stock, stock_minimo, (stock_minimo - stock) AS diferencia
        FROM productos
        WHERE stock <= stock_minimo
        ORDER BY diferencia DESC
    ''').fetchall()
    
    informe_ventas = conn.execute('''
        SELECT strftime('%Y-%m', fecha) AS mes, COUNT(*) AS num_pedidos, SUM(total) AS ingresos
        FROM pedidos
        WHERE estado IN ('pagado', 'procesando', 'enviado', 'entregado')
        GROUP BY mes
        ORDER BY mes DESC
        LIMIT 12
    ''').fetchall()
    
    informe_top = conn.execute('''
        SELECT p.id, p.nombre, SUM(dp.cantidad) AS unidades, SUM(dp.cantidad * dp.precio_unitario) AS ingresos
        FROM detalles_pedido dp
        JOIN productos p ON dp.producto_id = p.id
        JOIN pedidos pe ON dp.pedido_id = pe.id
        WHERE pe.estado IN ('pagado', 'procesando', 'enviado', 'entregado')
        GROUP BY p.id, p.nombre
        ORDER BY unidades DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    stats = {
        'total_clientes': total_clientes + len(clientes_invitados),
        'total_pedidos': total_pedidos,
        'total_ventas': ventas_formateadas,
        'total_compras': compras_formateadas,
        'balance_neto': balance_formateado,
        'balance_raw': balance_neto
    }
    
    return render_template('admin.html', stats=stats, clientes=todos_clientes, usuarios=usuarios,
                           pedidos=pedidos, productos=productos, categorias=categorias,
                           resenas_pendientes=resenas_pendientes,
                           proveedores=proveedores, compras=compras, informe_stock=informe_stock,
                           informe_ventas=informe_ventas, informe_top=informe_top, user_rol=user_rol)

@app.route('/admin/compra/crear', methods=['POST'])
def admin_compra_crear():
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    proveedor_id = request.form.get('proveedor_id')
    concepto = request.form.get('concepto')
    monto = request.form.get('monto')
    fecha = request.form.get('fecha')
    
    if concepto and monto:
        conn = get_db_connection()
        prov_val = int(proveedor_id) if proveedor_id else None
        
        if fecha:
            conn.execute('''
                INSERT INTO compras (proveedor_id, concepto, monto, fecha)
                VALUES (?, ?, ?, ?)
            ''', (prov_val, concepto, float(monto), fecha))
        else:
            conn.execute('''
                INSERT INTO compras (proveedor_id, concepto, monto)
                VALUES (?, ?, ?)
            ''', (prov_val, concepto, float(monto)))
            
        conn.commit()
        conn.close()
        flash("Gasto de proveedor registrado con éxito.", "success")
    else:
        flash("Datos incompletos para registrar gasto.", "warning")
    return redirect(url_for('admin'))

@app.route('/admin/compra/eliminar/<int:compra_id>', methods=['POST'])
def admin_compra_eliminar(compra_id):
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    conn = get_db_connection()
    conn.execute("DELETE FROM compras WHERE id=?", (compra_id,))
    conn.commit()
    conn.close()
    flash("Registro de gasto eliminado.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/reporte_financiero.pdf')
def admin_reporte_financiero():
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        return "No autorizado", 403
        
    conn = get_db_connection()
    
    # 1. Ventas
    ventas = conn.execute('''
        SELECT id, fecha, contacto AS empresa, cif, total, estado
        FROM pedidos
        WHERE estado IN ('pagado', 'procesando', 'enviado', 'entregado')
        ORDER BY fecha DESC
    ''').fetchall()
    
    # 2. Compras
    compras = conn.execute('''
        SELECT c.*, p.nombre AS proveedor_nombre
        FROM compras c
        LEFT JOIN proveedores p ON c.proveedor_id = p.id
        ORDER BY c.fecha DESC
    ''').fetchall()
    
    # Totales
    total_ventas = conn.execute("SELECT sum(total) FROM pedidos WHERE estado IN ('pagado', 'procesando', 'enviado', 'entregado')").fetchone()[0] or 0.0
    total_compras = conn.execute("SELECT sum(monto) FROM compras").fetchone()[0] or 0.0
    balance_neto = total_ventas - total_compras
    
    conn.close()
    
    from pdf_generator import generar_reporte_financiero_pdf
    pdf_buffer = generar_reporte_financiero_pdf(ventas, compras, total_ventas, total_compras, balance_neto)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='reporte_financiero_vetesia.pdf'
    )


@app.route('/admin/pedido/<int:pedido_id>/estado', methods=['POST'])
def admin_pedido_estado(pedido_id):
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    nuevo_estado = request.form.get('estado')
    if nuevo_estado:
        conn = get_db_connection()
        conn.execute("UPDATE pedidos SET estado=? WHERE id=?", (nuevo_estado, pedido_id))
        conn.commit()
        conn.close()
        flash(f"Estado del pedido #{pedido_id} actualizado con éxito.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/producto/editar', methods=['POST'])
def admin_producto_editar():
    if 'user_id' not in session:
        flash("Acceso restringido. Por favor inicia sesión.", "danger")
        return redirect(url_for('cuenta'))
        
    conn = get_db_connection()
    user = conn.execute('SELECT rol FROM usuarios WHERE id=?', (session['user_id'],)).fetchone()
    
    if not user or user['rol'] not in ('admin', 'trabajador'):
        conn.close()
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    producto_id = request.form.get('id')
    stock = request.form.get('stock')
    
    if user['rol'] == 'trabajador':
        if producto_id and stock is not None:
            conn.execute("UPDATE productos SET stock=? WHERE id=?", (int(stock), int(producto_id)))
            conn.commit()
            conn.close()
            flash("Stock de producto actualizado con éxito por Trabajador.", "success")
        else:
            conn.close()
            flash("Datos incompletos para actualizar el stock.", "warning")
    else:
        precio = request.form.get('precio')
        stock_minimo = request.form.get('stock_minimo', 5)
        activo = request.form.get('activo', '1')
        imagen_url = request.form.get('imagen_url')
        
        if producto_id and precio is not None and stock is not None and imagen_url:
            conn.execute("UPDATE productos SET precio=?, stock=?, stock_minimo=?, activo=?, imagen_url=? WHERE id=?", 
                         (float(precio), int(stock), int(stock_minimo), int(activo), imagen_url, int(producto_id)))
            conn.commit()
            conn.close()
            flash("Producto actualizado con éxito por Administrador.", "success")
        else:
            conn.close()
            flash("Datos incompletos.", "warning")
            
    return redirect(url_for('admin'))

@app.route('/admin/producto/crear', methods=['POST'])
def admin_producto_crear():
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    nombre = request.form.get('nombre')
    slug = request.form.get('slug')
    categoria = request.form.get('categoria')
    precio = request.form.get('precio')
    descripcion = request.form.get('descripcion')
    stock = request.form.get('stock', 20)
    stock_minimo = request.form.get('stock_minimo', 5)
    imagen_url = request.form.get('imagen_url', 'logo.webp')
    
    if nombre and slug and categoria and precio:
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO productos (nombre, slug, categoria, precio, descripcion, imagen_url, stock, stock_minimo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nombre, slug, categoria, float(precio), descripcion, imagen_url, int(stock), int(stock_minimo)))
            conn.commit()
            flash(f"Producto '{nombre}' creado con éxito.", "success")
        except sqlite3.IntegrityError:
            flash(f"Error: El slug '{slug}' ya está en uso.", "danger")
        finally:
            conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/producto/eliminar/<int:producto_id>', methods=['POST'])
def admin_producto_eliminar(producto_id):
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    conn = get_db_connection()
    conn.execute("DELETE FROM productos WHERE id=?", (producto_id,))
    conn.commit()
    conn.close()
    flash("Producto eliminado con éxito.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/usuario/<int:usuario_id>/rol', methods=['POST'])
def admin_usuario_rol(usuario_id):
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    nuevo_rol = request.form.get('rol')
    if nuevo_rol in ('admin', 'cliente', 'trabajador'):
        conn = get_db_connection()
        conn.execute("UPDATE usuarios SET rol=? WHERE id=?", (nuevo_rol, usuario_id))
        conn.commit()
        conn.close()
        flash("Rol de usuario actualizado con éxito.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/usuario/<int:usuario_id>/eliminar', methods=['POST'])
def admin_usuario_eliminar(usuario_id):
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    if usuario_id == session.get('user_id'):
        flash("No puedes eliminar tu propio usuario.", "danger")
        return redirect(url_for('admin'))
        
    conn = get_db_connection()
    target_user = conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if target_user and target_user['email'] == 'admin@vetesia.com':
        conn.close()
        flash("No se puede eliminar la cuenta principal de administrador.", "danger")
        return redirect(url_for('admin'))
        
    conn.execute("DELETE FROM usuarios WHERE id=?", (usuario_id,))
    conn.commit()
    conn.close()
    flash("Usuario eliminado de forma permanente con éxito.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/usuario/crear', methods=['POST'])
def admin_usuario_crear():
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    empresa = request.form.get('empresa')
    email = request.form.get('email')
    password = request.form.get('password')
    rol = request.form.get('rol')
    
    # Opcionales B2B
    cif = request.form.get('cif')
    contacto = request.form.get('contacto')
    telefono = request.form.get('telefono')
    direccion = request.form.get('direccion')
    codigo_postal = request.form.get('codigo_postal')
    municipio = request.form.get('municipio')
    zona = request.form.get('zona')
    banco = request.form.get('banco')
    iban = request.form.get('iban')
    
    if empresa and email and password and rol:
        conn = get_db_connection()
        exist = conn.execute("SELECT * FROM usuarios WHERE email=?", (email,)).fetchone()
        if exist:
            conn.close()
            flash("El correo electrónico ya está registrado.", "danger")
            return redirect(url_for('admin'))
            
        password_hash = generate_password_hash(password)
        conn.execute('''
            INSERT INTO usuarios (
                nombre_empresa, email, password_hash, rol, cif, contacto, telefono, 
                direccion, codigo_postal, municipio, zona, banco, iban
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (empresa, email, password_hash, rol, cif, contacto, telefono,
              direccion, codigo_postal, municipio, zona, banco, iban))
        conn.commit()
        conn.close()
        flash("Nuevo usuario creado con éxito desde administración.", "success")
    else:
        flash("Datos obligatorios incompletos para crear el usuario.", "warning")
    return redirect(url_for('admin'))

@app.route('/admin/categoria/crear', methods=['POST'])
def admin_categoria_crear():
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    
    if nombre:
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
            conn.commit()
            flash("Categoría creada con éxito.", "success")
        except sqlite3.IntegrityError:
            flash("La categoría ya existe.", "danger")
        finally:
            conn.close()
    return redirect(url_for('admin'))

@app.route('/admin/categoria/eliminar/<int:categoria_id>', methods=['POST'])
def admin_categoria_eliminar(categoria_id):
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    conn = get_db_connection()
    conn.execute("DELETE FROM categorias WHERE id=?", (categoria_id,))
    conn.commit()
    conn.close()
    flash("Categoría eliminada con éxito.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/resena/<int:resena_id>/verificar', methods=['POST'])
def admin_resena_verificar(resena_id):
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    conn = get_db_connection()
    conn.execute("UPDATE resenas SET verificada=1 WHERE id=?", (resena_id,))
    conn.commit()
    conn.close()
    flash("Reseña verificada con éxito.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/resena/eliminar/<int:resena_id>', methods=['POST'])
def admin_resena_eliminar(resena_id):
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    conn = get_db_connection()
    conn.execute("DELETE FROM resenas WHERE id=?", (resena_id,))
    conn.commit()
    conn.close()
    flash("Reseña eliminada con éxito.", "success")
    return redirect(url_for('admin'))



@app.route('/admin/proveedor/crear', methods=['POST'])
def admin_proveedor_crear():
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    nombre = request.form.get('nombre')
    contacto = request.form.get('contacto')
    email = request.form.get('email')
    telefono = request.form.get('telefono')
    direccion = request.form.get('direccion')
    condiciones = request.form.get('condiciones')
    
    if nombre:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO proveedores (nombre, contacto, email, telefono, direccion, condiciones)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nombre, contacto, email, telefono, direccion, condiciones))
        conn.commit()
        conn.close()
        flash("Proveedor agregado con éxito.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/proveedor/eliminar/<int:prov_id>', methods=['POST'])
def admin_proveedor_eliminar(prov_id):
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido.", "danger")
        return redirect(url_for('cuenta'))
        
    conn = get_db_connection()
    conn.execute("UPDATE proveedores SET activo = CASE WHEN activo=1 THEN 0 ELSE 1 END WHERE id=?", (prov_id,))
    conn.commit()
    conn.close()
    flash("Estado del proveedor actualizado con éxito.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/reporte_clientes.pdf')
def admin_reporte_clientes():
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        return "No autorizado", 403
        
    conn = get_db_connection()
    clientes_registrados = conn.execute('''
        SELECT u.id, u.nombre_empresa, u.email, p.cif, p.contacto, p.telefono, p.banco, p.iban, p.municipio
        FROM usuarios u
        LEFT JOIN (
            SELECT usuario_id, cif, contacto, telefono, banco, iban, municipio, max(fecha) 
            FROM pedidos 
            GROUP BY usuario_id
        ) p ON u.id = p.usuario_id
        WHERE u.email != 'admin@vetesia.com'
        ORDER BY u.id ASC
    ''').fetchall()
    
    clientes_invitados = conn.execute('''
        SELECT NULL as id, empresa as nombre_empresa, email, cif, contacto, telefono, banco, iban, municipio
        FROM pedidos
        WHERE usuario_id IS NULL
        GROUP BY cif
    ''').fetchall()
    
    todos_clientes = list(clientes_registrados) + list(clientes_invitados)
    conn.close()
    
    pdf_buffer = generar_reporte_clientes_pdf(todos_clientes)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='reporte_clientes_vetesia.pdf'
    )

@app.route('/api/health')
def api_health():
    return {"status": "healthy"}, 200

@app.route('/api/productos')
def api_productos():
    conn = get_db_connection()
    productos_db = conn.execute('SELECT * FROM productos').fetchall()
    conn.close()
    
    productos = []
    for p in productos_db:
        productos.append({
            'id': p['id'],
            'slug': p['slug'],
            'nombre': p['nombre'],
            'categoria': p['categoria'],
            'precio': p['precio'],
            'descripcion': p['descripcion'],
            'imagen_url': p['imagen_url']
        })
    return {"productos": productos}, 200

@app.route('/favorito/<int:producto_id>', methods=['POST'])
def favorito(producto_id):

    if 'user_id' not in session:
        flash('Debes iniciar sesión para guardar favoritos.', 'warning')
        return redirect(url_for('cuenta'))

    conn = get_db_connection()

    existe = conn.execute(
        'SELECT * FROM favoritos WHERE usuario_id=? AND producto_id=?',
        (session['user_id'], producto_id)
    ).fetchone()

    if existe:
        conn.execute(
            'DELETE FROM favoritos WHERE usuario_id=? AND producto_id=?',
            (session['user_id'], producto_id)
        )
    else:
        conn.execute(
            'INSERT INTO favoritos (usuario_id, producto_id) VALUES (?, ?)',
            (session['user_id'], producto_id)
        )

    conn.commit()
    conn.close()

    return redirect(url_for('tienda'))

@app.route('/favoritos.html')
def favoritos():

    if 'user_id' not in session:
        flash('Debes iniciar sesión.', 'warning')
        return redirect(url_for('cuenta'))

    conn = get_db_connection()

    productos = conn.execute('''
        SELECT p.*
        FROM productos p
        JOIN favoritos f ON p.id = f.producto_id
        WHERE f.usuario_id = ?
    ''', (session['user_id'],)).fetchall()

    conn.close()

    return render_template(
        'favoritos.html',
        productos=productos
    )

if __name__ == '__main__':
    app.run(debug=True)
