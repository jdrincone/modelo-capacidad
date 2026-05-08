"""Validadores de la solución antes de exportar el CSV final.

Cada función levanta AssertionError con un mensaje útil si la restricción se viola.
Las validaciones cubren las 5 reglas duras del PDF.
"""

from __future__ import annotations

import pandas as pd


def validar_unico_gerente(asignaciones: pd.DataFrame) -> None:
    """Cada ejecutivo aparece a lo más 1 vez."""
    dup = asignaciones["cod_ejec_bco"].duplicated().sum()
    assert dup == 0, f"{dup} ejecutivos asignados a múltiples gerentes"


def validar_misma_zona(
    asignaciones: pd.DataFrame, df_ejec: pd.DataFrame, df_ger: pd.DataFrame
) -> None:
    z_e = df_ejec.set_index("cod_ejec_bco")["zona"]
    z_g = df_ger.set_index("cod_gte_inv")["zona"]
    a = asignaciones.copy()
    a["zona_e"] = a["cod_ejec_bco"].map(z_e)
    a["zona_g"] = a["cod_gte_inv"].map(z_g)
    bad = a[a["zona_e"] != a["zona_g"]]
    assert bad.empty, f"{len(bad)} asignaciones cruzan zonas: {bad.head()}"


def validar_capacidad(
    asignaciones: pd.DataFrame, df_ejec: pd.DataFrame, df_ger: pd.DataFrame
) -> pd.DataFrame:
    """Devuelve uso por gerente; falla si algún gerente excede capacidad."""
    t_e = df_ejec.set_index("cod_ejec_bco")["t_e"]
    a = asignaciones.copy()
    a["t_e"] = a["cod_ejec_bco"].map(t_e)
    uso = a.groupby("cod_gte_inv")["t_e"].sum().reset_index(name="usado")
    uso = uso.merge(df_ger[["cod_gte_inv", "T_g"]], on="cod_gte_inv", how="left")
    uso["holgura"] = uso["T_g"] - uso["usado"]
    bad = uso[uso["usado"] > uso["T_g"] + 1e-6]
    assert bad.empty, f"{len(bad)} gerentes exceden capacidad: {bad.head()}"
    return uso


def expandir_a_clientes(
    asignaciones_ejec: pd.DataFrame,
    clientes: pd.DataFrame,
    planta: pd.DataFrame,
) -> pd.DataFrame:
    """Convierte (ejec, gerente) a filas (cliente, ejec, gerente, num_doc_gte_inv).

    Sigue el esquema exacto de resultado_prueba_template.csv:
        num_doc_cli, cod_tipo_doc_cli, cod_ejec_bco, num_doc_gte_inv, cod_gte_inv
    """
    num_doc_gte = planta.drop_duplicates("cod_gte_inv").set_index("cod_gte_inv")[
        "num_doc_gte_inv"
    ]
    a = asignaciones_ejec.copy()
    a["num_doc_gte_inv"] = a["cod_gte_inv"].map(num_doc_gte)

    cli = clientes[["num_doc_cli", "cod_tipo_doc_cli", "cod_ejec_bco"]].copy()
    out = cli.merge(
        a[["cod_ejec_bco", "num_doc_gte_inv", "cod_gte_inv"]],
        on="cod_ejec_bco",
        how="inner",
    )
    out = out[
        ["num_doc_cli", "cod_tipo_doc_cli", "cod_ejec_bco", "num_doc_gte_inv", "cod_gte_inv"]
    ]
    return out


def metrica_oficial(resultado_clientes: pd.DataFrame, clientes: pd.DataFrame) -> dict:
    """Calcula la métrica x/y oficial del PDF."""
    asignados = clientes.merge(
        resultado_clientes[["num_doc_cli"]].drop_duplicates(),
        on="num_doc_cli",
        how="inner",
    )
    n_a = (asignados["marca_mac_inv"] == "A").sum()
    n_b = (asignados["marca_mac_inv"] == "B").sum()
    n_c = (asignados["marca_mac_inv"] == "C").sum()
    total_a = (clientes["marca_mac_inv"] == "A").sum()
    total_b = (clientes["marca_mac_inv"] == "B").sum()
    total_c = (clientes["marca_mac_inv"] == "C").sum()
    y = len(clientes)
    x = n_a + n_b
    return {
        "x": int(x),
        "y": int(y),
        "metrica_x_y": float(x / y),
        "n_asignados": int(len(asignados)),
        "pct_asignados": float(len(asignados) / y * 100),
        "A_asignados": int(n_a),
        "A_total": int(total_a),
        "pct_A": float(n_a / total_a * 100) if total_a else 0.0,
        "B_asignados": int(n_b),
        "B_total": int(total_b),
        "pct_B": float(n_b / total_b * 100) if total_b else 0.0,
        "C_asignados": int(n_c),
        "C_total": int(total_c),
        "pct_C": float(n_c / total_c * 100) if total_c else 0.0,
    }


def validar_y_exportar(
    asignaciones_ejec: pd.DataFrame,
    df_ejec: pd.DataFrame,
    df_ger: pd.DataFrame,
    clientes: pd.DataFrame,
    planta: pd.DataFrame,
    out_path: str,
) -> tuple[pd.DataFrame, dict]:
    """Pipeline completo: valida, expande a clientes, calcula métrica, exporta CSV."""
    validar_unico_gerente(asignaciones_ejec)
    validar_misma_zona(asignaciones_ejec, df_ejec, df_ger)
    uso = validar_capacidad(asignaciones_ejec, df_ejec, df_ger)
    resultado = expandir_a_clientes(asignaciones_ejec, clientes, planta)
    metricas = metrica_oficial(resultado, clientes)
    metricas["utilizacion_media_pct"] = float((uso["usado"] / uso["T_g"]).mean() * 100)
    resultado.to_csv(out_path, index=False, encoding="utf-8")
    return resultado, metricas
