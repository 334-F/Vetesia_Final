"""
Rutas de proveedores y pedidos a proveedor (gestión de reposición).

Todos estos endpoints son exclusivos del admin.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models import (
    Proveedor, ProductoProveedor, PedidoProveedor,
    LineaPedidoProveedor, Producto
)
from ..utils.decorators import admin_required

proveedores_bp = Blueprint("proveedores", __name__)


# --- Proveedores ---

@proveedores_bp.route("", methods=["GET"])
@admin_required
def listar_proveedores():
    proveedores = Proveedor.query.filter_by(activo=True).all()
    return jsonify([p.to_dict() for p in proveedores])


@proveedores_bp.route("/<int:prov_id>", methods=["GET"])
@admin_required
def get_proveedor(prov_id):
    prov = Proveedor.query.get(prov_id)
    if not prov:
        return jsonify({"error": "Proveedor no encontrado"}), 404
    return jsonify({
        **prov.to_dict(),
        "productos": [pp.to_dict() for pp in prov.productos]
    })


@proveedores_bp.route("", methods=["POST"])
@admin_required
def crear_proveedor():
    datos = request.get_json() or {}
    if not datos.get("nombre"):
        return jsonify({"error": "El nombre es obligatorio"}), 400
    prov = Proveedor(**{
        k: v for k, v in datos.items()
        if k in ("nombre", "persona_contacto", "email", "telefono", "direccion", "condiciones")
    })
    db.session.add(prov)
    db.session.commit()
    return jsonify(prov.to_dict()), 201


@proveedores_bp.route("/<int:prov_id>", methods=["PATCH"])
@admin_required
def actualizar_proveedor(prov_id):
    prov = Proveedor.query.get(prov_id)
    if not prov:
        return jsonify({"error": "Proveedor no encontrado"}), 404
    datos = request.get_json() or {}
    for campo in ("nombre", "persona_contacto", "email", "telefono",
                  "direccion", "condiciones", "activo"):
        if campo in datos:
            setattr(prov, campo, datos[campo])
    db.session.commit()
    return jsonify(prov.to_dict())


@proveedores_bp.route("/<int:prov_id>", methods=["DELETE"])
@admin_required
def baja_proveedor(prov_id):
    prov = Proveedor.query.get(prov_id)
    if not prov:
        return jsonify({"error": "Proveedor no encontrado"}), 404
    prov.activo = False
    db.session.commit()
    return jsonify({"mensaje": "Proveedor desactivado"})


# --- Asociación producto-proveedor ---

@proveedores_bp.route("/<int:prov_id>/productos", methods=["POST"])
@admin_required
def asociar_producto(prov_id):
    """Asocia un producto a un proveedor con su precio de compra."""
    prov = Proveedor.query.get(prov_id)
    if not prov:
        return jsonify({"error": "Proveedor no encontrado"}), 404
    datos = request.get_json() or {}
    producto = Producto.query.get(datos.get("producto_id"))
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404

    pp = ProductoProveedor(
        proveedor_id=prov.id,
        producto_id=producto.id,
        precio_compra=datos["precio_compra"],
        plazo_entrega_dias=datos.get("plazo_entrega_dias"),
        es_principal=datos.get("es_principal", False),
    )
    db.session.add(pp)
    db.session.commit()
    return jsonify(pp.to_dict()), 201


# --- Pedidos a proveedor ---

@proveedores_bp.route("/pedidos", methods=["GET"])
@admin_required
def listar_pedidos_proveedor():
    estado = request.args.get("estado")
    query = PedidoProveedor.query
    if estado:
        query = query.filter_by(estado=estado)
    pedidos = query.order_by(PedidoProveedor.fecha.desc()).all()
    return jsonify([p.to_dict(incluir_lineas=False) for p in pedidos])


@proveedores_bp.route("/pedidos", methods=["POST"])
@admin_required
def crear_pedido_proveedor():
    """Crea un pedido de reposición a un proveedor."""
    admin_id = int(get_jwt_identity())
    datos = request.get_json() or {}

    prov = Proveedor.query.get(datos.get("proveedor_id"))
    if not prov:
        return jsonify({"error": "Proveedor no encontrado"}), 400

    lineas = datos.get("lineas") or []
    if not lineas:
        return jsonify({"error": "El pedido debe tener al menos una línea"}), 400

    pedido = PedidoProveedor(
        proveedor_id=prov.id,
        admin_id=admin_id,
        notas=datos.get("notas"),
    )
    db.session.add(pedido)
    db.session.flush()

    for linea in lineas:
        prod = Producto.query.get(linea.get("producto_id"))
        if not prod:
            db.session.rollback()
            return jsonify({"error": f"Producto {linea.get('producto_id')} no encontrado"}), 400
        lp = LineaPedidoProveedor(
            pedido_proveedor_id=pedido.id,
            producto_id=prod.id,
            cantidad=linea["cantidad"],
            precio_unitario=linea["precio_unitario"],
        )
        db.session.add(lp)

    db.session.flush()
    db.session.refresh(pedido)
    pedido.calcular_total()
    db.session.commit()
    return jsonify(pedido.to_dict()), 201


@proveedores_bp.route("/pedidos/<int:pp_id>/estado", methods=["PATCH"])
@admin_required
def cambiar_estado_pedido_proveedor(pp_id):
    """
    Cambia el estado de un pedido a proveedor. Al marcarlo como 'recibido',
    suma el stock automáticamente.
    """
    pedido = PedidoProveedor.query.get(pp_id)
    if not pedido:
        return jsonify({"error": "Pedido no encontrado"}), 404
    nuevo = (request.get_json() or {}).get("estado")
    if not nuevo:
        return jsonify({"error": "Estado requerido"}), 400

    estado_anterior = pedido.estado
    try:
        pedido.cambiar_estado(nuevo)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Si pasa a "recibido", actualizar stock
    if nuevo == "recibido" and estado_anterior != "recibido":
        for linea in pedido.lineas:
            if linea.producto:
                linea.producto.actualizar_stock(linea.cantidad)

    db.session.commit()
    return jsonify(pedido.to_dict())
