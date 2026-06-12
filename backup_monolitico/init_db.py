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
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Tabla de Productos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            precio REAL NOT NULL,
            descripcion TEXT NOT NULL,
            especificaciones_json TEXT,
            imagen_url TEXT NOT NULL
        )
    ''')

    # 3. Tabla de Pedidos
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

    # 4. Tabla de Detalles del Pedido
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
            "imagen_url": "Veta5plus.webp"
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
            "imagen_url": "WATO20.png"
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
            "imagen_url": "Circuito de anestesia.jpg"
        }
    ]

    for p in productos_iniciales:
        cursor.execute('''
            INSERT OR REPLACE INTO productos (slug, nombre, categoria, precio, descripcion, especificaciones_json, imagen_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (p["slug"], p["nombre"], p["categoria"], p["precio"], p["descripcion"], p["especificaciones_json"], p["imagen_url"]))

    # 5. Insertar el usuario administrador por defecto si no existe
    from werkzeug.security import generate_password_hash
    admin_email = 'admin@vetesia.com'
    admin_password_hash = generate_password_hash('admin123')
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (nombre_empresa, email, password_hash)
        VALUES (?, ?, ?)
    ''', ('Administrador', admin_email, admin_password_hash))

    # 6. Insertar el usuario invitado por defecto si no existe
    guest_email = 'invitado@vetesia.com'
    guest_password_hash = generate_password_hash('invitado123')
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (nombre_empresa, email, password_hash)
        VALUES (?, ?, ?)
    ''', ('Invitado Test', guest_email, guest_password_hash))

    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente con los productos de VetÉsia, cuenta admin y cuenta de invitado.")

if __name__ == '__main__':
    init_db()
