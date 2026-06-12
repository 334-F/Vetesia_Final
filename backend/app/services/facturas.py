"""
Servicio de generación de facturas PDF.

Usa ReportLab para crear un PDF profesional con la cabecera de VetÉsia,
los datos del cliente, las líneas del pedido y los totales.

La factura se guarda en disco y la ruta se almacena en pedido.factura_url.
"""
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# Colores de marca de VetÉsia
VERDE_PRINCIPAL = colors.HexColor("#7ED957")
AZUL_VERDOSO = colors.HexColor("#3EB3A0")
GRIS_CLARO = colors.HexColor("#F5F5F5")


def generar_factura_pdf(pedido, ruta_destino: str) -> str:
    """
    Genera el PDF de factura de un pedido y lo guarda en ruta_destino.
    Devuelve la ruta del archivo creado.
    """
    os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)

    doc = SimpleDocTemplate(
        ruta_destino,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Factura {pedido.id} - VetÉsia",
        author="VetÉsia",
    )

    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "TituloFactura", parent=styles["Heading1"],
        textColor=AZUL_VERDOSO, fontSize=24, alignment=TA_LEFT, spaceAfter=4
    )
    estilo_subtitulo = ParagraphStyle(
        "Subtitulo", parent=styles["Normal"],
        textColor=colors.grey, fontSize=10, alignment=TA_LEFT, spaceAfter=12
    )
    estilo_seccion = ParagraphStyle(
        "Seccion", parent=styles["Heading3"],
        textColor=AZUL_VERDOSO, fontSize=12, spaceBefore=10, spaceAfter=6
    )
    estilo_normal = ParagraphStyle(
        "Normal", parent=styles["Normal"], fontSize=10, leading=14
    )
    estilo_total = ParagraphStyle(
        "Total", parent=styles["Normal"], fontSize=12,
        fontName="Helvetica-Bold", alignment=TA_RIGHT
    )

    elementos = []

    # --- Cabecera de la factura ---
    elementos.append(Paragraph("VetÉsia", estilo_titulo))
    elementos.append(Paragraph(
        "Productos veterinarios y uniformidad personalizable",
        estilo_subtitulo
    ))

    # Tabla con datos de la empresa y datos de la factura (dos columnas)
    datos_empresa = [
        ["VetÉsia S.L.", ""],
        ["CIF: B-12345678", ""],
        ["Calle Mayor, 1", ""],
        ["28001 Madrid", ""],
        ["info@vetesia.com", ""],
    ]
    datos_factura = [
        ["Factura nº:", f"VE-{pedido.id:06d}"],
        ["Fecha:", pedido.fecha.strftime("%d/%m/%Y")],
        ["Estado:", pedido.estado.replace("_", " ").upper()],
        ["Método de pago:", pedido.metodo_pago.nombre if pedido.metodo_pago else "-"],
        ["Zona de envío:", pedido.zona_envio.nombre if pedido.zona_envio else "-"],
    ]

    tabla_cabecera = Table(
        [
            [_celdas_lista(datos_empresa, estilo_normal),
             _celdas_lista(datos_factura, estilo_normal)]
        ],
        colWidths=[85 * mm, 85 * mm]
    )
    tabla_cabecera.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
    ]))
    elementos.append(tabla_cabecera)
    elementos.append(Spacer(1, 10 * mm))

    # --- Datos del cliente ---
    elementos.append(Paragraph("Datos del cliente", estilo_seccion))
    cliente = pedido.usuario
    direccion = pedido.direccion_envio

    datos_cliente = [
        ["Nombre:", cliente.nombre_completo],
        ["Email:", cliente.email],
        ["Teléfono:", cliente.telefono or "-"],
    ]
    if direccion:
        datos_cliente.append(["Dirección de envío:", direccion.linea_completa()])

    tabla_cliente = Table(datos_cliente, colWidths=[40 * mm, 130 * mm])
    tabla_cliente.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_cliente)
    elementos.append(Spacer(1, 10 * mm))

    # --- Tabla de líneas del pedido ---
    elementos.append(Paragraph("Detalle del pedido", estilo_seccion))

    cabecera = ["Producto", "Personalización", "Cantidad", "P. Unit.", "Subtotal"]
    filas = [cabecera]
    for linea in pedido.lineas:
        nombre_producto = linea.producto.nombre if linea.producto else "(producto eliminado)"
        if linea.tipo_servicio:
            nombre_producto += f"\n[{linea.tipo_servicio.nombre}]"
        filas.append([
            Paragraph(nombre_producto, estilo_normal),
            Paragraph(linea.personalizacion or "-", estilo_normal),
            str(linea.cantidad),
            f"{float(linea.precio_unitario):.2f} €",
            f"{float(linea.subtotal):.2f} €",
        ])

    tabla_lineas = Table(filas, colWidths=[60 * mm, 50 * mm, 20 * mm, 20 * mm, 20 * mm])
    tabla_lineas.setStyle(TableStyle([
        # Cabecera
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_VERDOSO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        # Cuerpo
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla_lineas)
    elementos.append(Spacer(1, 8 * mm))

    # --- Totales ---
    datos_totales = [
        ["Subtotal:", f"{float(pedido.subtotal):.2f} €"],
        ["Coste de envío:", f"{float(pedido.coste_envio):.2f} €"],
    ]
    if float(pedido.descuento) > 0:
        datos_totales.append(["Descuento:", f"-{float(pedido.descuento):.2f} €"])
    datos_totales.append(["TOTAL:", f"{float(pedido.total):.2f} €"])

    tabla_totales = Table(datos_totales, colWidths=[40 * mm, 30 * mm], hAlign="RIGHT")
    tabla_totales.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -2), 10),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BACKGROUND", (0, -1), (-1, -1), VERDE_PRINCIPAL),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elementos.append(tabla_totales)
    elementos.append(Spacer(1, 15 * mm))

    # --- Pie de página ---
    elementos.append(Paragraph(
        "Gracias por confiar en VetÉsia. Para cualquier consulta sobre tu "
        "pedido, escríbenos a soporte@vetesia.com indicando el número de factura.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=9,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))
    elementos.append(Paragraph(
        f"Documento generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle("FooterDate", parent=styles["Normal"], fontSize=8,
                       textColor=colors.lightgrey, alignment=TA_CENTER)
    ))

    doc.build(elementos)
    return ruta_destino


def _celdas_lista(filas, estilo):
    """Convierte una lista de [campo, valor] en una mini-tabla anidada."""
    paragrafos = []
    for fila in filas:
        if isinstance(fila, list) and len(fila) == 2:
            texto = f"<b>{fila[0]}</b> {fila[1]}" if fila[1] else f"<b>{fila[0]}</b>"
            paragrafos.append(Paragraph(texto, estilo))
        else:
            paragrafos.append(Paragraph(str(fila), estilo))
    return paragrafos
