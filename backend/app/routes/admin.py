"""
Rutas del panel de administración.

Endpoints exclusivos del rol admin:
  - listado completo de pedidos y cambio de estado
  - verificación / borrado de reseñas
  - gestión de promociones
  - informes (ventas, stock bajo, productos más vendidos)
  - webhook de Stripe (para confirmar pagos)
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from ..extensions import db
from ..models import (
    Pedido, Resena, Promocion, Producto, Categoria, Usuario
)
from ..services.emails import enviar_email_cambio_estado
from ..services.pagos import confirmar_webhook
from ..utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__)


# --- Gestión de pedidos ---

@admin_bp.route("/pedidos", methods=["GET"])
@admin_required
def listar_todos_pedidos():
    """Lista de todos los pedidos del sistema."""
    estado = request.args.get("estado")
    query = Pedido.query
    if estado:
        query = query.filter_by(estado=estado)
    pedidos = query.order_by(Pedido.fecha.desc()).all()
    return jsonify([p.to_dict(incluir_lineas=False) for p in pedidos])


@admin_bp.route("/pedidos/<int:pedido_id>/estado", methods=["PATCH"])
@admin_required
def cambiar_estado_pedido(pedido_id):
    """Cambia el estado de un pedido del cliente."""
    pedido = Pedido.query.get(pedido_id)
    if not pedido:
        return jsonify({"error": "Pedido no encontrado"}), 404

    nuevo = (request.get_json() or {}).get("estado")
    if not nuevo:
        return jsonify({"error": "Estado requerido"}), 400

    try:
        pedido.cambiar_estado(nuevo)
        db.session.commit()
        enviar_email_cambio_estado(pedido)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(pedido.to_dict())


# --- Gestión de reseñas ---

@admin_bp.route("/resenas/pendientes", methods=["GET"])
@admin_required
def resenas_pendientes():
    """Reseñas sin verificar."""
    resenas = Resena.query.filter_by(verificada=False).order_by(Resena.fecha.desc()).all()
    return jsonify([r.to_dict() for r in resenas])


@admin_bp.route("/resenas/<int:resena_id>/verificar", methods=["PATCH"])
@admin_required
def verificar_resena(resena_id):
    resena = Resena.query.get(resena_id)
    if not resena:
        return jsonify({"error": "Reseña no encontrada"}), 404
    resena.verificar()
    db.session.commit()
    return jsonify(resena.to_dict())


@admin_bp.route("/resenas/<int:resena_id>", methods=["DELETE"])
@admin_required
def borrar_resena(resena_id):
    resena = Resena.query.get(resena_id)
    if not resena:
        return jsonify({"error": "Reseña no encontrada"}), 404
    db.session.delete(resena)
    db.session.commit()
    return jsonify({"mensaje": "Reseña eliminada"})


# --- Promociones ---

@admin_bp.route("/promociones", methods=["GET"])
@admin_required
def listar_promociones():
    promos = Promocion.query.order_by(Promocion.fecha_inicio.desc()).all()
    return jsonify([p.to_dict() for p in promos])


@admin_bp.route("/promociones", methods=["POST"])
@admin_required
def crear_promocion():
    datos = request.get_json() or {}
    requeridos = ["nombre", "tipo", "valor", "fecha_inicio", "fecha_fin"]
    faltantes = [c for c in requeridos if datos.get(c) is None]
    if faltantes:
        return jsonify({"error": "Faltan campos", "campos": faltantes}), 400

    if datos["tipo"] not in ("porcentaje", "fijo"):
        return jsonify({"error": "Tipo debe ser 'porcentaje' o 'fijo'"}), 400

    try:
        fecha_inicio = datetime.fromisoformat(datos["fecha_inicio"])
        fecha_fin = datetime.fromisoformat(datos["fecha_fin"])
    except (TypeError, ValueError):
        return jsonify({"error": "Formato de fecha incorrecto (ISO 8601)"}), 400

    if fecha_fin <= fecha_inicio:
        return jsonify({"error": "La fecha fin debe ser posterior a la inicio"}), 400

    promo = Promocion(
        nombre=datos["nombre"],
        descripcion=datos.get("descripcion"),
        tipo=datos["tipo"],
        valor=datos["valor"],
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        producto_id=datos.get("producto_id"),
        categoria_id=datos.get("categoria_id"),
        activa=datos.get("activa", True),
    )
    db.session.add(promo)
    db.session.commit()
    return jsonify(promo.to_dict()), 201


@admin_bp.route("/promociones/<int:promo_id>", methods=["PATCH"])
@admin_required
def actualizar_promocion(promo_id):
    promo = Promocion.query.get(promo_id)
    if not promo:
        return jsonify({"error": "Promoción no encontrada"}), 404
    datos = request.get_json() or {}
    for campo in ("nombre", "descripcion", "tipo", "valor",
                  "producto_id", "categoria_id", "activa"):
        if campo in datos:
            setattr(promo, campo, datos[campo])
    for campo in ("fecha_inicio", "fecha_fin"):
        if campo in datos:
            setattr(promo, campo, datetime.fromisoformat(datos[campo]))
    db.session.commit()
    return jsonify(promo.to_dict())


@admin_bp.route("/promociones/<int:promo_id>", methods=["DELETE"])
@admin_required
def borrar_promocion(promo_id):
    promo = Promocion.query.get(promo_id)
    if not promo:
        return jsonify({"error": "Promoción no encontrada"}), 404
    db.session.delete(promo)
    db.session.commit()
    return jsonify({"mensaje": "Promoción eliminada"})


# --- Informes ---

@admin_bp.route("/informes/stock-bajo", methods=["GET"])
@admin_required
def informe_stock_bajo():
    """Productos con stock por debajo del mínimo."""
    productos = (Producto.query.filter(Producto.activo == True,
                                       Producto.stock <= Producto.stock_minimo).all())
    return jsonify([{
        **p.to_dict(),
        "diferencia": p.stock_minimo - p.stock,
    } for p in productos])


@admin_bp.route("/informes/ventas-por-mes", methods=["GET"])
@admin_required
def informe_ventas_mes():
    """
    Resumen de ventas por mes.

    La función para extraer 'AÑO-MES' de una fecha NO es estándar SQL:
    MySQL usa DATE_FORMAT() y SQLite usa strftime(). Como en producción
    corremos sobre SQLite y en local podemos usar MySQL, detectamos el
    motor activo y elegimos la función adecuada. Así el mismo endpoint
    funciona en ambos entornos sin reescribir la consulta.
    """
    dialecto = db.engine.dialect.name  # 'sqlite', 'mysql', etc.
    if dialecto == "mysql":
        expr_mes = "DATE_FORMAT(fecha, '%Y-%m')"
    else:  # sqlite (producción) y compatibles
        expr_mes = "strftime('%Y-%m', fecha)"

    sql = f"""
        SELECT {expr_mes} AS mes,
               COUNT(*) AS num_pedidos,
               SUM(total) AS ingresos
        FROM Pedidos
        WHERE estado IN ('pagado','preparando','enviado','entregado')
        GROUP BY mes
        ORDER BY mes DESC
        LIMIT 12
    """
    rows = db.session.execute(db.text(sql)).fetchall()
    return jsonify([{
        "mes": r[0],
        "num_pedidos": r[1],
        "ingresos": float(r[2]) if r[2] else 0,
    } for r in rows])


@admin_bp.route("/informes/productos-mas-vendidos", methods=["GET"])
@admin_required
def informe_productos_vendidos():
    """Top de productos más vendidos."""
    sql = """
        SELECT p.id, p.nombre,
               SUM(lp.cantidad) AS unidades,
               SUM(lp.subtotal) AS ingresos
        FROM Productos p
        JOIN LineasPedido lp ON lp.producto_id = p.id
        JOIN Pedidos pe ON pe.id = lp.pedido_id
        WHERE pe.estado IN ('pagado','preparando','enviado','entregado')
        GROUP BY p.id, p.nombre
        ORDER BY unidades DESC
        LIMIT 20
    """
    rows = db.session.execute(db.text(sql)).fetchall()
    return jsonify([{
        "producto_id": r[0],
        "nombre": r[1],
        "unidades": int(r[2]),
        "ingresos": float(r[3]) if r[3] else 0,
    } for r in rows])


# --- Estadísticas / KPIs ---

@admin_bp.route("/stats", methods=["GET"])
@admin_required
def stats_panel():
    """Resumen de KPIs para las tarjetas del panel de administración."""
    total_clientes = Usuario.query.filter(
        Usuario.rol == "cliente",
        Usuario.activo == True,
    ).count()

    total_pedidos = Pedido.query.count()

    from sqlalchemy import func
    total_ventas = db.session.query(func.coalesce(func.sum(Pedido.total), 0)).filter(
        Pedido.estado.in_(["pagado", "preparando", "enviado", "entregado"])
    ).scalar()

    return jsonify({
        "total_clientes": total_clientes,
        "total_pedidos": total_pedidos,
        "total_ventas": float(total_ventas),
    })


# --- Gestión de usuarios ---

@admin_bp.route("/usuarios", methods=["GET"])
@admin_required
def listar_usuarios():
    """Lista de todos los usuarios del sistema."""
    usuarios = Usuario.query.order_by(Usuario.fecha_registro.desc()).all()
    return jsonify([u.to_dict() for u in usuarios])


@admin_bp.route("/usuarios/<int:user_id>/rol", methods=["PATCH"])
@admin_required
def cambiar_rol_usuario(user_id):
    """Cambia el rol de un usuario (cliente <-> admin)."""
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    nuevo = (request.get_json() or {}).get("rol")
    if nuevo not in ("cliente", "admin"):
        return jsonify({"error": "Rol no válido"}), 400
    usuario.rol = nuevo
    db.session.commit()
    return jsonify(usuario.to_dict())


# --- Webhook de Stripe (recibe confirmaciones de pago) ---

@admin_bp.route("/webhook/stripe", methods=["POST"])
def webhook_stripe():
    """
    Endpoint público (sin auth) que recibe los webhooks de Stripe.
    La autenticación se hace verificando la firma del propio Stripe.
    Cuando un pago se confirma, marcamos el pedido como 'pagado'.
    """
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")
    try:
        evento = confirmar_webhook(payload, sig_header)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if evento["type"] == "payment_intent.succeeded":
        intent = evento["data"]["object"]
        pedido_id = intent.get("metadata", {}).get("pedido_id")
        if pedido_id:
            pedido = Pedido.query.get(int(pedido_id))
            if pedido:
                pedido.cambiar_estado("pagado")
                pedido.transaccion_id = intent["id"]
                db.session.commit()
                current_app.logger.info(f"Pedido {pedido_id} pagado vía Stripe")

    return jsonify({"received": True})