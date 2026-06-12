"""
Modelos Pedido y LineaPedido.

Pedido es la cabecera (un usuario, una fecha, totales, estado).
LineaPedido es el detalle (cada producto del pedido con su cantidad
y personalización).

La relación Pedido -> LineaPedido es de composición: las líneas
no tienen sentido sin un pedido, por eso cascade="all, delete-orphan".
"""
from datetime import datetime
from ..extensions import db


ESTADOS_PEDIDO = (
    "pendiente_pago",
    "pagado",
    "preparando",
    "enviado",
    "entregado",
    "cancelado",
    "reembolsado",
)


class Pedido(db.Model):
    __tablename__ = "Pedidos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("Usuarios.id"), nullable=False, index=True)
    direccion_envio_id = db.Column(db.Integer, db.ForeignKey("DireccionesEnvio.id"), nullable=False)
    metodo_pago_id = db.Column(db.Integer, db.ForeignKey("MetodosPago.id"), nullable=False)
    zona_envio_id = db.Column(db.Integer, db.ForeignKey("ZonasEnvio.id"), nullable=False)

    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    estado = db.Column(db.Enum(*ESTADOS_PEDIDO), nullable=False, default="pendiente_pago", index=True)

    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    coste_envio = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    descuento = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    notas = db.Column(db.Text)
    transaccion_id = db.Column(db.String(255))  # ID de Stripe / pasarela
    factura_url = db.Column(db.String(255))     # ruta al PDF generado

    # Relaciones
    usuario = db.relationship("Usuario", back_populates="pedidos")
    direccion_envio = db.relationship("DireccionEnvio", back_populates="pedidos")
    metodo_pago = db.relationship("MetodoPago", back_populates="pedidos")
    zona_envio = db.relationship("ZonaEnvio", back_populates="pedidos")
    lineas = db.relationship("LineaPedido", back_populates="pedido", cascade="all, delete-orphan")

    # --- Lógica de negocio ---

    def calcular_total(self) -> None:
        """Recalcula subtotal, descuento y total a partir de las líneas."""
        self.subtotal = sum(float(l.subtotal) for l in self.lineas)
        self.total = float(self.subtotal) + float(self.coste_envio) - float(self.descuento)

    def cambiar_estado(self, nuevo: str) -> None:
        if nuevo not in ESTADOS_PEDIDO:
            raise ValueError(f"Estado no válido: {nuevo}")
        self.estado = nuevo

    def puede_cancelarse(self) -> bool:
        """Solo se puede cancelar antes de envío."""
        return self.estado in ("pendiente_pago", "pagado", "preparando")

    def to_dict(self, incluir_lineas: bool = True):
        data = {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "usuario_nombre": self.usuario.nombre_completo if self.usuario else None,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "estado": self.estado,
            "subtotal": float(self.subtotal),
            "coste_envio": float(self.coste_envio),
            "descuento": float(self.descuento),
            "total": float(self.total),
            "metodo_pago": self.metodo_pago.nombre if self.metodo_pago else None,
            "zona_envio": self.zona_envio.nombre if self.zona_envio else None,
            "direccion_envio": self.direccion_envio.to_dict() if self.direccion_envio else None,
            "notas": self.notas,
            "factura_url": self.factura_url,
            "transaccion_id": self.transaccion_id,
        }
        if incluir_lineas:
            data["lineas"] = [l.to_dict() for l in self.lineas]
        return data


class LineaPedido(db.Model):
    __tablename__ = "LineasPedido"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("Pedidos.id"), nullable=False, index=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("Productos.id"), nullable=False, index=True)
    tipo_servicio_id = db.Column(db.Integer, db.ForeignKey("TiposServicio.id"), nullable=True)

    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    personalizacion = db.Column(db.Text)
    archivo_diseno_url = db.Column(db.String(255))
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    # Relaciones
    pedido = db.relationship("Pedido", back_populates="lineas")
    producto = db.relationship("Producto", back_populates="lineas_pedido")
    tipo_servicio = db.relationship("TipoServicio", back_populates="lineas_pedido")

    def calcular_subtotal(self) -> None:
        """
        Recalcula el subtotal. precio_unitario ya incluye el escalado
        por cantidad; aquí solo añadimos el precio extra del servicio.
        """
        precio = float(self.precio_unitario)
        if self.tipo_servicio:
            precio += float(self.tipo_servicio.precio_extra)
        self.subtotal = round(precio * self.cantidad, 2)

    def to_dict(self):
        return {
            "id": self.id,
            "producto_id": self.producto_id,
            "producto_nombre": self.producto.nombre if self.producto else None,
            "imagen_url": self.producto.imagen_url if self.producto else None,
            "tipo_servicio": self.tipo_servicio.nombre if self.tipo_servicio else None,
            "cantidad": self.cantidad,
            "precio_unitario": float(self.precio_unitario),
            "personalizacion": self.personalizacion,
            "archivo_diseno_url": self.archivo_diseno_url,
            "subtotal": float(self.subtotal),
        }
