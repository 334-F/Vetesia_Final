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

# Inyectar el número de items del carrito y estado de login en todas las plantillas
@app.context_processor
def inject_global_data():
    cart = session.get('cart', {})
    cart_count = sum(cart.values())
    
    logged_in = 'user_id' in session
    user_name = session.get('user_name', '')
    
    return dict(cart_count=cart_count, logged_in=logged_in, user_name=user_name)

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
    conn.close()
    return render_template('tienda.html', productos=productos)

@app.route('/servicios.html')
def servicios():
    return render_template('servicios.html')

@app.route('/informacion.html')
def informacion():
    return render_template('informacion.html')

# --- RUTAS DE PRODUCTO ---

@app.route('/veta5plus.html')
def producto_veta5plus():
    conn = get_db_connection()
    producto = conn.execute('SELECT * FROM productos WHERE slug = ?', ('veta5plus',)).fetchone()
    conn.close()
    if not producto:
        return "Producto no encontrado", 404
    especificaciones = json.loads(producto['especificaciones_json']) if producto['especificaciones_json'] else {}
    return render_template('veta5plus.html', producto=producto, especificaciones=especificaciones)

@app.route('/wato20.html')
def producto_wato20():
    conn = get_db_connection()
    producto = conn.execute('SELECT * FROM productos WHERE slug = ?', ('wato20',)).fetchone()
    conn.close()
    if not producto:
        return "Producto no encontrado", 404
    especificaciones = json.loads(producto['especificaciones_json']) if producto['especificaciones_json'] else {}
    return render_template('wato20.html', producto=producto, especificaciones=especificaciones)

@app.route('/circuito.html')
def producto_circuito():
    conn = get_db_connection()
    producto = conn.execute('SELECT * FROM productos WHERE slug = ?', ('circuito',)).fetchone()
    conn.close()
    if not producto:
        return "Producto no encontrado", 404
    especificaciones = json.loads(producto['especificaciones_json']) if producto['especificaciones_json'] else {}
    return render_template('circuito.html', producto=producto, especificaciones=especificaciones)

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
            'INSERT INTO usuarios (nombre_empresa, email, password_hash) VALUES (?, ?, ?)',
            (nombre_empresa, email, password_hash)
        )
        conn.commit()
        
        # Iniciar sesión automáticamente después de registrarse
        new_user_id = cursor.lastrowid
        session['user_id'] = new_user_id
        session['user_name'] = nombre_empresa
        session['user_email'] = email
        
        conn.close()
        flash('Cuenta creada con éxito.', 'success')
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
    return render_template('pago.html')

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
    direccion = request.form.get('cp') # El input de dirección tiene name="cp" en el original
    codigo_postal = request.form.get('cp') # El input de CP tiene name="cp" también en el original, pero usemos lo que venga
    
    # Para manejar los dos inputs con name="cp", podemos sacarlos por orden o por request.form.getlist('cp')
    cp_list = request.form.getlist('cp')
    direccion_val = cp_list[0] if len(cp_list) > 0 else ""
    codigo_postal_val = cp_list[1] if len(cp_list) > 1 else ""
    
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
        usuario_id, empresa, email, cif, contacto, telefono, zona_val, municipio, direccion_val, codigo_postal_val,
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
    
    pdf_buffer = generar_factura_pdf(pedido, items)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'factura_vetesia_{pedido_id}.pdf'
    )

@app.route('/admin.html')
def admin():
    if 'user_email' not in session or session['user_email'] != 'admin@vetesia.com':
        flash("Acceso restringido. Debes iniciar sesión como administrador.", "danger")
        return redirect(url_for('cuenta'))
        
    conn = get_db_connection()
    
    # Estadísticas básicas B2B
    total_clientes = conn.execute("SELECT count(*) FROM usuarios WHERE email != 'admin@vetesia.com'").fetchone()[0]
    total_pedidos = conn.execute("SELECT count(*) FROM pedidos").fetchone()[0]
    total_ventas = conn.execute("SELECT sum(total) FROM pedidos").fetchone()[0] or 0.0
    
    ventas_formateadas = f"{total_ventas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
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
        
    conn.close()
    
    stats = {
        'total_clientes': total_clientes + len(clientes_invitados),
        'total_pedidos': total_pedidos,
        'total_ventas': ventas_formateadas
    }
    
    return render_template('admin.html', stats=stats, clientes=todos_clientes, pedidos=pedidos)

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

if __name__ == '__main__':
    app.run(debug=True)
