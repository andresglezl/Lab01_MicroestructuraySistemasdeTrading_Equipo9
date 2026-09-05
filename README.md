# Laboratorio 01: Cotizaciones Óptimas de un Formador de Mercado (Copeland & Galai, 1983)

**Microestructura y Sistemas de Trading — Equipo 9**

Integrante(s): Adrián Marcelo Ballesteros Herrera

---

## Descripción del proyecto

Este proyecto implementa de principio a fin el modelo de Copeland y Galai (1983) para un
formador de mercado (dealer) que debe elegir simultáneamente un precio de compra (Bid, `B`)
y un precio de venta (Ask, `A`) alrededor de un precio de referencia `S0`, enfrentando dos
tipos de contrapartes: traders **informados** (probabilidad `pi_I`), que conocen el valor
fundamental `P` y solo operan cuando les conviene, generando una **pérdida esperada por
selección adversa**; y traders de **liquidez** (probabilidad `pi_L = 1 - pi_I`), que operan
sin información privada y generan una **ganancia esperada** al dealer. El repositorio
resuelve numéricamente las cotizaciones óptimas `(A*, B*)` que maximizan la utilidad
esperada por trade, simula 10,000 trades secuenciales y un análisis de Monte Carlo
(1,000 corridas × 1,000 trades) para tres regímenes de cotización (Óptimo, Estrecho y
Amplio), y documenta los resultados en figuras, pruebas unitarias y una presentación en
PDF generada automáticamente.

## Estructura del repositorio

```
Lab01_MicroestructuraySistemasdeTrading_Equipo9/
│── README.md
│── requirements.txt
│── .gitignore
│── main.py
│── src/
│   ├── model.py        # Función de utilidad y optimización (Copeland-Galai)
│   ├── simulation.py   # Simulador de trades y Monte Carlo
│   ├── plots.py        # Generación de las 5 figuras obligatorias
│   └── report.py       # Generador automático de docs/presentacion.pdf
│── tests/
│   └── test_model.py   # Pruebas unitarias con pytest
│── notebooks/
│   └── analysis.ipynb  # Notebook interactivo (solo imports y visualización)
└── docs/
    ├── figures/         # Figuras PNG generadas
    └── presentacion.pdf # Presentación PDF generada automáticamente
```

## Instalación y reproducción

```bash
# 1. Crear y activar un entorno virtual (opcional pero recomendado)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar el pipeline completo
python main.py
```

`python main.py`, ejecutado desde la raíz del proyecto, realiza en una sola corrida:

1. La optimización de `(A*, B*)` y despliega los resultados numéricos en consola (2 decimales).
2. Las pruebas unitarias con `pytest`.
3. La simulación de 10,000 trades y el análisis de Monte Carlo (1,000 × 1,000) para los tres
   regímenes de cotización, imprimiendo las tablas de resultados.
4. La generación de las 5 figuras obligatorias en `docs/figures/`.
5. La generación de la presentación `docs/presentacion.pdf`.

## Reproducibilidad

Toda la aleatoriedad del proyecto se fija con **`np.random.seed(42)`**: una vez al inicio de
`main.py`, y nuevamente al inicio de cada llamada a `simulate_trades` (`src/simulation.py`),
de modo que (a) la corrida completa del script es 100% reproducible extremo a extremo, y
(b) usar la misma semilla base en los tres regímenes de cotización permite comparar
Óptimo/Estrecho/Amplio sobre el **mismo camino de mercado simulado**, aislando el efecto de
la cotización elegida. En el análisis de Monte Carlo, la corrida `i` usa `seed = 42 + i`, de
forma que las 1,000 corridas son independientes entre sí pero el lote completo es
reproducible.

## Parámetros del modelo (fijos)

| Parámetro | Valor |
|---|---|
| `S0` (precio de referencia) | 19.90 |
| Distribución de `P` | Erlang(k=60, λ=3) → `scipy.stats.gamma(a=60, scale=1/3)` |
| `pi_I` (prob. informado) | 0.40 |
| `pi_L` (prob. liquidez) | 0.60 |
| Demanda no informada | `pi_LB(x) = pi_LS(x) = max(0.50 - 0.08·x, 0)` |

## Uso de Asistencia de Inteligencia Artificial

En cumplimiento de la regla 6 del laboratorio, se declara explícitamente que este proyecto
fue desarrollado con asistencia del asistente de IA **Claude Code (Anthropic, modelo Claude
Sonnet 5)**. El uso de la IA se limitó a:

- Estructurar el proyecto y escribir el código en `src/`, `tests/`, `main.py` y `notebooks/`
  a partir de la especificación matemática del modelo Copeland-Galai (1983) provista en el
  enunciado del laboratorio.
- Generar el script de creación automática de la presentación PDF (`src/report.py`) y las
  5 figuras obligatorias (`src/plots.py`).
- Redactar la documentación (`README.md`, docstrings) y verificar/ejecutar las pruebas
  unitarias y el pipeline completo (`python main.py`) para validar que los resultados
  numéricos reportados en este documento son reales y reproducibles.

Todos los resultados numéricos citados en la sección de análisis a continuación provienen
de una ejecución real de `python main.py` con `seed=42`, no de valores estimados o
inventados por el asistente. El equipo revisó y validó la lógica matemática (integración de
la pérdida esperada con `scipy.integrate.quad`, optimización con `scipy.optimize.minimize`,
y las pruebas unitarias) antes de aceptar el código como definitivo.

---

## Resultados de la optimización

Con los parámetros base (`S0=19.90`, `pi_I=0.40`, `pi_L=0.60`):

| Cantidad | Valor |
|---|---|
| Ask óptimo `A*` | **23.43** |
| Bid óptimo `B*` | **16.45** |
| Spread óptimo `A*-B*` | **6.98** |
| Utilidad esperada por trade `Π(A*,B*)` | **0.8403** |

Como caso de control, con `pi_I=0` (sin selección adversa) el spread óptimo converge al
monopolista teórico `0.50/0.08 = 6.25` (3.125 por lado), verificado en
`tests/test_model.py::test_monopolist_spread_zero_informed`.

## Regímenes de cotización comparados

| Régimen | Bid | Ask | Spread | P&L (10,000 trades) | Inventario final | % trades ejecutados |
|---|---|---|---|---|---|---|
| **Óptimo** | 16.45 | 23.43 | 6.98 | **+8,376.87** | -93 | 33.5% |
| **Estrecho** | 19.75 | 20.05 | 0.30 | **-6,766.82** | -8 | 96.7% |
| **Amplio** | 18.40 | 21.40 | 3.00 | **+3,246.05** | -112 | 67.6% |

## Monte Carlo (1,000 corridas × 1,000 trades)

| Régimen | P&L medio | Desv. estándar | P(pérdida) |
|---|---|---|---|
| **Óptimo** | +840.89 | 54.12 | **0.0%** |
| **Estrecho** | -675.26 | 45.42 | **100.0%** |
| **Amplio** | +326.22 | 44.60 | **0.0%** |

## Sensibilidad del spread óptimo vs. `pi_I`

| `pi_I` | Spread óptimo `A*-B*` |
|---|---|
| 0.1 | 6.40 |
| 0.4 | 6.98 |
| 0.7 | 7.99 |

---

## Análisis: respuestas a las 5 preguntas del cliente

### a. ¿Por qué los traders informados generan la necesidad de un spread?

Un trader informado conoce el valor fundamental `P` y solo opera cuando el precio cotizado
le favorece: compra en `A` si `P>A` y vende en `B` si `P<B`. Si el dealer cotizara sin
spread (`A=B=S0`), perdería en promedio `E[P]-S0` en cada operación contra un informado.
El régimen **Estrecho** (Bid=19.75, Ask=20.05, spread=0.30) ilustra esto con cifras reales:
al ser el spread casi nulo, el **96.7%** de los 10,000 trades simulados se ejecuta (contra
solo 33.5% en el régimen Óptimo), y dentro de esos trades ejecutados, exactamente el
**40.0%** corresponde a traders informados — es decir, prácticamente *todo* trader
informado que llega logra ejecutar, porque el spread es demasiado angosto para filtrarlo.
El resultado es un **P&L acumulado de -6,766.82** en 10,000 trades y una **probabilidad de
pérdida del 100%** en el Monte Carlo (P&L medio = -675.26 por cada 1,000 trades). El spread
existe precisamente para reducir la probabilidad de que un informado encuentre rentable
operar contra el dealer, sacrificando volumen de traders de liquidez a cambio de reducir la
selección adversa.

### b. ¿Cómo cambia el costo de selección adversa conforme se amplía el spread?

La pérdida esperada por lado, `L_ask(A) = pi_I · ∫_A^∞ (P-A) f(P) dP`, es estrictamente
decreciente en `A` (demostrado en `tests/test_model.py::test_expected_loss_decreasing_in_A`
y verificable numéricamente):

| Ask (`A`) | `L_ask(A)` | Bid (`B`) | `L_bid(B)` |
|---|---|---|---|
| 20.05 (Estrecho) | 0.4019 | 19.75 (Estrecho) | 0.3617 |
| 21.40 (Amplio) | 0.1988 | 18.40 (Amplio) | 0.1590 |
| 23.43 (Óptimo) | 0.0539 | 16.45 (Óptimo) | 0.0305 |

Al ampliar el ask de 20.05 a 23.43, la pérdida esperada por selección adversa en ese lado
cae de 0.4019 a 0.0539 (una reducción de **~86.6%**); el lado bid muestra el mismo patrón
(0.3617 → 0.0305, **~91.6%** de reducción). Sin embargo, ampliar el spread también reduce
`pi_LB(x)` y `pi_LS(x)` (menos volumen de liquidez capturado), lo que explica por qué el
óptimo no es "spread infinito": el dealer maximiza `Π(A,B)=G(A,B)-L(A,B)`, no minimiza
`L(A,B)` en solitario.

### c. ¿Cuál régimen acumula el mayor desbalance de inventario y por qué? ¿A qué riesgo real lo expone eso que el modelo no captura?

La respuesta depende de la métrica:

- **En una sola trayectoria larga (10,000 trades, mismo camino simulado):** el régimen
  **Amplio** termina con el mayor desbalance direccional (inventario final = **-112**),
  seguido del Óptimo (-93), y muy por debajo el Estrecho (-8). Esto ocurre porque la media
  de `P` (20.0, dado Erlang(k=60,λ=3)) está ligeramente por encima de `S0` (19.90); en
  bandas anchas y poco frecuentes, esa pequeña asimetría se traduce en una deriva neta y
  persistente hacia más compras ejecutadas por informados que ventas, acumulada trade a
  trade a lo largo de miles de operaciones.
- **En dispersión entre corridas de Monte Carlo (1,000 corridas × 1,000 trades):** el
  régimen **Estrecho** exhibe la mayor volatilidad de inventario (desviación estándar =
  **31.30**, e inventario absoluto promedio = 25.00), muy por encima de Amplio (std=25.81,
  abs. medio=20.61) y Óptimo (std=18.90, abs. medio=15.43). Esto se debe a que, al ejecutar
  casi el 97% de los trades que llegan, el inventario del dealer hace un "random walk" con
  muchísima más frecuencia y volumen que en los regímenes con spread ancho.

En ambos casos, el modelo **no captura el riesgo de precio (inventory risk)** de mantener
una posición direccional grande: si el precio fundamental se mueve mientras el dealer carga
un inventario neto largo o corto de decenas o cientos de unidades, sufre pérdidas de
mark-to-market que el modelo estático de Copeland-Galai (evaluado trade a trade, sin
dinámica temporal del precio ni costo de mantener inventario) simplemente no contempla.

### d. ¿Cómo se comporta el spread óptimo al variar `pi_I`? ¿Coincide con la teoría?

El spread óptimo crece monótonamente con `pi_I`:

| `pi_I` | Spread óptimo |
|---|---|
| 0.1 | 6.40 |
| 0.4 | 6.98 |
| 0.7 | 7.99 |

A mayor probabilidad de enfrentar un trader informado, mayor es la pérdida esperada por
selección adversa en cualquier cotización dada, por lo que el dealer óptimo compensa
ampliando el spread (de 6.40 con `pi_I=0.1` a 7.99 con `pi_I=0.7`, un incremento de
**+24.8%**). Esto **coincide exactamente con la teoría de selección adversa** de
Copeland-Galai / Glosten-Milgrom: el spread bid-ask es, en gran medida, un mecanismo de
protección contra la información asimétrica, y crece con la proporción de contrapartes
informadas en el mercado. En el límite `pi_I → 0`, el spread converge al óptimo del
monopolista sin información asimétrica (6.25), confirmando que el término adicional de
spread observado con `pi_I>0` es enteramente atribuible al costo de selección adversa.

### e. Tres limitaciones del modelo para un formador de mercado real

1. **La simulación fuerza un trade por iteración y mide rentabilidad por trade, no por
   tiempo.** ⚠️ Cada "trade" en `simulate_trades` corresponde a la llegada garantizada de
   exactamente un trader (informado o de liquidez) por iteración, sin noción de tiempo de
   calendario, tasa de llegada (intensidad de Poisson), ni periodos sin actividad. Un
   régimen con spread muy amplio (Amplio) ejecuta 67.6% de sus 10,000 "trades" simulados,
   pero en la realidad un spread amplio reduciría drásticamente la *tasa* de llegada de
   órdenes, no solo la probabilidad condicional de ejecución dado que ya llegó un trader.
   Comparar regímenes por P&L acumulado en N trades es, por tanto, una comparación de
   rentabilidad *por operación*, no de rentabilidad *por unidad de tiempo* (que es la
   métrica que realmente le importaría a un formador de mercado real, sujeto a costos de
   capital y de oportunidad).
2. **No hay riesgo de inventario ni límites de posición.** Como se documentó en la
   pregunta (c), el dealer acumula inventarios netos de más de 100 unidades sin que el
   modelo penalice el riesgo de precio de mantener esa posición, ni le permita ajustar sus
   cotizaciones dinámicamente para gestionar (sesgar) su inventario, como sí hacen los
   formadores de mercado reales (inventory-based market making, à la Ho-Stoll o
   Avellaneda-Stoikov).
3. **Cotización estática, sin competencia ni aprendizaje.** El modelo asume que `pi_I`,
   `pi_L` y la demanda no informada son constantes y conocidas de antemano, que el dealer
   es monopolista (no compite con otros formadores de mercado por el flujo de órdenes), y
   que no actualiza sus creencias sobre el valor fundamental `P` a partir del flujo de
   órdenes observado (aprendizaje tipo Glosten-Milgrom secuencial). En un mercado real, el
   spread y las cotizaciones se ajustan continuamente en respuesta a la competencia, a la
   información revelada por el propio flujo de órdenes y a cambios en la volatilidad de
   `P`.
