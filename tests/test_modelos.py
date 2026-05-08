"""Tests para modelos — analytical, greedy, milp deben respetar restricciones."""

from __future__ import annotations

import pandas as pd
import pytest

from modelo_capacidad.models.analytical import asignar_analytical
from modelo_capacidad.models.greedy import asignar_greedy
from modelo_capacidad.models.milp import asignar_milp
from modelo_capacidad.utils.validators import (
    validar_capacidad,
    validar_misma_zona,
    validar_unico_gerente,
)


@pytest.fixture
def problema_simple():
    """Caso pequeño con solución conocida."""
    df_ejec = pd.DataFrame(
        [
            {"cod_ejec_bco": "E1", "zona": 1, "n_clientes": 5, "n_a": 3, "n_b": 2, "n_c": 0,
             "score_medio": 0.5, "t_e": 100.0, "v_e": 3200.0, "densidad": 32.0},
            {"cod_ejec_bco": "E2", "zona": 1, "n_clientes": 4, "n_a": 0, "n_b": 4, "n_c": 0,
             "score_medio": 0.3, "t_e": 80.0, "v_e": 400.0, "densidad": 5.0},
            {"cod_ejec_bco": "E3", "zona": 2, "n_clientes": 3, "n_a": 1, "n_b": 1, "n_c": 1,
             "score_medio": 0.4, "t_e": 60.0, "v_e": 1101.0, "densidad": 18.35},
        ]
    )
    df_ger = pd.DataFrame(
        [
            {"cod_gte_inv": "G1", "zona": 1, "T_g": 200.0},  # cabe E1+E2 (180 ≤ 200)
            {"cod_gte_inv": "G2", "zona": 2, "T_g": 100.0},  # cabe E3
        ]
    )
    return df_ejec, df_ger


def test_analytical_respeta_restricciones(problema_simple):
    df_ejec, df_ger = problema_simple
    a = asignar_analytical(df_ejec, df_ger)
    validar_unico_gerente(a)
    validar_misma_zona(a, df_ejec, df_ger)
    validar_capacidad(a, df_ejec, df_ger)


def test_greedy_respeta_restricciones(problema_simple):
    df_ejec, df_ger = problema_simple
    a = asignar_greedy(df_ejec, df_ger)
    validar_unico_gerente(a)
    validar_misma_zona(a, df_ejec, df_ger)
    validar_capacidad(a, df_ejec, df_ger)


def test_milp_resuelve_optimo(problema_simple):
    df_ejec, df_ger = problema_simple
    res = asignar_milp(df_ejec, df_ger, time_limit=30, msg=False)
    assert res.status == "Optimal"
    # Esperado: E1+E2 a G1, E3 a G2 → todos asignados → objetivo = 3200+400+1101 = 4701
    assert res.objective == pytest.approx(4701.0, abs=1.0)
    assert len(res.asignaciones) == 3
    validar_unico_gerente(res.asignaciones)
    validar_misma_zona(res.asignaciones, df_ejec, df_ger)
    validar_capacidad(res.asignaciones, df_ejec, df_ger)


def test_milp_no_excede_capacidad():
    """Caso donde la capacidad obliga a dejar uno fuera."""
    df_ejec = pd.DataFrame(
        [
            {"cod_ejec_bco": "E1", "zona": 1, "n_clientes": 1, "n_a": 1, "n_b": 0, "n_c": 0,
             "score_medio": 0.5, "t_e": 80.0, "v_e": 1000.0, "densidad": 12.5},
            {"cod_ejec_bco": "E2", "zona": 1, "n_clientes": 1, "n_a": 1, "n_b": 0, "n_c": 0,
             "score_medio": 0.5, "t_e": 80.0, "v_e": 1000.0, "densidad": 12.5},
        ]
    )
    df_ger = pd.DataFrame([{"cod_gte_inv": "G1", "zona": 1, "T_g": 100.0}])  # solo cabe uno
    res = asignar_milp(df_ejec, df_ger, time_limit=30, msg=False)
    assert res.status == "Optimal"
    assert len(res.asignaciones) == 1  # solo cabe uno
    assert res.objective == pytest.approx(1000.0)


def test_greedy_y_milp_coinciden_si_problema_holgado(problema_simple):
    """Cuando el problema es holgado, ambos algoritmos llegan al mismo valor objetivo."""
    df_ejec, df_ger = problema_simple
    g = asignar_greedy(df_ejec, df_ger)
    m = asignar_milp(df_ejec, df_ger, time_limit=30, msg=False)
    valor_greedy = (g.merge(df_ejec[["cod_ejec_bco", "v_e"]], on="cod_ejec_bco")["v_e"].sum())
    assert valor_greedy == pytest.approx(m.objective, abs=1.0)
