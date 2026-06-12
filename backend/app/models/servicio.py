"""
Modelo TipoServicio.

Servicios de personalización para los productos de uniformidad:
- Estándar: DTG sin extras
- Premium DTG: DTG con revisión manual y etiquetado
- Premium Bordado: Bordado con producción prioritaria
"""
from ..extensions import db


class TipoServicio(db.Model):
    __tablename__ = "TiposServicio"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    precio_extra = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    dtg = db.Column(db.Boolean, nullable=False, default=False)
    bordado = db.Column(db.Boolean, nullable=False, default=False)
    revision_manual = db.Column(db.Boolean, nullable=False, default=False)
    etiquetado = db.Column(db.Boolean, nullable=False, default=False)
    produccion_prioritaria = db.Column(db.Boolean, nullable=False, default=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    lineas_pedido = db.relationship("LineaPedido", back_populates="tipo_servicio")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "precio_extra": float(self.precio_extra),
            "dtg": self.dtg,
            "bordado": self.bordado,
            "revision_manual": self.revision_manual,
            "etiquetado": self.etiquetado,
            "produccion_prioritaria": self.produccion_prioritaria,
            "activo": self.activo,
        }
