"""
Tareas Celery para generación de reportes PDF
"""
import os
from celery import shared_task
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime

from app.models.base import get_argentina_now

# Ruta al logo
LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'logo_la_rufina.png')


def generar_ticket_pesaje_pdf_multiple(pesaje_data: dict, num_copias: int = 1) -> BytesIO:
    """
    Genera un PDF con múltiples copias del ticket en una sola hoja A4.

    Args:
        pesaje_data: Diccionario con los datos del pesaje
        num_copias: 1 = original, 2 = original + duplicado, 3 = original + duplicado + triplicado

    Returns:
        BytesIO con el PDF generado
    """
    buffer = BytesIO()

    # Definir tipos de copia
    tipos_copia = ["ORIGINAL", "DUPLICADO", "TRIPLICADO"][:num_copias]

    # Calcular altura disponible por copia
    page_height = A4[1]  # ~842 puntos
    page_width = A4[0]   # ~595 puntos
    margin = 8 * mm
    usable_height = page_height - (2 * margin)
    copy_height = usable_height / num_copias - (5 * mm)  # Espacio entre copias

    # Crear documento PDF
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(buffer, pagesize=A4)

    for i, tipo_copia in enumerate(tipos_copia):
        # Calcular posición Y de inicio para esta copia (de arriba hacia abajo)
        y_start = page_height - margin - (i * (copy_height + 5 * mm))

        _dibujar_ticket_compacto(c, pesaje_data, tipo_copia, margin, y_start, copy_height, page_width - 2 * margin)

        # Línea separadora entre copias (excepto la última)
        if i < num_copias - 1:
            y_line = y_start - copy_height - 2.5 * mm
            c.setStrokeColor(colors.gray)
            c.setDash(3, 3)
            c.line(margin, y_line, page_width - margin, y_line)
            c.setDash()

    c.save()
    buffer.seek(0)
    return buffer


def _dibujar_ticket_compacto(c, pesaje_data: dict, tipo_copia: str, x: float, y_top: float, height: float, width: float):
    """
    Dibuja un ticket compacto en la posición especificada.
    Diseño mejorado con mejor espaciado y tipografía más legible.
    """
    from reportlab.lib.utils import ImageReader

    # Parsear fecha
    fecha = pesaje_data.get('fecha', get_argentina_now())
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
        except:
            fecha = get_argentina_now()

    # Formatear pesos
    def format_peso(peso):
        try:
            return f"{int(float(peso)):,}".replace(',', '.') + " kg"
        except:
            return "- kg"

    peso_bruto = pesaje_data.get('peso_bruto', 0)
    peso_tara = pesaje_data.get('peso_tara', 0)
    peso_neto = pesaje_data.get('peso_neto', 0)

    # Datos de conversión m3
    factor_conversion = pesaje_data.get('factor_conversion')
    cantidad_m3 = pesaje_data.get('cantidad_m3')
    peso_neto_tn = pesaje_data.get('peso_neto_tn', peso_neto / 1000 if peso_neto else 0)

    # Tamaños de fuente más grandes y legibles
    font_title = 14
    font_subtitle = 12
    font_normal = 11
    font_label = 10
    font_small = 9
    line_height = 16
    section_spacing = 10

    y = y_top - 8  # Empezar con más margen

    # ==================== ENCABEZADO ====================
    # Logo a la izquierda, info empresa al centro, tipo copia a la derecha
    logo_height = 20 * mm
    logo_width = 35 * mm

    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(LOGO_PATH, x, y - logo_height,
                       width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error al cargar logo: {e}")

    # Info empresa (al lado del logo)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x + logo_width + 10, y - 8, "Canteras La Rufina")
    c.setFont("Helvetica", font_label)
    c.drawString(x + logo_width + 10, y - 20, "TBF SRL")
    c.drawString(x + logo_width + 10, y - 32, "Ruta C45 - Km 11 - Falda del Carmen")
    c.drawString(x + logo_width + 10, y - 44, "Tel: 351 537-2741")

    # Tipo de copia (esquina derecha)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor('#666666'))
    c.drawRightString(x + width, y - 8, tipo_copia)
    c.setFillColor(colors.black)

    y -= logo_height + section_spacing

    # ==================== TÍTULO ====================
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(x + width / 2, y, "CONTROL DE PESADA")
    y -= line_height + section_spacing

    # ==================== DATOS PRINCIPALES ====================
    col1_x = x + 5
    col2_x = x + width / 2 + 5
    label_width = 55

    def draw_field(label, value, col_x, y_pos, bold_value=False):
        c.setFont("Helvetica-Bold", font_label)
        c.setFillColor(colors.HexColor('#555555'))
        c.drawString(col_x, y_pos, f"{label}:")
        c.setFillColor(colors.black)
        if bold_value:
            c.setFont("Helvetica-Bold", font_normal)
        else:
            c.setFont("Helvetica", font_normal)
        c.drawString(col_x + label_width, y_pos, str(value or "-"))

    # Fila 1: Ticket y Fecha/Hora
    draw_field("Ticket", f"#{pesaje_data.get('numero_pesaje', '-')}", col1_x, y, bold_value=True)
    draw_field("Fecha", fecha.strftime('%d/%m/%Y  %H:%M'), col2_x, y)
    y -= line_height

    # Fila 2: Patente y Chofer
    draw_field("Patente", pesaje_data.get('camion_patente', '-'), col1_x, y, bold_value=True)
    draw_field("Chofer", pesaje_data.get('chofer', '-'), col2_x, y)
    y -= line_height

    # Fila 3: Acoplado y Transportista
    draw_field("Acoplado", pesaje_data.get('acoplado', '-'), col1_x, y)
    draw_field("Transportista", pesaje_data.get('transportista', '-'), col2_x, y)
    y -= line_height

    # Fila 4: Cliente y Material
    draw_field("Cliente", pesaje_data.get('cliente_destino', '-'), col1_x, y)
    draw_field("Material", pesaje_data.get('material', '-'), col2_x, y, bold_value=True)
    y -= line_height + section_spacing

    # ==================== SECCIÓN DE PESOS ====================
    # Recuadro destacado para pesos
    peso_box_height = 34
    c.setStrokeColor(colors.HexColor('#999999'))
    c.setFillColor(colors.HexColor('#f0f0f0'))
    c.roundRect(x, y - peso_box_height, width, peso_box_height, 3, fill=1, stroke=1)
    c.setFillColor(colors.black)

    peso_y = y - 12
    peso_section_width = width / 3

    # Bruto
    c.setFont("Helvetica", font_label)
    c.setFillColor(colors.HexColor('#555555'))
    c.drawCentredString(x + peso_section_width / 2, peso_y, "BRUTO")
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", font_subtitle)
    c.drawCentredString(x + peso_section_width / 2, peso_y - 14, format_peso(peso_bruto))

    # Tara
    c.setFont("Helvetica", font_label)
    c.setFillColor(colors.HexColor('#555555'))
    c.drawCentredString(x + peso_section_width + peso_section_width / 2, peso_y, "TARA")
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", font_subtitle)
    c.drawCentredString(x + peso_section_width + peso_section_width / 2, peso_y - 14, format_peso(peso_tara))

    # Neto (destacado en verde)
    c.setFont("Helvetica", font_label)
    c.setFillColor(colors.HexColor('#006600'))
    c.drawCentredString(x + 2 * peso_section_width + peso_section_width / 2, peso_y, "NETO")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(x + 2 * peso_section_width + peso_section_width / 2, peso_y - 14, format_peso(peso_neto))
    c.setFillColor(colors.black)

    y -= peso_box_height + section_spacing

    # ==================== CONVERSIÓN A M³ (si aplica) ====================
    if factor_conversion and cantidad_m3:
        # Recuadro para conversión m³
        conversion_box_height = 28
        c.setStrokeColor(colors.HexColor('#0066cc'))
        c.setFillColor(colors.HexColor('#e6f2ff'))
        c.roundRect(x, y - conversion_box_height, width, conversion_box_height, 3, fill=1, stroke=1)
        c.setFillColor(colors.black)

        conv_y = y - 10
        c.setFont("Helvetica", font_label)
        c.setFillColor(colors.HexColor('#0066cc'))
        c.drawString(x + 8, conv_y, "CONVERSIÓN:")
        c.setFont("Helvetica-Bold", font_normal)
        c.drawString(x + 80, conv_y, f"{peso_neto_tn:.2f} tn ÷ {factor_conversion} = ")
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.HexColor('#004499'))
        c.drawString(x + 200, conv_y, f"{cantidad_m3:.2f} m³")
        c.setFillColor(colors.black)

        y -= conversion_box_height + section_spacing

    # ==================== OPERARIO ====================
    draw_field("Operario", pesaje_data.get('operario', '-'), col1_x, y)
    y -= line_height + section_spacing + 4

    # ==================== FIRMAS ====================
    c.setStrokeColor(colors.black)
    firma_width = width / 2 - 30

    # Línea firma chofer
    c.line(x + 15, y, x + 15 + firma_width, y)
    # Línea firma operario
    c.line(x + width / 2 + 15, y, x + width / 2 + 15 + firma_width, y)

    y -= 10
    c.setFont("Helvetica", font_small)
    c.drawCentredString(x + 15 + firma_width / 2, y, "Firma Chofer")
    c.drawCentredString(x + width / 2 + 15 + firma_width / 2, y, "Firma Operario")


def generar_ticket_pesaje_pdf(pesaje_data: dict, tipo_copia: str = "original") -> BytesIO:
    """
    Genera un PDF con el ticket de pesaje/control de pesada

    Args:
        pesaje_data: Diccionario con los datos del pesaje
        tipo_copia: "original", "duplicado" o "triplicado"

    Returns:
        BytesIO con el PDF generado
    """
    buffer = BytesIO()

    # Crear documento PDF con márgenes más amplios
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    # Estilos con tipografía más grande
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        spaceAfter=2*mm
    )

    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_LEFT,
        spaceAfter=1*mm,
        textColor=colors.HexColor('#444444')
    )

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=16,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceBefore=8*mm,
        spaceAfter=8*mm,
        textColor=colors.HexColor('#1a1a1a')
    )

    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14
    )

    # Estilo para tipo de copia (Original/Duplicado/Triplicado)
    tipo_copia_style = ParagraphStyle(
        'TipoCopiaStyle',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#666666'),
    )

    elements = []

    # ===== ENCABEZADO CON LOGO A LA IZQUIERDA =====
    # Crear tabla para logo + info empresa + tipo copia
    header_data = []

    logo_cell = ""
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image(LOGO_PATH, width=45*mm, height=35*mm, kind='proportional')
            logo_cell = logo
        except Exception as e:
            print(f"Error al cargar logo: {e}")

    # Info de empresa
    empresa_info = Paragraph(
        "<b>Canteras La Rufina – TBF SRL</b><br/>"
        "<font size='10'>Ruta C45 – Km 11 – Falda del Carmen</font><br/>"
        "<font size='10'>Tel: 351 537-2741</font>",
        ParagraphStyle('EmpresaInfo', parent=styles['Normal'], fontSize=14, leading=18)
    )

    # Tipo de copia
    tipo_label = tipo_copia.upper()
    tipo_cell = Paragraph(f"<b>{tipo_label}</b>", tipo_copia_style)

    header_table = Table(
        [[logo_cell, empresa_info, tipo_cell]],
        colWidths=[50*mm, 85*mm, 35*mm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 5*mm))

    # Título principal
    elements.append(Paragraph("CONTROL DE PESADA", header_style))

    # Parsear fecha
    fecha = pesaje_data.get('fecha', get_argentina_now())
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
        except:
            fecha = get_argentina_now()

    # Formatear números
    def format_peso(peso):
        try:
            return f"{int(float(peso)):,}".replace(',', '.') + " kg"
        except:
            return "- kg"

    peso_bruto = pesaje_data.get('peso_bruto', 0)
    peso_tara = pesaje_data.get('peso_tara', 0)
    peso_neto = pesaje_data.get('peso_neto', 0)

    # ===== TABLA PRINCIPAL CON DOS COLUMNAS =====
    # Ancho total disponible: 170mm (A4 - márgenes de 20mm cada lado)
    col_width = 85*mm

    # Datos organizados en dos columnas con fuente más grande
    main_data = [
        # Fila 1: Ticket y Fecha
        [
            Table([['Ticket:', str(pesaje_data.get('numero_pesaje', '-'))]],
                  colWidths=[32*mm, 50*mm]),
            Table([['Fecha:', fecha.strftime('%d/%m/%Y')]],
                  colWidths=[32*mm, 50*mm]),
        ],
        # Fila 2: Camión y Hora
        [
            Table([['Camión:', str(pesaje_data.get('camion_patente', '-'))]],
                  colWidths=[32*mm, 50*mm]),
            Table([['Hora:', fecha.strftime('%H:%M:%S')]],
                  colWidths=[32*mm, 50*mm]),
        ],
        # Fila 3: Acoplado y Chofer
        [
            Table([['Acoplado:', str(pesaje_data.get('acoplado', '-') or '-')]],
                  colWidths=[32*mm, 50*mm]),
            Table([['Chofer:', str(pesaje_data.get('chofer', '-') or '-')]],
                  colWidths=[32*mm, 50*mm]),
        ],
        # Fila 4: Transportista y Remitente
        [
            Table([['Transportista:', str(pesaje_data.get('transportista', '-') or '-')]],
                  colWidths=[32*mm, 50*mm]),
            Table([['Remitente:', str(pesaje_data.get('remitente', 'LA RUFINA') or 'LA RUFINA')]],
                  colWidths=[32*mm, 50*mm]),
        ],
        # Fila 5: Destinatario y Producto
        [
            Table([['Destinatario:', str(pesaje_data.get('cliente_destino', '-') or '-')]],
                  colWidths=[32*mm, 50*mm]),
            Table([['Producto:', str(pesaje_data.get('producto', '-') or '-')]],
                  colWidths=[32*mm, 50*mm]),
        ],
        # Fila 6: Material y Nro. Guía
        [
            Table([['Material:', str(pesaje_data.get('material', '-') or '-')]],
                  colWidths=[32*mm, 50*mm]),
            Table([['Nro. Guía:', str(pesaje_data.get('numero_guia', '-') or '-')]],
                  colWidths=[32*mm, 50*mm]),
        ],
    ]

    # Aplicar estilos a las sub-tablas con fuente más grande
    cell_style = TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ])

    for row in main_data:
        for cell in row:
            cell.setStyle(cell_style)

    main_table = Table(main_data, colWidths=[col_width, col_width])
    main_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(main_table)
    elements.append(Spacer(1, 8*mm))

    # ===== SECCIÓN DE PESOS (centrada, destacada) =====
    pesos_header = ParagraphStyle(
        'PesosHeader',
        parent=styles['Heading3'],
        fontSize=14,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceBefore=4*mm,
        spaceAfter=5*mm,
        textColor=colors.HexColor('#333333')
    )
    elements.append(Paragraph("PESOS", pesos_header))

    # Pesos en una fila horizontal con fuente más grande
    pesos_data = [
        ['Bruto:', format_peso(peso_bruto), 'Tara:', format_peso(peso_tara), 'Neto:', format_peso(peso_neto)],
    ]

    pesos_table = Table(pesos_data, colWidths=[22*mm, 38*mm, 22*mm, 38*mm, 22*mm, 38*mm])
    pesos_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, 0), 'Helvetica'),
        ('FONTNAME', (4, 0), (4, 0), 'Helvetica-Bold'),
        ('FONTNAME', (5, 0), (5, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 13),
        ('FONTSIZE', (4, 0), (5, 0), 16),
        ('TEXTCOLOR', (5, 0), (5, 0), colors.HexColor('#006600')),
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('ALIGN', (3, 0), (3, 0), 'LEFT'),
        ('ALIGN', (4, 0), (4, 0), 'RIGHT'),
        ('ALIGN', (5, 0), (5, 0), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#aaaaaa')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
    ]))
    elements.append(pesos_table)
    elements.append(Spacer(1, 8*mm))

    # ===== OPERARIO =====
    operario_style = TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ])

    operario_data = [
        [
            Table([['Operario:', str(pesaje_data.get('operario', '-') or '-')]],
                  colWidths=[32*mm, 50*mm]),
            '',
        ],
    ]
    operario_data[0][0].setStyle(operario_style)

    operario_table = Table(operario_data, colWidths=[col_width, col_width])
    operario_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(operario_table)
    elements.append(Spacer(1, 5*mm))

    # Observaciones
    observaciones = pesaje_data.get('observaciones', '')
    if observaciones:
        obs_style = ParagraphStyle(
            'ObsTitle',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            spaceAfter=3*mm,
        )
        elements.append(Paragraph("Observaciones:", obs_style))
        elements.append(Paragraph(str(observaciones), normal_style))
        elements.append(Spacer(1, 8*mm))

    # ===== LÍNEAS PARA FIRMA =====
    elements.append(Spacer(1, 15*mm))
    firma_data = [
        ['_' * 40, '_' * 40],
        ['Firma Chofer', 'Firma Operario'],
    ]

    firma_table = Table(firma_data, colWidths=[85*mm, 85*mm])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('TOPPADDING', (0, 1), (-1, 1), 5),
    ]))
    elements.append(firma_table)

    # Pie de página
    elements.append(Spacer(1, 15*mm))
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.gray
    )
    elements.append(Paragraph("Sistema de Control de Pesada - Canteras La Rufina", footer_style))
    elements.append(Paragraph(f"Generado: {get_argentina_now().strftime('%d/%m/%Y %H:%M:%S')}", footer_style))

    # Construir PDF
    doc.build(elements)

    buffer.seek(0)
    return buffer


@shared_task
def generar_pdf_remito(remito_id: str):
    """
    Tarea Celery para generar PDF de remito en background

    Args:
        remito_id: ID del remito (string UUID)
    """
    from app.db.session import SessionLocal
    from app.services import remito_service

    db = SessionLocal()
    try:
        from uuid import UUID
        remito = remito_service.obtener_por_id(db, UUID(remito_id))

        if not remito:
            return {"status": "error", "message": "Remito no encontrado"}

        # Obtener datos del pesaje asociado
        pesaje_data = {}
        if remito.pesaje:
            pesaje = remito.pesaje
            pesaje_data = {
                "numero_pesaje": pesaje.numero_pesaje,
                "fecha": pesaje.fecha,
                "camion_patente": pesaje.camion.patente if pesaje.camion else None,
                "acoplado": pesaje.acoplado,
                "transportista": pesaje.transportista,
                "remitente": pesaje.remitente,
                "cliente_destino": pesaje.cliente_destino,
                "producto": pesaje.producto,
                "material": pesaje.material,
                "numero_guia": pesaje.numero_guia,
                "chofer": pesaje.chofer,
                "peso_bruto": pesaje.peso_bruto,
                "peso_tara": pesaje.peso_tara,
                "peso_neto": pesaje.peso_neto,
                "operario": pesaje.operario,
                "observaciones": pesaje.observaciones,
            }

        # Generar PDF
        pdf_buffer = generar_ticket_pesaje_pdf(pesaje_data)

        # Guardar en disco o almacenamiento (por ahora solo loguear)
        print(f"✅ PDF generado para remito #{remito.numero_remito}")

        return {
            "status": "success",
            "remito_id": remito_id,
            "numero_remito": remito.numero_remito
        }

    finally:
        db.close()


def generar_comprobante_movimiento_cc_pdf(data: dict) -> BytesIO:
    """Genera un PDF tipo comprobante para un movimiento de cuenta corriente.

    Soporta los tres tipos: cargo, pago y ajuste. Incluye datos del cliente,
    descripción, monto y saldos anterior/posterior.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        'NormalCmp', parent=styles['Normal'], fontSize=11, leading=14
    )
    tipo_style = ParagraphStyle(
        'TipoCmp', parent=styles['Normal'], fontSize=12,
        fontName='Helvetica-Bold', alignment=TA_RIGHT,
        textColor=colors.HexColor('#666666'),
    )
    title_style = ParagraphStyle(
        'TitleCmp', parent=styles['Heading2'], fontSize=18,
        fontName='Helvetica-Bold', alignment=TA_CENTER,
        spaceBefore=4 * mm, spaceAfter=6 * mm,
    )

    elements = []

    # Encabezado: logo + empresa + tipo de comprobante
    logo_cell = ""
    if os.path.exists(LOGO_PATH):
        try:
            logo_cell = Image(LOGO_PATH, width=45 * mm, height=35 * mm, kind='proportional')
        except Exception as e:
            print(f"Error al cargar logo: {e}")

    empresa_info = Paragraph(
        "<b>Canteras La Rufina – TBF SRL</b><br/>"
        "<font size='10'>Ruta C45 – Km 11 – Falda del Carmen</font><br/>"
        "<font size='10'>Tel: 351 537-2741</font>",
        ParagraphStyle('EmpresaInfoCmp', parent=styles['Normal'], fontSize=14, leading=18),
    )

    tipo_movimiento = (data.get("tipo") or "").upper()
    tipo_label = {
        "CARGO": "COMPROBANTE DE CARGO",
        "PAGO": "RECIBO DE PAGO",
        "AJUSTE": "COMPROBANTE DE AJUSTE",
    }.get(tipo_movimiento, "COMPROBANTE DE MOVIMIENTO")

    tipo_cell = Paragraph(f"<b>{tipo_label}</b>", tipo_style)

    header_table = Table(
        [[logo_cell, empresa_info, tipo_cell]],
        colWidths=[50 * mm, 80 * mm, 40 * mm],
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4 * mm))

    elements.append(Paragraph(tipo_label, title_style))

    # Datos del cliente y movimiento
    fecha = data.get("fecha")
    if isinstance(fecha, datetime):
        fecha_str = fecha.strftime("%d/%m/%Y")
    elif fecha:
        try:
            fecha_str = datetime.fromisoformat(str(fecha)).strftime("%d/%m/%Y")
        except Exception:
            fecha_str = str(fecha)
    else:
        fecha_str = "-"

    monto = data.get("monto") or 0
    saldo_anterior = data.get("saldo_anterior") or 0
    saldo_posterior = data.get("saldo_posterior") or 0

    def fmt_money(v):
        try:
            return f"$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return f"$ {v}"

    info_rows = [
        [Paragraph("<b>Fecha:</b>", normal_style), Paragraph(fecha_str, normal_style)],
        [Paragraph("<b>Cliente:</b>", normal_style), Paragraph(data.get("cliente_nombre") or "-", normal_style)],
        [Paragraph("<b>CUIT:</b>", normal_style), Paragraph(data.get("cliente_cuit") or "-", normal_style)],
        [Paragraph("<b>Tipo:</b>", normal_style), Paragraph(tipo_movimiento or "-", normal_style)],
    ]
    if data.get("metodo_pago"):
        info_rows.append([
            Paragraph("<b>Método de pago:</b>", normal_style),
            Paragraph(str(data["metodo_pago"]).capitalize(), normal_style),
        ])
    if data.get("numero_comprobante"):
        info_rows.append([
            Paragraph("<b>N° comprobante:</b>", normal_style),
            Paragraph(str(data["numero_comprobante"]), normal_style),
        ])
    if data.get("banco"):
        info_rows.append([
            Paragraph("<b>Banco:</b>", normal_style),
            Paragraph(str(data["banco"]), normal_style),
        ])
    if data.get("referencia_pago"):
        info_rows.append([
            Paragraph("<b>Referencia:</b>", normal_style),
            Paragraph(str(data["referencia_pago"]), normal_style),
        ])

    info_table = Table(info_rows, colWidths=[45 * mm, 120 * mm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4 * mm))

    # Descripción
    elements.append(Paragraph("<b>Descripción</b>", normal_style))
    elements.append(Paragraph(data.get("descripcion") or "-", normal_style))
    if data.get("detalle"):
        elements.append(Paragraph(f"<i>{data['detalle']}</i>", normal_style))
    elements.append(Spacer(1, 4 * mm))

    # Tabla de montos
    monto_label = "Importe"
    monto_color_hex = "#1a1a1a"
    if tipo_movimiento == "CARGO":
        monto_color_hex = "#b91c1c"
    elif tipo_movimiento == "PAGO":
        monto_color_hex = "#15803d"

    montos_data = [
        [Paragraph(f"<b>{monto_label}</b>", normal_style),
         Paragraph(f"<font color='{monto_color_hex}'><b>{fmt_money(monto)}</b></font>", normal_style)],
        [Paragraph("Saldo anterior", normal_style), Paragraph(fmt_money(saldo_anterior), normal_style)],
        [Paragraph("<b>Saldo posterior</b>", normal_style),
         Paragraph(f"<b>{fmt_money(saldo_posterior)}</b>", normal_style)],
    ]
    montos_table = Table(montos_data, colWidths=[100 * mm, 65 * mm])
    montos_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f3f4f6')),
    ]))
    elements.append(montos_table)
    elements.append(Spacer(1, 6 * mm))

    # Detalle de aplicaciones (cuando el pago proviene de un cobro multi-aplicación)
    aplicaciones = data.get("aplicaciones") or []
    if aplicaciones:
        elements.append(Paragraph("<b>Aplicaciones</b>", normal_style))
        elements.append(Spacer(1, 2 * mm))

        aplic_rows = [[
            Paragraph("<b>Documento</b>", normal_style),
            Paragraph("<b>Monto</b>", normal_style),
        ]]
        total_aplic = 0
        for a in aplicaciones:
            monto_a = a.get("monto") or 0
            total_aplic += monto_a
            aplic_rows.append([
                Paragraph(a.get("descripcion") or "-", normal_style),
                Paragraph(fmt_money(monto_a), normal_style),
            ])
        aplic_rows.append([
            Paragraph("<b>Total aplicado</b>", normal_style),
            Paragraph(f"<b>{fmt_money(total_aplic)}</b>", normal_style),
        ])

        aplic_table = Table(aplic_rows, colWidths=[100 * mm, 65 * mm])
        aplic_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
        ]))
        elements.append(aplic_table)
        elements.append(Spacer(1, 6 * mm))

    if data.get("anulado"):
        elements.append(Paragraph(
            "<font color='#b91c1c'><b>** MOVIMIENTO ANULADO **</b></font>",
            ParagraphStyle('AnuladoCmp', parent=normal_style, alignment=TA_CENTER),
        ))
        if data.get("motivo_anulacion"):
            elements.append(Paragraph(
                f"<i>Motivo: {data['motivo_anulacion']}</i>",
                ParagraphStyle('MotivoCmp', parent=normal_style, alignment=TA_CENTER),
            ))
        elements.append(Spacer(1, 4 * mm))

    if data.get("notas"):
        elements.append(Paragraph("<b>Notas</b>", normal_style))
        elements.append(Paragraph(data["notas"], normal_style))
        elements.append(Spacer(1, 4 * mm))

    # Pie con espacio para firma
    elements.append(Spacer(1, 12 * mm))
    firma_table = Table(
        [["", ""], [Paragraph("________________________", normal_style),
                    Paragraph("________________________", normal_style)],
         [Paragraph("Firma cliente", normal_style),
          Paragraph("Firma autorizada", normal_style)]],
        colWidths=[80 * mm, 80 * mm],
    )
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(firma_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
