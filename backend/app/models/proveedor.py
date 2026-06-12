"""
Modelos Proveedor, ProductoProveedor, PedidoProveedor y LineaPedidoProveedor.

ProductoProveedor es la tabla intermedia de la N a N entre Producto
y Proveedor. Guarda el precio de compra y el plazo de entrega, y
marca cuál es el proveedor principal de cada producto (al que se le
pide reposición por defecto).
"""
from datetime import datetime
from ..extensions import db


ESTADOS_PEDIDO_PROVEEDOR = ("creado", "enviado", "recibido", "cancelado")


class Proveedor(db.Model):
    __tablename__ = "Proveedores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    persona_contacto = db.Column(db.String(100))
    email = db.Column(db.String(150))
    telefono = db.Column(db.String(15))
    direccion = db.Column(db.String(200))
    condiciones = db.Column(db.Text)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    productos = db.relationship("ProductoProveedor", back_populates="proveedor", cascade="all, delete-orphan")
    pedidos = db.relationship("PedidoProveedor", back_populates="proveedor")

    def get_productos(self):
        """Devuelve la lista de productos que suministra este proveedor."""
        return [pp.producto for pp in self.productos]

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "persona_contacto": self.persona_contacto,
            "email": self.email,
            "telefono": self.telefono,
            "direccion": self.direccion,
            "condiciones": self.condiciones,
            "activo": self.activo,
        }


class ProductoProveedor(db.Model):
    __tablename__ = "ProductosProveedor"

    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey("Proveedores.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("Productos.id"), nullable=False)
    precio_compra = db.Column(db.Numeric(10, 2), nullable=False)
    plazo_entrega_dias = db.Column(db.Integer)
    es_principal = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (db.UniqueConstraint("proveedor_id", "producto_id"),)

    proveedor = db.relationship("Proveedor", back_populates="productos")
    producto = db.relationship("Producto", back_populates="proveedores")

    def to_dict(self):
        return {
            "id": self.id,
            "proveedor_id": self.proveedor_id,
            "proveedor_nombre": self.proveedor.nombre if self.proveedor else None,
            "producto_id": self.producto_id,
            "producto_nombre": self.producto.nombre if self.producto else None,
            "precio_compra": float(self.precio_compra),
            "plazo_entrega_dias": self.plazo_entrega_dias,
            "es_principal": self.es_principal,
        }


class PedidoProveedor(db.Model):
    __tablename__ = "PedidosProveedor"

    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey("Proveedores.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("Usuarios.id"), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    estado = db.Column(db.Enum(*ESTADOS_PEDIDO_PROVEEDOR), nullable=False, default="creado")
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    notas = db.Column(db.Text)

    proveedor = db.relationship("Proveedor", back_populates="pedidos")
    lineas = db.relationship("LineaPedidoProveedor", back_populates="pedido", cascade="all, delete-orphan")

    def calcular_total(self) -> None:
        self.total = sum(float(l.precio_unitario) * l.cantidad for l in self.lineas)

    def cambiar_estado(self, nuevo: str) -> None:
        if nuevo not in ESTADOS_PEDIDO_PROVEEDOR:
            raise ValueError(f"Estado no válido: {nuevo}")
        self.estado = nuevo

    def to_dict(self, incluir_lineas: bool = True):
        data = {
            "id": self.id,
            "proveedor_id": self.proveedor_id,
            "proveedor_nombre": self.proveedor.nombre if self.proveedor else None,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "estado": self.estado,
            "total": float(self.total),
            "notas": self.notas,
        }
        if incluir_lineas:
            data["lineas"] = [l.to_dict() for l in self.lineas]
        return data


class LineaPedidoProveedor(db.Model):
    __tablename__ = "LineasPedidoProveedor"

    id = db.Column(db.Integer, primary_key=True)
    pedido_proveedor_id = db.Column(db.Integer, db.ForeignKey("PedidosProveedor.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("Productos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    pedido = db.relationship("PedidoProveedor", back_populates="lineas")
    producto = db.relationship("Producto")

    def to_dict(self):
        return {
            "id": self.id,
            "producto_id": self.producto_id,
            "producto_nombre": self.producto.nombre if self.producto else None,
            "cantidad": self.cantidad,
            "precio_unitario": float(self.precio_unitario),
            "subtotal": float(self.precio_unitario) * self.cantidad,
        }
