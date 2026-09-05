"""
Pruebas unitarias del modelo Copeland-Galai (src/model.py). Ejecutar con:

    pytest tests/test_model.py -v
"""

import numpy as np

from src.model import (
    S0,
    pi_uninformed,
    expected_loss_ask,
    optimize_quotes,
)


def test_uninformed_prob_non_negative():
    """pi_LB(s) y pi_LS(s) nunca deben ser negativos, para cualquier costo s."""
    costs = np.array([-5.0, 0.0, 1.0, 3.125, 6.25, 6.26, 10.0, 100.0])
    probs = pi_uninformed(costs)
    assert np.all(probs >= 0.0), f"Se encontraron probabilidades negativas: {probs}"
    # Ademas, mas alla del punto de corte (6.25) la probabilidad debe ser exactamente 0
    assert pi_uninformed(6.25) == 0.0
    assert pi_uninformed(100.0) == 0.0


def test_expected_loss_decreasing_in_A():
    """L_ask(A) = pi_I * integral_A^inf (P-A) f(P) dP debe ser estrictamente
    decreciente conforme A aumenta (a mayor ask, menor perdida por seleccion
    adversa en el lado de venta del dealer)."""
    A_values = [S0 + 0.5, S0 + 1.0, S0 + 2.0, S0 + 4.0]
    losses = [expected_loss_ask(A) for A in A_values]

    for i in range(len(losses) - 1):
        assert losses[i] > losses[i + 1], (
            f"Se esperaba que la perdida decreciera de A={A_values[i]} "
            f"(L={losses[i]:.6f}) a A={A_values[i+1]} (L={losses[i+1]:.6f})"
        )
    assert all(l >= 0 for l in losses), "La perdida esperada no puede ser negativa"


def test_monopolist_spread_zero_informed():
    """Con pi_I = 0 (sin traders informados) no hay seleccion adversa, y el
    spread optimo debe coincidir con el del monopolista teorico:

        s* = 0.50 / 0.08 = 6.25 (total), es decir 3.125 por lado.
    """
    A_opt, B_opt, spread_opt, utility_opt = optimize_quotes(pi_I=0.0)

    theoretical_half_spread = 0.50 / 0.08 / 2.0  # 3.125
    theoretical_total_spread = 0.50 / 0.08        # 6.25

    assert np.isclose(A_opt - S0, theoretical_half_spread, atol=0.05)
    assert np.isclose(S0 - B_opt, theoretical_half_spread, atol=0.05)
    assert np.isclose(spread_opt, theoretical_total_spread, atol=0.1)
