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

    # Orientación horizontal y márgenes finos para maximizar el área útil
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=8*mm,
        leftMargin=8*mm,
        topMargin=8*mm,
        bottomMargin=8*mm
    )

    # Estilos compactos
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=13,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=1*mm,
        spaceBefore=0
    )

    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=11
    )

    elements = []

    # ===== ENCABEZADO COMPACTO =====
    logo_cell = ""
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image(LOGO_PATH, width=28*mm, height=18*mm, kind='proportional')
            logo_cell = logo
        except Exception as e:
            print(f"Error al cargar logo: {e}")

    empresa_info = Paragraph(
        "<b>Canteras La Rufina – TBF SRL</b><br/>"
        "<font size='8'>Ruta C45 – Km 11 – Falda del Carmen · Tel: 351 537-2741</font>",
        ParagraphStyle('EmpresaInfo', parent=styles['Normal'], fontSize=10, leading=12)
    )

    cliente_periodo = Paragraph(
        f"<b>Cliente:</b> {estado_cuenta.empresa_nombre}<br/>"
        f"<b>CUIT:</b> {estado_cuenta.cuit or '-'}  ·  "
        f"<b>Período:</b> {estado_cuenta.fecha_desde.strftime('%d/%m/%Y')} al {estado_cuenta.fecha_hasta.strftime('%d/%m/%Y')}<br/>"
        f"<font size='8' color='#666666'>Emitido: {get_argentina_now().strftime('%d/%m/%Y %H:%M')}</font>",
        info_style
    )

    header_table = Table(
        [[logo_cell, empresa_info, cliente_periodo]],
        colWidths=[32*mm, 110*mm, 135*mm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 2*mm))

    # Título compacto
    elements.append(Paragraph("ESTADO DE CUENTA", title_style))
    elements.append(Spacer(1, 1*mm))

    # ===== TABLA DE MOVIMIENTOS =====
    table_data = [
        ['Fecha', 'Tipo', 'Comprobante', 'Descripción', 'Debe', 'Haber', 'Saldo']
    ]

    # Formatear montos
    def format_monto(monto):
        if monto == 0:
            return "-"
        return f"${monto:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    # Agregar movimientos (descripción más larga ya que tenemos más ancho)
    for mov in estado_cuenta.movimientos:
        table_data.append([
            mov.fecha.strftime('%d/%m/%Y'),
            mov.tipo.upper(),
            mov.numero,
            mov.descripcion[:60] + ('...' if len(mov.descripcion) > 60 else ''),
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

    # Crear tabla. Total ancho ~ 281 / 277mm útiles
    col_widths = [20*mm, 16*mm, 28*mm, 120*mm, 28*mm, 28*mm, 30*mm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Estilos de tabla compactos
    table_style = TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Contenido
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 7),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Fecha
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Tipo
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Comprobante
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),  # Montos

        # Fila de totales
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 8),

        # Bordes finos
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#64748b')),

        # Padding mínimo para fitear más filas
        ('TOPPADDING', (0, 0), (-1, 0), 3),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 3),
        ('TOPPADDING', (0, 1), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 1.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),

        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Alternar colores de fila
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8fafc')]),
    ])
    table.setStyle(table_style)
    elements.append(table)

    # ===== RESUMEN COMPACTO =====
    elements.append(Spacer(1, 3*mm))

    saldo_color = '#dc2626' if estado_cuenta.saldo_final > 0 else '#16a34a'
    saldo_formateado = f"${estado_cuenta.saldo_final:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    resumen_text = (
        f"<font size='10'><b>SALDO ACTUAL: </b></font>"
        f"<font size='12' color='{saldo_color}'><b>{saldo_formateado}</b></font>"
    )

    resumen_style = ParagraphStyle(
        'ResumenStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_RIGHT
    )
    elements.append(Paragraph(resumen_text, resumen_style))

    # Pie compacto
    elements.append(Spacer(1, 2*mm))
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.gray
    )
    elements.append(Paragraph(
        f"Sistema de Gestión - Canteras La Rufina · Generado el {get_argentina_now().strftime('%d/%m/%Y %H:%M:%S')}",
        footer_style
    ))

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
