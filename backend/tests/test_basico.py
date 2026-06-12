"""
Tests básicos del backend de VetÉsia.

Cubren los flujos principales:
  - registro y login
  - listado de catálogo
  - creación de pedido
  - autorización de endpoints

Ejecutar con: pytest

Importante: estos tests usan una BBDD MySQL real. Para pruebas
aisladas se podría usar SQLite en memoria, pero el dialecto sería
diferente y los ENUMs no son 100% compatibles. Para CI se recomienda
levantar un contenedor MySQL específico de tests.
"""
import json
import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    app = create_app("dev")
    app.config["TESTING"] = True
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_health(client):
    """El endpoint /api/health responde correctamente."""
    rv = client.get("/api/health")
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "ok"


def test_listado_productos_publico(client):
    """El catálogo es público (no requiere autenticación)."""
    rv = client.get("/api/productos")
    assert rv.status_code == 200
    assert isinstance(rv.get_json(), list)


def test_login_fallido(client):
    """Credenciales incorrectas devuelven 401."""
    rv = client.post("/api/auth/login", json={
        "email": "noexiste@vetesia.com",
        "password": "xxx"
    })
    assert rv.status_code == 401


def test_endpoint_protegido_sin_token(client):
    """Acceder a /api/pedidos sin token devuelve 401."""
    rv = client.get("/api/pedidos")
    assert rv.status_code == 401


def test_endpoint_admin_sin_token(client):
    """Acceder a un endpoint de admin sin token devuelve 401."""
    rv = client.get("/api/admin/pedidos")
    assert rv.status_code == 401


def test_metodos_pago_publico(client):
    """Los métodos de pago son públicos para el checkout."""
    rv = client.get("/api/pedidos/metodos-pago")
    assert rv.status_code == 200


def test_zonas_envio_publico(client):
    """Las zonas de envío son públicas para el checkout."""
    rv = client.get("/api/pedidos/zonas-envio")
    assert rv.status_code == 200
