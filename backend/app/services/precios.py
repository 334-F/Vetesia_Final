"""
Servicio de cálculo de precios.

Centraliza la lógica de aplicar:
  1. Precio escalado por cantidad (si el producto tiene)
  2. Promociones activas (por producto o categoría)
  3. Descuento por tipo de cliente (particular vs profesional)

Esto está en un servicio aparte para que los endpoints solo se ocupen
de la parte HTTP. Si el día de mañana cambian las reglas de negocio,
se modifican aquí.
"""
from datetime import datetime
from ..models import Promocion


class CalculadoraPrecios:
    """Calcula el precio final de una línea de pedido."""

    def __init__(self, producto, cantidad: int, tipo_servicio=None, usuario=None):
        self.producto = producto
        self.cantidad = cantidad
        self.tipo_servicio = tipo_servicio
        self.usuario = usuario
        self.detalle = {}  # explicación del cálculo (útil para mostrar al usuario)

    def calcular(self) -> float:
        """Devuelve el subtotal final de la línea."""
        # 1. Precio unitario base (con escalado si aplica)
        precio_unit = self.producto.precio_por_cantidad(self.cantidad)
        self.detalle["precio_base"] = float(self.producto.precio_base)
        self.detalle["precio_escalado"] = precio_unit

        # 2. Aplicar promoción si hay alguna activa
        descuento_promo = 0.0
        promo_activa = self._buscar_promocion_activa()
        if promo_activa:
            descuento_promo = promo_activa.calcular_descuento(precio_unit)
            precio_unit -= descuento_promo
            self.detalle["promocion"] = {
                "id": promo_activa.id,
                "nombre": promo_activa.nombre,
                "descuento_unitario": descuento_promo,
            }

        # 3. Coste extra del servicio de personalización (si aplica)
        extra_servicio = 0.0
        if self.tipo_servicio:
            extra_servicio = float(self.tipo_servicio.precio_extra)
            precio_unit += extra_servicio
            self.detalle["servicio_extra"] = extra_servicio

        # 4. Descuento por tipo de cliente
        if self.usuario and self.usuario.tipo_cliente and self.usuario.tipo_cliente.descuento > 0:
            desc_tc = float(self.usuario.tipo_cliente.descuento)
            precio_unit *= (1 - desc_tc / 100)
            self.detalle["descuento_tipo_cliente"] = desc_tc

        precio_unit = round(precio_unit, 2)
        subtotal = round(precio_unit * self.cantidad, 2)
        self.detalle["precio_unitario_final"] = precio_unit
        self.detalle["subtotal"] = subtotal
        return subtotal

    def _buscar_promocion_activa(self):
        """Busca la promoción más beneficiosa aplicable al producto."""
        ahora = datetime.utcnow()
        candidatas = Promocion.query.filter(
            Promocion.activa == True,
            Promocion.fecha_inicio <= ahora,
            Promocion.fecha_fin >= ahora,
        ).all()
        aplicables = [p for p in candidatas if p.aplica_a_producto(self.producto)]
        if not aplicables:
            return None
        # Devolvemos la que más descuento aplique
        precio = float(self.producto.precio_base)
        return max(aplicables, key=lambda p: p.calcular_descuento(precio))


def calcular_totales_pedido(lineas, zona_envio) -> dict:
    """
    Calcula los totales de un pedido a partir de una lista de líneas
    ya con sus subtotales. Añade el coste de envío.

    Devuelve un dict con: subtotal, coste_envio, descuento, total.
    """
    subtotal = sum(float(l.subtotal) for l in lineas)
    coste_envio = float(zona_envio.coste_envio) if zona_envio else 0
    descuento = 0  # el descuento ya está aplicado dentro de cada línea
    total = round(subtotal + coste_envio - descuento, 2)
    return {
        "subtotal": round(subtotal, 2),
        "coste_envio": round(coste_envio, 2),
        "descuento": round(descuento, 2),
        "total": total,
    }
