"""
Estadística de los resultados.

Por cada punto del experimento (estructura, orden de datos, N, M ...) hay
`repeticiones` mediciones independientes. De ellas se calcula:

  media, desviación estándar, coeficiente de variación (CV = desv/media),
  mediana, cuartiles Q1–Q3, mínimo, máximo,
  intervalo de confianza del 95 % para la media (t de Student),
  número de valores atípicos según la regla de Tukey (fuera de Q1−1.5·IQR, Q3+1.5·IQR).

Los atípicos se CUENTAN y se REPORTAN pero no se eliminan: borrarlos sería
maquillar los datos. Si el CV es bajo, los atípicos no cambian la conclusión.

Además se ajustan curvas para comparar con la teoría:
  * Ley de potencia  t = a·N^b  (recta en log-log). b ≈ 1 -> lineal; b ≈ 0 -> casi constante.
  * Logarítmica      t = a + b·log2(N). Si R² ≈ 1 el crecimiento es logarítmico.
"""

import math
import statistics

import numpy as np

# Valor crítico t de Student (dos colas, 95 %) según grados de libertad.
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
        8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160,
        14: 2.145, 15: 2.131, 19: 2.093, 24: 2.064, 29: 2.045}


def t_critico(gl):
    if gl in _T95:
        return _T95[gl]
    menores = [k for k in _T95 if k <= gl]
    return _T95[max(menores)] if gl < 30 else 1.96


def resumir(valores):
    """Resumen estadístico de una lista de mediciones."""
    n = len(valores)
    media = statistics.fmean(valores)
    desv = statistics.stdev(valores) if n > 1 else 0.0
    if n >= 2:
        q1, mediana, q3 = statistics.quantiles(valores, n=4, method="inclusive")
    else:
        q1 = mediana = q3 = valores[0]
    iqr = q3 - q1
    atipicos = sum(1 for v in valores if v < q1 - 1.5 * iqr or v > q3 + 1.5 * iqr)
    margen = t_critico(n - 1) * desv / math.sqrt(n) if n > 1 else 0.0
    return {
        "ejecuciones": n,
        "media": media,
        "desv_est": desv,
        "cv_pct": 100 * desv / media if media else 0.0,
        "mediana": mediana,
        "q1": q1,
        "q3": q3,
        "minimo": min(valores),
        "maximo": max(valores),
        "ic95_inf": media - margen,
        "ic95_sup": media + margen,
        "atipicos": atipicos,
    }


def agrupar_y_resumir(filas, claves, campo):
    """Agrupa filas (dicts) por `claves` y resume la columna `campo`."""
    grupos = {}
    for f in filas:
        if f.get(campo) in (None, ""):
            continue
        grupos.setdefault(tuple(f[c] for c in claves), []).append(float(f[campo]))
    salida = []
    for llave, valores in grupos.items():
        fila = dict(zip(claves, llave))
        fila["medida"] = campo
        fila.update(resumir(valores))
        salida.append(fila)
    return salida


def ajuste_potencia(xs, ys):
    """t = a·N^b. Devuelve (a, b, R²) del ajuste lineal en log-log."""
    lx, ly = np.log(np.asarray(xs, float)), np.log(np.asarray(ys, float))
    b, log_a = np.polyfit(lx, ly, 1)
    pred = log_a + b * lx
    r2 = 1 - np.sum((ly - pred) ** 2) / np.sum((ly - ly.mean()) ** 2)
    return math.exp(log_a), b, r2


def ajuste_logaritmico(xs, ys):
    """t = a + b·log2(N). Devuelve (a, b, R²)."""
    lx, y = np.log2(np.asarray(xs, float)), np.asarray(ys, float)
    b, a = np.polyfit(lx, y, 1)
    pred = a + b * lx
    r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)
    return a, b, r2


def ajuste_lineal(xs, ys):
    """t = a + b·x. Devuelve (a, b, R²)."""
    x, y = np.asarray(xs, float), np.asarray(ys, float)
    b, a = np.polyfit(x, y, 1)
    pred = a + b * x
    r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)
    return a, b, r2
