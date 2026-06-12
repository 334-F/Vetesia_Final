"""
Rutas de usuario (perfil del propio usuario).
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..extensions import db
from ..models import Usuario

usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/me", methods=["GET"])
@jwt_required()
def get_perfil():
    """Datos del usuario autenticado."""
    usuario = Usuario.query.get(int(get_jwt_identity()))
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(usuario.to_dict())


@usuarios_bp.route("/me", methods=["PATCH"])
@jwt_required()
def update_perfil():
    """Actualizar datos personales (no email ni contraseña, que tienen su flujo aparte)."""
    usuario = Usuario.query.get(int(get_jwt_identity()))
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    datos = request.get_json() or {}
    campos_editables = ("nombre", "apellidos", "telefono", "direccion")
    for campo in campos_editables:
        if campo in datos:
            setattr(usuario, campo, datos[campo])

    db.session.commit()
    return jsonify({"mensaje": "Perfil actualizado", "usuario": usuario.to_dict()})


@usuarios_bp.route("/me", methods=["DELETE"])
@jwt_required()
def baja_cuenta():
    """Baja lógica: marca activo=False (no se borra para no romper pedidos antiguos)."""
    usuario = Usuario.query.get(int(get_jwt_identity()))
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    usuario.activo = False
    db.session.commit()
    return jsonify({"mensaje": "Cuenta dada de baja"})
