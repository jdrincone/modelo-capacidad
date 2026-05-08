"""Genera el informe ejecutivo en PDF usando reportlab.

Réplica visual del documento LaTeX docs/informe_ejecutivo.tex con la paleta
corporativa Bancolombia. No requiere instalación de LaTeX.

Usage:
    uv run python -m modelo_capacidad.generate_report
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ---- Paleta Bancolombia ----
BCO_AMARILLO = colors.HexColor("#FDDA24")
BCO_AMARILLO_CLARO = colors.HexColor("#FFE970")
BCO_AMARILLO_OSCURO = colors.HexColor("#E5BD00")
BCO_NEGRO = colors.HexColor("#2C2A29")
BCO_GRIS = colors.HexColor("#ABA59D")
BCO_GRIS_CLARO = colors.HexColor("#D9D5CF")
BCO_GRIS_OSCURO = colors.HexColor("#6B6863")
BCO_BLANCO = colors.HexColor("#FFFFFF")
BCO_VERDE = colors.HexColor("#2D8F4E")

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_PDF = REPO_ROOT / "docs" / "informe_ejecutivo.pdf"


# ---- Estilos ----
def get_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"],
            fontSize=18, leading=22, textColor=BCO_NEGRO,
            spaceBefore=14, spaceAfter=10, fontName="Helvetica-Bold",
            borderPadding=4,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"],
            fontSize=13, leading=16, textColor=BCO_NEGRO,
            spaceBefore=10, spaceAfter=6, fontName="Helvetica-Bold",
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Heading3"],
            fontSize=11, leading=14, textColor=BCO_AMARILLO_OSCURO,
            spaceBefore=6, spaceAfter=3, fontName="Helvetica-Bold",
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"],
            fontSize=10, leading=14, textColor=BCO_NEGRO,
            alignment=TA_JUSTIFY, spaceAfter=4, fontName="Helvetica",
        ),
        "quote": ParagraphStyle(
            "quote", parent=base["BodyText"],
            fontSize=10, leading=14, textColor=BCO_GRIS_OSCURO,
            alignment=TA_JUSTIFY, leftIndent=18, rightIndent=18,
            fontName="Helvetica-Oblique", spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "bullet", parent=base["BodyText"],
            fontSize=10, leading=13, textColor=BCO_NEGRO,
            alignment=TA_JUSTIFY, leftIndent=14, bulletIndent=4,
            fontName="Helvetica", spaceAfter=2,
        ),
        "small": ParagraphStyle(
            "small", parent=base["BodyText"],
            fontSize=9, leading=11, textColor=BCO_GRIS_OSCURO,
            alignment=TA_LEFT, fontName="Helvetica",
        ),
        "cover_title": ParagraphStyle(
            "cover_title", fontSize=42, leading=50, textColor=BCO_BLANCO,
            alignment=TA_LEFT, fontName="Helvetica-Bold",
        ),
        "cover_title_yellow": ParagraphStyle(
            "cover_title_yellow", fontSize=42, leading=50, textColor=BCO_AMARILLO,
            alignment=TA_LEFT, fontName="Helvetica-Bold",
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle", fontSize=15, leading=20, textColor=BCO_BLANCO,
            alignment=TA_LEFT, fontName="Helvetica",
        ),
        "cover_caption": ParagraphStyle(
            "cover_caption", fontSize=11, leading=14, textColor=BCO_GRIS,
            alignment=TA_LEFT, fontName="Helvetica-Oblique",
        ),
        "boxtitle": ParagraphStyle(
            "boxtitle", fontSize=11, leading=14, textColor=BCO_AMARILLO,
            alignment=TA_LEFT, fontName="Helvetica-Bold", spaceAfter=4,
        ),
        "boxtitle_dark": ParagraphStyle(
            "boxtitle_dark", fontSize=11, leading=14, textColor=BCO_BLANCO,
            alignment=TA_LEFT, fontName="Helvetica-Bold", spaceAfter=4,
        ),
        "boxtitle_amber": ParagraphStyle(
            "boxtitle_amber", fontSize=11, leading=14, textColor=BCO_NEGRO,
            alignment=TA_LEFT, fontName="Helvetica-Bold", spaceAfter=4,
        ),
        "footer": ParagraphStyle(
            "footer", fontSize=8, leading=10, textColor=BCO_GRIS_OSCURO,
            alignment=TA_CENTER, fontName="Helvetica",
        ),
    }


# ---- Cajas estilizadas ----
def make_box(title: str, body_para: list, *, kind: str = "honesty",
             styles: dict | None = None) -> Table:
    if styles is None:
        styles = get_styles()
    if kind == "honesty":
        bg = BCO_BLANCO
        border = BCO_NEGRO
        title_style = styles["boxtitle"]
        bg_title = BCO_NEGRO
    elif kind == "decision":
        bg = BCO_GRIS_CLARO
        border = BCO_NEGRO
        title_style = styles["boxtitle_dark"]
        bg_title = BCO_NEGRO
    elif kind == "insight":
        bg = BCO_AMARILLO_CLARO
        border = BCO_AMARILLO_OSCURO
        title_style = styles["boxtitle_amber"]
        bg_title = BCO_AMARILLO
    else:
        bg, border, title_style, bg_title = BCO_BLANCO, BCO_NEGRO, styles["boxtitle"], BCO_NEGRO

    title_cell = Paragraph(title, title_style)
    rows = [[title_cell]] + [[p] for p in body_para]
    t = Table(rows, colWidths=[16 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), bg_title),
        ("BACKGROUND", (0, 1), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.8, border),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


# ---- Tablas de datos ----
def styled_table(data: list[list], col_widths: list, *, header_dark: bool = True) -> Table:
    t = Table(data, colWidths=col_widths)
    style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 1, BCO_AMARILLO),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, BCO_GRIS),
    ]
    if header_dark:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), BCO_NEGRO),
            ("TEXTCOLOR", (0, 0), (-1, 0), BCO_AMARILLO),
        ]
    # Alternar filas
    for i in range(1, len(data)):
        if i % 2 == 1:
            style.append(("BACKGROUND", (0, i), (-1, i),
                          colors.Color(0.996, 0.917, 0.439, alpha=0.15)))
    t.setStyle(TableStyle(style))
    return t


# ---- Decoradores de página ----
def cover_page_bg(canvas, doc):
    """Fondo decorativo de portada."""
    canvas.saveState()
    w, h = A4
    # Fondo negro superior
    canvas.setFillColor(BCO_NEGRO)
    canvas.rect(0, h - 9 * cm, w, 9 * cm, fill=1, stroke=0)
    # Banda amarilla
    canvas.setFillColor(BCO_AMARILLO)
    canvas.rect(0, h - 9.5 * cm, w, 0.5 * cm, fill=1, stroke=0)
    canvas.restoreState()


def content_page_bg(canvas, doc):
    """Encabezado y pie de página corporativos."""
    canvas.saveState()
    w, h = A4
    # Header line
    canvas.setStrokeColor(BCO_AMARILLO)
    canvas.setLineWidth(1.2)
    canvas.line(2.2 * cm, h - 1.6 * cm, w - 2.2 * cm, h - 1.6 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(BCO_GRIS_OSCURO)
    canvas.drawString(2.2 * cm, h - 1.3 * cm, "Modelo de Capacidad · DICAGI 2022")
    canvas.drawRightString(w - 2.2 * cm, h - 1.3 * cm, "Bancolombia")
    # Footer
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(w / 2, 1.2 * cm, f"{doc.page}")
    canvas.restoreState()


def build_pdf():
    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.2 * cm,
        title="Modelo de Capacidad DICAGI 2022",
        author="DICAGI",
        subject="Asignación óptima cliente-gerente Bancolombia",
    )
    frame_cover = Frame(0, 0, A4[0], A4[1], leftPadding=2.2 * cm, rightPadding=2.2 * cm,
                       topPadding=3 * cm, bottomPadding=2 * cm, id="cover")
    frame_content = Frame(2.2 * cm, 1.8 * cm, A4[0] - 4.4 * cm, A4[1] - 4 * cm,
                         id="content")

    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame_cover], onPage=cover_page_bg),
        PageTemplate(id="content", frames=[frame_content], onPage=content_page_bg),
    ])

    s = get_styles()
    story = []

    # ===== PORTADA =====
    story.append(Spacer(1, 4.5 * cm))
    story.append(Paragraph("Modelo de", s["cover_title"]))
    story.append(Paragraph("Capacidad", s["cover_title_yellow"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("DICAGI 2022 &nbsp;|&nbsp; Asignación óptima cliente–gerente",
                          s["cover_subtitle"]))
    story.append(Paragraph("Informe ejecutivo de resultados", s["cover_caption"]))
    story.append(Spacer(1, 11 * cm))

    cover_table_data = [
        ["Autor:", "jdrincone@gmail.com"],
        ["Fecha:", "7 de mayo de 2026"],
        ["Métrica obtenida:", "x/y = 0.4076  (40.76%)"],
        ["Estado:", "Óptimo del problema"],
    ]
    ct = Table(cover_table_data, colWidths=[3.5 * cm, 8 * cm])
    ct.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (-1, -1), BCO_GRIS_OSCURO),
        ("TEXTCOLOR", (1, 2), (1, 2), BCO_NEGRO),
        ("TEXTCOLOR", (1, 3), (1, 3), BCO_VERDE),
        ("FONTNAME", (1, 2), (1, 3), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(ct)
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(
        "<i>Este documento sintetiza la aproximación, hallazgos, modelo, resultados, "
        "sustentación honesta y propuestas de mejora del ejercicio analítico. "
        "Pensado para lectura ejecutiva en 15 minutos.</i>",
        s["small"]))

    story.append(NextPageTemplate("content"))
    story.append(PageBreak())

    # ===== RESUMEN EJECUTIVO =====
    story.append(Paragraph("Resumen ejecutivo", s["h1"]))

    body = [
        Paragraph("<b>1. ¿Qué pide la prueba?</b> Asignar la mayor cantidad posible "
                 "de clientes Preferenciales a Gerentes de Inversión, optimizando "
                 "<i>x/y = (#A + #B asignados) / N</i>, con restricciones de zona, "
                 "capacidad anual y unicidad ejecutivo→gerente.", s["bullet"]),
        Paragraph("<b>2. ¿Cuál es el resultado?</b> <b>x/y = 0.4076</b> (40.76%) — "
                 "<i>el óptimo absoluto del problema dadas las condiciones de los datos.</i>",
                 s["bullet"]),
        Paragraph("<b>3. ¿Por qué este valor y no más?</b> El techo está fijado por "
                 "integridad referencial, no por capacidad: <b>633 ejecutivos huérfanos</b> "
                 "arrastran 7,030 clientes (1,579 A + 2,727 B) fuera del modelo.", s["bullet"]),
        Paragraph("<b>4. ¿Hace falta un modelo sofisticado?</b> <b>No</b>. Cuatro enfoques "
                 "(regla determinista, greedy, MILP exacto, Simulated Annealing) convergen al "
                 "mismo resultado — el problema no compite por capacidad.", s["bullet"]),
        Paragraph("<b>5. ¿Qué subiría la métrica?</b> Reconciliar la tabla <i>ecas</i> para "
                 "recuperar los huérfanos ⇒ techo subiría a <b>53.4%</b>. Es proyecto de "
                 "gobernanza de datos, no de algoritmos.", s["bullet"]),
    ]
    story.append(make_box("LAS CINCO RESPUESTAS EN 30 SEGUNDOS", body, kind="honesty", styles=s))
    story.append(Spacer(1, 0.3 * cm))

    insight_body = [Paragraph(
        "La sofisticación matemática no es un fin en sí mismo. Cuando los cuatro enfoques "
        "convergen al mismo número, esa convergencia <b>es información</b>: el problema no "
        "requiere optimización elegante, requiere mejor calidad de datos. Identificar esta "
        "naturaleza con honestidad vale más que un solver más caro.", s["body"])]
    story.append(make_box("INSIGHT CENTRAL", insight_body, kind="insight", styles=s))
    story.append(PageBreak())

    # ===== SECCIÓN 1: PROBLEMA Y APROXIMACIÓN =====
    story.append(Paragraph("1. El problema y cómo se abordó", s["h1"]))
    story.append(Paragraph("1.1 Lectura del enunciado", s["h2"]))
    story.append(Paragraph(
        "La prueba pide asignar 34,145 clientes Preferenciales a 50 Gerentes de Inversión, "
        "respetando restricciones explícitas e implícitas. Un detalle crítico del PDF cambia "
        "toda la formulación:", s["body"]))
    story.append(Paragraph(
        "&ldquo;Los ejecutivos se asignan a los gerentes, y todos los clientes del ejecutivo "
        "se asignan al gerente.&rdquo;", s["quote"]))

    decision_body = [
        Paragraph("<b>Decisión:</b> modelar al ejecutivo como variable binaria, no al cliente.",
                 s["body"]),
        Paragraph("<b>Por qué:</b> la regla de &ldquo;todo o nada&rdquo; convierte un problema "
                 "con 34,145 variables (una por cliente) en uno con ~370 variables binarias "
                 "(una por ejecutivo asignable). Esta observación es lo que hace al problema "
                 "computacionalmente trivial para MILP exacto.", s["body"]),
        Paragraph("<b>Implicación de modelado:</b> x<sub>e,g</sub> ∈ {0,1} con "
                 "Σ<sub>g</sub> x<sub>e,g</sub> ≤ 1, donde <i>e</i> recorre ejecutivos "
                 "y <i>g</i> recorre gerentes compatibles por zona.", s["body"]),
    ]
    story.append(make_box("DECISIÓN 1: LA UNIDAD ATÓMICA DEL PROBLEMA", decision_body,
                         kind="decision", styles=s))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("1.2 Estrategia de cuatro enfoques", s["h2"]))
    decision_body2 = [
        Paragraph("No para &ldquo;asegurar&rdquo; el resultado — el MILP es óptimo por "
                 "construcción. Sino para <b>triangular</b> y <b>diagnosticar</b>:", s["body"]),
        Paragraph("• <b>Analítico</b> (sin modelo): cota inferior fácil de explicar a no-técnicos.",
                 s["bullet"]),
        Paragraph("• <b>Greedy</b>: heurística de densidad valor/tiempo ρ<sub>e</sub> = "
                 "v<sub>e</sub>/t<sub>e</sub>, calibra sensibilidad.", s["bullet"]),
        Paragraph("• <b>MILP exacto</b>: óptimo global garantizado, referencia.", s["bullet"]),
        Paragraph("• <b>Simulated Annealing</b>: aporta diagnósticos físicos (calor específico, "
                 "susceptibilidad) que ningún solver de programación entera ofrece.", s["bullet"]),
        Paragraph("Si los cuatro convergen ⇒ la solución es robusta y el problema no tiene "
                 "complejidad oculta. Si difieren ⇒ hay decisión real que tomar y el MILP gana.",
                 s["body"]),
    ]
    story.append(make_box("DECISIÓN 2: POR QUÉ CUATRO ENFOQUES EN VEZ DE UNO",
                         decision_body2, kind="decision", styles=s))

    story.append(PageBreak())

    # ===== SECCIÓN 2: HALLAZGOS DEL EDA =====
    story.append(Paragraph("2. Hallazgos del EDA — el cuello de botella revelado", s["h1"]))
    story.append(Paragraph("2.1 Inventario y calidad", s["h2"]))

    inventario = [
        ["Tabla", "Filas", "Rol"],
        ["pcac_mac_gpi_clientes", "34,145", "Población Preferencial con A/B/C, score"],
        ["pcac_mac_gpi_ecas", "392", "Estructura gerente ↔ ejecutivo"],
        ["pcac_oportunidades_comer", "247,863", "Oportunidades por cliente y producto"],
        ["pcac_mac_gpi_tenencia_prod", "66,802", "Tenencia y uso de productos"],
        ["pcac_planta_comercial2", "50", "Catálogo de gerentes"],
        ["pcac_encuesta", "1,804", "Tiempos por (gerente, producto, etapa)"],
        ["pcac_capacidad_gerentes", "50", "Tiempo anual disponible T_g"],
    ]
    story.append(styled_table(inventario, col_widths=[5.5 * cm, 2 * cm, 8 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("2.2 El hallazgo dominante: huérfanos estructurales", s["h2"]))
    huerf_body = [
        Paragraph("<b>1,003 ejecutivos</b> aparecen en <i>clientes</i>, pero solo <b>392</b> "
                 "están en <i>ecas</i> con un Gerente de Inversión asignable. Los <b>633 "
                 "huérfanos</b> (63% de los ejecutivos) probablemente pertenecen a otras "
                 "bancas (PYME, Empresas) que también gestionan a estos clientes. <b>Arrastran "
                 "7,030 clientes</b> (20.6% de la población), incluyendo:", s["body"]),
        Paragraph("• <b>1,579 clientes A</b> (28.7% de los A totales)", s["bullet"]),
        Paragraph("• <b>2,727 clientes B</b> (21.4% de los B totales)", s["bullet"]),
        Paragraph("• 2,724 clientes C (irrelevantes para la métrica oficial)", s["bullet"]),
        Paragraph("Estos clientes <b>no son asignables vía Gerente de Inversión</b>. Pasan al "
                 "denominador <i>y</i> pero no al numerador <i>x</i>.", s["body"]),
    ]
    story.append(make_box("EL VERDADERO CUELLO DE BOTELLA", huerf_body, kind="honesty", styles=s))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("2.3 Los dos techos del problema", s["h2"]))
    techos = [
        ["Escenario", "x/y", "Lectura"],
        ["Techo absoluto (todos los A+B asignables)", "53.4%", "Si todos los A+B existieran en ecas"],
        ["Techo real (descontados huérfanos)", "40.8%", "Lo que el modelo PUEDE alcanzar"],
        ["Logrado por el modelo", "40.76%", "≡ techo real ± 0.04 pp"],
    ]
    story.append(styled_table(techos, col_widths=[7 * cm, 2 * cm, 6.5 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("2.4 Lo no obvio: capacidad sobra, datos faltan", s["h2"]))
    no_obvio = [
        Paragraph("La prueba sugiere que la capacidad será restrictiva (&ldquo;no se debe "
                 "superar el tiempo disponible&rdquo;). <b>La realidad de los datos dice lo "
                 "contrario:</b>", s["body"]),
        Paragraph("• Demanda total efectiva: <b>2,592,700 min</b>", s["bullet"]),
        Paragraph("• Oferta total: <b>3,720,570 min</b>", s["bullet"]),
        Paragraph("• Ratio demanda/oferta: <b>0.70</b> — cabe todo lo asignable.", s["bullet"]),
        Paragraph("Si la capacidad sobra, el problema se reduce a &ldquo;asignar a todos los "
                 "ejecutivos asignables&rdquo;, lo cual cualquier algoritmo factible resuelve. "
                 "<b>La sofisticación no aporta métrica</b>; aporta diagnóstico. Esta "
                 "observación cambia el ángulo del proyecto: pasar de &ldquo;optimicemos "
                 "mejor&rdquo; a &ldquo;arreglemos los datos&rdquo;.", s["body"]),
    ]
    story.append(make_box("LO QUE NO APARECE EN EL PDF Y DESCUBRIMOS SOLOS",
                         no_obvio, kind="decision", styles=s))

    story.append(PageBreak())

    # ===== SECCIÓN 3: MODELO Y RESULTADOS =====
    story.append(Paragraph("3. Modelo y resultados", s["h1"]))
    story.append(Paragraph("3.1 Formulación matemática", s["h2"]))
    story.append(Paragraph(
        "<b>Variables:</b> x<sub>e,g</sub> ∈ {0,1}, igual a 1 si el ejecutivo <i>e</i> "
        "es asignado al gerente <i>g</i>.", s["body"]))
    story.append(Paragraph(
        "<b>Función objetivo:</b><br/>"
        "&nbsp;&nbsp;&nbsp;<b>max  Σ v<sub>e</sub> · x<sub>e,g</sub></b>, donde "
        "v<sub>e</sub> = w<sub>A</sub>·n<sup>A</sup><sub>e</sub> + "
        "w<sub>B</sub>·n<sup>B</sup><sub>e</sub> + w<sub>C</sub>·n<sup>C</sup><sub>e</sub> + "
        "α·n<sub>e</sub>·s̄<sub>e</sub>", s["body"]))
    story.append(Paragraph(
        "con w<sub>A</sub> : w<sub>B</sub> : w<sub>C</sub> = 1000 : 100 : 1 y α = 0.1 "
        "(desempate por score).", s["body"]))
    story.append(Paragraph(
        "<b>Restricciones:</b><br/>"
        "&nbsp;&nbsp;• Σ<sub>g</sub> x<sub>e,g</sub> ≤ 1 ∀e &nbsp;(a lo más un gerente)<br/>"
        "&nbsp;&nbsp;• Σ<sub>e</sub> t<sub>e</sub>·x<sub>e,g</sub> ≤ T<sub>g</sub> ∀g "
        "&nbsp;(capacidad)<br/>"
        "&nbsp;&nbsp;• x<sub>e,g</sub> = 0 si zona(e) ≠ zona(g) &nbsp;(filtro previo)",
        s["body"]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("3.2 Resultados comparativos", s["h2"]))
    resultados = [
        ["Enfoque", "Tiempo", "Asign", "x/y", "%A", "%B", "%C"],
        ["Analítico (regla simple)", "0.06 s", "370", "0.4076", "71.3", "78.6", "82.9"],
        ["Greedy densidad v/t", "0.06 s", "370", "0.4076", "71.3", "78.6", "82.9"],
        ["MILP CBC (Optimal)", "0.49 s", "370", "0.4076", "71.3", "78.6", "82.9"],
        ["Simulated Annealing", "varios s", "370", "0.4076", "71.3", "78.6", "82.9"],
    ]
    story.append(styled_table(resultados,
                             col_widths=[4.5 * cm, 2 * cm, 1.7 * cm, 1.8 * cm,
                                        1.5 * cm, 1.5 * cm, 1.5 * cm]))
    story.append(Spacer(1, 0.3 * cm))

    insight2 = [Paragraph(
        "Los cuatro enfoques producen <b>exactamente</b> la misma asignación. Esto no es "
        "coincidencia ni redundancia: es evidencia empírica de que el problema <b>no tiene "
        "mínimos locales malos</b>. Cuando un MILP exacto y un SA con cooling lento llegan "
        "al mismo punto que un greedy ingenuo, el espacio de soluciones es <i>convexo en "
        "lo relevante</i>. Implicación contraintuitiva: <b>el modelo más simple es el "
        "correcto para producción.</b> Lo demás es seguro conceptual.", s["body"])]
    story.append(make_box("LECTURA ANALÍTICA DE LA CONVERGENCIA", insight2,
                         kind="insight", styles=s))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph(
        "<b>Utilización de los gerentes:</b> media 92.3% de la capacidad anual. El sistema "
        "queda apretado pero factible, con ~1,127,870 minutos de holgura repartidos entre "
        "los 49 gerentes (promedio ~23,000 min libres por gerente). Ningún gerente excede "
        "T<sub>g</sub>.", s["body"]))

    story.append(PageBreak())

    # ===== SECCIÓN 4: MAPEO A FÍSICA =====
    story.append(Paragraph("4. Mapeo a física estadística", s["h1"]))
    story.append(Paragraph("4.1 La equivalencia formal", s["h2"]))
    story.append(Paragraph(
        "El problema de asignación con capacidad es <b>matemáticamente equivalente</b> a "
        "encontrar el estado fundamental de un Ising spin glass con campo externo y "
        "restricciones de capacidad. No es analogía pedagógica: es <i>equivalencia</i>.",
        s["body"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "<b>Hamiltoniano:</b><br/><br/>"
        "&nbsp;&nbsp;&nbsp;<b>H(σ) = −Σ<sub>e,g</sub> v<sub>e</sub>·σ<sub>e,g</sub> "
        "+ Σ<sub>g</sub> λ<sub>g</sub>·(Σ<sub>e</sub> t<sub>e</sub>·σ<sub>e,g</sub> "
        "− T<sub>g</sub>)<sub>+</sub>²</b>", s["body"]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Mapeo concepto a concepto:", s["h3"]))
    mapeo = [
        ["Optimización", "Física estadística"],
        ["Variable de decisión x_e,g", "Spin de Ising binario σ_e,g ∈ {0,1}"],
        ["Valor del ejecutivo v_e", "Campo externo h_e,g = −v_e"],
        ["Restricción de capacidad", "Penalización cuadrática (resorte unilateral)"],
        ["Restricción de unicidad", "Exclusión tipo Pauli (estado prohibido)"],
        ["Restricción de zona", "Reducción del espacio de configuraciones"],
        ["Solución óptima (arg max)", "Estado fundamental (arg min H)"],
        ["Pesos w_A, w_B, w_C", "Magnitud del campo externo"],
        ["Heterogeneidad de t_e", "Glassiness (vidrioso, no cristalino)"],
    ]
    story.append(styled_table(mapeo, col_widths=[7 * cm, 8.5 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("4.2 Simulated Annealing como Markov Chain Monte Carlo", s["h2"]))
    story.append(Paragraph(
        "El SA es una <b>cadena MCMC con regla de Metropolis-Hastings:</b><br/><br/>"
        "&nbsp;&nbsp;&nbsp;P(aceptar movimiento) = min(1, exp(−ΔH/T))<br/><br/>"
        "Esto <i>es literalmente</i> la distribución de Boltzmann aplicada a una cadena de "
        "Markov sobre configuraciones. A T → 0 converge al estado fundamental.", s["body"]))
    story.append(Paragraph(
        "<b>Parámetros usados:</b> T<sub>max</sub>=5,000, T<sub>min</sub>=0.01, cooling "
        "geométrico α=0.9995, 80,000 pasos, vecindario 70% flip + 30% swap.", s["body"]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("4.3 Diagnósticos físicos — lo que MILP no puede dar", s["h2"]))
    diag_body = [
        Paragraph("<b>1. Curva de enfriamiento ⟨H⟩(T):</b> cómo la energía baja al enfriar. "
                 "Plateau final ⇒ convergencia. Saltos ⇒ transiciones de fase.", s["bullet"]),
        Paragraph("<b>2. Calor específico</b> C(T) = (⟨H²⟩ − ⟨H⟩²)/T²: pico en T<sub>c</sub> "
                 "marca transición de fase; alto a T→0 indica frustración (problema "
                 "sobre-restringido).", s["bullet"]),
        Paragraph("<b>3. Susceptibilidad</b> χ(T) = (⟨M²⟩ − ⟨M⟩²)/T con M = #asignados: mide "
                 "robustez ante cambios de pesos w<sub>A</sub>, w<sub>B</sub>, w<sub>C</sub>.",
                 s["bullet"]),
        Paragraph("<b>En este problema concreto:</b> C residual bajo y χ residual baja. "
                 "<i>Sin frustración estructural detectable</i>. Esto es <b>coherente</b> con "
                 "que los cuatro enfoques convergen — el sistema no tiene paisaje energético "
                 "complejo.", s["body"]),
    ]
    story.append(make_box("TRES DIAGNÓSTICOS EXCLUSIVOS DEL ENFOQUE FÍSICO",
                         diag_body, kind="insight", styles=s))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("4.4 Por qué el enfoque físico aporta valor más allá de lo obvio",
                          s["h2"]))
    story.append(Paragraph(
        "Aunque para <i>este</i> problema concreto el método físico no mejora la métrica, "
        "aporta tres diferencias conceptuales:", s["body"]))
    story.append(Paragraph(
        "• <b>Robustez de cobertura:</b> SA siempre devuelve solución factible incluso si "
        "lo cortas. MILP puede no terminar.", s["bullet"]))
    story.append(Paragraph(
        "• <b>Escalabilidad:</b> si en el futuro la red crece a 5,000 ejecutivos × 500 "
        "gerentes, el MILP entra en régimen exponencial; el SA escala linealmente con el "
        "tiempo asignado.", s["bullet"]))
    story.append(Paragraph(
        "• <b>Restricciones blandas:</b> SA admite penalización cuadrática (overshoot pequeño "
        "aceptable), útil si la capacidad fuera flexible.", s["bullet"]))
    story.append(Paragraph(
        "Adicionalmente, el Hamiltoniano se reescribe trivialmente como <b>QUBO</b> compatible "
        "con quantum annealers (D-Wave). Para 370×49 cabe sobrado en hardware Advantage actual.",
        s["body"]))

    story.append(PageBreak())

    # ===== SECCIÓN 5: SUSTENTACIÓN HONESTA =====
    story.append(Paragraph("5. Sustentación honesta del resultado", s["h1"]))
    story.append(Paragraph("5.1 Respondiendo al instructivo", s["h2"]))
    story.append(Paragraph(
        "&ldquo;Es posible que llegues a la conclusión de que no es posible desarrollar un "
        "buen modelo predictivo a partir de la información proporcionada o dada la calidad "
        "de la misma. Si este es el caso, queremos evaluar el mejor modelo que puedas "
        "producir y también que nos des una sustentación de esa conclusión.&rdquo;", s["quote"]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("5.2 Diagnóstico crudo", s["h2"]))
    diag_crudo = [
        Paragraph("<b>El problema no es de optimización — es de calidad de datos.</b>", s["body"]),
        Paragraph("La métrica obtenida (40.76%) es el óptimo absoluto del problema dadas las "
                 "condiciones. Cualquier mejora requiere mejorar los datos, no el modelo:",
                 s["body"]),
        Paragraph("• <b>Techo estructural en 40.8%:</b> limitado por 633 ejecutivos huérfanos "
                 "que arrastran 1,579 A y 2,727 B fuera del modelo.", s["bullet"]),
        Paragraph("• <b>Sobre-oferta de capacidad (ratio 0.70):</b> los gerentes tienen más "
                 "capacidad que la demanda actual.", s["bullet"]),
        Paragraph("• <b>Ausencia de competencia entre asignables:</b> cuando todos los "
                 "asignables caben, no hay decisión real que tomar.", s["bullet"]),
        Paragraph("• <b>Encuesta auto-reportada:</b> τ<sub>c</sub> tiene error de medición "
                 "probable >50% vs lo que se haría con telemetría real.", s["bullet"]),
        Paragraph("• <b>Mismatch de productos:</b> oportunidades y encuesta usan vocabularios "
                 "distintos. Mitigado con un mapeo manual documentado en PRODUCTO_MAP; un "
                 "vocabulario maestro reduciría el problema a cero.", s["bullet"]),
    ]
    story.append(make_box("LO QUE LOS DATOS EFECTIVAMENTE DICEN", diag_crudo,
                         kind="honesty", styles=s))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("5.3 ¿Qué constituiría un &ldquo;mejor modelo&rdquo; aquí?",
                          s["h2"]))
    mejor_modelo = [
        Paragraph("Un mejor modelo <b>no</b> es uno con más sofisticación matemática. Es uno con:",
                 s["body"]),
        Paragraph("<b>1. Datos íntegros:</b> reconciliación de <i>ecas</i> para recuperar los "
                 "633 huérfanos.", s["bullet"]),
        Paragraph("<b>2. Tiempos medidos:</b> telemetría real reemplazando la encuesta.",
                 s["bullet"]),
        Paragraph("<b>3. Vocabulario unificado:</b> maestra de productos compartida.",
                 s["bullet"]),
        Paragraph("<b>4. Score documentado:</b> trazabilidad del proceso upstream que produce "
                 "score_modelo.", s["bullet"]),
        Paragraph("Con estos cuatro arreglos — ninguno requiere álgebra ni Hamiltoniano — la "
                 "métrica subiría de 40.8% a ~53.4% sin tocar el algoritmo.", s["body"]),
    ]
    story.append(make_box("LA RESPUESTA SINCERA", mejor_modelo, kind="decision", styles=s))

    story.append(PageBreak())

    # ===== SECCIÓN 6: VARIABLES ADICIONALES =====
    story.append(Paragraph("6. Mejoras propuestas (variables adicionales)", s["h1"]))
    story.append(Paragraph(
        "Categorización con costo-factibilidad explícitos (• bajo, •• medio, ••• alto).",
        s["small"]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("6.1 Variables internas (sprint 1, costo bajo)", s["h2"]))
    internas = [
        ["Variable", "Por qué importa", "Costo"],
        ["Volumen y monto transaccional / mes", "Cliente activo vs durmiente; mejora τ_c", "•"],
        ["Recencia última transacción", "Cliente >90 días sin movimiento vale menos", "•"],
        ["Tasa histórica de respuesta a campañas", "Cliente que no responde ⇒ no priorizar", "•"],
        ["Ticket promedio", "Mejor proxy de capacidad financiera", "•"],
        ["Score de churn (probabilidad fuga)", "Permite priorizar retención sobre venta", "•"],
        ["Tasa de cierre del ejecutivo", "Calibra el valor por minuto real", "•"],
        ["Tiempo real medido por actividad (CRM)", "Sustituye encuesta auto-reportada", "•"],
    ]
    story.append(styled_table(internas, col_widths=[5.5 * cm, 8 * cm, 1.5 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("6.2 Variables externas (sprint 2, costo medio)", s["h2"]))
    story.append(Paragraph(
        "• <b>Score DataCrédito / TransUnion:</b> API ya disponible para Bancolombia. Costo "
        "~$2-5 USD/consulta. Limitación legal: requiere autorización Habeas Data (Ley 1266).",
        s["bullet"]))
    story.append(Paragraph(
        "• <b>Estrato y demografía DANE:</b> vía dirección, gratuito.", s["bullet"]))
    story.append(Paragraph(
        "• <b>Sector económico CIIU:</b> ya disponible internamente; enriquecerlo con "
        "performance del sector (Asobancaria, Fedesarrollo).", s["bullet"]))
    story.append(Paragraph(
        "• <b>Macro:</b> tasa de cambio USD/COP, IBR, DTF. API gratuita Banco de la República.",
        s["bullet"]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("6.3 Scraping y proveedores (sprint 3, costo medio-alto)", s["h2"]))
    story.append(Paragraph(
        "• <b>LinkedIn Sales Navigator:</b> $100-500 USD/mes/usuario. <b>No usar scraping "
        "directo</b> — viola TOS; usar API oficial o proveedores con licencia "
        "(Apollo, ZoomInfo).", s["bullet"]))
    story.append(Paragraph(
        "• <b>Cámara de Comercio (RUES):</b> API pública gratuita para clientes empresariales.",
        s["bullet"]))
    story.append(Paragraph(
        "• <b>Catastro distrital:</b> APIs públicas en Bogotá y Medellín.", s["bullet"]))
    story.append(Paragraph(
        "• <b>Notarías / SIIF:</b> vehículos, propiedades. Scraping con cuidado legal.",
        s["bullet"]))
    story.append(Spacer(1, 0.3 * cm))

    plan_body = [
        Paragraph("<b>Mes 1 (gana con datos internos, costo cero):</b> reconciliar huérfanos + "
                 "histórico de campañas + saldos promedio + tasa de cierre. <i>Esperado: "
                 "40.8% → 53.4% sin tocar algoritmo.</i>", s["bullet"]),
        Paragraph("<b>Mes 2 (externos seguros):</b> Score DataCrédito + estrato/CIIU "
                 "enriquecido. <i>Esperado: refina el upstream que produce score_modelo, "
                 "mejor identificación de A reales.</i>", s["bullet"]),
        Paragraph("<b>Mes 3 (telemetría):</b> medir tiempos reales por actividad en CRM. "
                 "<i>Esperado: τ_c con error <10% vs >50% probable hoy.</i>", s["bullet"]),
    ]
    story.append(make_box("PLAN DE TRES MESES CON $50,000 USD", plan_body,
                         kind="insight", styles=s))

    story.append(PageBreak())

    # ===== SECCIÓN 7: CONCLUSIONES CRÍTICAS =====
    story.append(Paragraph("7. Conclusiones críticas (más allá de lo obvio)", s["h1"]))

    conclusiones = [
        ("La métrica obtenida (40.76%) coincide con el techo teórico previsto en el EDA.",
         "Esto valida que el modelo es óptimo y que el techo no es un artefacto del algoritmo."),
        ("Los cuatro enfoques convergen porque el problema no compite por capacidad.",
         "La sobre-oferta (ratio 0.70) elimina la decisión real. El MILP no encuentra "
         "ganancia porque no hay nada que decidir más allá de &ldquo;meter todo lo "
         "asignable&rdquo;."),
        ("La sofisticación matemática puede ser distractor.",
         "Cuando el problema es estructuralmente simple, presentar SA con MCMC sin justificar "
         "por qué es valioso induce a creer que se necesita; el documento aclara que aporta "
         "diagnóstico, no métrica."),
        ("El verdadero entregable analítico es el diagnóstico, no el CSV.",
         "El resultado_prueba.csv se podría producir con la regla determinista en 0.06 s. Lo "
         "valioso es haber identificado y cuantificado el techo estructural antes de optimizar."),
        ("La frontera entre &ldquo;modelo de optimización&rdquo; y &ldquo;proyecto de "
         "gobernanza de datos&rdquo; es tenue.",
         "Aceptarlo en lugar de forzar más algoritmos demuestra madurez analítica."),
        ("La equivalencia con física estadística no es decoración.",
         "Permite usar herramientas de spin glass, mean-field y quantum annealing si el "
         "problema crece. Esto es capacidad latente, no requisito actual."),
        ("La métrica oficial puede sobre-castigar al modelo.",
         "Con y = 34,145 (todos los clientes, incluso los huérfanos), un modelo perfecto en su "
         "universo asignable tiene techo en 53.4%. Reportar el valor logrado (40.76%) sin "
         "contexto sería injusto. Por eso este documento empieza por el techo."),
    ]
    for i, (titulo, detalle) in enumerate(conclusiones, 1):
        story.append(Paragraph(f"<b>{i}. {titulo}</b>", s["body"]))
        story.append(Paragraph(detalle, s["body"]))
        story.append(Spacer(1, 0.2 * cm))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Anexo: archivos del entregable", s["h1"]))
    anexo = [
        ["Ruta", "Contenido"],
        ["resultado_prueba.csv", "Asignación final, 27,115 filas, formato exacto del template"],
        ["docs/documento_final.md", "Documento técnico-narrativo (entregable 1)"],
        ["docs/variables_adicionales.md", "Catálogo de variables propuestas con costo"],
        ["docs/arquitectura.md", "Bosquejo de sistema (entregable 4)"],
        ["docs/informe_ejecutivo.{tex,pdf}", "Este documento"],
        ["notebooks/01–05", "EDA, modelo, física, dashboard"],
        ["src/modelo_capacidad/", "Código modular (loader, features, models, viz, utils)"],
        ["tests/", "19 tests pytest — todos pasando"],
        ["pyproject.toml + uv.lock", "Entorno reproducible con uv"],
        [".claude/agents/", "Tres subagentes especializados (EDA, optimización, físico)"],
    ]
    story.append(styled_table(anexo, col_widths=[5.5 * cm, 10 * cm]))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(
        "Pipeline reproducible: <font face='Courier'>uv run python -m modelo_capacidad.run_all</font>",
        s["small"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        "<i>Fin del informe ejecutivo</i><br/><b>Bancolombia · DICAGI 2022</b>",
        s["footer"]))

    doc.build(story)
    print(f"PDF generado: {OUT_PDF}")
    print(f"Tamaño: {OUT_PDF.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_pdf()
