"""
Modelo DireccionEnvio.

Resuelve la crítica de la tutora: la dirección del usuario y la
dirección de envío son cosas distintas. Aquí guardamos varias
direcciones por usuario y cada pedido referencia la concreta usada.
"""
from ..extensions import db


class DireccionEnvio(db.Model):
    __tablename__ = "DireccionesEnvio"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("Usuarios.id"), nullable=False, index=True)
    alias = db.Column(db.String(50), nullable=False)
    destinatario = db.Column(db.String(150), nullable=False)
    calle = db.Column(db.String(200), nullable=False)
    numero = db.Column(db.String(10))
    piso = db.Column(db.String(20))
    codigo_postal = db.Column(db.String(10), nullable=False)
    municipio = db.Column(db.String(100), nullable=False)
    provincia = db.Column(db.String(100), nullable=False)
    telefono_contacto = db.Column(db.String(15))
    predeterminada = db.Column(db.Boolean, nullable=False, default=False)

    usuario = db.relationship("Usuario", back_populates="direcciones")
    pedidos = db.relationship("Pedido", back_populates="direccion_envio")

    def linea_completa(self) -> str:
        """Devuelve la dirección como una línea de texto (útil para PDF)."""
        partes = [self.calle]
        if self.numero:
            partes.append(self.numero)
        if self.piso:
            partes.append(self.piso)
        return ", ".join(partes) + f", {self.codigo_postal} {self.municipio} ({self.provincia})"

    def to_dict(self):
        return {
            "id": self.id,
            "alias": self.alias,
            "destinatario": self.destinatario,
            "calle": self.calle,
            "numero": self.numero,
            "piso": self.piso,
            "codigo_postal": self.codigo_postal,
            "municipio": self.municipio,
            "provincia": self.provincia,
            "telefono_contacto": self.telefono_contacto,
            "predeterminada": self.predeterminada,
        }
