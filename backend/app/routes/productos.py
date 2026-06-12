"""
Rutas del catálogo de productos.

GET /api/productos       - listado con filtros opcionales
GET /api/productos/:id   - ficha de producto
POST /api/productos      - alta (solo admin)
PATCH /api/productos/:id - edición (solo admin)
DELETE /api/productos/:id - baja lógica (solo admin)
"""
from flask import Blueprint, request, jsonify

from ..extensions import db
from ..models import Producto, Categoria
from ..utils.decorators import admin_required

productos_bp = Blueprint("productos", __name__)


@productos_bp.route("", methods=["GET"])
def listar_productos():
    """
    Lista de productos activos. Filtros opcionales:
      ?categoria_id=  filtrar por categoría
      ?q=             búsqueda por nombre/descripción
      ?tipo=          'estandar' o 'personalizable'
      ?orden=         'precio_asc', 'precio_desc', 'novedades'
      ?incluir_inactivos=true (solo si el admin lo solicita)
    """
    query = Producto.query

    if request.args.get("incluir_inactivos") != "true":
        query = query.filter(Producto.activo == True)

    categoria_id = request.args.get("categoria_id", type=int)
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)

    tipo = request.args.get("tipo")
    if tipo in ("estandar", "personalizable"):
        query = query.filter(Producto.tipo == tipo)

    q = request.args.get("q")
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Producto.nombre.ilike(like)) | (Producto.descripcion.ilike(like))
        )

    orden = request.args.get("orden")
    if orden == "precio_asc":
        query = query.order_by(Producto.precio_base.asc())
    elif orden == "precio_desc":
        query = query.order_by(Producto.precio_base.desc())
    elif orden == "novedades":
        query = query.order_by(Producto.fecha_alta.desc())
    else:
        query = query.order_by(Producto.nombre.asc())

    productos = query.all()
    return jsonify([p.to_dict() for p in productos])


@productos_bp.route("/<int:producto_id>", methods=["GET"])
def get_producto(producto_id):
    """Ficha completa de un producto, con reseñas verificadas."""
    producto = Producto.query.get(producto_id)
    if not producto or not producto.activo:
        return jsonify({"error": "Producto no encontrado"}), 404
    return jsonify(producto.to_dict(incluir_resenas=True))


@productos_bp.route("", methods=["POST"])
@admin_required
def crear_producto():
    """Crea un nuevo producto (solo admin)."""
    datos = request.get_json() or {}

    requeridos = ["categoria_id", "nombre", "precio_base"]
    faltantes = [c for c in requeridos if datos.get(c) is None]
    if faltantes:
        return jsonify({"error": "Faltan campos", "campos": faltantes}), 400

    if not Categoria.query.get(datos["categoria_id"]):
        return jsonify({"error": "Categoría no válida"}), 400

    if datos.get("tipo") and datos["tipo"] not in ("estandar", "personalizable"):
        return jsonify({"error": "Tipo de producto no válido"}), 400

    producto = Producto(
        categoria_id=datos["categoria_id"],
        nombre=datos["nombre"],
        descripcion=datos.get("descripcion"),
        tipo=datos.get("tipo", "estandar"),
        precio_base=datos["precio_base"],
        stock=datos.get("stock", 0),
        stock_minimo=datos.get("stock_minimo", 5),
        imagen_url=datos.get("imagen_url"),
    )
    db.session.add(producto)
    db.session.commit()
    return jsonify(producto.to_dict()), 201


@productos_bp.route("/<int:producto_id>", methods=["PATCH"])
@admin_required
def actualizar_producto(producto_id):
    producto = Producto.query.get(producto_id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404

    datos = request.get_json() or {}
    campos = ("nombre", "descripcion", "categoria_id", "tipo",
              "precio_base", "stock", "stock_minimo", "imagen_url", "activo")
    for campo in campos:
        if campo in datos:
            setattr(producto, campo, datos[campo])

    db.session.commit()
    return jsonify(producto.to_dict())


@productos_bp.route("/<int:producto_id>", methods=["DELETE"])
@admin_required
def baja_producto(producto_id):
    """Baja lógica del producto (no se borra para no romper pedidos antiguos)."""
    producto = Producto.query.get(producto_id)
    if not producto:
        return jsonify({"error": "Producto no encontrado"}), 404
    producto.activo = False
    db.session.commit()
    return jsonify({"mensaje": "Producto desactivado"})
