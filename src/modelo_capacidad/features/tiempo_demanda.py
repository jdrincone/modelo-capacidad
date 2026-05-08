"""Cálculo del tiempo demandado por cliente (τ_c) y por ejecutivo (t_e).

Fórmula:
    τ_c = Σ_p [
        1{no tiene}            · (t_venta_p + t_instrum_p)
      + 1{tiene pero no usa}   · t_post_p
    ]
    t_e = Σ_{c en C_e} τ_c

Los tiempos por (producto, etapa) se toman como mediana sobre la encuesta
para robustez frente a outliers de auto-reporte.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

ETAPAS_VENTA_NUEVA = ("Venta", "Instrumentación", "Conexión")
ETAPA_POSTVENTA = "Postventa"

# Mapeo manual de nombres de producto en oportunidades → nombres en encuesta.
# Razón: las dos tablas usan vocabularios distintos. Sin este mapeo, ~55% de las
# oportunidades quedan con τ_c = 0 al no encontrar tiempo en la encuesta.
PRODUCTO_MAP: dict[str, str] = {
    # Inversión renta fija — el más voluminoso (108k oport)
    "tiene_rta_fija_valores": "Renta Fija",
    # Derivados / opciones
    "tiene_opciones": "Derivados",
    # Productos sofisticados — usar tiene_ubs como proxy
    "grp_inversiones_sofisticadas": "tiene_ubs",
    # Fondos especializados — promedio de fondos
    "grp_fondos_especializados": "tiene_fondo_balanceado",
    # "Otros" — sin match razonable, queda en 0 (transparencia)
}


@dataclass
class TablaTiempos:
    """Lookup table de minutos medianos por (producto, etapa)."""

    df: pd.DataFrame  # columnas: producto, etapa_del_producto, minutos_mediana

    def get(self, producto: str, etapa: str, default: float = 0.0) -> float:
        m = self.df[(self.df["producto"] == producto) & (self.df["etapa_del_producto"] == etapa)]
        if m.empty:
            return default
        return float(m["minutos_mediana"].iloc[0])


def construir_tabla_tiempos(encuesta: pd.DataFrame) -> TablaTiempos:
    """Mediana de minutos por (producto, etapa)."""
    df = (
        encuesta.dropna(subset=["producto", "etapa_del_producto", "total_promedio_tiempo_min_x_actividad"])
        .groupby(["producto", "etapa_del_producto"])["total_promedio_tiempo_min_x_actividad"]
        .median()
        .reset_index()
        .rename(columns={"total_promedio_tiempo_min_x_actividad": "minutos_mediana"})
    )
    return TablaTiempos(df=df)


def _minutos_caso(
    tabla: TablaTiempos,
    producto: str,
    tiene: int | float,
    usa: int | float,
) -> float:
    """Aplica la regla de τ por caso de tenencia."""
    if pd.isna(tiene) or tiene == 0:
        # Caso 1: venta nueva — paga venta + instrumentación + conexión
        return sum(tabla.get(producto, e) for e in ETAPAS_VENTA_NUEVA)
    if pd.isna(usa) or usa == 0:
        # Caso 2: tiene pero no usa — paga post-venta (activación)
        return tabla.get(producto, ETAPA_POSTVENTA)
    # Caso 3: tiene y usa — sin tiempo
    return 0.0


def calcular_tau_cliente(
    oportunidades: pd.DataFrame,
    tenencia: pd.DataFrame,
    encuesta: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula τ_c para cada cliente. Vectorizado: ~1 s para 250k oportunidades.

    Returns
    -------
    DataFrame[num_doc_cli, tau, n_oportunidades]
    """
    tabla = construir_tabla_tiempos(encuesta)

    # Precomputar tiempo agregado por producto y caso (venta nueva vs activación)
    venta_nueva = (
        tabla.df[tabla.df["etapa_del_producto"].isin(ETAPAS_VENTA_NUEVA)]
        .groupby("producto")["minutos_mediana"]
        .sum()
        .to_dict()
    )
    postventa = (
        tabla.df[tabla.df["etapa_del_producto"] == ETAPA_POSTVENTA]
        .groupby("producto")["minutos_mediana"]
        .sum()
        .to_dict()
    )

    ten = tenencia[["num_doc_cli", "cod_prod", "tenencia", "usa_producto"]].rename(
        columns={"cod_prod": "cod_producto"}
    )
    df = oportunidades.merge(ten, on=["num_doc_cli", "cod_producto"], how="left")
    df["producto_norm"] = df["producto"].replace(PRODUCTO_MAP)

    # Lookup vectorizado (np.where por caso)
    t_venta = df["producto_norm"].map(venta_nueva).fillna(0.0).to_numpy()
    t_post = df["producto_norm"].map(postventa).fillna(0.0).to_numpy()

    tenencia_arr = df["tenencia"].fillna(0).to_numpy()
    usa_arr = df["usa_producto"].fillna(0).to_numpy()

    # Caso 1: no tiene → t_venta_nueva
    # Caso 2: tiene pero no usa → t_postventa
    # Caso 3: tiene y usa → 0
    no_tiene = tenencia_arr == 0
    tiene_no_usa = (tenencia_arr == 1) & (usa_arr == 0)
    minutos = np.where(no_tiene, t_venta, np.where(tiene_no_usa, t_post, 0.0))

    df["minutos"] = minutos
    tau = (
        df.groupby("num_doc_cli")
        .agg(tau=("minutos", "sum"), n_oportunidades=("minutos", "count"))
        .reset_index()
    )
    return tau


def construir_df_ejecutivos(
    clientes: pd.DataFrame,
    tau_cliente: pd.DataFrame,
    ecas: pd.DataFrame,
    *,
    w_a: float = 1000.0,
    w_b: float = 100.0,
    w_c: float = 1.0,
    alpha_score: float = 0.1,
) -> pd.DataFrame:
    """Agrega clientes a nivel ejecutivo y calcula t_e y v_e.

    Solo se conservan ejecutivos que aparecen en `ecas` (con gerente asignable).
    """
    ejec_validos = set(ecas["cod_ejec_bco"].dropna().unique())
    cli = clientes.merge(tau_cliente, on="num_doc_cli", how="left")
    cli["tau"] = cli["tau"].fillna(0.0)

    cli = cli[cli["cod_ejec_bco"].isin(ejec_validos)].copy()

    df_ejec = (
        cli.groupby("cod_ejec_bco")
        .agg(
            zona=("cod_region_gte_inv", "first"),
            n_clientes=("num_doc_cli", "count"),
            n_a=("marca_mac_inv", lambda s: int((s == "A").sum())),
            n_b=("marca_mac_inv", lambda s: int((s == "B").sum())),
            n_c=("marca_mac_inv", lambda s: int((s == "C").sum())),
            score_medio=("score_modelo", "mean"),
            t_e=("tau", "sum"),
        )
        .reset_index()
    )
    df_ejec["score_medio"] = df_ejec["score_medio"].fillna(0.0)
    df_ejec["v_e"] = (
        w_a * df_ejec["n_a"]
        + w_b * df_ejec["n_b"]
        + w_c * df_ejec["n_c"]
        + alpha_score * df_ejec["score_medio"] * df_ejec["n_clientes"]
    )
    df_ejec["densidad"] = df_ejec["v_e"] / df_ejec["t_e"].clip(lower=1.0)
    return df_ejec


def construir_df_gerentes(capacidad: pd.DataFrame, ecas: pd.DataFrame) -> pd.DataFrame:
    """Agrega capacidad y zona por gerente. Solo gerentes con equipo en ecas."""
    gtes_con_equipo = set(ecas["cod_gte_inv"].dropna().unique())
    df_ger = capacidad[capacidad["cod_gte_inv"].isin(gtes_con_equipo)].copy()
    df_ger = df_ger.rename(columns={"cod_region_gte_inv": "zona", "tiempo_restante": "T_g"})[
        ["cod_gte_inv", "zona", "T_g"]
    ].reset_index(drop=True)
    return df_ger
