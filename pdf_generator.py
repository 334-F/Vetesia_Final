from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def generar_factura_pdf(pedido, items):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    # Estilos de párrafo personalizados
    style_title = ParagraphStyle(
        name='InvoiceTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#3eb3a0'),
        spaceAfter=6
    )
    style_section = ParagraphStyle(
        name='InvoiceSection',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.HexColor('#4a4a4a'),
        spaceAfter=6,
        spaceBefore=10
    )
    style_body = ParagraphStyle(
        name='InvoiceBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#555555')
    )
    style_body_bold = ParagraphStyle(
        name='InvoiceBodyBold',
        parent=style_body,
        fontName='Helvetica-Bold'
    )
    
    # 1. Cabecera (VetÉsia y metadatos)
    header_data = [
        [
            Paragraph("VETÉSIA S.L.", style_title),
            Paragraph(f"FACTURA: #{pedido['id']}", ParagraphStyle('RightBold', parent=style_title, alignment=2, fontSize=16))
        ],
        [
            Paragraph("Calle de Don Ramón de la Cruz 41, Madrid, España<br/>info@vetesia.com | www.vetesia.com", style_body),
            Paragraph(f"Fecha: {pedido['fecha']}<br/>Estado: PENDIENTE (Cargo B2B)", ParagraphStyle('RightNormal', parent=style_body, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[4.0*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # 2. Datos del cliente
    story.append(Paragraph("DATOS DE FACTURACIÓN B2B", style_section))
    client_data = [
        [Paragraph("<b>Empresa:</b>", style_body), Paragraph(pedido['contacto'], style_body),
         Paragraph("<b>Contacto:</b>", style_body), Paragraph(pedido['contacto'], style_body)],
        [Paragraph("<b>CIF/NIF:</b>", style_body), Paragraph(pedido['cif'], style_body),
         Paragraph("<b>Teléfono:</b>", style_body), Paragraph(pedido['telefono'], style_body)],
        [Paragraph("<b>Dirección:</b>", style_body), Paragraph(pedido['direccion'], style_body),
         Paragraph("<b>C. Postal:</b>", style_body), Paragraph(pedido['codigo_postal'], style_body)],
        [Paragraph("<b>Municipio:</b>", style_body), Paragraph(pedido['municipio'], style_body),
         Paragraph("<b>Zona:</b>", style_body), Paragraph(pedido['zona'], style_body)]
    ]
    client_table = Table(client_data, colWidths=[1.0*inch, 2.75*inch, 1.0*inch, 2.75*inch])
    client_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9f9f9')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#eeeeee')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 20))
    
    # 3. Detalle de productos
    story.append(Paragraph("DETALLES DE LA COMPRA", style_section))
    table_header = [
        Paragraph("<b>Producto</b>", style_body_bold),
        Paragraph("<b>Cantidad</b>", style_body_bold),
        Paragraph("<b>Precio Unitario</b>", style_body_bold),
        Paragraph("<b>Total</b>", style_body_bold)
    ]
    table_rows = [table_header]
    for item in items:
        table_rows.append([
            Paragraph(item['nombre'], style_body),
            Paragraph(str(item['cantidad']), style_body),
            Paragraph(f"{item['precio_unitario']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), style_body),
            Paragraph(f"{item['precio_unitario'] * item['cantidad']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), style_body)
        ])
    
    # 4. Totales
    subtotal = pedido['subtotal']
    iva = pedido['iva']
    total = pedido['total']
    envio = total - subtotal - iva
    
    table_rows.append([Paragraph("", style_body), Paragraph("", style_body), Paragraph("<b>Subtotal:</b>", style_body_bold), Paragraph(f"{subtotal:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), style_body)])
    table_rows.append([Paragraph("", style_body), Paragraph("", style_body), Paragraph("<b>Envío B2B:</b>", style_body_bold), Paragraph(f"{envio:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), style_body)])
    table_rows.append([Paragraph("", style_body), Paragraph("", style_body), Paragraph("<b>IVA (21%):</b>", style_body_bold), Paragraph(f"{iva:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), style_body)])
    table_rows.append([Paragraph("", style_body), Paragraph("", style_body), Paragraph("<b>Total con IVA:</b>", style_body_bold), Paragraph(f"{total:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), style_body_bold)])
    
    products_table = Table(table_rows, colWidths=[4.0*inch, 1.0*inch, 1.25*inch, 1.25*inch])
    products_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1, len(items)), 0.5, colors.HexColor('#eeeeee')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eeeeee')),
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor('#3eb3a0')),
        ('LINEABOVE', (2, -4), (3, -4), 1.0, colors.HexColor('#7ed957')),
        ('BACKGROUND', (2, -1), (3, -1), colors.HexColor('#e8f7f5')),
    ]))
    story.append(products_table)
    story.append(Spacer(1, 20))
    
    # 5. Información bancaria de pago
    story.append(Paragraph("MÉTODO DE COBRO ASOCIADO (TRANSFERENCIA B2B)", style_section))
    bank_data = [
        [Paragraph("<b>Banco:</b>", style_body), Paragraph(pedido['banco'], style_body),
         Paragraph("<b>Titular:</b>", style_body), Paragraph(pedido['titular_cuenta'], style_body)],
        [Paragraph("<b>IBAN de cargo:</b>", style_body), Paragraph(pedido['iban'], style_body),
         Paragraph("<b>Condición:</b>", style_body), Paragraph("Pago diferido por Transferencia B2B", style_body)]
    ]
    bank_table = Table(bank_data, colWidths=[1.25*inch, 2.5*inch, 1.25*inch, 2.5*inch])
    bank_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0fcf9')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#3eb3a0')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(bank_table)
    story.append(Spacer(1, 30))
    
    # 6. Disclaimer legal
    legal_text = (
        "Esta factura B2B se rige por las condiciones de venta oficiales de VETÉSIA S.L. "
        "El cobro correspondiente se procesará de forma automática en la cuenta IBAN facilitada "
        "conforme a los plazos comerciales estipulados para clínicas asociadas. "
        "Para cualquier duda o modificación de datos de facturación, por favor contacte a info@vetesia.com."
    )
    story.append(Paragraph(legal_text, ParagraphStyle('Legal', parent=style_body, fontSize=7, leading=9, textColor=colors.HexColor('#999999'), alignment=1)))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generar_reporte_clientes_pdf(clientes):
    buffer = BytesIO()
    # Tamaño de página horizontal (landscape)
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                            rightMargin=30, leftMargin=30,
                            topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    style_title = ParagraphStyle(
        name='ReportTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#3eb3a0'),
        spaceAfter=4
    )
    style_subtitle = ParagraphStyle(
        name='ReportSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20
    )
    style_th = ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )
    style_td = ParagraphStyle(
        name='TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#4a4a4a')
    )
    
    # 1. Cabecera del Reporte
    story.append(Paragraph("VETÉSIA - REPORTE CONSOLIDADO DE CLIENTES B2B", style_title))
    from datetime import datetime
    current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    story.append(Paragraph(f"Generado el: {current_date} | Confidencial - Solo para uso administrativo interno", style_subtitle))
    
    # 2. Tabla de Clientes
    # Columnas: ID, Empresa, CIF, Contacto, Teléfono, Correo, Banco, IBAN
    headers = [
        Paragraph("<b>ID</b>", style_th),
        Paragraph("<b>Empresa</b>", style_th),
        Paragraph("<b>CIF</b>", style_th),
        Paragraph("<b>Contacto</b>", style_th),
        Paragraph("<b>Teléfono</b>", style_th),
        Paragraph("<b>Correo</b>", style_th),
        Paragraph("<b>Banco</b>", style_th),
        Paragraph("<b>IBAN</b>", style_th)
    ]
    
    table_rows = [headers]
    for idx, c in enumerate(clientes):
        cif = c['cif'] if c['cif'] else '-'
        contacto = c['contacto'] if c['contacto'] else '-'
        telefono = c['telefono'] if c['telefono'] else '-'
        banco = c['banco'] if c['banco'] else '-'
        iban = c['iban'] if c['iban'] else '-'
        
        table_rows.append([
            Paragraph(str(c['id'] or idx + 1), style_td),
            Paragraph(c['nombre_empresa'] or '-', style_td),
            Paragraph(cif, style_td),
            Paragraph(contacto, style_td),
            Paragraph(telefono, style_td),
            Paragraph(c['email'] or '-', style_td),
            Paragraph(banco, style_td),
            Paragraph(iban, style_td)
        ])
        
    # Ancho total: 732 puntos en landscape
    col_widths = [30, 110, 60, 100, 70, 130, 80, 152]
    
    clients_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
    
    table_style = TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3eb3a0')),
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor('#7ed957')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
    ])
    
    for i in range(1, len(table_rows)):
        if i % 2 == 0:
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9f9f9'))
            
    clients_table.setStyle(table_style)
    story.append(clients_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generar_reporte_financiero_pdf(ventas, compras, total_ventas, total_compras, balance_neto):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    style_title = ParagraphStyle(
        name='FinTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#3eb3a0'),
        spaceAfter=6
    )
    style_subtitle = ParagraphStyle(
        name='FinSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=20
    )
    style_section = ParagraphStyle(
        name='FinSection',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#333333'),
        spaceBefore=15,
        spaceAfter=10
    )
    style_th = ParagraphStyle(
        name='FinTH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    style_td = ParagraphStyle(
        name='FinTD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#333333')
    )
    
    # 1. Cabecera del Reporte
    story.append(Paragraph("VETÉSIA - REPORTE FINANCIERO CONSOLIDADO", style_title))
    from datetime import datetime
    current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    story.append(Paragraph(f"Generado el: {current_date} | Ventas, Gastos de Proveedores y Balance de Resultados", style_subtitle))
    
    # 2. Resumen General (KPIs)
    story.append(Paragraph("<b>Balance General de Resultados</b>", style_section))
    
    # Tabla de resumen
    resumen_data = [
        [Paragraph("<b>Concepto</b>", style_th), Paragraph("<b>Total</b>", style_th)],
        [Paragraph("Ingresos por Ventas (Pedidos B2B)", style_td), Paragraph(f"+ {total_ventas:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), style_td)],
        [Paragraph("Gastos de Proveedores (Compras)", style_td), Paragraph(f"- {total_compras:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), style_td)]
    ]
    
    # Balance color indicator
    balance_color = '#28a745' if balance_neto >= 0 else '#dc3545'
    balance_sign = '+' if balance_neto >= 0 else ''
    style_balance_td = ParagraphStyle(
        name='FinBalanceTD',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor(balance_color)
    )
    resumen_data.append([
        Paragraph("<b>BALANCE NETO</b>", style_td),
        Paragraph(f"<b>{balance_sign}{balance_neto:,.2f} €</b>".replace(",", "X").replace(".", ",").replace("X", "."), style_balance_td)
    ])
    
    resumen_table = Table(resumen_data, colWidths=[350, 182])
    resumen_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#3eb3a0')),
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor('#7ed957')),
        ('BACKGROUND', (0,1), (-1,-2), colors.HexColor('#f9f9f9')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#eeeeee')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
    ]))
    story.append(resumen_table)
    story.append(Spacer(1, 15))
    
    # 3. Sección Ventas
    story.append(Paragraph("<b>Detalle de Ingresos (Ventas)</b>", style_section))
    ventas_rows = [
        [Paragraph("<b>Pedido ID</b>", style_th), Paragraph("<b>Fecha</b>", style_th), Paragraph("<b>Empresa / CIF</b>", style_th), Paragraph("<b>Estado</b>", style_th), Paragraph("<b>Monto</b>", style_th)]
    ]
    for v in ventas:
        ventas_rows.append([
            Paragraph(f"#{v['id']}", style_td),
            Paragraph(v['fecha'][:10] if len(v['fecha']) >= 10 else v['fecha'], style_td),
            Paragraph(f"{v['empresa']} (CIF: {v['cif']})", style_td),
            Paragraph(v['estado'].upper(), style_td),
            Paragraph(f"{v['total']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), style_td)
        ])
    
    if len(ventas_rows) == 1:
        ventas_rows.append([Paragraph("No hay ventas registradas.", style_td), "", "", "", ""])
        
    ventas_table = Table(ventas_rows, colWidths=[60, 80, 230, 80, 82])
    ventas_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3eb3a0')),
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor('#7ed957')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
    ]))
    # Add alternating background
    for i in range(1, len(ventas_rows)):
        if i % 2 == 0:
            ventas_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9f9f9'))]))
    story.append(ventas_table)
    story.append(Spacer(1, 15))
    
    # 4. Sección Compras
    story.append(Paragraph("<b>Detalle de Gastos (Proveedores)</b>", style_section))
    compras_rows = [
        [Paragraph("<b>Gasto ID</b>", style_th), Paragraph("<b>Fecha</b>", style_th), Paragraph("<b>Proveedor</b>", style_th), Paragraph("<b>Concepto</b>", style_th), Paragraph("<b>Monto</b>", style_th)]
    ]
    for c in compras:
        compras_rows.append([
            Paragraph(f"#{c['id']}", style_td),
            Paragraph(c['fecha'][:10] if len(c['fecha']) >= 10 else c['fecha'], style_td),
            Paragraph(c['proveedor_nombre'] or 'Proveedor Desconocido', style_td),
            Paragraph(c['concepto'], style_td),
            Paragraph(f"{c['monto']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", "."), style_td)
        ])
        
    if len(compras_rows) == 1:
        compras_rows.append([Paragraph("No hay compras de proveedores registradas.", style_td), "", "", "", ""])
        
    compras_table = Table(compras_rows, colWidths=[60, 80, 130, 180, 82])
    compras_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3eb3a0')),
        ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor('#7ed957')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
    ]))
    for i in range(1, len(compras_rows)):
        if i % 2 == 0:
            compras_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9f9f9'))]))
    story.append(compras_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer
