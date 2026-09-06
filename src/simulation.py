"""
Simulador de trades y motor de Monte Carlo para el modelo Copeland-Galai (1983).

Cada trade se simula de la siguiente manera:

1. Llega un trader. Es informado con probabilidad pi_I, o de liquidez con
   probabilidad (1 - pi_I).
2. Se dibuja el valor fundamental P ~ Erlang(60, 3) para ese instante.
3. Trader informado:
     - Si P > A: compra en A (el dealer vende con perdida esperada, pnl = A - P).
     - Si P < B: vende en B (el dealer compra con perdida esperada, pnl = P - B).
     - Si B <= P <= A: no opera.
4. Trader de liquidez (no observa P, opera por necesidad de liquidez):
     - Compra en A con prob. pi_LB(A - S0)  -> pnl = A - S0.
     - Vende en B con prob. pi_LS(S0 - B)   -> pnl = S0 - B.
     - En otro caso, no opera.

El pnl reportado es siempre desde la perspectiva del formador de mercado (dealer).
El inventario del dealer disminuye en una unidad cuando vende (compra del
trader) y aumenta en una unidad cuando compra (venta del trader).
"""

import numpy as np
import pandas as pd

from src.model import S0, GAMMA_A, GAMMA_SCALE, PI_I, pi_uninformed

# Regimenes de cotizacion de referencia usados en el analisis comparativo
TIGHT_BID, TIGHT_ASK = 19.75, 20.05
WIDE_BID, WIDE_ASK = 18.40, 21.40


def simulate_trades(A, B, n_trades=10000, pi_I=PI_I, S0=S0, seed=42):
    """
    Simula `n_trades` trades secuenciales contra un dealer que cotiza (A, B).

    La semilla aleatoria se fija con np.random.seed(seed) al inicio de la
    funcion para garantizar reproducibilidad absoluta. Usar la misma `seed`
    en distintos regimenes de cotizacion produce la misma secuencia de
    llegadas (tipo de trader y valor fundamental P), permitiendo comparar
    los regimenes sobre el mismo camino de mercado.

    Returns
    -------
    pandas.DataFrame con columnas:
        trader_type   : 'informado' | 'liquidez'
        direction     : 'compra' | 'venta' | 'ninguna'
        P             : valor fundamental dibujado para el trade
        pnl           : P&L del dealer en ese trade
        cum_pnl       : P&L acumulado del dealer
        inventory_chg : cambio de inventario del dealer en ese trade
        cum_inventory : inventario acumulado del dealer
    """
    if seed is not None:
        np.random.seed(seed)

    is_informed = np.random.rand(n_trades) < pi_I
    P = np.random.gamma(shape=GAMMA_A, scale=GAMMA_SCALE, size=n_trades)

    p_buy_liq = float(pi_uninformed(A - S0))
    p_sell_liq = float(pi_uninformed(S0 - B))
    liquidity_draw = np.random.rand(n_trades)

    pnl = np.zeros(n_trades)
    inventory_chg = np.zeros(n_trades)
    direction = np.empty(n_trades, dtype=object)
    trader_type = np.where(is_informed, "informado", "liquidez")

    for i in range(n_trades):
        if is_informed[i]:
            Pi = P[i]
            if Pi > A:
                direction[i] = "compra"
                pnl[i] = A - Pi
                inventory_chg[i] = -1
            elif Pi < B:
                direction[i] = "venta"
                pnl[i] = Pi - B
                inventory_chg[i] = 1
            else:
                direction[i] = "ninguna"
        else:
            u = liquidity_draw[i]
            if u < p_buy_liq:
                direction[i] = "compra"
                pnl[i] = A - S0
                inventory_chg[i] = -1
            elif u < p_buy_liq + p_sell_liq:
                direction[i] = "venta"
                pnl[i] = S0 - B
                inventory_chg[i] = 1
            else:
                direction[i] = "ninguna"

    df = pd.DataFrame(
        {
            "trader_type": trader_type,
            "direction": direction,
            "P": P,
            "pnl": pnl,
            "cum_pnl": np.cumsum(pnl),
            "inventory_chg": inventory_chg,
            "cum_inventory": np.cumsum(inventory_chg),
        }
    )
    return df


def run_monte_carlo(A, B, n_runs=1000, trades_per_run=1000, pi_I=PI_I, S0=S0, base_seed=42):
    """
    Ejecuta `n_runs` corridas independientes de `trades_per_run` trades cada
    una para las cotizaciones (A, B), y agrega el P&L final de cada corrida.

    Cada corrida i usa seed = base_seed + i, de forma que:
    - El conjunto completo de corridas es reproducible (base_seed fijo).
    - Las corridas son independientes entre si (distinta seed por corrida).
    - Usando el mismo base_seed en distintos regimenes de cotizacion, la
      corrida i comparte el mismo camino de mercado subyacente en todos los
      regimenes, permitiendo una comparacion justa.

    Returns
    -------
    dict con:
        final_pnls   : np.ndarray de tamano n_runs con el P&L final de c/corrida
        mean_pnl     : promedio del P&L final
        std_pnl      : desviacion estandar del P&L final
        prob_loss    : proporcion de corridas con P&L final < 0
    """
    final_pnls = np.empty(n_runs)
    for i in range(n_runs):
        df = simulate_trades(
            A, B, n_trades=trades_per_run, pi_I=pi_I, S0=S0, seed=base_seed + i
        )
        final_pnls[i] = df["cum_pnl"].iloc[-1]

    return {
        "final_pnls": final_pnls,
        "mean_pnl": float(final_pnls.mean()),
        "std_pnl": float(final_pnls.std(ddof=1)),
        "prob_loss": float((final_pnls < 0).mean()),
    }


def get_regimes(A_opt, B_opt):
    """Diccionario ordenado con los tres regimenes de cotizacion a comparar."""
    return {
        "Optimo": (A_opt, B_opt),
        "Estrecho": (TIGHT_ASK, TIGHT_BID),
        "Amplio": (WIDE_ASK, WIDE_BID),
    }
