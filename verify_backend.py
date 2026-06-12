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
            'confirm_password': 'password123',
            'cif': 'B12345678',
            'contacto': 'Dr. Juan Pérez',
            'telefono': '912345678',
            'direccion': 'Calle Gran Vía 12',
            'codigo_postal': '28013',
            'municipio': 'Madrid',
            'zona': 'PI',
            'banco': 'Banco de España',
            'iban': 'ES1234567890123456789012'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Panel de Control de Hospital Vet Prueba', response.data)
        self.assertIn(b'Hospital Vet Prueba', response.data)
        
        # 1b. Verificar la tienda y favoritos estando logueado (para evitar errores de tabla favoritos)
        response_tienda = self.client.get('/tienda.html')
        self.assertEqual(response_tienda.status_code, 200)
        self.assertIn(b'Wato 20', response_tienda.data)
        
        response_fav = self.client.get('/favoritos.html')
        self.assertEqual(response_fav.status_code, 200)
        
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
            'direccion': 'Calle Gran Vía 12',
            'codigo_postal': '28013',
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

        # 10. Descargar reporte financiero consolidado en PDF
        response = self.client.get('/admin/reporte_financiero.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')
        self.assertTrue(response.data.startswith(b'%PDF'))

        # 11. Probar la creación de una compra/gasto de proveedor
        conn = get_db_connection()
        prov = conn.execute("SELECT id FROM proveedores LIMIT 1").fetchone()
        prov_id = prov['id'] if prov else None
        conn.close()

        response = self.client.post('/admin/compra/crear', data={
            'proveedor_id': prov_id or '',
            'concepto': 'Compra de ecógrafo portátil para pruebas',
            'monto': '1500.50',
            'fecha': '2026-06-12'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Gasto de proveedor registrado con éxito.'.encode('utf-8'), response.data)

        # Buscar el ID de la compra recién creada
        conn = get_db_connection()
        compra_db = conn.execute("SELECT id FROM compras WHERE concepto = ? ORDER BY id DESC LIMIT 1", ('Compra de ecógrafo portátil para pruebas',)).fetchone()
        compra_id = compra_db['id']
        conn.close()

        # 12. Probar la eliminación del gasto de proveedor
        response = self.client.post(f'/admin/compra/eliminar/{compra_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Registro de gasto eliminado.'.encode('utf-8'), response.data)

        # 13. Crear un usuario Trabajador como Administrador
        worker_email = "trabajador_test@prueba.com"
        # Limpiar cualquier residuo de pruebas anteriores
        conn = get_db_connection()
        conn.execute("DELETE FROM usuarios WHERE email = ?", (worker_email,))
        conn.commit()
        conn.close()

        response = self.client.post('/admin/usuario/crear', data={
            'empresa': 'Trabajador Test S.L.',
            'email': worker_email,
            'password': 'workerpassword',
            'rol': 'trabajador'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Nuevo usuario creado con \u00e9xito desde administraci\u00f3n.'.encode('utf-8'), response.data)

        # Buscar el ID del trabajador creado
        conn = get_db_connection()
        worker_user = conn.execute("SELECT id FROM usuarios WHERE email = ?", (worker_email,)).fetchone()
        worker_id = worker_user['id']
        conn.close()

        # 14. Cerrar sesión de Admin e iniciar sesión como Trabajador
        self.client.get('/logout')
        response = self.client.post('/cuenta.html', data={
            'empresa': 'Trabajador Test S.L.',
            'password': 'workerpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 15. Acceder al panel de administración como Trabajador
        response = self.client.get('/admin.html')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Panel de Control de Administraci\u00f3n'.encode('utf-8'), response.data)
        self.assertIn(b'Inventario de Productos B2B', response.data)
        self.assertNotIn(b'Reporte Clientes PDF', response.data)

        # 16. Intentar descargar reportes como Trabajador (debe dar 403 o restringido)
        response = self.client.get('/admin/reporte_clientes.pdf')
        self.assertEqual(response.status_code, 403)

        response = self.client.get('/admin/reporte_financiero.pdf')
        self.assertEqual(response.status_code, 403)

        # 17. Como Trabajador, editar el stock de un producto
        conn = get_db_connection()
        prod = conn.execute("SELECT id, precio, stock, imagen_url FROM productos WHERE slug = 'veta5plus'").fetchone()
        prod_id = prod['id']
        old_precio = prod['precio']
        old_imagen = prod['imagen_url']
        conn.close()

        response = self.client.post('/admin/producto/editar', data={
            'id': prod_id,
            'stock': '99',
            'precio': '9999.99',
            'imagen_url': 'hack.jpg'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Stock de producto actualizado con \u00e9xito por Trabajador.'.encode('utf-8'), response.data)

        # Verificar en base de datos que el stock cambió pero no el precio o la imagen
        conn = get_db_connection()
        prod_updated = conn.execute("SELECT precio, stock, imagen_url FROM productos WHERE id = ?", (prod_id,)).fetchone()
        self.assertEqual(prod_updated['stock'], 99)
        self.assertEqual(prod_updated['precio'], old_precio)
        self.assertEqual(prod_updated['imagen_url'], old_imagen)
        conn.close()

        # 18. Cerrar sesión de Trabajador e iniciar sesión como Cliente para dejar reseña
        self.client.get('/logout')
        response = self.client.post('/cuenta.html', data={
            'empresa': 'Hospital Vet Prueba',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Crear una reseña nueva (debe ser verificada = 0 al inicio)
        response = self.client.post(f'/producto/{prod_id}/resena/crear', data={
            'valoracion': '5',
            'texto': 'Excelente equipo, muy preciso.'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Tu valoraci\u00f3n ha sido enviada con \u00e9xito.'.encode('utf-8'), response.data)

        # Buscar la reseña recién creada
        conn = get_db_connection()
        resena_db = conn.execute("SELECT id, verificada FROM resenas WHERE producto_id = ? ORDER BY id DESC LIMIT 1", (prod_id,)).fetchone()
        resena_id = resena_db['id']
        self.assertEqual(resena_db['verificada'], 0)
        conn.close()

        # 19. Iniciar sesión como Administrador para verificar o eliminar la reseña
        self.client.get('/logout')
        self.client.post('/cuenta.html', data={
            'empresa': 'Administrador',
            'password': 'admin123'
        }, follow_redirects=True)

        # Verificar la reseña
        response = self.client.post(f'/admin/resena/{resena_id}/verificar', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        conn = get_db_connection()
        resena_db = conn.execute("SELECT verificada FROM resenas WHERE id = ?", (resena_id,)).fetchone()
        self.assertEqual(resena_db['verificada'], 1)
        conn.close()

        # Eliminar la reseña de prueba
        response = self.client.post(f'/admin/resena/eliminar/{resena_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 20. Borrar permanentemente al usuario Trabajador de prueba
        response = self.client.post(f'/admin/usuario/{worker_id}/eliminar', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Usuario eliminado de forma permanente con \u00e9xito.'.encode('utf-8'), response.data)

        conn = get_db_connection()
        user_exists = conn.execute("SELECT count(*) FROM usuarios WHERE id = ?", (worker_id,)).fetchone()[0]
        self.assertEqual(user_exists, 0)
        conn.close()

if __name__ == '__main__':
    unittest.main()
