"""
Generación de PDFs para Facturación
"""
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from decimal import Decimal

from app.schemas.factura import EstadoCuentaCliente
from app.models.base import get_argentina_now

# Ruta al logo
LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'logo_la_rufina.png')


def generar_estado_cuenta_pdf(estado_cuenta: EstadoCuentaCliente) -> BytesIO:
    """
    Genera un PDF con el estado de cuenta del cliente

    Args:
        estado_cuenta: Datos del estado de cuenta

    Returns:
        BytesIO con el PDF generado
    """
    buffer = BytesIO()

    # Usar orientación horizontal para más espacio
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    # Estilos
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=5*mm
    )

    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=3*mm,
        textColor=colors.HexColor('#444444')
    )

    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14
    )

    elements = []

    # ===== ENCABEZADO =====
    # Logo y datos empresa
    header_data = []

    logo_cell = ""
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image(LOGO_PATH, width=40*mm, height=30*mm, kind='proportional')
            logo_cell = logo
        except Exception as e:
            print(f"Error al cargar logo: {e}")

    empresa_info = Paragraph(
        "<b>Canteras La Rufina – TBF SRL</b><br/>"
        "<font size='10'>Ruta C45 – Km 11 – Falda del Carmen</font><br/>"
        "<font size='10'>Tel: 351 537-2741</font>",
        ParagraphStyle('EmpresaInfo', parent=styles['Normal'], fontSize=12, leading=16)
    )

    fecha_emision = Paragraph(
        f"<b>Fecha emisión:</b> {get_argentina_now().strftime('%d/%m/%Y %H:%M')}",
        info_style
    )

    header_table = Table(
        [[logo_cell, empresa_info, fecha_emision]],
        colWidths=[45*mm, 140*mm, 70*mm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8*mm))

    # Título
    elements.append(Paragraph("ESTADO DE CUENTA", title_style))

    # Datos del cliente
    cliente_info = f"""
    <b>Cliente:</b> {estado_cuenta.empresa_nombre}<br/>
    <b>CUIT:</b> {estado_cuenta.cuit or '-'}<br/>
    <b>Período:</b> {estado_cuenta.fecha_desde.strftime('%d/%m/%Y')} al {estado_cuenta.fecha_hasta.strftime('%d/%m/%Y')}
    """
    elements.append(Paragraph(cliente_info, info_style))
    elements.append(Spacer(1, 8*mm))

    # ===== TABLA DE MOVIMIENTOS =====
    # Encabezados
    table_data = [
        ['Fecha', 'Tipo', 'Comprobante', 'Descripción', 'Debe', 'Haber', 'Saldo']
    ]

    # Formatear montos
    def format_monto(monto):
        if monto == 0:
            return "-"
        return f"${monto:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Agregar movimientos
    for mov in estado_cuenta.movimientos:
        table_data.append([
            mov.fecha.strftime('%d/%m/%Y'),
            mov.tipo.upper(),
            mov.numero,
            mov.descripcion[:40] + ('...' if len(mov.descripcion) > 40 else ''),
            format_monto(mov.debe),
            format_monto(mov.haber),
            format_monto(mov.saldo)
        ])

    # Fila de totales
    total_debe = sum(m.debe for m in estado_cuenta.movimientos)
    total_haber = sum(m.haber for m in estado_cuenta.movimientos)

    table_data.append([
        '', '', '', 'TOTALES',
        format_monto(total_debe),
        format_monto(total_haber),
        format_monto(estado_cuenta.saldo_final)
    ])

    # Crear tabla
    col_widths = [22*mm, 18*mm, 30*mm, 90*mm, 28*mm, 28*mm, 32*mm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Estilos de tabla
    table_style = TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Contenido
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 9),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Fecha
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Tipo
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Montos

        # Fila de totales
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 10),

        # Bordes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#64748b')),

        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),

        # Alternar colores de fila
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8fafc')]),
    ])
    table.setStyle(table_style)
    elements.append(table)

    # ===== RESUMEN =====
    elements.append(Spacer(1, 10*mm))

    saldo_color = '#dc2626' if estado_cuenta.saldo_final > 0 else '#16a34a'
    resumen_text = f"""
    <font size='12'><b>SALDO ACTUAL: </b></font>
    <font size='14' color='{saldo_color}'><b>${estado_cuenta.saldo_final:,.2f}</b></font>
    """.replace(',', 'X').replace('.', ',').replace('X', '.')

    resumen_style = ParagraphStyle(
        'ResumenStyle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_RIGHT
    )
    elements.append(Paragraph(resumen_text, resumen_style))

    # Pie de página
    elements.append(Spacer(1, 15*mm))
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.gray
    )
    elements.append(Paragraph("Sistema de Gestión - Canteras La Rufina", footer_style))
    elements.append(Paragraph(f"Documento generado el {get_argentina_now().strftime('%d/%m/%Y %H:%M:%S')}", footer_style))

    # Construir PDF
    doc.build(elements)

    buffer.seek(0)
    return buffer


def generar_factura_pdf(factura_data: dict) -> BytesIO:
    """
    Genera un PDF de factura

    Args:
        factura_data: Diccionario con datos de la factura

    Returns:
        BytesIO con el PDF generado
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    elements = []

    # Similar estructura al estado de cuenta pero con datos de factura
    # ... (implementar según necesidades)

    # Por ahora retornar buffer vacío
    doc.build(elements)
    buffer.seek(0)
    return buffer
