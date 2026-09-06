"""
Modelo de cotizaciones optimas de un formador de mercado (Copeland & Galai, 1983).

Un formador de mercado (dealer) cotiza un precio de compra (Bid, B) y un precio
de venta (Ask, A) alrededor de un precio de referencia S0. Dos tipos de traders
llegan al mercado:

- Traders informados (prob. pi_I): conocen el valor fundamental P (una variable
  aleatoria) y operan solo si les conviene, generando una perdida esperada para
  el dealer (seleccion adversa).
- Traders de liquidez / no informados (prob. pi_L = 1 - pi_I): operan sin
  informacion privada, generando una ganancia esperada para el dealer.

El dealer elige (A, B) para maximizar la utilidad esperada por trade:

    Pi(A, B) = G(A, B) - L(A, B)
"""

import numpy as np
from scipy import stats
from scipy.integrate import quad
from scipy.optimize import minimize

# ---------------------------------------------------------------------------
# Parametros fijos del modelo (Equipo 9)
# ---------------------------------------------------------------------------
S0 = 19.90                 # Precio fundamental / de referencia
GAMMA_A = 60                # Forma (k) de la distribucion Erlang/Gamma de P
GAMMA_SCALE = 1.0 / 3.0      # Escala (1/lambda) de la distribucion de P
PI_I = 0.40                  # Probabilidad de trader informado
PI_L = 0.60                  # Probabilidad de trader de liquidez
UNINFORMED_INTERCEPT = 0.50  # Ordenada al origen de la demanda no informada
UNINFORMED_SLOPE = 0.08      # Pendiente de la demanda no informada

# Distribucion del valor fundamental P: Erlang(k=60, lambda=3)
P_DIST = stats.gamma(a=GAMMA_A, scale=GAMMA_SCALE)


def f_P(P):
    """Densidad de probabilidad (pdf) del valor fundamental P ~ Erlang(60, 3)."""
    return P_DIST.pdf(P)


def pi_uninformed(cost):
    """
    Probabilidad de que un trader de liquidez este dispuesto a operar dado un
    costo `cost` (= A - S0 para el lado compra, o S0 - B para el lado venta).

    pi_LB(x) = pi_LS(x) = max(0.50 - 0.08 * x, 0)
    """
    cost = np.asarray(cost, dtype=float)
    return np.maximum(UNINFORMED_INTERCEPT - UNINFORMED_SLOPE * cost, 0.0)


def expected_gain(A, B, S0=S0, pi_L=PI_L):
    """
    Ganancia esperada por trade proveniente de traders de liquidez:

    G(A,B) = pi_L * [ pi_LB(A-S0) * (A-S0) + pi_LS(S0-B) * (S0-B) ]
    """
    x_ask = A - S0
    x_bid = S0 - B
    gain_ask = pi_uninformed(x_ask) * x_ask
    gain_bid = pi_uninformed(x_bid) * x_bid
    return pi_L * (gain_ask + gain_bid)


def expected_loss_ask(A, pi_I=PI_I):
    """
    Perdida esperada por seleccion adversa en el lado ASK (venta del dealer):

    L_ask(A) = pi_I * integral_A^inf (P - A) f(P) dP
    """
    integral, _ = quad(lambda P: (P - A) * f_P(P), A, np.inf)
    return pi_I * integral


def expected_loss_bid(B, pi_I=PI_I):
    """
    Perdida esperada por seleccion adversa en el lado BID (compra del dealer):

    L_bid(B) = pi_I * integral_0^B (B - P) f(P) dP
    """
    integral, _ = quad(lambda P: (B - P) * f_P(P), 0, B)
    return pi_I * integral


def expected_loss(A, B, pi_I=PI_I):
    """
    Perdida esperada total por seleccion adversa frente a traders informados:

    L(A,B) = pi_I * [ integral_A^inf (P-A) f(P) dP + integral_0^B (B-P) f(P) dP ]
    """
    return expected_loss_ask(A, pi_I) + expected_loss_bid(B, pi_I)


def expected_utility(A, B, S0=S0, pi_I=PI_I, pi_L=PI_L):
    """Utilidad esperada por trade del formador de mercado: Pi(A,B) = G(A,B) - L(A,B)."""
    return expected_gain(A, B, S0=S0, pi_L=pi_L) - expected_loss(A, B, pi_I=pi_I)


def optimize_quotes(pi_I=PI_I, pi_L=None, S0=S0):
    """
    Encuentra las cotizaciones optimas (A*, B*) que maximizan la utilidad
    esperada del formador de mercado, sujeto a:

        B in (0, S0]
        A in [S0, inf)

    Se resuelve minimizando -Pi(A,B) con scipy.optimize.minimize.

    Parameters
    ----------
    pi_I : float
        Probabilidad de trader informado.
    pi_L : float, optional
        Probabilidad de trader de liquidez. Si es None, se usa 1 - pi_I.
    S0 : float
        Precio fundamental / de referencia.

    Returns
    -------
    A_opt, B_opt, spread_opt, utility_opt : float
    """
    if pi_L is None:
        pi_L = 1.0 - pi_I

    def objective(params):
        A, B = params
        return -expected_utility(A, B, S0=S0, pi_I=pi_I, pi_L=pi_L)

    x0 = [S0 + 0.5, S0 - 0.5]
    bounds = [(S0, S0 + 50.0), (1e-6, S0)]

    result = minimize(objective, x0, method="L-BFGS-B", bounds=bounds)

    A_opt, B_opt = result.x
    spread_opt = A_opt - B_opt
    utility_opt = expected_utility(A_opt, B_opt, S0=S0, pi_I=pi_I, pi_L=pi_L)

    return A_opt, B_opt, spread_opt, utility_opt
