"""
Rutas de direcciones de envío.

Cada usuario gestiona sus propias direcciones. Solo puede ver/editar/borrar
las que le pertenecen (no las de otros usuarios).
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models import DireccionEnvio

direcciones_bp = Blueprint("direcciones", __name__)


@direcciones_bp.route("", methods=["GET"])
@jwt_required()
def listar_direcciones():
    """Lista las direcciones del usuario autenticado."""
    usuario_id = int(get_jwt_identity())
    direcciones = DireccionEnvio.query.filter_by(usuario_id=usuario_id).all()
    return jsonify([d.to_dict() for d in direcciones])


@direcciones_bp.route("", methods=["POST"])
@jwt_required()
def crear_direccion():
    """Crea una nueva dirección de envío para el usuario actual."""
    usuario_id = int(get_jwt_identity())
    datos = request.get_json() or {}

    requeridos = ["alias", "destinatario", "calle", "codigo_postal", "municipio", "provincia"]
    faltantes = [c for c in requeridos if not datos.get(c)]
    if faltantes:
        return jsonify({"error": "Faltan campos", "campos": faltantes}), 400

    # Si es la primera dirección, la marcamos como predeterminada
    existentes = DireccionEnvio.query.filter_by(usuario_id=usuario_id).count()
    predeterminada = datos.get("predeterminada", existentes == 0)

    # Si esta nueva es predeterminada, desmarcamos las otras
    if predeterminada:
        DireccionEnvio.query.filter_by(usuario_id=usuario_id).update(
            {"predeterminada": False}
        )

    direccion = DireccionEnvio(
        usuario_id=usuario_id,
        alias=datos["alias"],
        destinatario=datos["destinatario"],
        calle=datos["calle"],
        numero=datos.get("numero"),
        piso=datos.get("piso"),
        codigo_postal=datos["codigo_postal"],
        municipio=datos["municipio"],
        provincia=datos["provincia"],
        telefono_contacto=datos.get("telefono_contacto"),
        predeterminada=predeterminada,
    )
    db.session.add(direccion)
    db.session.commit()
    return jsonify(direccion.to_dict()), 201


@direcciones_bp.route("/<int:dir_id>", methods=["PATCH"])
@jwt_required()
def actualizar_direccion(dir_id):
    usuario_id = int(get_jwt_identity())
    direccion = DireccionEnvio.query.filter_by(id=dir_id, usuario_id=usuario_id).first()
    if not direccion:
        return jsonify({"error": "Dirección no encontrada"}), 404

    datos = request.get_json() or {}

    if datos.get("predeterminada"):
        DireccionEnvio.query.filter_by(usuario_id=usuario_id).update(
            {"predeterminada": False}
        )

    for campo in ("alias", "destinatario", "calle", "numero", "piso",
                  "codigo_postal", "municipio", "provincia",
                  "telefono_contacto", "predeterminada"):
        if campo in datos:
            setattr(direccion, campo, datos[campo])

    db.session.commit()
    return jsonify(direccion.to_dict())


@direcciones_bp.route("/<int:dir_id>", methods=["DELETE"])
@jwt_required()
def borrar_direccion(dir_id):
    usuario_id = int(get_jwt_identity())
    direccion = DireccionEnvio.query.filter_by(id=dir_id, usuario_id=usuario_id).first()
    if not direccion:
        return jsonify({"error": "Dirección no encontrada"}), 404
    db.session.delete(direccion)
    db.session.commit()
    return jsonify({"mensaje": "Dirección eliminada"})
