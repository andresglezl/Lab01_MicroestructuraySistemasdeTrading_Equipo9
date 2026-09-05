"""
Generacion de las 5 figuras obligatorias del laboratorio. Todas las figuras se
guardan como PNG en `docs/figures/` con ejes etiquetados, leyenda y titulo.
"""

import os

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.model import (
    S0,
    PI_I,
    UNINFORMED_INTERCEPT,
    UNINFORMED_SLOPE,
    pi_uninformed,
    optimize_quotes,
)
from src.simulation import simulate_trades, run_monte_carlo, get_regimes

plt.rcParams.update(
    {
        "figure.figsize": (9, 5.5),
        "axes.grid": True,
        "grid.alpha": 0.3,
        "font.size": 11,
    }
)

FIGURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "figures")
REGIME_COLORS = {"Optimo": "#1f77b4", "Estrecho": "#2ca02c", "Amplio": "#d62728"}


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def plot_execution_probability(save_path=None):
    """
    Figura 1: Probabilidad de ejecucion de un trader de liquidez pi_LB(s) vs.
    el costo/spread s = A - S0 (o S0 - B), marcando el punto exacto s* = 6.25
    donde la demanda cae a cero.
    """
    save_path = save_path or os.path.join(FIGURES_DIR, "fig1_execution_probability.png")
    _ensure_dir(os.path.dirname(save_path))

    s_zero = UNINFORMED_INTERCEPT / UNINFORMED_SLOPE  # 0.50 / 0.08 = 6.25
    s = np.linspace(0, s_zero * 1.3, 400)
    prob = pi_uninformed(s)

    fig, ax = plt.subplots()
    ax.plot(s, prob, color="#1f77b4", lw=2.5, label=r"$\pi_{LB}(s) = \max(0.50 - 0.08\,s,\ 0)$")
    ax.axvline(s_zero, color="#d62728", ls="--", lw=1.5, label=f"$s^* = {s_zero:.2f}$ (demanda = 0)")
    ax.scatter([s_zero], [0], color="#d62728", zorder=5, s=60)
    ax.annotate(
        f"({s_zero:.2f}, 0)",
        xy=(s_zero, 0),
        xytext=(s_zero + 0.3, 0.05),
        fontsize=10,
        color="#d62728",
    )
    ax.set_xlabel("Spread respecto al precio de referencia, s = A - S0 (o S0 - B)")
    ax.set_ylabel(r"Probabilidad de ejecucion $\pi_{LB}(s)$")
    ax.set_title("Figura 1. Probabilidad de ejecucion del trader de liquidez vs. Spread")
    ax.set_ylim(bottom=-0.02)
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    return save_path


def plot_cumulative_pnl(paths, save_path=None):
    """
    Figura 2: P&L acumulado del dealer a lo largo de los trades, una curva por
    regimen de cotizacion (Optimo, Estrecho, Amplio) en el mismo grafico.
    """
    save_path = save_path or os.path.join(FIGURES_DIR, "fig2_cumulative_pnl.png")
    _ensure_dir(os.path.dirname(save_path))

    fig, ax = plt.subplots()
    for name, df in paths.items():
        ax.plot(np.arange(1, len(df) + 1), df["cum_pnl"], label=name, color=REGIME_COLORS.get(name), lw=1.4)
    ax.axhline(0, color="black", lw=0.8, ls=":")
    ax.set_xlabel("Numero de trade")
    ax.set_ylabel("P&L acumulado del dealer")
    ax.set_title("Figura 2. P&L acumulado a lo largo de 10,000 trades")
    ax.legend(title="Regimen")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    return save_path


def plot_cumulative_inventory(paths, save_path=None):
    """
    Figura 3: Inventario acumulado del dealer a lo largo de los trades, una
    curva por regimen de cotizacion en el mismo grafico.
    """
    save_path = save_path or os.path.join(FIGURES_DIR, "fig3_cumulative_inventory.png")
    _ensure_dir(os.path.dirname(save_path))

    fig, ax = plt.subplots()
    for name, df in paths.items():
        ax.plot(
            np.arange(1, len(df) + 1),
            df["cum_inventory"],
            label=name,
            color=REGIME_COLORS.get(name),
            lw=1.4,
        )
    ax.axhline(0, color="black", lw=0.8, ls=":")
    ax.set_xlabel("Numero de trade")
    ax.set_ylabel("Inventario acumulado del dealer (unidades)")
    ax.set_title("Figura 3. Inventario acumulado a lo largo de 10,000 trades")
    ax.legend(title="Regimen")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    return save_path


def plot_mc_histogram(mc_results, save_path=None):
    """
    Figura 4: Histograma comparativo del P&L final del Monte Carlo (1,000
    corridas) para los tres regimenes de cotizacion.
    """
    save_path = save_path or os.path.join(FIGURES_DIR, "fig4_mc_histogram.png")
    _ensure_dir(os.path.dirname(save_path))

    fig, ax = plt.subplots()
    for name, res in mc_results.items():
        ax.hist(
            res["final_pnls"],
            bins=40,
            alpha=0.55,
            label=f"{name} (media={res['mean_pnl']:.1f}, P(perdida)={res['prob_loss']*100:.1f}%)",
            color=REGIME_COLORS.get(name),
        )
    ax.axvline(0, color="black", lw=0.8, ls=":")
    ax.set_xlabel("P&L final de la corrida")
    ax.set_ylabel("Frecuencia (de 1,000 corridas)")
    ax.set_title("Figura 4. Distribucion Monte Carlo del P&L final por regimen")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    return save_path


def plot_spread_sensitivity(pi_values=(0.1, 0.4, 0.7), save_path=None):
    """
    Figura 5: Sensibilidad del spread optimo A*-B* respecto a pi_I, evaluado
    en pi_I in {0.1, 0.4, 0.7}, comparado contra la teoria de seleccion adversa
    (a mayor pi_I, mayor spread optimo).
    """
    save_path = save_path or os.path.join(FIGURES_DIR, "fig5_spread_sensitivity.png")
    _ensure_dir(os.path.dirname(save_path))

    spreads = []
    for pi in pi_values:
        _, _, spread_opt, _ = optimize_quotes(pi_I=pi)
        spreads.append(spread_opt)

    fig, ax = plt.subplots()
    ax.plot(pi_values, spreads, marker="o", markersize=9, lw=2.2, color="#9467bd", label="Spread optimo (A*-B*)")
    for pi, sp in zip(pi_values, spreads):
        ax.annotate(f"{sp:.2f}", xy=(pi, sp), xytext=(0, 10), textcoords="offset points", ha="center")
    ax.set_xlabel(r"Probabilidad de trader informado, $\pi_I$")
    ax.set_ylabel("Spread optimo, A* - B*")
    ax.set_title(r"Figura 5. Sensibilidad del Spread Optimo vs. $\pi_I$ (teoria de seleccion adversa)")
    ax.set_xticks(list(pi_values))
    ax.legend()
    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    return save_path, spreads


def generate_all_figures(A_opt, B_opt, mc_n_runs=1000, mc_trades_per_run=1000, n_trades_path=10000):
    """
    Genera las 5 figuras obligatorias y devuelve un diccionario con las rutas
    de los PNG generados y los resultados intermedios (paths de 10,000 trades
    y resultados de Monte Carlo) para reutilizar en el reporte PDF.
    """
    _ensure_dir(FIGURES_DIR)
    regimes = get_regimes(A_opt, B_opt)

    paths = {name: simulate_trades(A, B, n_trades=n_trades_path, seed=42) for name, (A, B) in regimes.items()}
    mc_results = {
        name: run_monte_carlo(A, B, n_runs=mc_n_runs, trades_per_run=mc_trades_per_run, base_seed=42)
        for name, (A, B) in regimes.items()
    }

    fig_paths = {}
    fig_paths["execution_probability"] = plot_execution_probability()
    fig_paths["cumulative_pnl"] = plot_cumulative_pnl(paths)
    fig_paths["cumulative_inventory"] = plot_cumulative_inventory(paths)
    fig_paths["mc_histogram"] = plot_mc_histogram(mc_results)
    sens_path, sens_spreads = plot_spread_sensitivity()
    fig_paths["spread_sensitivity"] = sens_path

    return {
        "figures": fig_paths,
        "paths": paths,
        "mc_results": mc_results,
        "regimes": regimes,
        "sensitivity_pi": (0.1, 0.4, 0.7),
        "sensitivity_spreads": sens_spreads,
    }
