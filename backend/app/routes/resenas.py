"""
Rutas de reseñas.

GET /api/resenas?producto_id=  - reseñas verificadas de un producto
POST /api/resenas              - crear reseña (requiere login)

Las reseñas se crean con verificada=False. Un admin debe verificarlas
(endpoint en /api/admin) para que aparezcan públicamente.

Restricción: un usuario solo puede dejar una reseña por producto y
solo si ha comprado el producto previamente (pedido en estado entregado).
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Resena, Producto, Pedido, LineaPedido

resenas_bp = Blueprint("resenas", __name__)


@resenas_bp.route("", methods=["GET"])
def listar_resenas():
    """Lista de reseñas verificadas (opcionalmente filtrado por producto)."""
    query = Resena.query.filter_by(verificada=True)
    producto_id = request.args.get("producto_id", type=int)
    if producto_id:
        query = query.filter_by(producto_id=producto_id)
    resenas = query.order_by(Resena.fecha.desc()).all()
    return jsonify([r.to_dict() for r in resenas])


@resenas_bp.route("", methods=["POST"])
@jwt_required()
def crear_resena():
    """Crea una nueva reseña. Comprueba que el usuario ha comprado el producto."""
    usuario_id = int(get_jwt_identity())
    datos = request.get_json() or {}

    producto_id = datos.get("producto_id")
    valoracion = datos.get("valoracion")
    texto = datos.get("texto")

    if not producto_id or not valoracion:
        return jsonify({"error": "Faltan campos requeridos"}), 400

    if not isinstance(valoracion, int) or not (1 <= valoracion <= 5):
        return jsonify({"error": "La valoración debe ser un entero entre 1 y 5"}), 400

    if not Producto.query.get(producto_id):
        return jsonify({"error": "Producto no encontrado"}), 404

    # Verificar que el usuario ha comprado el producto
    ha_comprado = (db.session.query(LineaPedido)
                    .join(Pedido)
                    .filter(Pedido.usuario_id == usuario_id,
                            Pedido.estado.in_(["entregado", "enviado", "preparando", "pagado"]),
                            LineaPedido.producto_id == producto_id)
                    .first())
    if not ha_comprado:
        return jsonify({"error": "Solo puedes reseñar productos que has comprado"}), 403

    try:
        resena = Resena(
            usuario_id=usuario_id,
            producto_id=producto_id,
            valoracion=valoracion,
            texto=texto,
            verificada=False,  # pendiente de verificación por admin
        )
        db.session.add(resena)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Ya has reseñado este producto"}), 409

    return jsonify({
        "mensaje": "Reseña enviada. Se publicará tras la verificación del administrador.",
        "resena": resena.to_dict()
    }), 201


@resenas_bp.route("/mias", methods=["GET"])
@jwt_required()
def mis_resenas():
    """Reseñas escritas por el usuario autenticado (verificadas o no)."""
    usuario_id = int(get_jwt_identity())
    resenas = Resena.query.filter_by(usuario_id=usuario_id).order_by(Resena.fecha.desc()).all()
    return jsonify([r.to_dict() for r in resenas])


@resenas_bp.route("/<int:resena_id>", methods=["DELETE"])
@jwt_required()
def borrar_resena_propia(resena_id):
    """Permite al usuario borrar una reseña suya."""
    usuario_id = int(get_jwt_identity())
    resena = Resena.query.filter_by(id=resena_id, usuario_id=usuario_id).first()
    if not resena:
        return jsonify({"error": "Reseña no encontrada"}), 404
    db.session.delete(resena)
    db.session.commit()
    return jsonify({"mensaje": "Reseña eliminada"})
