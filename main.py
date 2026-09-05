"""
Script principal del Laboratorio 01 - Cotizaciones Optimas de un Formador de
Mercado (Copeland & Galai, 1983) - Equipo 9.

Ejecutar con:

    python main.py

Este script:
  1. Fija la semilla aleatoria (np.random.seed(42)) para reproducibilidad.
  2. Optimiza las cotizaciones (A*, B*) y muestra los resultados en consola.
  3. Corre las pruebas unitarias con pytest.
  4. Simula 10,000 trades y ejecuta el analisis de Monte Carlo (1,000 x 1,000)
     para los tres regimenes de cotizacion (Optimo, Estrecho, Amplio).
  5. Genera las 5 figuras obligatorias en docs/figures/.
  6. Genera la presentacion docs/presentacion.pdf.
"""

import sys
import os

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.model import optimize_quotes, S0, PI_I, PI_L
from src.plots import generate_all_figures
from src.report import generate_report


def main():
    np.random.seed(42)

    print("=" * 70)
    print(" LABORATORIO 01 - Cotizaciones Optimas de un Formador de Mercado")
    print(" Modelo de Copeland y Galai (1983) - Equipo 9")
    print("=" * 70)

    # -----------------------------------------------------------------
    # 1) Optimizacion de cotizaciones
    # -----------------------------------------------------------------
    print("\n[1] OPTIMIZACION DE COTIZACIONES")
    print("-" * 70)
    A_opt, B_opt, spread_opt, utility_opt = optimize_quotes(pi_I=PI_I)
    print(f"  S0 (precio de referencia)     : {S0:.2f}")
    print(f"  pi_I (prob. informado)        : {PI_I:.2f}")
    print(f"  pi_L (prob. liquidez)         : {PI_L:.2f}")
    print(f"  Ask optimo (A*)               : {A_opt:.2f}")
    print(f"  Bid optimo (B*)               : {B_opt:.2f}")
    print(f"  Spread optimo (A* - B*)       : {spread_opt:.2f}")
    print(f"  Utilidad esperada por trade   : {utility_opt:.4f}")

    # -----------------------------------------------------------------
    # 2) Pruebas unitarias
    # -----------------------------------------------------------------
    print("\n[2] PRUEBAS UNITARIAS (pytest)")
    print("-" * 70)
    test_exit_code = pytest.main(["-v", os.path.join("tests", "test_model.py")])
    if test_exit_code != 0:
        print("\n  ADVERTENCIA: una o mas pruebas fallaron (exit code = "
              f"{test_exit_code}). Se continua con el resto del pipeline.")
    else:
        print("\n  Todas las pruebas pasaron correctamente.")

    # -----------------------------------------------------------------
    # 3) Simulacion (10,000 trades) + Monte Carlo (1,000 x 1,000) + figuras
    # -----------------------------------------------------------------
    print("\n[3] SIMULACION DE TRADES Y ANALISIS DE MONTE CARLO")
    print("-" * 70)
    sim_out = generate_all_figures(A_opt, B_opt, mc_n_runs=1000, mc_trades_per_run=1000, n_trades_path=10000)

    print(f"\n  {'Regimen':<10}{'Bid':>10}{'Ask':>10}{'Spread':>10}   "
          f"{'P&L 10k trades':>16}{'Inv. final':>12}")
    for name, (a, b) in sim_out["regimes"].items():
        df = sim_out["paths"][name]
        print(f"  {name:<10}{b:>10.2f}{a:>10.2f}{a-b:>10.2f}   "
              f"{df['cum_pnl'].iloc[-1]:>16.2f}{df['cum_inventory'].iloc[-1]:>12.0f}")

    print(f"\n  Monte Carlo: 1,000 corridas x 1,000 trades por regimen")
    print(f"  {'Regimen':<10}{'P&L medio':>14}{'Desv. Std.':>14}{'P(perdida)':>14}")
    for name in sim_out["regimes"]:
        res = sim_out["mc_results"][name]
        print(f"  {name:<10}{res['mean_pnl']:>14.2f}{res['std_pnl']:>14.2f}{res['prob_loss']*100:>13.1f}%")

    print(f"\n  Sensibilidad del spread optimo vs pi_I:")
    for pi, spread in zip(sim_out["sensitivity_pi"], sim_out["sensitivity_spreads"]):
        print(f"    pi_I = {pi:.1f}  ->  spread optimo = {spread:.2f}")

    print("\n  Figuras generadas en docs/figures/:")
    for name, path in sim_out["figures"].items():
        print(f"    - {name}: {path}")

    # -----------------------------------------------------------------
    # 4) Generacion del PDF de presentacion
    # -----------------------------------------------------------------
    print("\n[4] GENERACION DE LA PRESENTACION PDF")
    print("-" * 70)
    results = {
        "S0": S0,
        "pi_I": PI_I,
        "pi_L": PI_L,
        "A_opt": A_opt,
        "B_opt": B_opt,
        "spread_opt": spread_opt,
        "utility_opt": utility_opt,
        "figures": sim_out["figures"],
        "mc_results": sim_out["mc_results"],
        "regimes": sim_out["regimes"],
        "sensitivity_pi": sim_out["sensitivity_pi"],
        "sensitivity_spreads": sim_out["sensitivity_spreads"],
    }
    pdf_path = generate_report(results)
    print(f"  Presentacion generada en: {pdf_path}")

    print("\n" + "=" * 70)
    print(" PIPELINE COMPLETO.")
    print("=" * 70)

    return 0 if test_exit_code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
