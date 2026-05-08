"""Solución analítica simple — sin optimización, solo reglas deterministas.

Estrategia:
1. Para cada zona, ordenar ejecutivos por (#A desc, #B desc, score desc).
2. Recorrer en orden y asignarlos al primer gerente compatible con capacidad libre.
3. Sin búsqueda, sin backtracking — first-fit.

Este enfoque es el que un analista presentaría sin entrenamiento en optimización.
Sirve como cota inferior y baseline ejecutivamente comprensible.
"""

from __future__ import annotations

import pandas as pd


def asignar_analytical(df_ejec: pd.DataFrame, df_ger: pd.DataFrame) -> pd.DataFrame:
    """First-fit por prioridad de cliente A>B>C, dentro de zona."""
    libre = df_ger.set_index("cod_gte_inv")["T_g"].astype(float).to_dict()
    zona_g = df_ger.set_index("cod_gte_inv")["zona"].to_dict()

    # Orden de prioridad: A desc, B desc, score desc
    ejec_ord = df_ejec.sort_values(
        by=["n_a", "n_b", "score_medio"], ascending=[False, False, False]
    )

    asign = []
    for _, e in ejec_ord.iterrows():
        candidatos = [g for g, z in zona_g.items() if z == e["zona"] and libre[g] >= e["t_e"]]
        if candidatos:
            # First-fit: el primero compatible
            elegido = candidatos[0]
            libre[elegido] -= e["t_e"]
            asign.append({"cod_ejec_bco": e["cod_ejec_bco"], "cod_gte_inv": elegido})

    return pd.DataFrame(asign)
