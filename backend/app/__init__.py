"""
app/__init__.py
Application factory de Flask. Patrón habitual para aplicaciones Flask
medianas/grandes: permite crear instancias separadas para testing,
desarrollo y producción sin duplicar código.
"""
from flask import Flask, jsonify
from .config import config_by_name
from .extensions import db, migrate, jwt, mail, cors


def create_app(config_name: str = "dev") -> Flask:
    """Crea y configura la app de Flask."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    # CORS: parsear el config a lista. Si es "*" o vacio, permite todo.
    cors_config = app.config.get("CORS_ORIGINS", "*")
    if isinstance(cors_config, str):
        if cors_config.strip() in ("", "*"):
            origins_list = "*"
        else:
            origins_list = [o.strip() for o in cors_config.split(",") if o.strip()]
    else:
        origins_list = cors_config

    # En desarrollo permitimos SIEMPRE cualquier origen. Así da igual el puerto
    # que use Live Server (5500, 5501, ...) y se ignora cualquier .env local
    # que pudiera restringir los orígenes. En producción se respeta CORS_ORIGINS.
    if config_name == "dev":
        origins_list = "*"

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": origins_list}},
        supports_credentials=False,
    )

    # Registrar blueprints (rutas)
    from .routes.auth import auth_bp
    from .routes.usuarios import usuarios_bp
    from .routes.productos import productos_bp
    from .routes.categorias import categorias_bp
    from .routes.pedidos import pedidos_bp
    from .routes.resenas import resenas_bp
    from .routes.direcciones import direcciones_bp
    from .routes.admin import admin_bp
    from .routes.proveedores import proveedores_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(usuarios_bp, url_prefix="/api/usuarios")
    app.register_blueprint(productos_bp, url_prefix="/api/productos")
    app.register_blueprint(categorias_bp, url_prefix="/api/categorias")
    app.register_blueprint(pedidos_bp, url_prefix="/api/pedidos")
    app.register_blueprint(resenas_bp, url_prefix="/api/resenas")
    app.register_blueprint(direcciones_bp, url_prefix="/api/direcciones")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(proveedores_bp, url_prefix="/api/proveedores")

    # Handlers de error globales
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Petición incorrecta", "detalle": str(e)}), 400

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Error interno del servidor"}), 500

    # Endpoint de salud (útil para Docker healthcheck)
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "vetesia-backend"})

    return app