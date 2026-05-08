"""Greedy basado en densidad valor/tiempo con best-fit por capacidad.

Estrategia:
1. Calcular densidad ρ_e = v_e / t_e (valor por minuto).
2. Ordenar ejecutivos por ρ_e descendente.
3. Para cada ejecutivo, escoger gerente compatible con menor capacidad libre suficiente
   (best-fit decreasing) — tiende a empacar mejor.
"""

from __future__ import annotations

import pandas as pd


def asignar_greedy(df_ejec: pd.DataFrame, df_ger: pd.DataFrame) -> pd.DataFrame:
    """Greedy con best-fit por densidad."""
    libre = df_ger.set_index("cod_gte_inv")["T_g"].astype(float).to_dict()
    zona_g = df_ger.set_index("cod_gte_inv")["zona"].to_dict()

    ejec_ord = df_ejec.sort_values("densidad", ascending=False)

    asign = []
    for _, e in ejec_ord.iterrows():
        candidatos = [
            (g, libre[g]) for g, z in zona_g.items() if z == e["zona"] and libre[g] >= e["t_e"]
        ]
        if candidatos:
            # Best-fit: gerente con menos capacidad libre (suficiente). Reduce fragmentación.
            elegido, _ = min(candidatos, key=lambda x: x[1])
            libre[elegido] -= e["t_e"]
            asign.append({"cod_ejec_bco": e["cod_ejec_bco"], "cod_gte_inv": elegido})

    return pd.DataFrame(asign)
