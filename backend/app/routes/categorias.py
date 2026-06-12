"""Rutas de categorías de productos."""
from flask import Blueprint, request, jsonify

from ..extensions import db
from ..models import Categoria
from ..utils.decorators import admin_required

categorias_bp = Blueprint("categorias", __name__)


@categorias_bp.route("", methods=["GET"])
def listar_categorias():
    categorias = Categoria.query.filter_by(activa=True).all()
    incluir = request.args.get("incluir_subcategorias") == "true"
    return jsonify([c.to_dict(incluir_subcategorias=incluir) for c in categorias])


@categorias_bp.route("/<int:cat_id>", methods=["GET"])
def get_categoria(cat_id):
    cat = Categoria.query.get(cat_id)
    if not cat:
        return jsonify({"error": "Categoría no encontrada"}), 404
    return jsonify(cat.to_dict(incluir_subcategorias=True))


@categorias_bp.route("", methods=["POST"])
@admin_required
def crear_categoria():
    datos = request.get_json() or {}
    if not datos.get("nombre"):
        return jsonify({"error": "El nombre es obligatorio"}), 400
    cat = Categoria(
        nombre=datos["nombre"],
        descripcion=datos.get("descripcion"),
        categoria_padre_id=datos.get("categoria_padre_id"),
        imagen_url=datos.get("imagen_url"),
    )
    db.session.add(cat)
    db.session.commit()
    return jsonify(cat.to_dict()), 201


@categorias_bp.route("/<int:cat_id>", methods=["PATCH"])
@admin_required
def actualizar_categoria(cat_id):
    cat = Categoria.query.get(cat_id)
    if not cat:
        return jsonify({"error": "Categoría no encontrada"}), 404
    datos = request.get_json() or {}
    for campo in ("nombre", "descripcion", "categoria_padre_id", "imagen_url", "activa"):
        if campo in datos:
            setattr(cat, campo, datos[campo])
    db.session.commit()
    return jsonify(cat.to_dict())


@categorias_bp.route("/<int:cat_id>", methods=["DELETE"])
@admin_required
def baja_categoria(cat_id):
    cat = Categoria.query.get(cat_id)
    if not cat:
        return jsonify({"error": "Categoría no encontrada"}), 404
    cat.activa = False
    db.session.commit()
    return jsonify({"mensaje": "Categoría desactivada"})
