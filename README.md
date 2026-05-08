# Modelo de Capacidad · Asignación cliente–gerente

Solución analítica al problema de asignación óptima de clientes Preferenciales a Gerentes de Inversión, con cuatro enfoques (analítico, greedy, MILP exacto y simulated annealing con MCMC) que convergen al mismo óptimo.

> **Resultado**: `x/y = 0.4076` (40.76%) — el techo teórico del problema dadas las restricciones e integridad de los datos.

## Estructura del repositorio

```
.
├── data/
│   ├── raw/           # CSVs originales (no en git)
│   ├── interim/       # Cruces intermedios (gitignored)
│   ├── processed/     # Parquets del pipeline (gitignored)
│   └── external/      # Diccionario y plantilla del cliente (no en git)
├── docs/
│   ├── documento_final.md        # Sustentación analítica
│   ├── variables_adicionales.md  # Catálogo de variables propuestas
│   ├── arquitectura.md           # Bosquejo de sistema
│   ├── informe_ejecutivo.tex     # LaTeX del informe ejecutivo
│   └── index.html  # HTML interactivo con Plotly + KaTeX
├── notebooks/
│   ├── 01_eda_clientes_y_red_comercial.ipynb
│   ├── 02_eda_capacidad_y_tiempos.ipynb
│   ├── 03_modelo_optimizacion.ipynb
│   ├── 04_modelo_fisica_estadistica.ipynb
│   └── 05_dashboard_ejecutivo.ipynb
├── src/modelo_capacidad/
│   ├── data/loader.py            # Carga las 7 tablas
│   ├── features/tiempo_demanda.py  # Cálculo de τ_c y t_e
│   ├── models/
│   │   ├── analytical.py         # Regla determinista (sin modelo)
│   │   ├── greedy.py             # Densidad valor/tiempo + best-fit
│   │   ├── milp.py               # PuLP/CBC exacto
│   │   └── simulated_annealing.py # Hamiltoniano Ising + MCMC
│   ├── utils/validators.py       # 5 reglas duras + métrica oficial
│   ├── viz/theme.py              # Tema corporativo Plotly
│   └── run_all.py                # Pipeline orquestador
├── tests/                        # 19 tests pytest
├── pyproject.toml + uv.lock      # Entorno reproducible con uv
└── .gitignore                    # Política: no subir datos del cliente
```

## Setup y reproducibilidad

Requisitos: Python ≥ 3.11 y [uv](https://docs.astral.sh/uv/).

```bash
# 1. Instalar dependencias y crear .venv
uv sync --extra dev --extra notebook --link-mode=copy

# 2. Colocar los CSVs originales en data/raw/
#    (no se distribuyen con el repo por contener PII)

# 3. Ejecutar el pipeline completo
uv run python -m modelo_capacidad.run_all

# 4. Correr los tests
uv run pytest -v

# 5. Abrir los notebooks
uv run jupyter lab notebooks/
```

El pipeline genera `resultado_prueba.csv` en la raíz (incluido en el repo como entregable #2) y artefactos intermedios en `data/processed/` (gitignored, se regeneran).

## Los cuatro enfoques

| # | Método | Tiempo | x/y | Aporte |
|---|---|---|---|---|
| 1 | Analítico (regla determinista) | 0.06 s | 0.4076 | Baseline explicable |
| 2 | Greedy densidad valor/tiempo | 0.06 s | 0.4076 | Producción rápida |
| 3 | MILP exacto (PuLP + CBC) | 0.49 s | 0.4076 | Óptimo formal |
| 4 | Simulated Annealing + MCMC | ~3 s | 0.4076 | Diagnóstico físico |

Los cuatro convergen al mismo valor porque el problema **no compite por capacidad**: el cuello de botella es la integridad referencial (633 ejecutivos sin Gerente de Inversión asignado en `pcac_mac_gpi_ecas`).

## Mapeo a física estadística

El problema es matemáticamente equivalente al estado fundamental de un Ising spin glass con campo externo y restricciones de capacidad:

$$
H(\boldsymbol{\sigma}) = -\sum_{e,g} v_e \sigma_{e,g} + \sum_g \lambda_g \big( \textstyle \sum_e t_e \sigma_{e,g} - T_g \big)_+^2
$$

Detalle completo en `notebooks/04_modelo_fisica_estadistica.ipynb` y en la sección Física del informe interactivo.

## Identidad visual

Todas las gráficas y reportes usan la paleta corporativa Bancolombia:

| Color | Hex | Uso |
|---|---|---|
| Candlelight | `#FDDA24` | Acento principal |
| Dune | `#2C2A29` | Texto, marca |
| Cloudy | `#ABA59D` | Neutros |

Activación automática del tema en Plotly:

```python
from modelo_capacidad.viz import apply_theme
apply_theme()
```

## Entregables del proyecto

| # | Entregable | Archivo |
|---|---|---|
| 1 | Documento explicativo | `docs/documento_final.md` + `docs/index.html` |
| 2 | Asignación final | `resultado_prueba.csv` (generado por el pipeline) |
| 3 | Código documentado | `src/modelo_capacidad/` + `tests/` |
| 4 | Bosquejo arquitectura | `docs/arquitectura.md` + sección Arquitectura del informe |

## Notas sobre datos

Los **datos fuente del cliente** no se versionan:
- 7 CSVs originales en `data/raw/` y diccionario en `data/external/` están gitignored.
- El pipeline asume que se colocan localmente en `data/raw/` para reproducir.

El **resultado del modelo (`resultado_prueba.csv`)** sí está incluido en el repo:
- Es el entregable #2 explícito del PDF de la prueba.
- 27,115 filas con la asignación cliente → ejecutivo → gerente.
- Los IDs son tokens de 19 dígitos ya anonimizados (no documentos reales).

## Licencia

Uso interno. Prueba analítica privada.
