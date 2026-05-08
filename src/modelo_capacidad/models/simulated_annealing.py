"""Simulated Annealing sobre el Hamiltoniano de Ising con restricciones de capacidad.

Hamiltoniano:
    H(σ) = -Σ_{e,g} v_e σ_eg  +  Σ_g λ_g (Σ_e t_e σ_eg - T_g)_+²

Variables:
    σ_eg ∈ {0,1} con Σ_g σ_eg ≤ 1 (restricción dura: estado 'no asignado' permitido)
    σ_eg = 0 si zona(e) ≠ zona(g) (filtro previo)

Algoritmo: Metropolis-Hastings con cooling schedule geométrico.
Movimientos del vecindario:
    - flip: cambia el gerente de un ejecutivo (incluye desasignar)
    - swap: intercambia gerentes entre dos ejecutivos compatibles
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class SAParams:
    T_max: float = 5_000.0
    T_min: float = 0.01
    cooling_rate: float = 0.9995
    n_steps: int = 100_000
    lambda_capacity: float = 0.001  # rigidez del muro (escalado al orden de v_e)
    p_swap: float = 0.3  # probabilidad de proponer swap vs flip
    seed: int = 42
    sample_every: int = 200  # cada cuántos steps registrar telemetría


@dataclass
class SAState:
    """Estado mutable del sistema."""

    asignacion: dict[str, Optional[str]]   # cod_ejec_bco -> cod_gte_inv (o None)
    capacidad_libre: dict[str, float]      # cod_gte_inv -> T_g - usado
    valor_total: float                     # Σ v_e por ejecutivos asignados
    exceso_total: float                    # Σ (max(0, usado-T_g))²


@dataclass
class SAHistory:
    T: list[float] = field(default_factory=list)
    H: list[float] = field(default_factory=list)
    valor: list[float] = field(default_factory=list)
    M: list[int] = field(default_factory=list)  # # ejecutivos asignados
    accept_rate: list[float] = field(default_factory=list)


def energia(state: SAState, lambda_cap: float) -> float:
    """H = -Σ v_e σ_eg + λ Σ exceso_g²."""
    return -state.valor_total + lambda_cap * state.exceso_total


def _exceso(usado: float, T_g: float) -> float:
    return max(0.0, usado - T_g) ** 2


def initialize_state(df_ejec: pd.DataFrame, df_ger: pd.DataFrame) -> SAState:
    """Estado inicial: nadie asignado (factible trivialmente)."""
    asign = {e: None for e in df_ejec["cod_ejec_bco"]}
    libre = df_ger.set_index("cod_gte_inv")["T_g"].astype(float).to_dict()
    return SAState(asignacion=asign, capacidad_libre=libre, valor_total=0.0, exceso_total=0.0)


def _candidatos_zona(
    e: str, df_ejec_idx: dict, df_ger: pd.DataFrame, gerentes_por_zona: dict
) -> list[str]:
    z = df_ejec_idx[e]["zona"]
    return gerentes_por_zona.get(z, [])


def _delta_assign(
    state: SAState,
    e: str,
    nuevo_g: Optional[str],
    df_ejec_idx: dict,
    df_ger_idx: dict,
    lambda_cap: float,
) -> tuple[float, dict]:
    """Calcula ΔH si reasignáramos el ejecutivo e a nuevo_g.

    Returns
    -------
    (delta_H, info_para_aplicar)
    """
    info = df_ejec_idx[e]
    t_e = info["t_e"]
    v_e = info["v_e"]
    g_actual = state.asignacion[e]

    if g_actual == nuevo_g:
        return 0.0, {}

    delta_valor = 0.0
    delta_exceso = 0.0
    libre_actualizado = {}

    # Quitar de g_actual
    if g_actual is not None:
        T_act = df_ger_idx[g_actual]["T_g"]
        usado_actual = T_act - state.capacidad_libre[g_actual]
        usado_nuevo = usado_actual - t_e
        exceso_old = _exceso(usado_actual, T_act)
        exceso_new = _exceso(usado_nuevo, T_act)
        delta_exceso += exceso_new - exceso_old
        delta_valor -= v_e
        libre_actualizado[g_actual] = state.capacidad_libre[g_actual] + t_e

    # Añadir a nuevo_g
    if nuevo_g is not None:
        T_new = df_ger_idx[nuevo_g]["T_g"]
        usado_actual = T_new - state.capacidad_libre[nuevo_g]
        usado_nuevo = usado_actual + t_e
        exceso_old = _exceso(usado_actual, T_new)
        exceso_new = _exceso(usado_nuevo, T_new)
        delta_exceso += exceso_new - exceso_old
        delta_valor += v_e
        libre_actualizado[nuevo_g] = state.capacidad_libre[nuevo_g] - t_e

    delta_H = -delta_valor + lambda_cap * delta_exceso
    return delta_H, {
        "delta_valor": delta_valor,
        "delta_exceso": delta_exceso,
        "libre_actualizado": libre_actualizado,
        "nuevo_g": nuevo_g,
    }


def _apply_assign(state: SAState, e: str, info: dict) -> None:
    if not info:
        return
    state.valor_total += info["delta_valor"]
    state.exceso_total += info["delta_exceso"]
    for g, libre in info["libre_actualizado"].items():
        state.capacidad_libre[g] = libre
    state.asignacion[e] = info["nuevo_g"]


def run_sa(
    df_ejec: pd.DataFrame,
    df_ger: pd.DataFrame,
    params: SAParams | None = None,
) -> tuple[SAState, SAHistory]:
    """Bucle principal de Simulated Annealing.

    Movimientos: 'flip' (probabilidad 1-p_swap) y 'swap' (p_swap).
    """
    if params is None:
        params = SAParams()
    rng = np.random.default_rng(params.seed)

    df_ejec_idx = df_ejec.set_index("cod_ejec_bco")[["zona", "t_e", "v_e"]].to_dict("index")
    df_ger_idx = df_ger.set_index("cod_gte_inv")[["zona", "T_g"]].to_dict("index")
    gerentes_por_zona: dict = {}
    for g, info in df_ger_idx.items():
        gerentes_por_zona.setdefault(info["zona"], []).append(g)

    state = initialize_state(df_ejec, df_ger)
    history = SAHistory()
    ejecutivos = list(df_ejec["cod_ejec_bco"])

    T = params.T_max
    accepts_window = 0
    n_window = 0

    for step in range(params.n_steps):
        if rng.random() < params.p_swap:
            # SWAP
            e1, e2 = rng.choice(ejecutivos, size=2, replace=False)
            if df_ejec_idx[e1]["zona"] != df_ejec_idx[e2]["zona"]:
                continue
            g1 = state.asignacion[e1]
            g2 = state.asignacion[e2]
            if g1 == g2:
                continue
            # Aplicar como dos flips secuenciales: e1 -> g2 y e2 -> g1
            d1, info1 = _delta_assign(state, e1, g2, df_ejec_idx, df_ger_idx, params.lambda_capacity)
            _apply_assign(state, e1, info1)
            d2, info2 = _delta_assign(state, e2, g1, df_ejec_idx, df_ger_idx, params.lambda_capacity)
            dH = d1 + d2
            if dH < 0 or rng.random() < np.exp(-dH / max(T, 1e-9)):
                _apply_assign(state, e2, info2)
                accepts_window += 1
            else:
                # Revertir e1
                _, rinfo = _delta_assign(state, e1, g1, df_ejec_idx, df_ger_idx, params.lambda_capacity)
                _apply_assign(state, e1, rinfo)
        else:
            # FLIP
            e = rng.choice(ejecutivos)
            cand = gerentes_por_zona.get(df_ejec_idx[e]["zona"], [])
            opciones = cand + [None]
            nuevo_g = opciones[rng.integers(0, len(opciones))]
            dH, info = _delta_assign(state, e, nuevo_g, df_ejec_idx, df_ger_idx, params.lambda_capacity)
            if dH < 0 or rng.random() < np.exp(-dH / max(T, 1e-9)):
                _apply_assign(state, e, info)
                accepts_window += 1

        n_window += 1

        if step % params.sample_every == 0:
            history.T.append(T)
            history.H.append(energia(state, params.lambda_capacity))
            history.valor.append(state.valor_total)
            history.M.append(sum(1 for v in state.asignacion.values() if v is not None))
            history.accept_rate.append(accepts_window / max(n_window, 1))
            accepts_window = 0
            n_window = 0

        T *= params.cooling_rate
        if T < params.T_min:
            T = params.T_min

    return state, history


def state_to_df(state: SAState) -> pd.DataFrame:
    """Convierte el dict de asignación a DataFrame [cod_ejec_bco, cod_gte_inv]."""
    rows = [
        {"cod_ejec_bco": e, "cod_gte_inv": g}
        for e, g in state.asignacion.items()
        if g is not None
    ]
    return pd.DataFrame(rows)


def diagnostics(history: SAHistory) -> pd.DataFrame:
    """Calcula diagnósticos físicos sobre la historia.

    - Calor específico C(T) = (<H²> - <H>²) / T² en bins de T.
    - Susceptibilidad χ(T) = (<M²> - <M>²) / T en bins de T.
    """
    df = pd.DataFrame(
        {"T": history.T, "H": history.H, "valor": history.valor, "M": history.M}
    )
    if df.empty:
        return df
    # Bin por log(T)
    df["log_T"] = np.log10(df["T"].clip(lower=1e-9))
    df["bin"] = pd.cut(df["log_T"], bins=20)
    diag = (
        df.groupby("bin", observed=True)
        .agg(T_med=("T", "mean"), H_med=("H", "mean"), H_var=("H", "var"),
             M_med=("M", "mean"), M_var=("M", "var"))
        .reset_index(drop=True)
    )
    diag["C_T"] = diag["H_var"] / diag["T_med"].clip(lower=1e-9) ** 2
    diag["chi_T"] = diag["M_var"] / diag["T_med"].clip(lower=1e-9)
    return diag
