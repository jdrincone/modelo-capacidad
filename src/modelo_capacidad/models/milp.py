"""MILP exacto del problema de asignación con PuLP/CBC.

Formulación:
    max  Σ v_e · x_eg
    s.a. Σ_g x_eg ≤ 1            ∀e   (a lo más un gerente)
         Σ_e t_e · x_eg ≤ T_g    ∀g   (capacidad anual)
         x_eg = 0 si zona(e)≠zona(g)  (eliminado del LP)
         x_eg ∈ {0,1}
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pulp as pl


@dataclass
class MILPResult:
    asignaciones: pd.DataFrame  # cod_ejec_bco, cod_gte_inv
    status: str
    objective: float
    time_seconds: float


def _build_pares(df_ejec: pd.DataFrame, df_ger: pd.DataFrame) -> list[tuple[str, str]]:
    """Pares (e, g) válidos por zona."""
    e_zona = df_ejec.set_index("cod_ejec_bco")["zona"]
    g_zona = df_ger.set_index("cod_gte_inv")["zona"]
    pares = []
    for e, ze in e_zona.items():
        for g, zg in g_zona.items():
            if ze == zg:
                pares.append((e, g))
    return pares


def asignar_milp(
    df_ejec: pd.DataFrame,
    df_ger: pd.DataFrame,
    *,
    time_limit: int = 300,
    gap_rel: float = 0.001,
    msg: bool = False,
    warm_start: pd.DataFrame | None = None,
) -> MILPResult:
    """Resuelve el MILP con CBC."""
    import time

    t0 = time.perf_counter()

    pares = _build_pares(df_ejec, df_ger)
    valor = df_ejec.set_index("cod_ejec_bco")["v_e"].to_dict()
    tiempo = df_ejec.set_index("cod_ejec_bco")["t_e"].to_dict()
    cap = df_ger.set_index("cod_gte_inv")["T_g"].to_dict()

    model = pl.LpProblem("asignacion", pl.LpMaximize)
    x = pl.LpVariable.dicts("x", pares, cat=pl.LpBinary)

    # Objetivo
    model += pl.lpSum(valor[e] * x[(e, g)] for (e, g) in pares)

    # Restricción 1: a lo más un gerente por ejecutivo
    by_e: dict[str, list] = {}
    for (e, g) in pares:
        by_e.setdefault(e, []).append((e, g))
    for e, lst in by_e.items():
        model += pl.lpSum(x[p] for p in lst) <= 1, f"unico_gte_{e}"

    # Restricción 2: capacidad por gerente
    by_g: dict[str, list] = {}
    for (e, g) in pares:
        by_g.setdefault(g, []).append((e, g))
    for g, lst in by_g.items():
        model += pl.lpSum(tiempo[e] * x[(e, g)] for (e, g) in lst) <= cap[g], f"cap_{g}"

    # Warm-start (opcional)
    if warm_start is not None and not warm_start.empty:
        ws_set = set(zip(warm_start["cod_ejec_bco"], warm_start["cod_gte_inv"], strict=False))
        for p in pares:
            if p in ws_set:
                x[p].setInitialValue(1)
            else:
                x[p].setInitialValue(0)

    solver = pl.PULP_CBC_CMD(msg=msg, timeLimit=time_limit, gapRel=gap_rel)
    model.solve(solver)
    elapsed = time.perf_counter() - t0

    asign = [
        {"cod_ejec_bco": e, "cod_gte_inv": g}
        for (e, g) in pares
        if x[(e, g)].value() is not None and x[(e, g)].value() > 0.5
    ]

    return MILPResult(
        asignaciones=pd.DataFrame(asign),
        status=pl.LpStatus[model.status],
        objective=float(pl.value(model.objective) or 0.0),
        time_seconds=elapsed,
    )
