"""
Modelo Resena (reseña).

Valoración (1-5) y texto de un usuario sobre un producto. Soluciona
la crítica de la tutora: las reseñas existen, se guardan en BBDD y
están asociadas a usuario y producto.

Un usuario solo puede dejar una reseña por producto (constraint UNIQUE).
El admin verifica las reseñas antes de que aparezcan públicamente.
"""
from datetime import datetime
from ..extensions import db


class Resena(db.Model):
    __tablename__ = "Resenas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("Usuarios.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("Productos.id"), nullable=False)
    valoracion = db.Column(db.SmallInteger, nullable=False)
    texto = db.Column(db.Text)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    verificada = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (
        db.UniqueConstraint("usuario_id", "producto_id"),
        db.CheckConstraint("valoracion BETWEEN 1 AND 5"),
    )

    usuario = db.relationship("Usuario", back_populates="resenas")
    producto = db.relationship("Producto", back_populates="resenas")

    def verificar(self) -> None:
        self.verificada = True

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "usuario_nombre": self.usuario.nombre if self.usuario else None,
            "producto_id": self.producto_id,
            "valoracion": self.valoracion,
            "texto": self.texto,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "verificada": self.verificada,
        }
