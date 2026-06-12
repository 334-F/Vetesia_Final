"""
Modelo Promocion.

Permite definir descuentos temporales (Black Friday, rebajas de verano)
aplicables a un producto concreto, a una categoría entera o globales.
"""
from datetime import datetime
from ..extensions import db


class Promocion(db.Model):
    __tablename__ = "Promociones"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Enum("porcentaje", "fijo"), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_inicio = db.Column(db.DateTime, nullable=False)
    fecha_fin = db.Column(db.DateTime, nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("Productos.id"), nullable=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("Categorias.id"), nullable=True)
    activa = db.Column(db.Boolean, nullable=False, default=True)

    producto = db.relationship("Producto", back_populates="promociones")
    categoria = db.relationship("Categoria", back_populates="promociones")

    def esta_activa(self, fecha: datetime = None) -> bool:
        """Comprueba si la promoción está vigente en una fecha (por defecto ahora)."""
        if not self.activa:
            return False
        if fecha is None:
            fecha = datetime.utcnow()
        return self.fecha_inicio <= fecha <= self.fecha_fin

    def calcular_descuento(self, precio: float) -> float:
        """Devuelve la cantidad de descuento a aplicar sobre un precio dado."""
        if self.tipo == "porcentaje":
            return round(precio * float(self.valor) / 100, 2)
        return float(self.valor)

    def aplica_a_producto(self, producto) -> bool:
        """Comprueba si esta promoción se aplica a un producto concreto."""
        if self.producto_id and self.producto_id == producto.id:
            return True
        if self.categoria_id and self.categoria_id == producto.categoria_id:
            return True
        if self.producto_id is None and self.categoria_id is None:
            return True  # promoción global
        return False

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "valor": float(self.valor),
            "fecha_inicio": self.fecha_inicio.isoformat(),
            "fecha_fin": self.fecha_fin.isoformat(),
            "producto_id": self.producto_id,
            "categoria_id": self.categoria_id,
            "activa": self.activa,
            "vigente_ahora": self.esta_activa(),
        }
