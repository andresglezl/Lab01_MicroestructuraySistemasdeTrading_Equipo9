"""
Generador automatico de la presentacion en PDF (docs/presentacion.pdf) usando
reportlab. La presentacion tiene un maximo de 12 diapositivas y resume el
planteamiento del problema, la optimizacion, la simulacion/Monte Carlo y el
analisis de sensibilidad, con los numeros reales obtenidos en la corrida.
"""

import os

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas

PAGE_SIZE = landscape(letter)
PAGE_W, PAGE_H = PAGE_SIZE
MARGIN = 0.6 * inch

NAVY = colors.HexColor("#1f2d50")
ACCENT = colors.HexColor("#1f77b4")
GRAY = colors.HexColor("#444444")
LIGHT_GRAY = colors.HexColor("#888888")


def _new_slide(c, title, subtitle=None):
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 1.05 * inch, PAGE_W, 1.05 * inch, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(MARGIN, PAGE_H - 0.72 * inch, title)
    if subtitle:
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.HexColor("#c9d4f0"))
        c.drawString(MARGIN, PAGE_H - 0.95 * inch, subtitle)
    c.setFillColor(colors.black)


def _bullets(c, items, x, y, width=None, font_size=13, leading=20, bold_first_line=False):
    c.setFont("Helvetica", font_size)
    c.setFillColor(GRAY)
    for i, item in enumerate(items):
        c.setFont("Helvetica-Bold" if (bold_first_line and i == 0) else "Helvetica", font_size)
        c.setFillColor(colors.black)
        c.drawString(x, y, u"• " + item)
        y -= leading
    return y


def _footer(c, page_num, total=12):
    c.setFont("Helvetica", 9)
    c.setFillColor(LIGHT_GRAY)
    c.drawString(MARGIN, 0.35 * inch, "Laboratorio 01 - Cotizaciones Optimas de un Formador de Mercado (Copeland & Galai, 1983) - Equipo 9")
    c.drawRightString(PAGE_W - MARGIN, 0.35 * inch, f"{page_num} / {total}")
    c.setFillColor(colors.black)


def _image_fit(c, path, x, y, max_w, max_h):
    if not path or not os.path.exists(path):
        return
    from reportlab.lib.utils import ImageReader

    img = ImageReader(path)
    iw, ih = img.getSize()
    scale = min(max_w / iw, max_h / ih)
    w, h = iw * scale, ih * scale
    c.drawImage(img, x + (max_w - w) / 2, y + (max_h - h) / 2, width=w, height=h, preserveAspectRatio=True, mask="auto")


def generate_report(results, output_path=None):
    """
    Construye docs/presentacion.pdf (12 diapositivas) a partir del
    diccionario `results` producido por main.py, con:

      - S0, distribucion de P, pi_I, pi_L, demanda no informada
      - A_opt, B_opt, spread_opt, utility_opt
      - resultados de simulacion de 10,000 trades y Monte Carlo por regimen
      - sensibilidad del spread optimo vs pi_I
      - rutas de las 5 figuras generadas en docs/figures/
    """
    if output_path is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_path = os.path.join(project_root, "docs", "presentacion.pdf")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    A_opt = results["A_opt"]
    B_opt = results["B_opt"]
    spread_opt = results["spread_opt"]
    utility_opt = results["utility_opt"]
    S0 = results["S0"]
    pi_I = results["pi_I"]
    pi_L = results["pi_L"]
    figures = results["figures"]
    mc_results = results["mc_results"]
    regimes = results["regimes"]
    sens_pi = results["sensitivity_pi"]
    sens_spreads = results["sensitivity_spreads"]

    c = canvas.Canvas(output_path, pagesize=PAGE_SIZE)
    page = 0

    # ---------------- Slide 1: Portada ----------------
    page += 1
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 0.6 * inch, "Cotizaciones Optimas de un Formador de Mercado")
    c.setFont("Helvetica", 18)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 + 0.1 * inch, "Modelo de Copeland y Galai (1983)")
    c.setFont("Helvetica", 14)
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 0.5 * inch, "Laboratorio 01 - Microestructura y Sistemas de Trading")
    c.drawCentredString(PAGE_W / 2, PAGE_H / 2 - 0.85 * inch, "Equipo 9")
    _footer(c, page)
    c.showPage()

    # ---------------- Slide 2: Planteamiento del problema ----------------
    page += 1
    _new_slide(c, "1. Planteamiento del problema", "Por que un formador de mercado necesita un spread")
    _bullets(
        c,
        [
            "Un formador de mercado (dealer) cotiza un precio Bid (B) y un precio Ask (A) alrededor",
            "  de un precio de referencia S0, sin saber si la contraparte esta informada.",
            "Trader informado (prob. pi_I): conoce el valor fundamental P y opera solo si le conviene",
            "  -> genera perdida esperada al dealer (seleccion adversa).",
            "Trader de liquidez (prob. pi_L = 1 - pi_I): opera sin informacion privada",
            "  -> genera ganancia esperada al dealer.",
            "El dealer debe elegir (A, B) que maximicen su utilidad esperada por trade, compensando",
            "  la ganancia de los traders de liquidez contra la perdida frente a los informados.",
        ],
        MARGIN,
        PAGE_H - 1.6 * inch,
    )
    _footer(c, page)
    c.showPage()

    # ---------------- Slide 3: Formulacion matematica ----------------
    page += 1
    _new_slide(c, "2. Formulacion matematica Copeland-Galai", "Ganancia, perdida y utilidad esperada")
    _bullets(
        c,
        [
            f"Precio de referencia: S0 = {S0:.2f}",
            "Valor fundamental P ~ Erlang(k=60, lambda=3)  [scipy.stats.gamma(a=60, scale=1/3)]",
            f"Probabilidad de informado: pi_I = {pi_I:.2f}      Probabilidad de liquidez: pi_L = {pi_L:.2f}",
            "Demanda no informada: pi_LB(x) = pi_LS(x) = max(0.50 - 0.08 x, 0)",
            "",
            "Ganancia esperada:",
            "   G(A,B) = pi_L [ pi_LB(A-S0)(A-S0) + pi_LS(S0-B)(S0-B) ]",
            "Perdida esperada (seleccion adversa):",
            "   L(A,B) = pi_I [ integral_A^inf (P-A) f(P) dP + integral_0^B (B-P) f(P) dP ]",
            "Utilidad esperada:  Pi(A,B) = G(A,B) - L(A,B)",
        ],
        MARGIN,
        PAGE_H - 1.6 * inch,
        font_size=12.5,
        leading=19,
    )
    _footer(c, page)
    c.showPage()

    # ---------------- Slide 4: Figura 1 ----------------
    page += 1
    _new_slide(c, "3. Demanda de liquidez no informada", "Probabilidad de ejecucion vs. spread")
    _image_fit(c, figures.get("execution_probability"), MARGIN, 1.0 * inch, PAGE_W - 2 * MARGIN, PAGE_H - 2.1 * inch)
    _footer(c, page)
    c.showPage()

    # ---------------- Slide 5: Resultados de optimizacion ----------------
    page += 1
    _new_slide(c, "4. Resultados de la optimizacion", f"scipy.optimize.minimize, pi_I = {pi_I:.2f}")
    _bullets(
        c,
        [
            f"Ask optimo:      A* = {A_opt:.2f}   (A* - S0 = {A_opt - S0:.2f})",
            f"Bid optimo:      B* = {B_opt:.2f}   (S0 - B* = {S0 - B_opt:.2f})",
            f"Spread optimo:   A* - B* = {spread_opt:.2f}",
            f"Utilidad esperada por trade:  Pi(A*,B*) = {utility_opt:.4f}",
            "",
            "El spread optimo se amplia respecto al caso sin informacion asimetrica para compensar",
            "la perdida esperada frente a los traders informados.",
        ],
        MARGIN,
        PAGE_H - 1.6 * inch,
        font_size=15,
        leading=26,
    )
    _footer(c, page)
    c.showPage()

    # ---------------- Slide 6: Interpretacion optimizacion ----------------
    page += 1
    _new_slide(c, "5. Interpretacion economica", "Trade-off ganancia vs. perdida esperada")
    _bullets(
        c,
        [
            f"Con pi_I = 0 (monopolista, sin informacion asimetrica): spread teorico = 0.50/0.08 = 6.25",
            "  (3.125 por lado), verificado por tests/test_model.py::test_monopolist_spread_zero_informed.",
            f"Con pi_I = {pi_I:.2f}: el spread optimo crece a {spread_opt:.2f}, es decir "
            f"{spread_opt - 6.25:.2f} unidades mas ancho.",
            "El dealer amplia el spread para reducir la frecuencia de ejecucion contra traders",
            "  informados, sacrificando parte del volumen de traders de liquidez.",
        ],
        MARGIN,
        PAGE_H - 1.6 * inch,
        font_size=13,
        leading=22,
    )
    _footer(c, page)
    c.showPage()

    # ---------------- Slide 7: Figura 2 ----------------
    page += 1
    _new_slide(c, "6. Simulacion de 10,000 trades", "P&L acumulado por regimen de cotizacion")
    _image_fit(c, figures.get("cumulative_pnl"), MARGIN, 1.0 * inch, PAGE_W - 2 * MARGIN, PAGE_H - 2.1 * inch)
    _footer(c, page)
    c.showPage()

    # ---------------- Slide 8: Figura 3 ----------------
    page += 1
    _new_slide(c, "7. Simulacion de 10,000 trades", "Inventario acumulado por regimen de cotizacion")
    _image_fit(c, figures.get("cumulative_inventory"), MARGIN, 1.0 * inch, PAGE_W - 2 * MARGIN, PAGE_H - 2.1 * inch)
    _footer(c, page)
    c.showPage()

    # ---------------- Slide 9: Monte Carlo (tabla + histograma) ----------------
    page += 1
    _new_slide(c, "8. Monte Carlo (1,000 corridas x 1,000 trades)", "P&L final por regimen")
    table_y = PAGE_H - 1.7 * inch
    headers = ["Regimen", "Bid", "Ask", "P&L medio", "Desv. Std.", "P(perdida)"]
    col_x = [MARGIN, MARGIN + 1.7 * inch, MARGIN + 2.6 * inch, MARGIN + 3.5 * inch, MARGIN + 4.8 * inch, MARGIN + 6.1 * inch]
    c.setFont("Helvetica-Bold", 11)
    for x, h in zip(col_x, headers):
        c.drawString(x, table_y, h)
    c.line(MARGIN, table_y - 5, PAGE_W - MARGIN, table_y - 5)
    c.setFont("Helvetica", 11)
    row_y = table_y - 24
    for name, (a, b) in regimes.items():
        res = mc_results[name]
        row = [name, f"{b:.2f}", f"{a:.2f}", f"{res['mean_pnl']:.2f}", f"{res['std_pnl']:.2f}", f"{res['prob_loss']*100:.1f}%"]
        for x, v in zip(col_x, row):
            c.drawString(x, row_y, v)
        row_y -= 22
    _footer(c, page)
    c.showPage()

    # ---------------- Slide 10: Figura 4 ----------------
    page += 1
    _new_slide(c, "9. Distribucion Monte Carlo del P&L final", "Comparativa de los tres regimenes")
    _image_fit(c, figures.get("mc_histogram"), MARGIN, 1.0 * inch, PAGE_W - 2 * MARGIN, PAGE_H - 2.1 * inch)
    _footer(c, page)
    c.showPage()

    # ---------------- Slide 11: Figura 5 (sensibilidad) ----------------
    page += 1
    _new_slide(c, "10. Sensibilidad del spread optimo vs. pi_I", "Teoria de seleccion adversa")
    _image_fit(c, figures.get("spread_sensitivity"), MARGIN, 1.4 * inch, PAGE_W - 2 * MARGIN, PAGE_H - 2.5 * inch)
    sens_txt = "   ".join(f"pi_I={p}: spread={s:.2f}" for p, s in zip(sens_pi, sens_spreads))
    c.setFont("Helvetica", 11)
    c.setFillColor(GRAY)
    c.drawCentredString(PAGE_W / 2, 1.05 * inch, sens_txt)
    c.setFillColor(colors.black)
    _footer(c, page)
    c.showPage()

    # ---------------- Slide 12: Conclusiones / respuestas al cliente ----------------
    page += 1
    _new_slide(c, "11-12. Conclusiones y respuestas al cliente", "Preguntas 1-5 (ver README para el detalle numerico)")
    tight_res = mc_results["Estrecho"]
    optimo_res = mc_results["Optimo"]
    _bullets(
        c,
        [
            f"1) Traders informados -> spread: el regimen Estrecho pierde en promedio {tight_res['mean_pnl']:.1f}",
            f"   por 1,000 trades (P(perdida)={tight_res['prob_loss']*100:.0f}%) por operar casi siempre contra informados.",
            "2) El costo de seleccion adversa L(A,B) decrece monotonamente al ampliar A y B (test unitario).",
            "3) Inventario: en una trayectoria larga, el regimen Amplio acumula la mayor deriva neta",
            "   (inventario final mas alejado de 0); en Monte Carlo, el regimen Estrecho tiene la mayor",
            "   volatilidad de inventario entre corridas. Ambos casos exponen al dealer a riesgo de precio",
            "   (inventory risk) no modelado explicitamente.",
            f"4) El spread optimo crece con pi_I: {', '.join(f'{p}->{s:.2f}' for p, s in zip(sens_pi, sens_spreads))},",
            "   consistente con la teoria de seleccion adversa (Glosten-Milgrom / Copeland-Galai).",
            "5) Limitaciones: un trade forzado por iteracion, rentabilidad por trade y no por tiempo,",
            "   y ausencia de dinamica de precio/competencia entre dealers.",
        ],
        MARGIN,
        PAGE_H - 1.6 * inch,
        font_size=12,
        leading=19,
    )
    _footer(c, page)
    c.showPage()

    c.save()
    return output_path
