"""
init_db.py
Inicializa la BBDD desde cero usando SQLAlchemy.
Compatible con SQLite y MySQL.
"""
import sys
import os
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import (
    TipoCliente, MetodoPago, ZonaEnvio, TipoServicio, Categoria,
    Usuario, DireccionEnvio, Producto, PrecioEscalado, Promocion,
    Proveedor, ProductoProveedor, Resena, Pedido, LineaPedido
)

app = create_app("dev")
with app.app_context():
    print("Creando tablas...")
    db.drop_all()
    db.create_all()

    print("Insertando datos de prueba...")

    db.session.add_all([
        TipoCliente(id=1, nombre="Particular", descripcion="Duenyo de mascota", descuento=0),
        TipoCliente(id=2, nombre="Profesional", descripcion="Clinica veterinaria", descuento=10),
    ])

    db.session.add_all([
        MetodoPago(id=1, nombre="Tarjeta", descripcion="Pago con tarjeta", requiere_pasarela=True),
        MetodoPago(id=2, nombre="Transferencia bancaria", descripcion="Pago manual", requiere_pasarela=False),
        MetodoPago(id=3, nombre="Contrarreembolso", descripcion="Pago en entrega", requiere_pasarela=False),
        MetodoPago(id=4, nombre="Bizum", descripcion="Pago Bizum", requiere_pasarela=True),
    ])

    db.session.add_all([
        ZonaEnvio(id=1, nombre="Peninsula", coste_envio=4.95, plazo_dias=3),
        ZonaEnvio(id=2, nombre="Baleares", coste_envio=9.95, plazo_dias=5),
        ZonaEnvio(id=3, nombre="Canarias", coste_envio=14.95, plazo_dias=7),
        ZonaEnvio(id=4, nombre="Ceuta y Melilla", coste_envio=14.95, plazo_dias=7),
    ])

    db.session.add_all([
        TipoServicio(id=1, nombre="Estandar", descripcion="DTG basico", precio_extra=0, dtg=True),
        TipoServicio(id=2, nombre="Premium DTG", descripcion="DTG con revision", precio_extra=4.95, dtg=True, revision_manual=True, etiquetado=True),
        TipoServicio(id=3, nombre="Premium Bordado", descripcion="Bordado prioritario", precio_extra=9.95, bordado=True, revision_manual=True, etiquetado=True, produccion_prioritaria=True),
    ])

    db.session.add_all([
        Categoria(id=1, nombre="Alimentación", descripcion="Comida para mascotas"),
        Categoria(id=2, nombre="Higiene y cuidado", descripcion="Champús y cepillos"),
        Categoria(id=3, nombre="Salud y antiparasitarios", descripcion="Pipetas y suplementos"),
        Categoria(id=4, nombre="Accesorios", descripcion="Correas, transportines"),
        Categoria(id=5, nombre="Uniformidad veterinaria", descripcion="Batas y uniformidad"),
        Categoria(id=6, nombre="Máquina de Anestesia", descripcion="Estaciones de trabajo y respiradores"),
        Categoria(id=7, nombre="Monitoreo Completo", descripcion="Monitores de signos vitales multiparamétricos"),
        Categoria(id=8, nombre="Alta Calidad", descripcion="Accesorios y consumibles de alta calidad"),
    ])

    db.session.flush()

    admin = Usuario(tipo_cliente_id=1, nombre="Admin", apellidos="Sistema",
                    email="admin@vetesia.com", telefono="600000001",
                    direccion="Oficinas VetEsia, Madrid", rol="admin")
    admin.set_password("admin123")

    maria = Usuario(tipo_cliente_id=1, nombre="Maria", apellidos="Garcia Lopez",
                    email="maria@example.com", telefono="600000002",
                    direccion="Calle Mayor 1, Madrid", rol="cliente")
    maria.set_password("cliente123")

    carlos = Usuario(tipo_cliente_id=2, nombre="Carlos", apellidos="Ruiz Perez",
                     email="carlos@clinica.com", telefono="600000003",
                     direccion="Av. Veterinaria 22, Valencia", rol="cliente")
    carlos.set_password("cliente123")

    db.session.add_all([admin, maria, carlos])
    db.session.flush()

    dir_maria = DireccionEnvio(usuario_id=maria.id, alias="Casa", destinatario="Maria Garcia",
                   calle="Calle Mayor", numero="1", piso="3B",
                   codigo_postal="28001", municipio="Madrid", provincia="Madrid",
                   telefono_contacto="600000002", predeterminada=True)
    dir_carlos = DireccionEnvio(usuario_id=carlos.id, alias="Clinica", destinatario="Clinica Vet",
                   calle="Av. Veterinaria", numero="22",
                   codigo_postal="46001", municipio="Valencia", provincia="Valencia",
                   telefono_contacto="600000003", predeterminada=True)
    db.session.add_all([dir_maria, dir_carlos])

    productos = [
        Producto(categoria_id=1, nombre="Royal Canin Mini Adult 8kg",
                 descripcion="Alimentacion seca para perros pequenos",
                 tipo="estandar", precio_base=49.95, stock=50, stock_minimo=10,
                 imagen_url="/img/royal_canin_mini.jpg"),
        Producto(categoria_id=1, nombre="Hill's Science Diet Cat 3kg",
                 descripcion="Alimentacion premium para gatos adultos",
                 tipo="estandar", precio_base=29.95, stock=40, stock_minimo=10,
                 imagen_url="/img/hills_cat.jpg"),
        Producto(categoria_id=2, nombre="Champu Pelo Largo 500ml",
                 descripcion="Champu especial pelo largo",
                 tipo="estandar", precio_base=12.50, stock=80, stock_minimo=15,
                 imagen_url="/img/champu_largo.jpg"),
        Producto(categoria_id=3, nombre="Pipetas antipulgas pack 3 uds",
                 descripcion="Pipetas antiparasitarias",
                 tipo="estandar", precio_base=24.95, stock=100, stock_minimo=20,
                 imagen_url="/img/pipetas.jpg"),
        Producto(categoria_id=4, nombre="Correa retractil 5m",
                 descripcion="Correa retractil para perros",
                 tipo="estandar", precio_base=18.95, stock=30, stock_minimo=5,
                 imagen_url="/img/correa.jpg"),
        Producto(categoria_id=5, nombre="Bata veterinaria manga corta",
                 descripcion="Bata tecnica personalizable",
                 tipo="personalizable", precio_base=24.95, stock=25, stock_minimo=5,
                 imagen_url="/img/bata_corta.jpg"),
        Producto(categoria_id=5, nombre="Sudadera con capucha veterinaria",
                 descripcion="Sudadera tecnica con bolsillo",
                 tipo="personalizable", precio_base=34.95, stock=20, stock_minimo=5,
                 imagen_url="/img/sudadera.jpg"),
        Producto(categoria_id=5, nombre="Camiseta polo veterinaria",
                 descripcion="Polo tecnico transpirable",
                 tipo="personalizable", precio_base=19.95, stock=30, stock_minimo=5,
                 imagen_url="/img/polo.jpg"),
        Producto(categoria_id=6, nombre="Veta 5 Plus", slug="veta5plus",
                 descripcion="El modelo Veta 5 Plus es la estación de trabajo de anestesia digital más avanzada de su gama. Diseñada específicamente para garantizar la máxima seguridad en intervenciones veterinarias, combinando eficacia clínica con un diseño altamente intuitivo para el especialista.",
                 tipo="estandar", precio_base=2850.00, stock=10, stock_minimo=2,
                 imagen_url="/img/Veta5plus.webp",
                 especificaciones_json=json.dumps({
                     "Pantalla": "8 Pulgadas TFT capacitiva, pantalla táctil.",
                     "Modos de ventilación": "VCV, PCV, SIMV, PSV, Manual.",
                     "Volumen Tidal (Vt)": "5 mL a 1500 mL, adecuado para diferentes especies.",
                     "Batería interna": "Hasta 4 horas de respaldo."
                 })),
        Producto(categoria_id=7, nombre="Wato 20", slug="wato20",
                 descripcion="El WATO 20 es un monitor de signos vitales multiparamétrico creado bajo algoritmos especiales para animales pequeños. Proporciona datos precisos, continuos y fiables en cualquier entorno clínico y quirúrgico para asegurar la recuperación del paciente.",
                 tipo="estandar", precio_base=1550.00, stock=15, stock_minimo=3,
                 imagen_url="/img/WATO20.png",
                 especificaciones_json=json.dumps({
                     "Parámetros": "SpO2, PR, NIBP, ECG, RESP, TEMP opcional (Capnografía EtCO2).",
                     "Pantalla": "LCD a color de última generación (sin reflejos).",
                     "Batería interna": "Litio recargable de larga duración (> 6h continuas).",
                     "Memoria": "Almacenamiento de hasta 1000 horas de tendencias y alarmas."
                 })),
        Producto(categoria_id=8, nombre="Circuito de Anestesia", slug="circuito",
                 descripcion="Circuito de respiración resistente a la presión fabricado con los mejores polímeros de grado médico. Este circuito garantiza un flujo constante sin oclusiones ni dobladuras accidentales para mantener seguros a los pacientes en todo momento.",
                 tipo="estandar", precio_base=120.00, stock=50, stock_minimo=5,
                 imagen_url="/img/Circuito de anestesia.jpg",
                 especificaciones_json=json.dumps({
                     "Material": "Polipropileno / Silicona médica (variable según lote de seguridad).",
                     "Longitud Estándar": "150 cm (Adaptable / Extensible).",
                     "Diámetro de Conexión": "Conector de 22mm / 15mm ISO estándar.",
                     "Esterilización": "Autoclavable o descartable (consultar ficha CE adjunta al envío)."
                 })),
    ]
    db.session.add_all(productos)
    db.session.flush()

    db.session.add_all([
        PrecioEscalado(producto_id=productos[3].id, cantidad_min=3, cantidad_max=5, precio_unitario=22.95),
        PrecioEscalado(producto_id=productos[3].id, cantidad_min=6, cantidad_max=9, precio_unitario=20.95),
        PrecioEscalado(producto_id=productos[3].id, cantidad_min=10, cantidad_max=None, precio_unitario=18.95),
    ])

    now = datetime.utcnow()
    db.session.add_all([
        Promocion(nombre="Black Friday Alimentacion", tipo="porcentaje", valor=20,
                  fecha_inicio=now - timedelta(days=30), fecha_fin=now + timedelta(days=365),
                  categoria_id=1, activa=True),
        Promocion(nombre="Rebajas uniformidad", tipo="porcentaje", valor=15,
                  fecha_inicio=now - timedelta(days=30), fecha_fin=now + timedelta(days=365),
                  categoria_id=5, activa=True),
    ])

    prov1 = Proveedor(nombre="Suministros Vet S.L.", persona_contacto="Juan Perez",
                     email="jperez@suministrosvet.com", telefono="910000001",
                     direccion="Madrid", condiciones="Pago a 30 dias")
    prov2 = Proveedor(nombre="TextilPro Uniformes", persona_contacto="Ana Gomez",
                     email="agomez@textilpro.com", telefono="910000002",
                     direccion="Barcelona", condiciones="Pago a 60 dias")
    db.session.add_all([prov1, prov2])
    db.session.flush()

    for i in range(5):
        db.session.add(ProductoProveedor(proveedor_id=prov1.id, producto_id=productos[i].id,
                                          precio_compra=float(productos[i].precio_base) * 0.6,
                                          plazo_entrega_dias=5, es_principal=True))
    for i in range(5, 8):
        db.session.add(ProductoProveedor(proveedor_id=prov2.id, producto_id=productos[i].id,
                                          precio_compra=float(productos[i].precio_base) * 0.6,
                                          plazo_entrega_dias=10, es_principal=True))
    for i in range(8, 11):
        db.session.add(ProductoProveedor(proveedor_id=prov1.id, producto_id=productos[i].id,
                                          precio_compra=float(productos[i].precio_base) * 0.6,
                                          plazo_entrega_dias=7, es_principal=True))

    # --- Pedidos de ejemplo (entregados) para habilitar las reseñas ---
    # La regla de negocio exige haber comprado el producto antes de reseñarlo.
    # Sembramos un pedido entregado para Maria y otro para Carlos.
    pedido_maria = Pedido(usuario_id=maria.id, direccion_envio_id=dir_maria.id,
                          metodo_pago_id=1, zona_envio_id=1, estado="entregado",
                          coste_envio=4.95, descuento=0)
    pedido_maria.lineas = [
        LineaPedido(producto_id=productos[1].id, cantidad=1,
                    precio_unitario=float(productos[1].precio_base),
                    subtotal=float(productos[1].precio_base)),
        LineaPedido(producto_id=productos[2].id, cantidad=2,
                    precio_unitario=float(productos[2].precio_base),
                    subtotal=float(productos[2].precio_base) * 2),
    ]
    pedido_maria.calcular_total()

    pedido_carlos = Pedido(usuario_id=carlos.id, direccion_envio_id=dir_carlos.id,
                           metodo_pago_id=1, zona_envio_id=1, estado="entregado",
                           coste_envio=4.95, descuento=0)
    pedido_carlos.lineas = [
        LineaPedido(producto_id=productos[1].id, cantidad=1,
                    precio_unitario=float(productos[1].precio_base),
                    subtotal=float(productos[1].precio_base)),
        LineaPedido(producto_id=productos[3].id, cantidad=1,
                    precio_unitario=float(productos[3].precio_base),
                    subtotal=float(productos[3].precio_base)),
    ]
    pedido_carlos.calcular_total()

    db.session.add_all([pedido_maria, pedido_carlos])

    db.session.add(Resena(usuario_id=maria.id, producto_id=productos[0].id,
                          valoracion=5, texto="A mi perro le encanta esta comida.",
                          verificada=True))

    db.session.commit()
    print("Listo. BBDD inicializada con datos de prueba.")
    print("")
    print("Usuarios:")
    print("  admin@vetesia.com / admin123")
    print("  maria@example.com / cliente123")
    print("  carlos@clinica.com / cliente123")