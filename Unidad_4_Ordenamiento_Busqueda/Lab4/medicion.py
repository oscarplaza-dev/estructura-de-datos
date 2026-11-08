"""
Cómo se miden los tiempos y cómo se resumen (igual que en mi Lab3).

Reglas de medición:
  1. Reloj: time.perf_counter() (el de mayor resolución de Python).
  2. El recolector de basura (gc) se apaga mientras se cronometra, para que una
     limpieza de memoria no caiga dentro de la medición.
  3. "Ventana mínima": un bloque de consultas se repite hasta que el tiempo
     acumulado supere la ventana, y se divide por el total de consultas. Así nunca
     se mide algo que dure microsegundos sueltos (el ruido de la RAM, del navegador
     o de WhatsApp queda diluido).
  4. Antes de medir se hacen unas consultas de calentamiento que no se cuentan.

Estadística: media, desviación estándar, coeficiente de variación (CV),
intervalo de confianza del 95 % (t de Student) y ajuste t ≈ a·n^b en log-log.
"""

import gc
import math
import os
import platform
import sys
from time import perf_counter

import numpy as np


class SinRecolector:
    """with SinRecolector(): ...  -> apaga el gc y lo restaura al salir."""

    def __enter__(self):
        gc.collect()
        self._estaba = gc.isenabled()
        gc.disable()

    def __exit__(self, *exc):
        if self._estaba:
            gc.enable()


def segundos_por_consulta(funcion, consultas, ventana_s, calentamiento=5):
    """Tiempo promedio de UNA consulta (segundos). Repite el bloque hasta la ventana."""
    for c in consultas[:calentamiento]:
        funcion(c)
    with SinRecolector():
        bloques = 0
        inicio = perf_counter()
        while True:
            for c in consultas:
                funcion(c)
            bloques += 1
            total = perf_counter() - inicio
            if total >= ventana_s:
                break
    return total / (bloques * len(consultas))


def segundos_construccion(construir, ventana_s):
    """Tiempo promedio de construir la estructura completa (segundos).
    Si construir es muy rápido, se construye varias veces hasta la ventana.
    Devuelve (segundos, última estructura construida)."""
    with SinRecolector():
        veces = 0
        inicio = perf_counter()
        while True:
            estructura = construir()
            veces += 1
            total = perf_counter() - inicio
            if total >= ventana_s:
                break
    return total / veces, estructura


# --- Estadística ------------------------------------------------------------

# Valor t de Student (dos colas, 95 %) según los grados de libertad.
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
        8: 2.306, 9: 2.262, 10: 2.228, 15: 2.131, 20: 2.086, 30: 2.042}


def t95(gl):
    if gl in _T95:
        return _T95[gl]
    mayores = [g for g in _T95 if g >= gl]
    return _T95[min(mayores)] if mayores else 1.96


def resumen(valores):
    """media, desviación, CV (%), mitad del IC 95 %, mínimo, máximo."""
    v = np.asarray(valores, dtype=float)
    media = float(v.mean())
    desv = float(v.std(ddof=1)) if len(v) > 1 else 0.0
    cv = 100 * desv / media if media else 0.0
    ic = t95(len(v) - 1) * desv / math.sqrt(len(v)) if len(v) > 1 else 0.0
    return {"media": media, "desv": desv, "cv": cv, "ic95": ic,
            "min": float(v.min()), "max": float(v.max()), "reps": len(v)}


def ajuste_potencia(xs, ys):
    """Ajusta y = a·x^b con una recta en log-log. Devuelve (a, b, R²)."""
    lx, ly = np.log10(xs), np.log10(ys)
    b, log_a = np.polyfit(lx, ly, 1)
    predicho = log_a + b * lx
    ss_res = float(((ly - predicho) ** 2).sum())
    ss_tot = float(((ly - ly.mean()) ** 2).sum())
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    return 10 ** log_a, float(b), r2


def describir_entorno():
    """Texto con el hardware y el software usados (para resultados/entorno.txt)."""
    import matplotlib
    lineas = [
        f"Sistema operativo: {platform.platform()}",
        f"Procesador: {platform.processor() or platform.machine()}",
        f"Núcleos lógicos: {os.cpu_count()}",
        f"Python: {platform.python_version()} ({platform.python_implementation()})",
        f"numpy: {np.__version__}",
        f"matplotlib: {matplotlib.__version__}",
        "Reloj: time.perf_counter()",
    ]
    return "\n".join(lineas)
