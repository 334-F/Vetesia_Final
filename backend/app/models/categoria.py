"""
Modelo Categoria.

Jerarquía simple padre-hijo (autorrelacionada). Permite tener
categorías y subcategorías sin complicar el esquema.
"""
from ..extensions import db


class Categoria(db.Model):
    __tablename__ = "Categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    categoria_padre_id = db.Column(db.Integer, db.ForeignKey("Categorias.id"), nullable=True, index=True)
    imagen_url = db.Column(db.String(255))
    activa = db.Column(db.Boolean, nullable=False, default=True)

    # Autorrelación
    subcategorias = db.relationship(
        "Categoria",
        backref=db.backref("padre", remote_side=[id]),
        lazy="select"
    )
    productos = db.relationship("Producto", back_populates="categoria")
    promociones = db.relationship("Promocion", back_populates="categoria")

    def to_dict(self, incluir_subcategorias: bool = False):
        data = {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "categoria_padre_id": self.categoria_padre_id,
            "imagen_url": self.imagen_url,
            "activa": self.activa,
        }
        if incluir_subcategorias:
            data["subcategorias"] = [s.to_dict() for s in self.subcategorias]
        return data
