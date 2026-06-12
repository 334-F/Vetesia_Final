"""
Modelo MetodoPago.

Métodos de pago activables/desactivables desde el panel del admin.
El flag requiere_pasarela indica si hay que integrarse con Stripe
(tarjeta, Bizum) o si es manual (transferencia, contrarreembolso).
"""
from ..extensions import db


class MetodoPago(db.Model):
    __tablename__ = "MetodosPago"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    requiere_pasarela = db.Column(db.Boolean, nullable=False, default=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    pedidos = db.relationship("Pedido", back_populates="metodo_pago")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "requiere_pasarela": self.requiere_pasarela,
            "activo": self.activo,
        }
