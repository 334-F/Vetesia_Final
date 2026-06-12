"""
Rutas de autenticación.

Endpoints:
  POST /api/auth/register  - crea un usuario nuevo (rol cliente)
  POST /api/auth/login     - devuelve un JWT
  GET  /api/auth/me        - devuelve el usuario del JWT actual

Las contraseñas se hashean con bcrypt antes de guardar y se comparan
con bcrypt al hacer login. Nunca se almacenan en claro.
"""
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity
)
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Usuario, TipoCliente

auth_bp = Blueprint("auth", __name__)


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Registra un nuevo usuario con rol 'cliente'."""
    datos = request.get_json() or {}

    # Validaciones básicas
    requeridos = ["nombre", "apellidos", "email", "password"]
    faltantes = [c for c in requeridos if not datos.get(c)]
    if faltantes:
        return jsonify({"error": "Faltan campos requeridos", "campos": faltantes}), 400

    email = datos["email"].strip().lower()
    if not EMAIL_REGEX.match(email):
        return jsonify({"error": "Email no válido"}), 400

    password = datos["password"]
    if len(password) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400

    # Comprobar email único
    if Usuario.query.filter_by(email=email).first():
        return jsonify({"error": "Ya existe un usuario con ese email"}), 409

    # Tipo de cliente (por defecto, particular = id 1)
    tipo_id = datos.get("tipo_cliente_id", 1)
    tipo = TipoCliente.query.get(tipo_id)
    if not tipo:
        return jsonify({"error": "Tipo de cliente no válido"}), 400

    # Crear usuario
    usuario = Usuario(
        tipo_cliente_id=tipo_id,
        nombre=datos["nombre"].strip(),
        apellidos=datos["apellidos"].strip(),
        email=email,
        telefono=datos.get("telefono"),
        direccion=datos.get("direccion"),
        rol="cliente",
    )
    usuario.set_password(password)

    try:
        db.session.add(usuario)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Error al crear el usuario"}), 500

    # Generar token
    token = create_access_token(
        identity=str(usuario.id),
        additional_claims={"rol": usuario.rol, "email": usuario.email},
    )

    return jsonify({
        "mensaje": "Usuario registrado correctamente",
        "usuario": usuario.to_dict(),
        "access_token": token,
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Autentica un usuario y devuelve un JWT."""
    datos = request.get_json() or {}
    email = (datos.get("email") or "").strip().lower()
    password = datos.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email y contraseña son obligatorios"}), 400

    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario or not usuario.check_password(password):
        # Mismo mensaje para no filtrar si el email existe
        return jsonify({"error": "Credenciales incorrectas"}), 401

    if not usuario.activo:
        return jsonify({"error": "Usuario desactivado"}), 403

    token = create_access_token(
        identity=str(usuario.id),
        additional_claims={"rol": usuario.rol, "email": usuario.email},
    )

    return jsonify({
        "mensaje": "Login correcto",
        "usuario": usuario.to_dict(),
        "access_token": token,
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Devuelve los datos del usuario autenticado."""
    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(int(usuario_id))
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(usuario.to_dict())


@auth_bp.route("/password", methods=["PATCH"])
@jwt_required()
def cambiar_password():
    """Permite al usuario cambiar su contraseña."""
    datos = request.get_json() or {}
    actual = datos.get("password_actual")
    nueva = datos.get("password_nueva")

    if not actual or not nueva:
        return jsonify({"error": "Faltan datos"}), 400
    if len(nueva) < 8:
        return jsonify({"error": "La nueva contraseña debe tener al menos 8 caracteres"}), 400

    usuario_id = get_jwt_identity()
    usuario = Usuario.query.get(int(usuario_id))
    if not usuario or not usuario.check_password(actual):
        return jsonify({"error": "Contraseña actual incorrecta"}), 401

    usuario.set_password(nueva)
    db.session.commit()
    return jsonify({"mensaje": "Contraseña actualizada"})
