"""
Servicio para generación de PDFs de reportes
"""
import os
from io import BytesIO
from datetime import date
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.services import reportes_service
from app.models.base import get_argentina_now

# Ruta al logo
LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'logo_la_rufina.png')


def _format_number(value, decimals=2):
    """Formatea un número con separadores de miles"""
    if value is None:
        return "-"
    try:
        num = float(value)
        if decimals == 0:
            return f"{int(num):,}".replace(",", ".")
        return f"{num:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(value)


def _format_currency(value):
    """Formatea un valor como moneda"""
    return f"${_format_number(value, 2)}"


def _get_styles():
    """Obtiene los estilos para el PDF"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        'TituloReporte',
        parent=styles['Heading1'],
        fontSize=18,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=10*mm,
        textColor=colors.HexColor('#1a1a1a')
    ))

    styles.add(ParagraphStyle(
        'Subtitulo',
        parent=styles['Heading2'],
        fontSize=14,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        spaceBefore=8*mm,
        spaceAfter=4*mm,
        textColor=colors.HexColor('#333333')
    ))

    styles.add(ParagraphStyle(
        'Periodo',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=8*mm,
        textColor=colors.HexColor('#666666')
    ))

    styles.add(ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT,
        spaceBefore=4*mm
    ))

    return styles


def _crear_encabezado(elements, styles, titulo: str, fecha_desde: date, fecha_hasta: date):
    """Crea el encabezado común para todos los reportes"""

    # Logo y título
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image(LOGO_PATH, width=40*mm, height=30*mm, kind='proportional')
            elements.append(logo)
            elements.append(Spacer(1, 5*mm))
        except:
            pass

    elements.append(Paragraph("Canteras La Rufina - TBF SRL", styles['TituloReporte']))
    elements.append(Paragraph(titulo, styles['Subtitulo']))
    elements.append(Paragraph(
        f"Período: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}",
        styles['Periodo']
    ))


def _crear_pie_pagina(elements, styles):
    """Crea el pie de página"""
    elements.append(Spacer(1, 10*mm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.gray
    )
    elements.append(Paragraph(
        f"Generado: {get_argentina_now().strftime('%d/%m/%Y %H:%M')} - Sistema de Gestión Canteras La Rufina",
        footer_style
    ))


def _estilo_tabla_base():
    """Retorna el estilo base para las tablas"""
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90d9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),

        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ])


def generar_pdf_resumen(db: Session, fecha_desde: date, fecha_hasta: date) -> BytesIO:
    """Genera PDF del resumen general"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = _get_styles()
    elements = []

    # Obtener datos
    resumen = reportes_service.obtener_resumen_general(db, fecha_desde, fecha_hasta)

    # Encabezado
    _crear_encabezado(elements, styles, "RESUMEN GENERAL", fecha_desde, fecha_hasta)

    # Ventas
    elements.append(Paragraph("Ventas", styles['Subtitulo']))
    ventas_data = [
        ['Concepto', 'Valor'],
        ['Cantidad de Pesajes', str(resumen.cantidad_pesajes)],
        ['Total Kilogramos', f"{_format_number(resumen.total_kg, 0)} kg"],
        ['Total Toneladas', f"{_format_number(resumen.total_toneladas, 2)} tn"],
        ['Importe Total', _format_currency(resumen.importe_total_ventas)],
    ]
    tabla_ventas = Table(ventas_data, colWidths=[100*mm, 60*mm])
    tabla_ventas.setStyle(_estilo_tabla_base())
    elements.append(tabla_ventas)

    # Gastos
    elements.append(Paragraph("Gastos", styles['Subtitulo']))
    gastos_data = [
        ['Categoría', 'Monto'],
        ['Combustible', _format_currency(resumen.gasto_combustible)],
        ['Servicios/Mantenimiento', _format_currency(resumen.gasto_servicios)],
        ['Repuestos', _format_currency(resumen.gasto_repuestos)],
        ['TOTAL GASTOS', _format_currency(resumen.total_gastos)],
    ]
    tabla_gastos = Table(gastos_data, colWidths=[100*mm, 60*mm])
    estilo_gastos = _estilo_tabla_base()
    estilo_gastos.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    estilo_gastos.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8'))
    tabla_gastos.setStyle(estilo_gastos)
    elements.append(tabla_gastos)

    # Destacados
    elements.append(Paragraph("Destacados", styles['Subtitulo']))
    destacados_data = [
        ['Máquinas Activas', str(resumen.maquinas_activas)],
    ]
    if resumen.cliente_top_nombre:
        destacados_data.append(['Cliente Top', f"{resumen.cliente_top_nombre} ({_format_number(resumen.cliente_top_kg, 0)} kg)"])
    if resumen.material_top_nombre:
        destacados_data.append(['Material Top', f"{resumen.material_top_nombre} ({_format_number(resumen.material_top_kg, 0)} kg)"])

    tabla_dest = Table(destacados_data, colWidths=[80*mm, 80*mm])
    tabla_dest.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))
    elements.append(tabla_dest)

    _crear_pie_pagina(elements, styles)
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generar_pdf_ventas_material(db: Session, fecha_desde: date, fecha_hasta: date) -> BytesIO:
    """Genera PDF de ventas por material"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = _get_styles()
    elements = []

    # Obtener datos
    reporte = reportes_service.obtener_ventas_por_material(db, fecha_desde, fecha_hasta)

    # Encabezado
    _crear_encabezado(elements, styles, "VENTAS POR TIPO DE MATERIAL", fecha_desde, fecha_hasta)

    # Tabla de materiales
    data = [['Material', 'Pesajes', 'Kg', 'Toneladas', 'Importe', '$/kg']]
    for m in reporte.materiales:
        data.append([
            m.material,
            str(m.cantidad_pesajes),
            _format_number(m.total_kg, 0),
            _format_number(m.total_toneladas, 2),
            _format_currency(m.importe_total),
            _format_currency(m.precio_promedio)
        ])

    # Fila de totales
    data.append([
        'TOTAL',
        str(reporte.cantidad_pesajes),
        _format_number(reporte.total_kg, 0),
        _format_number(reporte.total_toneladas, 2),
        _format_currency(reporte.total_importe),
        ''
    ])

    tabla = Table(data, colWidths=[45*mm, 20*mm, 30*mm, 25*mm, 30*mm, 20*mm])
    estilo = _estilo_tabla_base()
    estilo.add('ALIGN', (1, 1), (-1, -1), 'RIGHT')
    estilo.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    estilo.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8'))
    tabla.setStyle(estilo)
    elements.append(tabla)

    _crear_pie_pagina(elements, styles)
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generar_pdf_ventas_semanal(db: Session, fecha_desde: date, fecha_hasta: date, material: Optional[str] = None) -> BytesIO:
    """Genera PDF de ventas semanales"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = _get_styles()
    elements = []

    # Obtener datos
    reporte = reportes_service.obtener_ventas_semanales(db, fecha_desde, fecha_hasta, material)

    # Encabezado
    titulo = "VENTAS SEMANALES"
    if material:
        titulo += f" - {material}"
    _crear_encabezado(elements, styles, titulo, fecha_desde, fecha_hasta)

    # Tabla de semanas
    data = [['Semana', 'Período', 'Pesajes', 'Kg', 'Toneladas', 'Importe']]
    for s in reporte.semanas:
        data.append([
            f"S{s.semana}/{s.anio}",
            f"{s.fecha_inicio.strftime('%d/%m')} - {s.fecha_fin.strftime('%d/%m')}",
            str(s.cantidad_pesajes),
            _format_number(s.total_kg, 0),
            _format_number(s.total_toneladas, 2),
            _format_currency(s.importe_total)
        ])

    # Fila de totales
    data.append([
        'TOTAL',
        '',
        str(sum(s.cantidad_pesajes for s in reporte.semanas)),
        _format_number(reporte.total_kg, 0),
        _format_number(reporte.total_toneladas, 2),
        _format_currency(reporte.total_importe)
    ])

    tabla = Table(data, colWidths=[25*mm, 35*mm, 20*mm, 30*mm, 25*mm, 30*mm])
    estilo = _estilo_tabla_base()
    estilo.add('ALIGN', (2, 1), (-1, -1), 'RIGHT')
    estilo.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    estilo.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8'))
    tabla.setStyle(estilo)
    elements.append(tabla)

    _crear_pie_pagina(elements, styles)
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generar_pdf_gastos(db: Session, fecha_desde: date, fecha_hasta: date) -> BytesIO:
    """Genera PDF de reporte de gastos"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = _get_styles()
    elements = []

    # Obtener datos
    reporte = reportes_service.obtener_reporte_gastos(db, fecha_desde, fecha_hasta)

    # Encabezado
    _crear_encabezado(elements, styles, "REPORTE DE GASTOS", fecha_desde, fecha_hasta)

    # Tabla de categorías
    data = [['Categoría', 'Cantidad', 'Total', '% del Total']]
    for c in reporte.categorias:
        data.append([
            c.categoria,
            str(c.cantidad),
            _format_currency(c.total),
            f"{_format_number(c.porcentaje, 1)}%"
        ])

    # Fila de totales
    data.append([
        'TOTAL GASTOS',
        '',
        _format_currency(reporte.total_gastos),
        '100%'
    ])

    tabla = Table(data, colWidths=[60*mm, 30*mm, 40*mm, 30*mm])
    estilo = _estilo_tabla_base()
    estilo.add('ALIGN', (1, 1), (-1, -1), 'RIGHT')
    estilo.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    estilo.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8'))
    tabla.setStyle(estilo)
    elements.append(tabla)

    # Desglose adicional
    elements.append(Paragraph("Desglose", styles['Subtitulo']))
    desglose_data = [
        ['Combustible', _format_currency(reporte.total_combustible)],
        ['Servicios/Mantenimiento', _format_currency(reporte.total_servicios)],
        ['Repuestos', _format_currency(reporte.total_repuestos)],
    ]
    tabla_desg = Table(desglose_data, colWidths=[80*mm, 60*mm])
    tabla_desg.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))
    elements.append(tabla_desg)

    _crear_pie_pagina(elements, styles)
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generar_pdf_maquinaria(db: Session, fecha_desde: date, fecha_hasta: date) -> BytesIO:
    """Genera PDF de reporte de maquinaria"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = _get_styles()
    elements = []

    # Obtener datos
    reporte = reportes_service.obtener_reporte_maquinaria(db, fecha_desde, fecha_hasta)

    # Encabezado
    _crear_encabezado(elements, styles, "REPORTE DE ACTIVIDAD DE MAQUINARIA", fecha_desde, fecha_hasta)

    # Resumen
    elements.append(Paragraph(f"Total máquinas activas: {reporte.total_maquinas_activas}", styles['Total']))

    # Tabla de máquinas
    data = [['Identificador', 'Pesajes', 'Kg Transportados', 'Días Activa', 'Combustible (L)', 'Servicios', 'Costo Servicios']]
    for m in reporte.maquinas:
        data.append([
            m.identificador,
            str(m.cantidad_pesajes),
            _format_number(m.total_kg, 0),
            str(m.dias_activa),
            _format_number(m.total_combustible, 0),
            str(m.cantidad_servicios),
            _format_currency(m.costo_servicios)
        ])

    # Totales
    data.append([
        'TOTAL',
        str(sum(m.cantidad_pesajes for m in reporte.maquinas)),
        _format_number(sum(m.total_kg for m in reporte.maquinas), 0),
        '',
        _format_number(reporte.total_combustible, 0),
        str(sum(m.cantidad_servicios for m in reporte.maquinas)),
        _format_currency(reporte.total_costo_servicios)
    ])

    tabla = Table(data, colWidths=[45*mm, 20*mm, 40*mm, 25*mm, 35*mm, 25*mm, 35*mm])
    estilo = _estilo_tabla_base()
    estilo.add('ALIGN', (1, 1), (-1, -1), 'RIGHT')
    estilo.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    estilo.add('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8'))
    tabla.setStyle(estilo)
    elements.append(tabla)

    _crear_pie_pagina(elements, styles)
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generar_pdf_top_clientes(db: Session, fecha_desde: date, fecha_hasta: date) -> BytesIO:
    """Genera PDF de top clientes"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = _get_styles()
    elements = []

    # Obtener datos
    reporte = reportes_service.obtener_top_clientes(db, fecha_desde, fecha_hasta, limite=20)

    # Encabezado
    _crear_encabezado(elements, styles, "RANKING DE CLIENTES", fecha_desde, fecha_hasta)

    # Resumen
    elements.append(Paragraph(f"Total clientes distintos: {reporte.total_clientes}", styles['Total']))

    # Tabla de clientes
    data = [['#', 'Cliente', 'Pesajes', 'Kg', 'Toneladas', 'Importe', '% Total']]
    for i, c in enumerate(reporte.clientes, 1):
        data.append([
            str(i),
            c.nombre[:30] + '...' if len(c.nombre) > 30 else c.nombre,
            str(c.cantidad_pesajes),
            _format_number(c.total_kg, 0),
            _format_number(c.total_toneladas, 2),
            _format_currency(c.importe_total),
            f"{_format_number(c.porcentaje_total, 1)}%"
        ])

    tabla = Table(data, colWidths=[10*mm, 50*mm, 20*mm, 30*mm, 25*mm, 30*mm, 20*mm])
    estilo = _estilo_tabla_base()
    estilo.add('ALIGN', (0, 1), (0, -1), 'CENTER')
    estilo.add('ALIGN', (2, 1), (-1, -1), 'RIGHT')
    # Destacar top 3
    for i in range(1, min(4, len(reporte.clientes) + 1)):
        estilo.add('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold')
    tabla.setStyle(estilo)
    elements.append(tabla)

    # Total
    elements.append(Paragraph(f"Total General: {_format_currency(reporte.total_general)}", styles['Total']))

    _crear_pie_pagina(elements, styles)
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generar_pdf_reporte(
    db: Session,
    tipo: str,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    material: Optional[str] = None
) -> BytesIO:
    """
    Genera el PDF según el tipo de reporte solicitado
    """
    # Fechas por defecto
    if not fecha_hasta:
        fecha_hasta = date.today()
    if not fecha_desde:
        fecha_desde = fecha_hasta - __import__('datetime').timedelta(days=30)

    if tipo == 'resumen':
        return generar_pdf_resumen(db, fecha_desde, fecha_hasta)
    elif tipo == 'ventas-material':
        return generar_pdf_ventas_material(db, fecha_desde, fecha_hasta)
    elif tipo == 'ventas-semanal':
        return generar_pdf_ventas_semanal(db, fecha_desde, fecha_hasta, material)
    elif tipo == 'gastos':
        return generar_pdf_gastos(db, fecha_desde, fecha_hasta)
    elif tipo == 'maquinaria':
        return generar_pdf_maquinaria(db, fecha_desde, fecha_hasta)
    elif tipo == 'top-clientes':
        return generar_pdf_top_clientes(db, fecha_desde, fecha_hasta)
    else:
        # Por defecto, resumen
        return generar_pdf_resumen(db, fecha_desde, fecha_hasta)
