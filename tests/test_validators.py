"""Tests para validators — las 5 reglas duras del PDF."""

from __future__ import annotations

import pandas as pd
import pytest

from modelo_capacidad.utils.validators import (
    metrica_oficial,
    validar_capacidad,
    validar_misma_zona,
    validar_unico_gerente,
)


@pytest.fixture
def df_ejec_simple() -> pd.DataFrame:
    """3 ejecutivos en 2 zonas."""
    return pd.DataFrame(
        [
            {"cod_ejec_bco": "E1", "zona": 1, "t_e": 100.0, "v_e": 1000},
            {"cod_ejec_bco": "E2", "zona": 1, "t_e": 200.0, "v_e": 500},
            {"cod_ejec_bco": "E3", "zona": 2, "t_e": 300.0, "v_e": 700},
        ]
    )


@pytest.fixture
def df_ger_simple() -> pd.DataFrame:
    """2 gerentes, uno por zona."""
    return pd.DataFrame(
        [
            {"cod_gte_inv": "G1", "zona": 1, "T_g": 500.0},
            {"cod_gte_inv": "G2", "zona": 2, "T_g": 400.0},
        ]
    )


def test_unico_gerente_ok():
    """Cada ejecutivo aparece a lo más una vez."""
    a = pd.DataFrame([{"cod_ejec_bco": "E1", "cod_gte_inv": "G1"},
                      {"cod_ejec_bco": "E2", "cod_gte_inv": "G1"}])
    validar_unico_gerente(a)  # no levanta


def test_unico_gerente_falla_si_duplicado():
    a = pd.DataFrame([{"cod_ejec_bco": "E1", "cod_gte_inv": "G1"},
                      {"cod_ejec_bco": "E1", "cod_gte_inv": "G2"}])
    with pytest.raises(AssertionError, match="múltiples gerentes"):
        validar_unico_gerente(a)


def test_misma_zona_ok(df_ejec_simple, df_ger_simple):
    a = pd.DataFrame([{"cod_ejec_bco": "E1", "cod_gte_inv": "G1"},
                      {"cod_ejec_bco": "E3", "cod_gte_inv": "G2"}])
    validar_misma_zona(a, df_ejec_simple, df_ger_simple)  # no levanta


def test_misma_zona_falla(df_ejec_simple, df_ger_simple):
    """E1 está en zona 1 pero asignado a G2 (zona 2)."""
    a = pd.DataFrame([{"cod_ejec_bco": "E1", "cod_gte_inv": "G2"}])
    with pytest.raises(AssertionError, match="cruzan zonas"):
        validar_misma_zona(a, df_ejec_simple, df_ger_simple)


def test_capacidad_ok(df_ejec_simple, df_ger_simple):
    """E1 (100) + E2 (200) = 300 ≤ 500 (T_g de G1)."""
    a = pd.DataFrame([{"cod_ejec_bco": "E1", "cod_gte_inv": "G1"},
                      {"cod_ejec_bco": "E2", "cod_gte_inv": "G1"}])
    uso = validar_capacidad(a, df_ejec_simple, df_ger_simple)
    assert uso.loc[uso["cod_gte_inv"] == "G1", "usado"].iloc[0] == 300.0


def test_capacidad_falla_si_excede(df_ejec_simple):
    """G1 con capacidad 200 no puede absorber E1 (100) + E2 (200) = 300."""
    df_ger = pd.DataFrame([{"cod_gte_inv": "G1", "zona": 1, "T_g": 200.0}])
    a = pd.DataFrame([{"cod_ejec_bco": "E1", "cod_gte_inv": "G1"},
                      {"cod_ejec_bco": "E2", "cod_gte_inv": "G1"}])
    with pytest.raises(AssertionError, match="exceden capacidad"):
        validar_capacidad(a, df_ejec_simple, df_ger)


def test_metrica_oficial_calcula_x_y():
    clientes = pd.DataFrame([
        {"num_doc_cli": "C1", "marca_mac_inv": "A"},
        {"num_doc_cli": "C2", "marca_mac_inv": "A"},
        {"num_doc_cli": "C3", "marca_mac_inv": "B"},
        {"num_doc_cli": "C4", "marca_mac_inv": "C"},
    ])
    resultado = pd.DataFrame([
        {"num_doc_cli": "C1"},
        {"num_doc_cli": "C3"},
        {"num_doc_cli": "C4"},
    ])
    m = metrica_oficial(resultado, clientes)
    # Asignados: C1 (A), C3 (B), C4 (C). x = 1A + 1B = 2. y = 4. x/y = 0.5
    assert m["x"] == 2
    assert m["y"] == 4
    assert m["metrica_x_y"] == 0.5
    assert m["A_asignados"] == 1
    assert m["B_asignados"] == 1
    assert m["C_asignados"] == 1
    assert m["pct_A"] == 50.0  # 1 de 2 totales
