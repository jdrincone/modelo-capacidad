"""Genera el informe ejecutivo en PDF renderizando el HTML con Playwright.

Esto garantiza que el PDF es una copia 1:1 del informe interactivo
(mismo diseño, mismas cifras, mismas gráficas Plotly y fórmulas KaTeX).

Usage:
    uv run python -m modelo_capacidad.generate_report
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HTML_PATH = REPO_ROOT / "docs" / "index.html"
OUT_PDF = REPO_ROOT / "docs" / "informe_ejecutivo.pdf"


def build_pdf() -> None:
    from playwright.sync_api import sync_playwright

    if not HTML_PATH.exists():
        raise FileNotFoundError(f"No existe {HTML_PATH}. ¿Está el HTML en docs/?")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1200, "height": 1700})
        page = context.new_page()
        page.goto(HTML_PATH.as_uri(), wait_until="networkidle", timeout=60_000)
        # Pausa para que Plotly y KaTeX terminen de renderizar
        page.wait_for_timeout(4000)

        page.emulate_media(media="print")
        page.pdf(
            path=str(OUT_PDF),
            format="A4",
            print_background=True,
            margin={"top": "12mm", "right": "10mm", "bottom": "12mm", "left": "10mm"},
            prefer_css_page_size=True,
        )
        browser.close()

    size_kb = OUT_PDF.stat().st_size / 1024
    print(f"PDF generado: {OUT_PDF}")
    print(f"Tamaño: {size_kb:.1f} KB")


if __name__ == "__main__":
    build_pdf()
