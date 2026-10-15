"""
Cómo se miden los tiempos.

Reglas que siguen todas las funciones:
  1. Reloj: time.perf_counter() (el reloj de mayor resolución de Python).
  2. El recolector de basura (gc) se apaga mientras se cronometra, para que
     una pausa de limpieza de memoria no caiga dentro de la medición.
  3. "Ventana mínima": si una operación es muy rápida se repite hasta que el
     tiempo total acumulado supere la ventana; luego se divide por el número
     de repeticiones. Así nunca se mide algo que dure microsegundos sueltos.
"""

import gc
import platform
import os
import sys
from time import perf_counter


class _SinRecolector:
    """with _SinRecolector(): ...  -> apaga el gc y lo restaura al salir."""

    def __enter__(self):
        gc.collect()
        self._estaba = gc.isenabled()
        gc.disable()

    def __exit__(self, *exc):
        if self._estaba:
            gc.enable()


def medir_busquedas(estructura, ids, ventana_s, calentamiento=50):
    """
    Tiempo promedio de UNA búsqueda (en microsegundos).
    Repite el lote completo de M búsquedas hasta superar `ventana_s`.
    Devuelve (us_por_busqueda, lotes_ejecutados, segundos_totales).
    """
    buscar = estructura.buscar
    for id_ in ids[:calentamiento]:          # calentar cachés
        buscar(id_)

    with _SinRecolector():
        lotes = 0
        inicio = perf_counter()
        while True:
            for id_ in ids:
                buscar(id_)
            lotes += 1
            total = perf_counter() - inicio
            if total >= ventana_s:
                break
    return total / (lotes * len(ids)) * 1e6, lotes, total


def medir_lote_unico(estructura, ids):
    """Tiempo TOTAL (segundos) de ejecutar una sola vez las M búsquedas.
    Se usa en el experimento B, donde lo que interesa es el total vs M."""
    buscar = estructura.buscar
    for id_ in ids[:50]:
        buscar(id_)
    with _SinRecolector():
        inicio = perf_counter()
        for id_ in ids:
            buscar(id_)
        return perf_counter() - inicio


def construir_y_medir(clase, estudiantes, ventana_s, **kw):
    """
    Construye la estructura insertando todos los estudiantes (en el orden de
    la lista) y mide el tiempo promedio por inserción en microsegundos.
    Si construir es muy rápido, se construye varias veces hasta la ventana.
    Devuelve (estructura, us_por_insercion).
    """
    with _SinRecolector():
        construcciones = 0
        inicio = perf_counter()
        while True:
            estructura = clase(**kw)
            insertar = estructura.insertar
            for est in estudiantes:
                insertar(est)
            construcciones += 1
            total = perf_counter() - inicio
            if total >= ventana_s:
                break
    return estructura, total / (construcciones * len(estudiantes)) * 1e6


def medir_listado(estructura, ventana_s):
    """Tiempo (milisegundos) de producir el listado completo ordenado por ID."""
    with _SinRecolector():
        veces = 0
        inicio = perf_counter()
        while True:
            estructura.listar()
            veces += 1
            total = perf_counter() - inicio
            if total >= ventana_s:
                break
    return total / veces * 1e3


def describir_entorno():
    """Hardware y software donde se corrió el experimento."""
    cpu = platform.processor() or platform.machine()
    try:                                             # Linux: nombre real del CPU
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for linea in f:
                if linea.startswith("model name"):
                    cpu = linea.split(":", 1)[1].strip()
                    break
    except OSError:
        pass
    try:
        ram = f"{os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 1024**3:.1f} GB"
    except (ValueError, OSError, AttributeError):
        ram = "(no disponible en este sistema operativo)"

    import matplotlib
    import numpy
    return {
        "Sistema operativo": platform.platform(),
        "Procesador": cpu,
        "Núcleos lógicos": str(os.cpu_count()),
        "RAM total": ram,
        "Python": f"{sys.version.split()[0]} ({platform.python_implementation()})",
        "numpy": numpy.__version__,
        "matplotlib": matplotlib.__version__,
        "Reloj": "time.perf_counter()",
    }
