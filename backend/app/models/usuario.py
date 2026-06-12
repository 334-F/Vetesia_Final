"""
Modelo Usuario y TipoCliente.

Decisión de diseño: tenemos una sola tabla Usuarios con un campo `rol`
('cliente' o 'admin') en lugar de dos tablas separadas. Esto evita
duplicar columnas comunes (nombre, email, password) y simplifica el
login: hay un solo punto de entrada para todos los usuarios.

La distinción Cliente / Administrador del diagrama de clases se
implementa con polimorfismo a nivel de aplicación (decoradores que
comprueban el rol) en lugar de herencia en BBDD.
"""
import bcrypt
from datetime import datetime
from ..extensions import db


class TipoCliente(db.Model):
    __tablename__ = "TiposCliente"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    descuento = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    usuarios = db.relationship("Usuario", back_populates="tipo_cliente")

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "descuento": float(self.descuento),
            "activo": self.activo,
        }


class Usuario(db.Model):
    __tablename__ = "Usuarios"

    id = db.Column(db.Integer, primary_key=True)
    tipo_cliente_id = db.Column(db.Integer, db.ForeignKey("TiposCliente.id"), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # NULL para invitados (compran sin cuenta)
    telefono = db.Column(db.String(15))
    direccion = db.Column(db.String(200))
    rol = db.Column(db.Enum("cliente", "admin", "invitado"), nullable=False, default="cliente")
    fecha_registro = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    activo = db.Column(db.Boolean, nullable=False, default=True)

    # Relaciones
    tipo_cliente = db.relationship("TipoCliente", back_populates="usuarios")
    direcciones = db.relationship("DireccionEnvio", back_populates="usuario", cascade="all, delete-orphan")
    pedidos = db.relationship("Pedido", back_populates="usuario")
    resenas = db.relationship("Resena", back_populates="usuario", cascade="all, delete-orphan")

    # --- Métodos de contraseña ---

    def set_password(self, plain_password: str) -> None:
        """Hashea la contraseña con bcrypt antes de guardar."""
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, plain_password: str) -> bool:
        """Compara una contraseña en claro con el hash almacenado.

        Los invitados no tienen contraseña (password_hash = NULL), así que
        nunca pueden iniciar sesión: devolvemos False directamente.
        """
        if not self.password_hash:
            return False
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )

    # --- Helpers ---

    @property
    def es_admin(self) -> bool:
        return self.rol == "admin"

    @property
    def es_invitado(self) -> bool:
        return self.rol == "invitado"

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellidos}".strip()

    def to_dict(self, incluir_sensible: bool = False) -> dict:
        """Serializa el usuario. Por defecto no incluye datos sensibles."""
        data = {
            "id": self.id,
            "nombre": self.nombre,
            "apellidos": self.apellidos,
            "email": self.email,
            "telefono": self.telefono,
            "direccion": self.direccion,
            "rol": self.rol,
            "tipo_cliente": self.tipo_cliente.nombre if self.tipo_cliente else None,
            "fecha_registro": self.fecha_registro.isoformat() if self.fecha_registro else None,
            "activo": self.activo,
        }
        return data