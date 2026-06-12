"""
Decoradores de autorización.

@admin_required y @rol_required(rol) comprueban el rol del usuario
autenticado a partir del JWT. Se aplican encima de los endpoints
que solo deben ejecutar administradores.
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from ..models import Usuario


def admin_required(fn):
    """Solo permite el acceso a usuarios con rol='admin'."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("rol") != "admin":
            return jsonify({"error": "Acceso restringido a administradores"}), 403
        return fn(*args, **kwargs)
    return wrapper


def rol_required(*roles_permitidos):
    """Permite el acceso si el rol del usuario está en la lista dada."""
    def decorador(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("rol") not in roles_permitidos:
                return jsonify({"error": "Acceso no autorizado"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorador


def usuario_actual():
    """Helper: devuelve el objeto Usuario del JWT (o None)."""
    try:
        verify_jwt_in_request()
        claims = get_jwt()
        usuario_id = claims.get("sub")
        if usuario_id is None:
            return None
        return Usuario.query.get(int(usuario_id))
    except Exception:
        return None
