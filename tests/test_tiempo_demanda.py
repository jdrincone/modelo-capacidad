"""Tests para tiempo_demanda."""

from __future__ import annotations

import numpy as np
import pandas as pd

from modelo_capacidad.features.tiempo_demanda import (
    PRODUCTO_MAP,
    calcular_tau_cliente,
    construir_df_ejecutivos,
    construir_df_gerentes,
    construir_tabla_tiempos,
)


def test_tabla_tiempos_calcula_mediana():
    encuesta = pd.DataFrame([
        {"producto": "X", "etapa_del_producto": "Venta",
         "total_promedio_tiempo_min_x_actividad": 30.0},
        {"producto": "X", "etapa_del_producto": "Venta",
         "total_promedio_tiempo_min_x_actividad": 60.0},
        {"producto": "X", "etapa_del_producto": "Venta",
         "total_promedio_tiempo_min_x_actividad": 600.0},  # outlier
    ])
    tabla = construir_tabla_tiempos(encuesta)
    # Mediana de [30, 60, 600] = 60 — robusto al outlier
    assert tabla.get("X", "Venta") == 60.0


def test_calcular_tau_cliente_caso_no_tiene():
    """Cliente sin tenencia debe pagar venta + instrumentación + conexión."""
    encuesta = pd.DataFrame([
        {"producto": "X", "etapa_del_producto": "Venta",
         "total_promedio_tiempo_min_x_actividad": 30.0},
        {"producto": "X", "etapa_del_producto": "Instrumentación",
         "total_promedio_tiempo_min_x_actividad": 10.0},
        {"producto": "X", "etapa_del_producto": "Conexión",
         "total_promedio_tiempo_min_x_actividad": 5.0},
        {"producto": "X", "etapa_del_producto": "Postventa",
         "total_promedio_tiempo_min_x_actividad": 20.0},
    ])
    oport = pd.DataFrame([{"num_doc_cli": "C1", "cod_producto": 1, "producto": "X"}])
    # Cliente C1 NO tiene producto X
    tenencia = pd.DataFrame(columns=["num_doc_cli", "cod_prod", "tenencia", "usa_producto"])

    tau = calcular_tau_cliente(oport, tenencia, encuesta)
    # τ = 30 + 10 + 5 = 45 (venta + instrum + conex)
    assert tau.loc[tau["num_doc_cli"] == "C1", "tau"].iloc[0] == 45.0


def test_calcular_tau_cliente_caso_tiene_no_usa():
    """Cliente que tiene pero no usa: solo tiempo de post-venta."""
    encuesta = pd.DataFrame([
        {"producto": "X", "etapa_del_producto": "Venta",
         "total_promedio_tiempo_min_x_actividad": 30.0},
        {"producto": "X", "etapa_del_producto": "Postventa",
         "total_promedio_tiempo_min_x_actividad": 20.0},
    ])
    oport = pd.DataFrame([{"num_doc_cli": "C1", "cod_producto": 1, "producto": "X"}])
    tenencia = pd.DataFrame([{"num_doc_cli": "C1", "cod_prod": 1, "tenencia": 1, "usa_producto": 0}])

    tau = calcular_tau_cliente(oport, tenencia, encuesta)
    # τ = 20 (solo postventa)
    assert tau.loc[tau["num_doc_cli"] == "C1", "tau"].iloc[0] == 20.0


def test_calcular_tau_cliente_caso_tiene_y_usa():
    """Cliente que tiene y usa: τ = 0."""
    encuesta = pd.DataFrame([
        {"producto": "X", "etapa_del_producto": "Venta",
         "total_promedio_tiempo_min_x_actividad": 30.0},
    ])
    oport = pd.DataFrame([{"num_doc_cli": "C1", "cod_producto": 1, "producto": "X"}])
    tenencia = pd.DataFrame([{"num_doc_cli": "C1", "cod_prod": 1, "tenencia": 1, "usa_producto": 1}])

    tau = calcular_tau_cliente(oport, tenencia, encuesta)
    assert tau.loc[tau["num_doc_cli"] == "C1", "tau"].iloc[0] == 0.0


def test_producto_map_aplica():
    """El mapeo PRODUCTO_MAP convierte nombres antes de buscar tiempos."""
    encuesta = pd.DataFrame([
        {"producto": "Renta Fija", "etapa_del_producto": "Venta",
         "total_promedio_tiempo_min_x_actividad": 50.0},
    ])
    # 'tiene_rta_fija_valores' debe mapearse a 'Renta Fija'
    assert PRODUCTO_MAP["tiene_rta_fija_valores"] == "Renta Fija"
    oport = pd.DataFrame([{"num_doc_cli": "C1", "cod_producto": 23, "producto": "tiene_rta_fija_valores"}])
    tenencia = pd.DataFrame(columns=["num_doc_cli", "cod_prod", "tenencia", "usa_producto"])

    tau = calcular_tau_cliente(oport, tenencia, encuesta)
    # Encontró el producto vía mapping → τ = 50
    assert tau.loc[tau["num_doc_cli"] == "C1", "tau"].iloc[0] == 50.0


def test_construir_df_ejecutivos_filtra_huerfanos():
    clientes = pd.DataFrame([
        {"num_doc_cli": "C1", "cod_ejec_bco": "E1", "cod_region_gte_inv": 1,
         "marca_mac_inv": "A", "score_modelo": 0.5},
        {"num_doc_cli": "C2", "cod_ejec_bco": "E_HUERFANO", "cod_region_gte_inv": 1,
         "marca_mac_inv": "B", "score_modelo": 0.2},
    ])
    tau = pd.DataFrame([{"num_doc_cli": "C1", "tau": 100.0},
                        {"num_doc_cli": "C2", "tau": 50.0}])
    ecas = pd.DataFrame([{"cod_ejec_bco": "E1"}])  # solo E1 está en ecas

    df_ejec = construir_df_ejecutivos(clientes, tau, ecas)
    assert len(df_ejec) == 1
    assert df_ejec.iloc[0]["cod_ejec_bco"] == "E1"
    assert df_ejec.iloc[0]["t_e"] == 100.0
    # v_e = 1000*1 + 100*0 + 1*0 + 0.1 * 0.5 * 1 = 1000.05
    assert df_ejec.iloc[0]["v_e"] == 1000.05


def test_construir_df_gerentes_filtra_sin_equipo():
    capacidad = pd.DataFrame([
        {"cod_gte_inv": "G1", "cod_region_gte_inv": 1, "tiempo_restante": 1000},
        {"cod_gte_inv": "G_SIN_EQUIPO", "cod_region_gte_inv": 1, "tiempo_restante": 1000},
    ])
    ecas = pd.DataFrame([{"cod_gte_inv": "G1"}])  # solo G1 tiene equipo

    df_ger = construir_df_gerentes(capacidad, ecas)
    assert len(df_ger) == 1
    assert df_ger.iloc[0]["cod_gte_inv"] == "G1"
