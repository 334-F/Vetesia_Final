import urllib.request
import json
import sys

print("==================================================")
print("INICIANDO PRUEBA DE INTEGRACIÓN Y SERVIDORES B2B")
print("==================================================")

tests = [
    # Frontend Pages
    {"type": "frontend", "url": "http://localhost:8080/index.html", "expected_type": "text/html"},
    {"type": "frontend", "url": "http://localhost:8080/pages/catalogo.html", "expected_type": "text/html"},
    {"type": "frontend", "url": "http://localhost:8080/pages/servicios.html", "expected_type": "text/html"},
    {"type": "frontend", "url": "http://localhost:8080/pages/informacion.html", "expected_type": "text/html"},
    {"type": "frontend", "url": "http://localhost:8080/pages/producto.html", "expected_type": "text/html"},
    # Backend REST API Endpoints
    {"type": "backend", "url": "http://localhost:5001/api/health", "expected_type": "application/json"},
    {"type": "backend", "url": "http://localhost:5001/api/productos", "expected_type": "application/json"},
    {"type": "backend", "url": "http://localhost:5001/api/categorias", "expected_type": "application/json"},
    {"type": "backend", "url": "http://localhost:5001/api/pedidos/metodos-pago", "expected_type": "application/json"},
    {"type": "backend", "url": "http://localhost:5001/api/pedidos/zonas-envio", "expected_type": "application/json"},
]

all_passed = True

for test in tests:
    print(f"\nProbando [{test['type'].upper()}] - {test['url']} ...")
    try:
        req = urllib.request.Request(test['url'], method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
            content_type = response.headers.get('Content-Type', '')
            
            print(f"  -> Estado HTTP: {status}")
            print(f"  -> Content-Type: {content_type}")
            
            # Validar tipo de contenido esperado
            if test['expected_type'] not in content_type:
                print(f"  [ERROR] Tipo de contenido inesperado. Se esperaba: {test['expected_type']}")
                all_passed = False
                continue
                
            # Validar JSON si corresponde
            if test['type'] == 'backend':
                body = response.read().decode('utf-8')
                data = json.loads(body)
                print(f"  [ÉXITO] Respuesta JSON válida. Elementos/Claves obtenidos: {list(data.keys()) if isinstance(data, dict) else len(data)}")
            else:
                body = response.read().decode('utf-8')
                # Comprobar si contiene etiquetas HTML clave
                if "<html" in body.lower():
                    print("  [ÉXITO] Estructura HTML detectada.")
                else:
                    print("  [ERROR] El archivo no parece ser un documento HTML válido.")
                    all_passed = False
                    
    except Exception as e:
        print(f"  [ERROR] No se pudo conectar con el servidor: {e}")
        all_passed = False

print("\n==================================================")
if all_passed:
    print("¡TODAS LAS PRUEBAS COMPLETADAS CON ÉXITO!")
    print("Los servidores de Frontend (8080) y Backend (5001) funcionan correctamente.")
else:
    print("[FALLO] Algunas pruebas de integración han fallado.")
print("==================================================")
sys.exit(0 if all_passed else 1)
