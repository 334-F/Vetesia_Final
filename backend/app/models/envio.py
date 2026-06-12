"""
Modelo ZonaEnvio.

Zonas geográficas con su coste de envío y plazo estimado.
Aplicado solo al pedido en función de la dirección de envío usada
(no al perfil del usuario, como pedía la tutora).
"""
from ..extensions import db


class ZonaEnvio(db.Model):
    __tablename__ = "ZonasEnvio"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    coste_envio = db.Column(db.Numeric(10, 2), nullable=False)
    plazo_dias = db.Column(db.Integer, nullable=False)
    activa = db.Column(db.Boolean, nullable=False, default=True)

    pedidos = db.relationship("Pedido", back_populates="zona_envio")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "coste_envio": float(self.coste_envio),
            "plazo_dias": self.plazo_dias,
            "activa": self.activa,
        }
