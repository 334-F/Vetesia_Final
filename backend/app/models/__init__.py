"""
app/models/__init__.py
Expone todos los modelos para que se puedan importar como
`from app.models import Usuario, Producto, ...`
"""
from .usuario import Usuario, TipoCliente
from .direccion import DireccionEnvio
from .categoria import Categoria
from .producto import Producto, PrecioEscalado
from .promocion import Promocion
from .servicio import TipoServicio
from .pago import MetodoPago
from .envio import ZonaEnvio
from .pedido import Pedido, LineaPedido
from .proveedor import Proveedor, ProductoProveedor, PedidoProveedor, LineaPedidoProveedor
from .resena import Resena

__all__ = [
    "Usuario", "TipoCliente", "DireccionEnvio", "Categoria",
    "Producto", "PrecioEscalado", "Promocion", "TipoServicio",
    "MetodoPago", "ZonaEnvio", "Pedido", "LineaPedido",
    "Proveedor", "ProductoProveedor", "PedidoProveedor",
    "LineaPedidoProveedor", "Resena",
]
