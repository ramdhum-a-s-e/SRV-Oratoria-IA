"""Generación de reportes PDF de desempeño con branding institucional (Charter S04).

El logo es opcional: si existe backend/assets/logo.png se inserta; si no, se dibuja
un recuadro reservado "[ LOGO ]" para colocarlo más adelante.
"""
import os
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
)

# Paleta institucional (coherente con el frontend "Lorito")
VERDE  = colors.HexColor("#2bb673")
CIELO  = colors.HexColor("#3fa9f5")
MORADO = colors.HexColor("#a06cf0")
NARANJA = colors.HexColor("#fb923c")
TEXTO  = colors.HexColor("#3a3340")
SUAVE  = colors.HexColor("#8a8294")
BORDE  = colors.HexColor("#efe3cf")

_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logo.png")

INSTITUCION = "I.E. Juan José Farfán — Lancones, Piura"
SISTEMA = "Sistema de Retroalimentación por Voz (SRV)"


def _estrellas(n):
    n = int(n or 0)
    return "★" * n + "☆" * (5 - n)


def _color_score(s):
    if s is None:
        return SUAVE
    if s >= 70:
        return VERDE
    if s >= 50:
        return colors.HexColor("#f5a623")
    return colors.HexColor("#ef5350")


def _cabecera():
    """Tabla de 2 columnas: logo (o placeholder) + datos de la institución."""
    estilos = getSampleStyleSheet()
    inst_style = ParagraphStyle("inst", parent=estilos["Normal"], fontSize=12,
                                textColor=TEXTO, fontName="Helvetica-Bold", leading=15)
    sub_style = ParagraphStyle("sub", parent=estilos["Normal"], fontSize=9,
                               textColor=SUAVE, leading=12)

    if os.path.exists(_LOGO_PATH):
        logo = Image(_LOGO_PATH, width=28 * mm, height=28 * mm)
    else:
        # Recuadro reservado para el logo (aún no disponible)
        logo = Table([["[ LOGO ]"]], colWidths=[28 * mm], rowHeights=[28 * mm])
        logo.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, BORDE),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TEXTCOLOR", (0, 0), (-1, -1), SUAVE),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))

    texto = [
        Paragraph(INSTITUCION, inst_style),
        Spacer(1, 2),
        Paragraph(SISTEMA, sub_style),
        Paragraph("Reporte de desempeño en oratoria", sub_style),
    ]
    cab = Table([[logo, texto]], colWidths=[32 * mm, 130 * mm])
    cab.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (1, 0), (1, 0), 8),
    ]))
    return cab


def _tabla(data, anchos, header_color):
    t = Table(data, colWidths=anchos)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbf7ee")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXTO),
    ]))
    return t


def build_session_report(sesion, d1, d2, d3, usuario, score_global=None) -> bytes:
    """Construye el PDF de una sesión y devuelve los bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            title=f"Reporte sesión {sesion.id}")
    estilos = getSampleStyleSheet()
    h2 = ParagraphStyle("h2", parent=estilos["Heading2"], textColor=TEXTO, fontSize=13)
    normal = ParagraphStyle("n", parent=estilos["Normal"], fontSize=9.5, textColor=TEXTO, leading=14)
    suave = ParagraphStyle("s", parent=estilos["Normal"], fontSize=9, textColor=SUAVE, leading=13)

    fb1 = (d1.feedback_json if d1 else None) or {}
    fb2 = (d2.feedback_json if d2 else None) or {}
    fb3 = (d3.feedback_json if d3 else None) or {}

    elems = [_cabecera(), Spacer(1, 10)]

    # Línea separadora
    sep = Table([[""]], colWidths=[162 * mm])
    sep.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1.2, VERDE)]))
    elems += [sep, Spacer(1, 10)]

    # Datos del estudiante
    fecha = sesion.created_at.strftime("%d/%m/%Y %H:%M") if sesion.created_at else "—"
    modo_txt = "Lectura" if sesion.modo == "lectura" else "Expresión libre"
    grado = " ".join([x for x in [usuario.grado, usuario.seccion] if x]) or "—"
    info = _tabla(
        [["Estudiante", "Grado/Sección", "Modo", "Fecha"],
         [f"{usuario.nombre} {usuario.apellido}", grado, modo_txt, fecha]],
        [50 * mm, 36 * mm, 38 * mm, 38 * mm], CIELO)
    elems += [info, Spacer(1, 14)]

    # Resultado global
    if score_global is not None:
        elems.append(Paragraph("Resultado global", h2))
        glob = Table(
            [[Paragraph(f"<font size=30><b>{score_global}</b></font> <font size=10 color='#8a8294'>/100 pts</font>", normal),
              Paragraph(f"<font size=16>{_estrellas(d1.estrellas if d1 else 0)}</font>", normal)]],
            colWidths=[90 * mm, 72 * mm])
        glob.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f3fbf6")),
            ("BOX", (0, 0), (-1, -1), 1, VERDE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        elems += [glob, Spacer(1, 14)]

    # Puntajes por dimensión
    elems.append(Paragraph("Puntajes por dimensión", h2))
    dim = _tabla(
        [["Dimensión", "Puntaje", "Estrellas"],
         ["D1 — Fluidez oral", f"{round(d1.score_d1) if d1 and d1.score_d1 is not None else '—'}", _estrellas(d1.estrellas if d1 else 0)],
         ["D2 — Vocabulario y coherencia", f"{round(d2.score_d2) if d2 and d2.score_d2 is not None else '—'}", _estrellas(d2.estrellas if d2 else 0)],
         ["D3 — Expresividad vocal", f"{round(d3.score_d3) if d3 and d3.score_d3 is not None else '—'}", _estrellas(d3.estrellas if d3 else 0)]],
        [86 * mm, 38 * mm, 38 * mm], MORADO)
    elems += [dim, Spacer(1, 14)]

    # Métricas clave
    elems.append(Paragraph("Métricas clave", h2))
    metricas = [["Indicador", "Valor"]]
    if d1:
        metricas += [
            ["Velocidad (PPM)", f"{round(d1.ppm) if d1.ppm is not None else '—'}"],
            ["Bloqueos (pausas largas)", f"{d1.long_pauses if d1.long_pauses is not None else '—'}"],
        ]
    if d2:
        metricas += [
            ["Muletillas", f"{d2.muletillas_count}"],
            ["Riqueza léxica (TTR)", f"{round((d2.ttr_score or 0)*100)}%"],
            ["Coherencia", f"{fb2.get('coherencia_nivel', '—')}"],
        ]
    if d3:
        metricas += [["Variación tonal (pts)", f"{round(d3.variacion_tonal_pts or 0)}"]]
    lectura = fb1.get("lectura")
    if lectura:
        metricas += [["Fidelidad de lectura", f"{lectura.get('fidelidad_score', '—')}%"]]
    elems += [_tabla(metricas, [100 * mm, 62 * mm], NARANJA), Spacer(1, 14)]

    # Consejos
    consejos = list(fb1.get("consejos", [])) + list(fb2.get("consejos", []))
    if consejos:
        elems.append(Paragraph("Recomendaciones para mejorar", h2))
        for c in consejos:
            elems.append(Paragraph(f"• {c}", normal))
        elems.append(Spacer(1, 12))

    # Transcripción
    if d1 and d1.transcripcion:
        elems.append(Paragraph("Transcripción", h2))
        elems.append(Paragraph(f"<i>“{d1.transcripcion}”</i>", suave))
        elems.append(Spacer(1, 12))

    # Pie
    elems.append(Spacer(1, 6))
    pie = Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} — {SISTEMA}. "
        f"Documento de uso académico (UPAO).", suave)
    elems.append(pie)

    doc.build(elems)
    return buf.getvalue()
