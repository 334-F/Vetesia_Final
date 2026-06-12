import sqlite3
import json

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 1. Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_empresa TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            rol TEXT DEFAULT 'cliente',
            activo INTEGER DEFAULT 1,
            cif TEXT,
            contacto TEXT,
            telefono TEXT,
            direccion TEXT,
            codigo_postal TEXT,
            municipio TEXT,
            zona TEXT,
            banco TEXT,
            iban TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Tabla de Categorías
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT
        )
    ''')

    # 3. Tabla de Productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            descripcion TEXT NOT NULL,
            especificaciones_json TEXT,
            imagen_url TEXT NOT NULL,
            stock INTEGER DEFAULT 20,
            stock_minimo INTEGER DEFAULT 5,
            activo INTEGER DEFAULT 1
        )
    ''')

    # 4. Tabla de Pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            empresa TEXT NOT NULL,
            email TEXT NOT NULL,
            cif TEXT NOT NULL,
            contacto TEXT NOT NULL,
            telefono TEXT NOT NULL,
            zona TEXT NOT NULL,
            municipio TEXT NOT NULL,
            direccion TEXT NOT NULL,
            codigo_postal TEXT NOT NULL,
            titular_cuenta TEXT NOT NULL,
            iban TEXT NOT NULL,
            banco TEXT NOT NULL,
            subtotal REAL NOT NULL,
            iva REAL NOT NULL,
            total REAL NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    # 5. Tabla de Detalles del Pedido
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detalles_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')

    # 6. Tabla de Reseñas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resenas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            producto_id INTEGER NOT NULL,
            valoracion INTEGER NOT NULL,
            texto TEXT,
            verificada INTEGER DEFAULT 0,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')

    # 6b. Tabla de Favoritos (mis favoritos de los clientes)
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

    # 7. Tabla de Promociones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS promociones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo TEXT NOT NULL, -- 'porcentaje' o 'fijo'
            valor REAL NOT NULL,
            fecha_inicio TIMESTAMP NOT NULL,
            fecha_fin TIMESTAMP NOT NULL,
            categoria_id INTEGER,
            activa INTEGER DEFAULT 1,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        )
    ''')

    # 8. Tabla de Proveedores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            contacto TEXT,
            email TEXT,
            telefono TEXT,
            direccion TEXT,
            condiciones TEXT,
            activo INTEGER DEFAULT 1
        )
    ''')

    # 9. Tabla de Compras (Gastos de Proveedores)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER,
            concepto TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
        )
    ''')

    # Insertar categorías iniciales
    categorias = [
        ("Máquina de Anestesia", "Estaciones de trabajo y respiradores"),
        ("Monitoreo Completo", "Monitores de signos vitales multiparamétricos"),
        ("Alta Calidad", "Accesorios y consumibles de alta calidad"),
        ("Accesorios", "Componentes complementarios"),
        ("Uniformidad veterinaria", "Batas y uniformidad")
    ]
    for cat in categorias:
        cursor.execute("INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES (?, ?)", cat)

    # Insertar o actualizar los productos iniciales
    productos_iniciales = [
        {
            "slug": "veta5plus",
            "nombre": "Veta 5 Plus",
            "categoria": "Máquina de Anestesia",
            "precio": 2850.00,
            "descripcion": "El modelo Veta 5 Plus es la estación de trabajo de anestesia digital más avanzada de su gama. Diseñada específicamente para garantizar la máxima seguridad en intervenciones veterinarias, combinando eficacia clínica con un diseño altamente intuitivo para el especialista.",
            "especificaciones_json": json.dumps({
                "Pantalla": "8 Pulgadas TFT capacitiva, pantalla táctil.",
                "Modos de ventilación": "VCV, PCV, SIMV, PSV, Manual.",
                "Volumen Tidal (Vt)": "5 mL a 1500 mL, adecuado para diferentes especies.",
                "Batería interna": "Hasta 4 horas de respaldo."
            }),
            "imagen_url": "Veta5plus.webp",
            "stock": 12,
            "stock_minimo": 3
        },
        {
            "slug": "wato20",
            "nombre": "Wato 20",
            "categoria": "Monitoreo Completo",
            "precio": 1550.00,
            "descripcion": "El WATO 20 es un monitor de signos vitales multiparamétrico creado bajo algoritmos especiales para animales pequeños. Proporciona datos precisos, continuos y fiables en cualquier entorno clínico y quirúrgico para asegurar la recuperación del paciente.",
            "especificaciones_json": json.dumps({
                "Parámetros": "SpO2, PR, NIBP, ECG, RESP, TEMP opcional (Capnografía EtCO2).",
                "Pantalla": "LCD a color de última generación (sin reflejos).",
                "Batería interna": "Litio recargable de larga duración (> 6h continuas).",
                "Memoria": "Almacenamiento de hasta 1000 horas de tendencias y alarmas."
            }),
            "imagen_url": "WATO20.png",
            "stock": 8,
            "stock_minimo": 3
        },
        {
            "slug": "circuito",
            "nombre": "Circuito de Anestesia",
            "categoria": "Alta Calidad",
            "precio": 120.00,
            "descripcion": "Circuito de respiración resistente a la presión fabricado con los mejores polímeros de grado médico. Este circuito garantiza un flujo constante sin oclusiones ni dobladuras accidentales para mantener seguros a los pacientes en todo momento.",
            "especificaciones_json": json.dumps({
                "Material": "Polipropileno / Silicona médica (variable según lote de seguridad).",
                "Longitud Estándar": "150 cm (Adaptable / Extensible).",
                "Diámetro de Conexión": "Conector de 22mm / 15mm ISO estándar.",
                "Esterilización": "Autoclavable o descartable (consultar ficha CE adjunta al envío)."
            }),
            "imagen_url": "Circuito de anestesia.jpg",
            "stock": 4,
            "stock_minimo": 10
        }
    ]

    for p in productos_iniciales:
        cursor.execute('''
            INSERT OR REPLACE INTO productos (slug, nombre, categoria, precio, descripcion, especificaciones_json, imagen_url, stock, stock_minimo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (p["slug"], p["nombre"], p["categoria"], p["precio"], p["descripcion"], p["especificaciones_json"], p["imagen_url"], p["stock"], p["stock_minimo"]))

    # Insertar usuarios
    from werkzeug.security import generate_password_hash
    admin_email = 'admin@vetesia.com'
    admin_password_hash = generate_password_hash('admin123')
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (nombre_empresa, email, password_hash, rol)
        VALUES (?, ?, ?, ?)
    ''', ('Administrador', admin_email, admin_password_hash, 'admin'))

    guest_email = 'invitado@vetesia.com'
    guest_password_hash = generate_password_hash('invitado123')
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (nombre_empresa, email, password_hash, rol)
        VALUES (?, ?, ?, ?)
    ''', ('Invitado Test', guest_email, guest_password_hash, 'cliente'))

    # Insertar proveedores
    proveedores = [
        ("Suministros Vet S.L.", "Juan Pérez", "jperez@suministrosvet.com", "910000001", "Madrid", "Pago a 30 días"),
        ("TextilPro Uniformes", "Ana Gómez", "agomez@textilpro.com", "910000002", "Barcelona", "Pago a 60 días")
    ]
    for prov in proveedores:
        cursor.execute('''
            INSERT OR IGNORE INTO proveedores (nombre, contacto, email, telefono, direccion, condiciones)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', prov)

    # Insertar pedidos de prueba (Ventas)
    cursor.execute('SELECT count(*) FROM pedidos')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO pedidos (id, usuario_id, empresa, email, cif, contacto, telefono, zona, municipio, direccion, codigo_postal, titular_cuenta, iban, banco, subtotal, iva, total, estado, fecha)
            VALUES (1, 2, 'Clínica Veterinaria María', 'maria@example.com', 'B12345678', 'María García', '600000002', 'Península', 'Madrid', 'Calle Mayor 1', '28001', 'María García', 'ES12345678901234567890', 'Banco de Prueba', 3090.00, 648.90, 3738.90, 'entregado', '2026-06-01 10:00:00')
        ''')
        cursor.execute('INSERT OR IGNORE INTO detalles_pedido (pedido_id, producto_id, cantidad, precio_unitario) VALUES (1, 1, 1, 2850.00)')
        cursor.execute('INSERT OR IGNORE INTO detalles_pedido (pedido_id, producto_id, cantidad, precio_unitario) VALUES (1, 3, 2, 120.00)')

        cursor.execute('''
            INSERT INTO pedidos (id, usuario_id, empresa, email, cif, contacto, telefono, zona, municipio, direccion, codigo_postal, titular_cuenta, iban, banco, subtotal, iva, total, estado, fecha)
            VALUES (2, 3, 'Clínica Carlos Ruiz', 'carlos@clinica.com', 'A87654321', 'Carlos Ruiz', '600000003', 'Península', 'Valencia', 'Av. Veterinaria 22', '46001', 'Carlos Ruiz', 'ES09876543210987654321', 'Banco de Prueba', 1670.00, 350.70, 2020.70, 'pagado', '2026-06-05 14:30:00')
        ''')
        cursor.execute('INSERT OR IGNORE INTO detalles_pedido (pedido_id, producto_id, cantidad, precio_unitario) VALUES (2, 2, 1, 1550.00)')
        cursor.execute('INSERT OR IGNORE INTO detalles_pedido (pedido_id, producto_id, cantidad, precio_unitario) VALUES (2, 3, 1, 120.00)')

    # Insertar compras de prueba (Gastos de Proveedores)
    cursor.execute('SELECT count(*) FROM compras')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO compras (proveedor_id, concepto, monto, fecha)
            VALUES (1, 'Compra de 3 Estaciones de Anestesia Veta 5 Plus', 4500.00, '2026-05-15 09:00:00')
        ''')
        cursor.execute('''
            INSERT INTO compras (proveedor_id, concepto, monto, fecha)
            VALUES (1, 'Adquisición de Consumibles y Circuitos', 1200.00, '2026-05-20 11:30:00')
        ''')
        cursor.execute('''
            INSERT INTO compras (proveedor_id, concepto, monto, fecha)
            VALUES (2, 'Uniformes personalizados para equipo técnico', 350.00, '2026-05-25 15:45:00')
        ''')

    # Insertar algunas reseñas de prueba
    cursor.execute('''
        INSERT OR IGNORE INTO resenas (usuario_id, producto_id, valoracion, texto, verificada)
        VALUES (2, 1, 5, 'Una estación de anestesia espectacular, muy precisa.', 0)
    ''')
    cursor.execute('''
        INSERT OR IGNORE INTO resenas (usuario_id, producto_id, valoracion, texto, verificada)
        VALUES (2, 2, 4, 'El monitor es excelente, pero la batería dura un poco menos de lo esperado.', 0)
    ''')

    # Insertar algunas promociones de prueba
    from datetime import datetime, timedelta
    ahora = datetime.now()
    inicio = ahora - timedelta(days=5)
    fin = ahora + timedelta(days=30)
    cursor.execute('''
        INSERT OR IGNORE INTO promociones (nombre, tipo, valor, fecha_inicio, fecha_fin, categoria_id, activa)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ("Descuento Especial de Lanzamiento", "porcentaje", 10.0, inicio.strftime("%Y-%m-%d %H:%M:%S"), fin.strftime("%Y-%m-%d %H:%M:%S"), 1, 1))

    conn.commit()
    conn.close()
    print("Base de datos inicializada con esquema extendido completo y compras.")

if __name__ == '__main__':
    init_db()
