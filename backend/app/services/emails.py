"""
Servicio de envío de emails.

Usa Flask-Mail con un servidor SMTP (configurable). Las plantillas
son inline para simplificar.
"""
from flask import current_app
from flask_mail import Message
from ..extensions import mail


def enviar_email_confirmacion_pedido(pedido, adjuntar_pdf: bool = True):
    """
    Envía email de confirmación al cliente con el PDF de la factura adjunto.
    """
    cliente = pedido.usuario
    if not cliente or not cliente.email:
        return

    asunto = f"VetÉsia - Confirmación de pedido #{pedido.id}"
    cuerpo = f"""
Hola {cliente.nombre},

Hemos recibido tu pedido #{pedido.id} correctamente.

Resumen:
- Productos: {len(pedido.lineas)} líneas
- Subtotal: {float(pedido.subtotal):.2f} €
- Envío: {float(pedido.coste_envio):.2f} €
- Total: {float(pedido.total):.2f} €

Estado actual: {pedido.estado.replace('_', ' ').upper()}
Dirección de envío: {pedido.direccion_envio.linea_completa() if pedido.direccion_envio else '-'}

Adjuntamos la factura en PDF.

Gracias por confiar en VetÉsia.
"""

    msg = Message(
        subject=asunto,
        recipients=[cliente.email],
        body=cuerpo.strip(),
    )

    if adjuntar_pdf and pedido.factura_url:
        try:
            with open(pedido.factura_url, "rb") as f:
                msg.attach(
                    filename=f"factura_VE-{pedido.id:06d}.pdf",
                    content_type="application/pdf",
                    data=f.read(),
                )
        except FileNotFoundError:
            current_app.logger.warning(
                f"No se ha encontrado la factura {pedido.factura_url} para adjuntar"
            )

    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Error al enviar email: {e}")


def enviar_email_cambio_estado(pedido):
    """Notifica al cliente cuando cambia el estado del pedido."""
    cliente = pedido.usuario
    if not cliente or not cliente.email:
        return

    asunto = f"VetÉsia - Tu pedido #{pedido.id} ha cambiado de estado"
    cuerpo = f"""
Hola {cliente.nombre},

Te informamos de que tu pedido #{pedido.id} se encuentra ahora en estado:

  {pedido.estado.replace('_', ' ').upper()}

Puedes consultar el detalle en tu zona de cliente en cualquier momento.

Gracias por confiar en VetÉsia.
"""
    msg = Message(subject=asunto, recipients=[cliente.email], body=cuerpo.strip())
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Error al enviar email: {e}")
