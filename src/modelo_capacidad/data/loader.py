"""Carga de las tablas fuente de la prueba.

Centraliza nombres de archivo, dtypes y rutas para evitar reescribir lógica
de I/O en notebooks y scripts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
DATA_RAW: Final[Path] = REPO_ROOT / "data" / "raw"
DATA_INTERIM: Final[Path] = REPO_ROOT / "data" / "interim"
DATA_PROCESSED: Final[Path] = REPO_ROOT / "data" / "processed"
DATA_EXTERNAL: Final[Path] = REPO_ROOT / "data" / "external"

ID_COLUMNS: Final[tuple[str, ...]] = (
    "num_doc_cli",
    "num_doc_cli_dv",
    "num_doc_gte_inv",
    "num_doc_gte_regional",
    "num_doc_ejec_bco",
    "cod_gte_inv",
    "cod_ejec_bco",
    "cod_gte_regional",
    "cod_sap_gte_inv",
    "cedula_comercial",
    "codigo_de_vendedor",
)


def _id_dtypes(columns: list[str]) -> dict[str, str]:
    """Fuerza ids como string para evitar pérdida de precisión en enteros largos."""
    return {c: "string" for c in columns if c in ID_COLUMNS}


def load_clientes() -> pd.DataFrame:
    path = DATA_RAW / "pcac_mac_gpi_clientes.csv"
    cols = pd.read_csv(path, nrows=0).columns.tolist()
    return pd.read_csv(path, dtype=_id_dtypes(cols))


def load_ecas() -> pd.DataFrame:
    path = DATA_RAW / "pcac_mac_gpi_ecas.csv"
    cols = pd.read_csv(path, nrows=0).columns.tolist()
    return pd.read_csv(path, dtype=_id_dtypes(cols))


def load_oportunidades() -> pd.DataFrame:
    path = DATA_RAW / "pcac_oportunidades_comer.csv"
    cols = pd.read_csv(path, nrows=0).columns.tolist()
    return pd.read_csv(path, dtype=_id_dtypes(cols))


def load_tenencia() -> pd.DataFrame:
    path = DATA_RAW / "pcac_mac_gpi_tenencia_prod.csv"
    cols = pd.read_csv(path, nrows=0).columns.tolist()
    return pd.read_csv(path, dtype=_id_dtypes(cols))


def load_planta() -> pd.DataFrame:
    path = DATA_RAW / "pcac_planta_comercial2.csv"
    cols = pd.read_csv(path, nrows=0).columns.tolist()
    return pd.read_csv(path, dtype=_id_dtypes(cols))


def load_encuesta() -> pd.DataFrame:
    path = DATA_RAW / "pcac_encuesta.csv"
    cols = pd.read_csv(path, nrows=0).columns.tolist()
    return pd.read_csv(path, dtype=_id_dtypes(cols))


def load_capacidad() -> pd.DataFrame:
    path = DATA_RAW / "pcac_capacidad_gerentes.csv"
    cols = pd.read_csv(path, nrows=0).columns.tolist()
    return pd.read_csv(path, dtype=_id_dtypes(cols))


def load_all() -> dict[str, pd.DataFrame]:
    """Carga todas las tablas en un dict para inspección rápida."""
    return {
        "clientes": load_clientes(),
        "ecas": load_ecas(),
        "oportunidades": load_oportunidades(),
        "tenencia": load_tenencia(),
        "planta": load_planta(),
        "encuesta": load_encuesta(),
        "capacidad": load_capacidad(),
    }
