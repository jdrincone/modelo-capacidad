"""Pipeline orquestador: corre los 4 enfoques y produce resultado_prueba.csv.

Usage:
    uv run python -m modelo_capacidad.run_all
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Forzar UTF-8 en stdout (Windows cp1252 por defecto rompe con caracteres científicos)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

import pandas as pd

from modelo_capacidad.data.loader import (
    DATA_PROCESSED,
    REPO_ROOT,
    load_capacidad,
    load_clientes,
    load_ecas,
    load_encuesta,
    load_oportunidades,
    load_planta,
    load_tenencia,
)
from modelo_capacidad.features.tiempo_demanda import (
    calcular_tau_cliente,
    construir_df_ejecutivos,
    construir_df_gerentes,
)
from modelo_capacidad.models.analytical import asignar_analytical
from modelo_capacidad.models.greedy import asignar_greedy
from modelo_capacidad.models.milp import asignar_milp
from modelo_capacidad.models.simulated_annealing import (
    SAParams,
    run_sa,
    state_to_df,
)
from modelo_capacidad.utils.validators import metrica_oficial, validar_y_exportar


def main() -> None:
    print("=" * 70)
    print("PIPELINE MODELO DE CAPACIDAD — DICAGI 2022")
    print("=" * 70)

    # 1. Carga
    print("\n[1/6] Cargando datos...")
    clientes = load_clientes()
    ecas = load_ecas()
    capacidad = load_capacidad()
    encuesta = load_encuesta()
    oport = load_oportunidades()
    tenencia = load_tenencia()
    planta = load_planta()
    print(f"  clientes={len(clientes):,}  ecas={len(ecas):,}  capacidad={len(capacidad):,}")

    # 2. Feature engineering
    print("\n[2/6] Calculando τ_c y t_e...")
    t0 = time.perf_counter()
    tau = calcular_tau_cliente(oport, tenencia, encuesta)
    df_ejec = construir_df_ejecutivos(clientes, tau, ecas)
    df_ger = construir_df_gerentes(capacidad, ecas)
    print(f"  ejecutivos asignables: {len(df_ejec):,}")
    print(f"  gerentes con equipo:   {len(df_ger):,}")
    print(f"  demanda total:  {df_ejec['t_e'].sum():>14,.0f} min")
    print(f"  oferta total:   {df_ger['T_g'].sum():>14,.0f} min")
    print(f"  ratio dem/ofer: {df_ejec['t_e'].sum() / df_ger['T_g'].sum():>14.2f}")
    print(f"  tiempo: {time.perf_counter() - t0:.1f}s")

    # Persistir features
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df_ejec.to_parquet(DATA_PROCESSED / "df_ejecutivos.parquet", index=False)
    df_ger.to_parquet(DATA_PROCESSED / "df_gerentes.parquet", index=False)
    tau.to_parquet(DATA_PROCESSED / "tau_cliente.parquet", index=False)

    # 3. Cuatro enfoques
    enfoques = {}

    print("\n[3/6] Enfoque 1: Analítico (sin modelo)...")
    t0 = time.perf_counter()
    a = asignar_analytical(df_ejec, df_ger)
    enfoques["analytical"] = (a, time.perf_counter() - t0)
    print(f"  asignaciones: {len(a)}, tiempo: {enfoques['analytical'][1]:.2f}s")

    print("\n[4/6] Enfoque 2: Greedy densidad valor/tiempo...")
    t0 = time.perf_counter()
    g = asignar_greedy(df_ejec, df_ger)
    enfoques["greedy"] = (g, time.perf_counter() - t0)
    print(f"  asignaciones: {len(g)}, tiempo: {enfoques['greedy'][1]:.2f}s")

    print("\n[5/6] Enfoque 3: MILP exacto (CBC)...")
    res_milp = asignar_milp(df_ejec, df_ger, time_limit=300, gap_rel=0.001, msg=False, warm_start=g)
    enfoques["milp"] = (res_milp.asignaciones, res_milp.time_seconds)
    print(f"  status: {res_milp.status}, objective={res_milp.objective:.0f}")
    print(f"  asignaciones: {len(res_milp.asignaciones)}, tiempo: {res_milp.time_seconds:.1f}s")

    print("\n[6/6] Enfoque 4: Simulated Annealing (Ising + MCMC)...")
    sa_state, sa_history = run_sa(df_ejec, df_ger, SAParams(n_steps=80_000, seed=42))
    sa_df = state_to_df(sa_state)
    enfoques["sa"] = (sa_df, 0.0)
    print(f"  asignaciones: {len(sa_df)}, energía final: {sa_history.H[-1]:.0f}")

    # 4. Métricas comparativas
    print("\n" + "=" * 70)
    print("RESULTADOS COMPARATIVOS")
    print("=" * 70)
    rows = []
    out_dir = REPO_ROOT
    for nombre, (asign, tsec) in enfoques.items():
        if asign.empty:
            continue
        from modelo_capacidad.utils.validators import expandir_a_clientes

        try:
            from modelo_capacidad.utils.validators import (
                validar_capacidad,
                validar_misma_zona,
                validar_unico_gerente,
            )

            validar_unico_gerente(asign)
            validar_misma_zona(asign, df_ejec, df_ger)
            validar_capacidad(asign, df_ejec, df_ger)
            valid = "✓"
        except AssertionError as e:
            valid = f"✗ {e}"

        res_cli = expandir_a_clientes(asign, clientes, planta)
        m = metrica_oficial(res_cli, clientes)
        rows.append({
            "enfoque": nombre,
            "valid": valid,
            "ejec_asign": len(asign),
            "cli_asign": m["n_asignados"],
            "pct_asign": round(m["pct_asignados"], 1),
            "x/y": round(m["metrica_x_y"], 4),
            "%A": round(m["pct_A"], 1),
            "%B": round(m["pct_B"], 1),
            "%C": round(m["pct_C"], 1),
            "tiempo_s": round(tsec, 2),
        })

    comp = pd.DataFrame(rows)
    print()
    print(comp.to_string(index=False))
    comp.to_csv(DATA_PROCESSED / "comparativa_enfoques.csv", index=False)

    # 5. Selección del mejor enfoque y exportación
    mejor = comp.sort_values("x/y", ascending=False).iloc[0]
    print(f"\n>>> MEJOR ENFOQUE: {mejor['enfoque']} (x/y = {mejor['x/y']})")

    asign_mejor = enfoques[mejor["enfoque"]][0]
    out_path = out_dir / "resultado_prueba.csv"
    resultado, metricas = validar_y_exportar(
        asign_mejor, df_ejec, df_ger, clientes, planta, str(out_path)
    )
    print(f"\n✓ resultado_prueba.csv exportado: {out_path}")
    print(f"  filas: {len(resultado):,}")
    print(f"  utilización media: {metricas['utilizacion_media_pct']:.1f}%")

    # Persistir history del SA para notebook 04
    pd.DataFrame({
        "T": sa_history.T,
        "H": sa_history.H,
        "valor": sa_history.valor,
        "M": sa_history.M,
        "accept_rate": sa_history.accept_rate,
    }).to_parquet(DATA_PROCESSED / "sa_history.parquet", index=False)

    print("\n=== FIN ===\n")


if __name__ == "__main__":
    main()
