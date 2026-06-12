"""
Servicio de integración con Stripe.

En modo test, Stripe permite probar el flujo completo de cobro con
tarjetas ficticias (la más conocida: 4242 4242 4242 4242).
La clave API se configura en .env como STRIPE_SECRET_KEY.

Flujo:
  1. Cuando el cliente confirma el pedido con método=tarjeta,
     creamos un PaymentIntent en Stripe.
  2. El frontend recibe el client_secret y completa el pago.
  3. Stripe nos notifica vía webhook cuando el pago se confirma.
  4. Al confirmarse, marcamos el pedido como 'pagado'.
"""
import stripe
from flask import current_app


def init_stripe():
    """Inicializa Stripe con la clave configurada."""
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]


def crear_payment_intent(pedido) -> dict:
    """
    Crea un PaymentIntent en Stripe para el pedido y devuelve los
    datos necesarios para que el frontend complete el cobro.
    """
    init_stripe()
    # Stripe trabaja con la cantidad mínima (céntimos)
    cantidad_centimos = int(round(float(pedido.total) * 100))
    intent = stripe.PaymentIntent.create(
        amount=cantidad_centimos,
        currency="eur",
        metadata={
            "pedido_id": pedido.id,
            "usuario_id": pedido.usuario_id,
            "email": pedido.usuario.email if pedido.usuario else "",
        },
        description=f"Pedido VetÉsia #{pedido.id}",
        receipt_email=pedido.usuario.email if pedido.usuario else None,
    )
    return {
        "client_secret": intent.client_secret,
        "payment_intent_id": intent.id,
        "publishable_key": current_app.config["STRIPE_PUBLISHABLE_KEY"],
    }


def confirmar_webhook(payload: bytes, sig_header: str):
    """
    Valida la firma del webhook de Stripe y devuelve el evento.
    Lanza ValueError si la firma no es válida.
    """
    init_stripe()
    secret = current_app.config["STRIPE_WEBHOOK_SECRET"]
    try:
        evento = stripe.Webhook.construct_event(payload, sig_header, secret)
        return evento
    except (stripe.error.SignatureVerificationError, ValueError) as e:
        raise ValueError(f"Webhook inválido: {e}")


def reembolsar_pago(transaction_id: str) -> dict:
    """Crea un reembolso completo en Stripe."""
    init_stripe()
    refund = stripe.Refund.create(payment_intent=transaction_id)
    return {"refund_id": refund.id, "status": refund.status}
