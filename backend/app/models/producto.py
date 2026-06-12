"""
Modelos Producto y PrecioEscalado.

Producto soporta dos tipos:
- estandar: producto de catálogo veterinario normal (alimentación, etc.)
- personalizable: uniformidad veterinaria con servicios de personalización

PrecioEscalado permite aplicar descuentos por cantidad: por ejemplo,
3-5 unidades a 22.95€, 6-9 unidades a 20.95€, 10+ unidades a 18.95€.
"""
from ..extensions import db


class Producto(db.Model):
    __tablename__ = "Productos"

    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey("Categorias.id"), nullable=False, index=True)
    nombre = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=True)
    especificaciones_json = db.Column(db.Text, nullable=True)
    descripcion = db.Column(db.Text)
    tipo = db.Column(db.Enum("estandar", "personalizable"), nullable=False, default="estandar")
    precio_base = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=5)
    imagen_url = db.Column(db.String(255))
    activo = db.Column(db.Boolean, nullable=False, default=True, index=True)
    fecha_alta = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    # Relaciones
    categoria = db.relationship("Categoria", back_populates="productos")
    precios_escalados = db.relationship("PrecioEscalado", back_populates="producto", cascade="all, delete-orphan")
    promociones = db.relationship("Promocion", back_populates="producto")
    lineas_pedido = db.relationship("LineaPedido", back_populates="producto")
    resenas = db.relationship("Resena", back_populates="producto", cascade="all, delete-orphan")
    proveedores = db.relationship("ProductoProveedor", back_populates="producto", cascade="all, delete-orphan")

    # --- Lógica de negocio ---

    def verificar_stock(self, cantidad: int) -> bool:
        """Devuelve True si hay stock suficiente."""
        return self.stock >= cantidad

    def actualizar_stock(self, cantidad_delta: int) -> None:
        """
        Modifica el stock. Positivo suma (reposición), negativo resta (venta).
        Lanza ValueError si el resultado sería negativo.
        """
        nuevo = self.stock + cantidad_delta
        if nuevo < 0:
            raise ValueError(f"Stock insuficiente para {self.nombre}")
        self.stock = nuevo

    def stock_bajo(self) -> bool:
        return self.stock <= self.stock_minimo

    def precio_por_cantidad(self, cantidad: int) -> float:
        """
        Calcula el precio unitario aplicando precios escalados si existen.
        Si no hay escalado aplicable, devuelve el precio_base.
        """
        for franja in self.precios_escalados:
            if cantidad >= franja.cantidad_min and (
                franja.cantidad_max is None or cantidad <= franja.cantidad_max
            ):
                return float(franja.precio_unitario)
        return float(self.precio_base)

    def valoracion_media(self) -> float:
        """Media de valoración de las reseñas verificadas."""
        verificadas = [r for r in self.resenas if r.verificada]
        if not verificadas:
            return 0.0
        return sum(r.valoracion for r in verificadas) / len(verificadas)

    def to_dict(self, incluir_resenas: bool = False):
        data = {
            "id": self.id,
            "nombre": self.nombre,
            "slug": self.slug,
            "especificaciones_json": self.especificaciones_json,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "precio_base": float(self.precio_base),
            "stock": self.stock,
            "imagen_url": self.imagen_url,
            "activo": self.activo,
            "categoria_id": self.categoria_id,
            "categoria_nombre": self.categoria.nombre if self.categoria else None,
            "valoracion_media": round(self.valoracion_media(), 2),
            "num_resenas": len([r for r in self.resenas if r.verificada]),
            "precios_escalados": [pe.to_dict() for pe in self.precios_escalados],
        }
        if incluir_resenas:
            data["resenas"] = [r.to_dict() for r in self.resenas if r.verificada]
        return data


class PrecioEscalado(db.Model):
    __tablename__ = "PreciosEscalados"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("Productos.id"), nullable=False, index=True)
    cantidad_min = db.Column(db.Integer, nullable=False)
    cantidad_max = db.Column(db.Integer, nullable=True)  # NULL = sin límite superior
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    producto = db.relationship("Producto", back_populates="precios_escalados")

    def to_dict(self):
        return {
            "cantidad_min": self.cantidad_min,
            "cantidad_max": self.cantidad_max,
            "precio_unitario": float(self.precio_unitario),
        }
