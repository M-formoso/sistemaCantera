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
    """
    from reportlab.lib.utils import ImageReader

    # Parsear fecha
    fecha = pesaje_data.get('fecha', datetime.now())
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
        except:
            fecha = datetime.now()

    # Formatear pesos
    def format_peso(peso):
        try:
            return f"{int(float(peso)):,}".replace(',', '.') + " kg"
        except:
            return "- kg"

    peso_bruto = pesaje_data.get('peso_bruto', 0)
    peso_tara = pesaje_data.get('peso_tara', 0)
    peso_neto = pesaje_data.get('peso_neto', 0)

    # Tamaños de fuente según número de copias (más pequeño = más copias)
    font_title = 10
    font_normal = 7
    font_small = 6
    line_height = 10

    y = y_top - 5  # Empezar un poco abajo del tope

    # --- LOGO (centrado arriba) ---
    logo_height = 18 * mm
    logo_width = 50 * mm
    if os.path.exists(LOGO_PATH):
        try:
            c.drawImage(LOGO_PATH, x + (width - logo_width) / 2, y - logo_height,
                       width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
            y -= logo_height + 2
        except Exception as e:
            print(f"Error al cargar logo: {e}")
            y -= 5

    # --- TIPO DE COPIA (esquina superior derecha) ---
    c.setFont("Helvetica-Bold", font_normal)
    c.setFillColor(colors.gray)
    c.drawRightString(x + width, y, tipo_copia)
    c.setFillColor(colors.black)

    # --- ENCABEZADO ---
    c.setFont("Helvetica-Bold", font_title)
    c.drawCentredString(x + width / 2, y, "Canteras La Rufina - TBF SRL")
    y -= line_height

    c.setFont("Helvetica", font_small)
    c.drawCentredString(x + width / 2, y, "Ruta C45 - Km 11 - Falda del Carmen | Tel: 351 537-2741")
    y -= line_height + 2

    # --- CONTROL DE PESADA ---
    c.setFont("Helvetica-Bold", font_title)
    c.drawCentredString(x + width / 2, y, "CONTROL DE PESADA")
    y -= line_height + 4

    # --- DATOS EN DOS COLUMNAS ---
    col1_x = x
    col2_x = x + width / 2

    def draw_field(label, value, col_x, y_pos):
        c.setFont("Helvetica-Bold", font_normal)
        c.drawString(col_x, y_pos, f"{label}:")
        c.setFont("Helvetica", font_normal)
        c.drawString(col_x + 45, y_pos, str(value or "-"))

    # Fila 1
    draw_field("Ticket", pesaje_data.get('numero_pesaje', '-'), col1_x, y)
    draw_field("Fecha", fecha.strftime('%d/%m/%Y %H:%M'), col2_x, y)
    y -= line_height

    # Fila 2
    draw_field("Patente", pesaje_data.get('camion_patente', '-'), col1_x, y)
    draw_field("Chofer", pesaje_data.get('chofer', '-'), col2_x, y)
    y -= line_height

    # Fila 3
    draw_field("Acoplado", pesaje_data.get('acoplado', '-'), col1_x, y)
    draw_field("Transportista", pesaje_data.get('transportista', '-'), col2_x, y)
    y -= line_height

    # Fila 4
    draw_field("Cliente", pesaje_data.get('cliente_destino', '-'), col1_x, y)
    draw_field("Material", pesaje_data.get('material', '-'), col2_x, y)
    y -= line_height + 4

    # --- PESOS (destacados) ---
    c.setStrokeColor(colors.HexColor('#cccccc'))
    c.setFillColor(colors.HexColor('#f5f5f5'))
    peso_box_height = line_height + 6
    c.rect(x, y - peso_box_height + 4, width, peso_box_height, fill=1, stroke=1)
    c.setFillColor(colors.black)

    c.setFont("Helvetica-Bold", font_normal)
    peso_y = y - 2

    # Bruto
    c.drawString(x + 5, peso_y, "Bruto:")
    c.setFont("Helvetica", font_normal)
    c.drawString(x + 35, peso_y, format_peso(peso_bruto))

    # Tara
    c.setFont("Helvetica-Bold", font_normal)
    c.drawString(x + width / 3, peso_y, "Tara:")
    c.setFont("Helvetica", font_normal)
    c.drawString(x + width / 3 + 25, peso_y, format_peso(peso_tara))

    # Neto (destacado)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 2 * width / 3, peso_y, "Neto:")
    c.setFillColor(colors.HexColor('#006600'))
    c.drawString(x + 2 * width / 3 + 28, peso_y, format_peso(peso_neto))
    c.setFillColor(colors.black)

    y -= peso_box_height + 4

    # --- OPERARIO ---
    draw_field("Operario", pesaje_data.get('operario', '-'), col1_x, y)
    y -= line_height + 4

    # --- FIRMAS ---
    c.setFont("Helvetica", font_small)
    firma_width = width / 2 - 20
    c.line(x + 10, y, x + 10 + firma_width, y)
    c.line(x + width / 2 + 10, y, x + width / 2 + 10 + firma_width, y)
    y -= 8
    c.drawCentredString(x + 10 + firma_width / 2, y, "Firma Chofer")
    c.drawCentredString(x + width / 2 + 10 + firma_width / 2, y, "Firma Operario")


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

    # Crear documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )

    # Estilos
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=2*mm
    )

    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        spaceAfter=2*mm
    )

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading2'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceBefore=3*mm,
        spaceAfter=4*mm,
        textColor=colors.HexColor('#1a1a1a')
    )

    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12
    )

    # Estilo para tipo de copia (Original/Duplicado/Triplicado)
    tipo_copia_style = ParagraphStyle(
        'TipoCopiaStyle',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#666666'),
        spaceAfter=3*mm
    )

    elements = []

    # Tipo de copia en la esquina superior derecha
    tipo_label = tipo_copia.upper()
    elements.append(Paragraph(tipo_label, tipo_copia_style))

    # Logo más ancho
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image(LOGO_PATH, width=120*mm, height=40*mm, kind='proportional')
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 2*mm))
        except Exception as e:
            print(f"Error al cargar logo: {e}")

    # Encabezado
    elements.append(Paragraph("Canteras La Rufina – TBF SRL", title_style))
    elements.append(Paragraph("Ruta C45 – Km 11 – Falda del Carmen", subtitle_style))
    elements.append(Paragraph("Tel: 351 537-2741", subtitle_style))

    # Título principal
    elements.append(Paragraph("CONTROL DE PESADA", header_style))

    # Parsear fecha
    fecha = pesaje_data.get('fecha', datetime.now())
    if isinstance(fecha, str):
        try:
            fecha = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
        except:
            fecha = datetime.now()

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
    # Ancho total disponible: 180mm (A4 - márgenes)
    col_width = 90*mm

    # Datos organizados en dos columnas
    main_data = [
        # Fila 1: Ticket y Fecha
        [
            Table([['Ticket:', str(pesaje_data.get('numero_pesaje', '-'))]],
                  colWidths=[25*mm, 60*mm]),
            Table([['Fecha:', fecha.strftime('%d/%m/%Y')]],
                  colWidths=[25*mm, 60*mm]),
        ],
        # Fila 2: Camión y Hora
        [
            Table([['Camión:', str(pesaje_data.get('camion_patente', '-'))]],
                  colWidths=[25*mm, 60*mm]),
            Table([['Hora:', fecha.strftime('%H:%M:%S')]],
                  colWidths=[25*mm, 60*mm]),
        ],
        # Fila 3: Acoplado y Chofer
        [
            Table([['Acoplado:', str(pesaje_data.get('acoplado', '-') or '-')]],
                  colWidths=[25*mm, 60*mm]),
            Table([['Chofer:', str(pesaje_data.get('chofer', '-') or '-')]],
                  colWidths=[25*mm, 60*mm]),
        ],
        # Fila 4: Transportista y Remitente
        [
            Table([['Transportista:', str(pesaje_data.get('transportista', '-') or '-')]],
                  colWidths=[25*mm, 60*mm]),
            Table([['Remitente:', str(pesaje_data.get('remitente', 'LA RUFINA') or 'LA RUFINA')]],
                  colWidths=[25*mm, 60*mm]),
        ],
        # Fila 5: Destinatario y Producto
        [
            Table([['Destinatario:', str(pesaje_data.get('cliente_destino', '-') or '-')]],
                  colWidths=[25*mm, 60*mm]),
            Table([['Producto:', str(pesaje_data.get('producto', '-') or '-')]],
                  colWidths=[25*mm, 60*mm]),
        ],
        # Fila 6: Material y Nro. Guía
        [
            Table([['Material:', str(pesaje_data.get('material', '-') or '-')]],
                  colWidths=[25*mm, 60*mm]),
            Table([['Nro. Guía:', str(pesaje_data.get('numero_guia', '-') or '-')]],
                  colWidths=[25*mm, 60*mm]),
        ],
    ]

    # Aplicar estilos a las sub-tablas
    cell_style = TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
    ])

    for row in main_data:
        for cell in row:
            cell.setStyle(cell_style)

    main_table = Table(main_data, colWidths=[col_width, col_width])
    main_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(main_table)
    elements.append(Spacer(1, 5*mm))

    # ===== SECCIÓN DE PESOS (centrada, destacada) =====
    pesos_header = ParagraphStyle(
        'PesosHeader',
        parent=styles['Heading3'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceBefore=2*mm,
        spaceAfter=3*mm,
        textColor=colors.HexColor('#333333')
    )
    elements.append(Paragraph("PESOS", pesos_header))

    # Pesos en una fila horizontal
    pesos_data = [
        ['Bruto:', format_peso(peso_bruto), 'Tara:', format_peso(peso_tara), 'Neto:', format_peso(peso_neto)],
    ]

    pesos_table = Table(pesos_data, colWidths=[20*mm, 40*mm, 20*mm, 40*mm, 20*mm, 40*mm])
    pesos_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica'),
        ('FONTNAME', (2, 0), (2, 0), 'Helvetica-Bold'),
        ('FONTNAME', (3, 0), (3, 0), 'Helvetica'),
        ('FONTNAME', (4, 0), (4, 0), 'Helvetica-Bold'),
        ('FONTNAME', (5, 0), (5, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('FONTSIZE', (4, 0), (5, 0), 13),
        ('TEXTCOLOR', (5, 0), (5, 0), colors.HexColor('#006600')),
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('ALIGN', (3, 0), (3, 0), 'LEFT'),
        ('ALIGN', (4, 0), (4, 0), 'RIGHT'),
        ('ALIGN', (5, 0), (5, 0), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
    ]))
    elements.append(pesos_table)
    elements.append(Spacer(1, 4*mm))

    # ===== OPERARIO =====
    operario_data = [
        [
            Table([['Operario:', str(pesaje_data.get('operario', '-') or '-')]],
                  colWidths=[25*mm, 60*mm]),
            '',
        ],
    ]
    operario_data[0][0].setStyle(cell_style)

    operario_table = Table(operario_data, colWidths=[col_width, col_width])
    operario_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(operario_table)
    elements.append(Spacer(1, 3*mm))

    # Observaciones
    observaciones = pesaje_data.get('observaciones', '')
    if observaciones:
        obs_style = ParagraphStyle(
            'ObsTitle',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            spaceAfter=2*mm,
        )
        elements.append(Paragraph("Observaciones:", obs_style))
        elements.append(Paragraph(str(observaciones), normal_style))
        elements.append(Spacer(1, 5*mm))

    # ===== LÍNEAS PARA FIRMA =====
    elements.append(Spacer(1, 10*mm))
    firma_data = [
        ['_' * 35, '_' * 35],
        ['Firma Chofer', 'Firma Operario'],
    ]

    firma_table = Table(firma_data, colWidths=[85*mm, 85*mm])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, 1), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 2),
    ]))
    elements.append(firma_table)

    # Pie de página
    elements.append(Spacer(1, 8*mm))
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.gray
    )
    elements.append(Paragraph("Sistema de Control de Pesada - Canteras La Rufina", footer_style))
    elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", footer_style))

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
