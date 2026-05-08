"""Tema visual corporativo Bancolombia para Plotly.

Paleta oficial:
    - Candlelight (amarillo principal): #FDDA24
    - Dune (negro / texto): #2C2A29
    - Cloudy (gris neutro): #ABA59D
    - Blanco: #FFFFFF

Uso:
    >>> from modelo_capacidad.viz import apply_theme
    >>> apply_theme()  # registra el template y lo activa por defecto
    >>> import plotly.express as px
    >>> px.bar(df, x="x", y="y")  # ya viene tematizado
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

BANCOLOMBIA_COLORS: dict[str, str] = {
    "amarillo": "#FDDA24",
    "amarillo_claro": "#FFE970",
    "amarillo_oscuro": "#E5BD00",
    "negro": "#2C2A29",
    "gris": "#ABA59D",
    "gris_claro": "#D9D5CF",
    "gris_oscuro": "#6B6863",
    "blanco": "#FFFFFF",
    "rojo_alerta": "#D62828",
    "verde_ok": "#2D8F4E",
    "azul_info": "#1F4E79",
}

BANCOLOMBIA_CATEGORICAL: list[str] = [
    "#FDDA24",
    "#2C2A29",
    "#ABA59D",
    "#1F4E79",
    "#2D8F4E",
    "#D62828",
    "#E5BD00",
    "#6B6863",
    "#FFE970",
    "#D9D5CF",
]

BANCOLOMBIA_SEQUENTIAL: list[list[float | str]] = [
    [0.00, "#FFFFFF"],
    [0.20, "#FFE970"],
    [0.45, "#FDDA24"],
    [0.70, "#E5BD00"],
    [1.00, "#2C2A29"],
]

BANCOLOMBIA_DIVERGING: list[list[float | str]] = [
    [0.00, "#1F4E79"],
    [0.50, "#FFFFFF"],
    [1.00, "#FDDA24"],
]


def bancolombia_template() -> go.layout.Template:
    """Construye el template Plotly de Bancolombia."""
    negro = BANCOLOMBIA_COLORS["negro"]
    gris = BANCOLOMBIA_COLORS["gris"]
    gris_claro = BANCOLOMBIA_COLORS["gris_claro"]

    return go.layout.Template(
        layout=go.Layout(
            font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=13, color=negro),
            title=dict(
                font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=18, color=negro),
                x=0.02,
                xanchor="left",
            ),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            colorway=BANCOLOMBIA_CATEGORICAL,
            xaxis=dict(
                showgrid=True,
                gridcolor=gris_claro,
                gridwidth=1,
                zeroline=False,
                linecolor=gris,
                ticks="outside",
                tickcolor=gris,
                title=dict(font=dict(size=13, color=negro)),
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=gris_claro,
                gridwidth=1,
                zeroline=False,
                linecolor=gris,
                ticks="outside",
                tickcolor=gris,
                title=dict(font=dict(size=13, color=negro)),
            ),
            legend=dict(
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor=gris_claro,
                borderwidth=1,
                font=dict(size=12, color=negro),
            ),
            hoverlabel=dict(
                bgcolor="#2C2A29",
                bordercolor="#FDDA24",
                font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=12, color="#FFFFFF"),
            ),
            colorscale=dict(
                sequential=BANCOLOMBIA_SEQUENTIAL,
                diverging=BANCOLOMBIA_DIVERGING,
            ),
            margin=dict(l=70, r=30, t=70, b=60),
        )
    )


def apply_theme(set_default: bool = True) -> None:
    """Registra el template y, opcionalmente, lo deja como default global."""
    pio.templates["bancolombia"] = bancolombia_template()
    if set_default:
        pio.templates.default = "bancolombia"


def watermark(fig: go.Figure, text: str = "DICAGI · Bancolombia") -> go.Figure:
    """Añade una marca tenue en la esquina inferior derecha del fig."""
    fig.add_annotation(
        text=text,
        xref="paper",
        yref="paper",
        x=1.0,
        y=-0.18,
        xanchor="right",
        yanchor="top",
        showarrow=False,
        font=dict(size=10, color=BANCOLOMBIA_COLORS["gris_oscuro"]),
        opacity=0.7,
    )
    return fig
