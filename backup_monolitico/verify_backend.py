import unittest
import os
import sqlite3
import json
from app import app, get_db_connection

class VetesiaBackendTestCase(unittest.TestCase):

    def setUp(self):
        # Configurar la app para pruebas
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = app.test_client()
        
        # Asegurarse de que la base de datos de prueba está inicializada
        # Para las pruebas, usaremos la base de datos actual database.db
        # pero primero verificamos que tenga los datos.
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM productos")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertGreater(count, 0, "La base de datos debe tener productos insertados.")

    def test_pages_load(self):
        # 1. Verificar que la home carga correctamente
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Veta 5 Plus', response.data)
        
        # 2. Verificar que la tienda carga correctamente
        response = self.client.get('/tienda.html')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Wato 20', response.data)
        self.assertIn(b'Circuito de Anestesia', response.data)
        
        # 3. Verificar que los servicios cargan correctamente
        response = self.client.get('/servicios.html')
        self.assertEqual(response.status_code, 200)

    def test_user_flow(self):
        # 1. Registrar un usuario de prueba
        # Generar un email único para evitar colisiones
        import random
        test_email = f"empresa_{random.randint(1000, 9999)}@prueba.com"
        
        response = self.client.post('/registro.html', data={
            'empresa': 'Hospital Vet Prueba',
            'email': test_email,
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Panel de Control de Hospital Vet Prueba', response.data)
        self.assertIn(b'Hospital Vet Prueba', response.data)
        
        # 2. Probar añadir un producto al carrito
        # Primero obtenemos un producto ID de la base de datos
        conn = get_db_connection()
        prod = conn.execute("SELECT id, precio FROM productos WHERE slug = 'veta5plus'").fetchone()
        prod_id = prod['id']
        prod_precio = prod['precio']
        conn.close()
        
        # Añadir al carrito
        response = self.client.post('/cart/add', data={
            'product_id': prod_id,
            'cantidad': 2
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Veta 5 Plus', response.data)
        self.assertIn(b'2', response.data)  # Debería mostrar cantidad 2
        
        # 3. Proceder al pago y completar un pedido
        # Enviar pedido
        response = self.client.post('/submit_order', data={
            'empresa': 'Hospital Vet Prueba',
            'contacto': 'Dr. Juan Pérez',
            'cif': 'A1234567B',
            'email': test_email,
            'telef': '912345678',
            'country': 'PI',
            'ct': 'Madrid',
            'cp': ['Calle Gran Vía 12', '28013'], # En el form original cp representaba dirección y CP
            'titular_cuenta': 'Hospital Vet Prueba S.L.',
            'iban': 'ES1234567890123456789012',
            'banco': 'Banco de España'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('Pedido Recibido'.encode('utf-8'), response.data)
        self.assertIn('Dr. Juan'.encode('utf-8'), response.data)
        self.assertIn(b'ES1234567890123456789012', response.data)
        
        # Obtener el ID del pedido creado desde la BD
        conn = get_db_connection()
        pedido_db = conn.execute("SELECT id FROM pedidos ORDER BY id DESC LIMIT 1").fetchone()
        pedido_id = pedido_db['id']
        conn.close()
        
        # 4. Verificar que el pedido aparece en el historial del usuario logueado en la cuenta
        response = self.client.get('/cuenta.html')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Historial de Pedidos', response.data)
        self.assertIn(b'A1234567B', response.data)

        # 5. Verificar que se puede descargar la factura PDF
        response = self.client.get(f'/factura/{pedido_id}.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertTrue(response.data.startswith(b'%PDF'))

        # 6. Cerrar sesión del usuario de prueba
        self.client.get('/logout')

        # 7. Iniciar sesión como Administrador
        response = self.client.post('/cuenta.html', data={
            'empresa': 'Administrador',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 8. Acceder al panel de administración
        response = self.client.get('/admin.html')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Panel de Control de Administración'.encode('utf-8'), response.data)

        # 9. Descargar reporte de clientes consolidado en PDF
        response = self.client.get('/admin/reporte_clientes.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertTrue(response.data.startswith(b'%PDF'))

if __name__ == '__main__':
    unittest.main()
