"""
Los tres experimentos. Cada uno escribe sus mediciones CRUDAS (una fila por
medición) en resultados/datos/*.csv. La estadística y las gráficas se
calculan después a partir de esos archivos, así se pueden regenerar sin
volver a correr nada.

  A. busqueda_vs_n   : varía N (estudiantes), M fijo, IDs aleatorios y ordenados.
                       Mide también inserción, listado, altura y nodos visitados.
  B. busqueda_vs_m   : N fijo (10 000), varía M (número de búsquedas).
  C. orden_bmas      : N fijo, varía el orden (hijos por nodo) del árbol B+.
"""

import csv
import os
import time

from .modelo import generar_estudiantes, generar_busquedas, nuevo_generador
from .estructuras import ListaPython, ArbolBinarioBusqueda, ArbolBMas
from . import medicion


def _semilla(cfg, n, rep):
    # Misma semilla para el caso aleatorio y el ordenado: son exactamente los
    # mismos IDs, solo cambia el orden en que llegan.
    return cfg.semilla + 7_919 * rep + n


class _EscritorCSV:
    """Escribe filas a medida que se miden (si se corta, no se pierde lo hecho)."""

    def __init__(self, ruta, columnas):
        self._archivo = open(ruta, "w", newline="", encoding="utf-8")
        self._w = csv.DictWriter(self._archivo, fieldnames=columnas)
        self._w.writeheader()

    def fila(self, **valores):
        self._w.writerow(valores)
        self._archivo.flush()

    def cerrar(self):
        self._archivo.close()


def _estructuras(cfg):
    return [(ListaPython, {}), (ArbolBinarioBusqueda, {}), (ArbolBMas, {"orden": cfg.orden_bmas})]


def _avance(texto, inicio):
    print(f"  [{time.perf_counter() - inicio:7.1f} s] {texto}", flush=True)


# ---------------------------------------------------------------------------
# A. Búsqueda (y construcción, listado, altura) vs N
# ---------------------------------------------------------------------------
COLUMNAS_A = ["orden_datos", "estructura", "n", "m", "repeticion", "semilla",
              "us_por_busqueda", "lotes", "segundos_medidos",
              "us_por_insercion", "ms_listado", "altura", "nodos_visitados",
              "ocupacion_hojas_pct"]


def experimento_busqueda_vs_n(cfg, carpeta_datos):
    print("\nExperimento A: búsqueda vs N")
    out = _EscritorCSV(os.path.join(carpeta_datos, "A_busqueda_vs_n.csv"), COLUMNAS_A)
    inicio = time.perf_counter()

    for orden_datos, tamanos in (("aleatorio", cfg.n_aleatorio), ("ordenado", cfg.n_ordenado)):
        for n in tamanos:
            for rep in range(cfg.repeticiones):
                semilla = _semilla(cfg, n, rep)
                rng = nuevo_generador(semilla)
                estudiantes = generar_estudiantes(n, rng, orden_datos)
                busquedas = generar_busquedas(estudiantes, cfg.m_fijo, rng)

                orden_medicion = _estructuras(cfg)
                rng.shuffle(orden_medicion)   # que ninguna estructura vaya siempre de primera
                for clase, kw in orden_medicion:
                    est, us_ins = medicion.construir_y_medir(
                        clase, estudiantes, cfg.ventana_construccion_s, **kw)
                    us_bus, lotes, seg = medicion.medir_busquedas(
                        est, busquedas, cfg.ventana_busqueda_s, cfg.calentamiento)
                    ms_lis = medicion.medir_listado(est, cfg.ventana_listado_s)
                    muestra = busquedas[:200]
                    visitados = sum(est.costo_busqueda(i) for i in muestra) / len(muestra)
                    out.fila(orden_datos=orden_datos, estructura=clase.nombre, n=n,
                             m=cfg.m_fijo, repeticion=rep, semilla=semilla,
                             us_por_busqueda=f"{us_bus:.6f}", lotes=lotes,
                             segundos_medidos=f"{seg:.4f}",
                             us_por_insercion=f"{us_ins:.6f}", ms_listado=f"{ms_lis:.6f}",
                             altura=est.altura() if est.altura() is not None else "",
                             nodos_visitados=f"{visitados:.2f}",
                             ocupacion_hojas_pct=(f"{est.ocupacion_hojas():.2f}"
                                                  if isinstance(est, ArbolBMas) else ""))
            _avance(f"IDs {orden_datos:<9} N = {n:>7,}  listo", inicio)
    out.cerrar()


# ---------------------------------------------------------------------------
# B. Tiempo total vs M (número de búsquedas), N fijo
# ---------------------------------------------------------------------------
COLUMNAS_B = ["estructura", "n", "m", "repeticion", "semilla", "segundos_total", "us_por_busqueda"]


def experimento_busqueda_vs_m(cfg, carpeta_datos):
    print("\nExperimento B: búsqueda vs M")
    out = _EscritorCSV(os.path.join(carpeta_datos, "B_busqueda_vs_m.csv"), COLUMNAS_B)
    inicio = time.perf_counter()
    n = cfg.n_fijo

    for rep in range(cfg.repeticiones):
        semilla = _semilla(cfg, n, rep) + 1
        rng = nuevo_generador(semilla)
        estudiantes = generar_estudiantes(n, rng, "aleatorio")
        estructuras = []
        for clase, kw in _estructuras(cfg):
            e = clase(**kw)
            for est in estudiantes:
                e.insertar(est)
            estructuras.append(e)

        for m in cfg.m_valores:
            busquedas = generar_busquedas(estudiantes, m, rng)
            rng.shuffle(estructuras)
            for e in estructuras:
                seg = medicion.medir_lote_unico(e, busquedas)
                out.fila(estructura=e.nombre, n=n, m=m, repeticion=rep, semilla=semilla,
                         segundos_total=f"{seg:.8f}", us_por_busqueda=f"{seg / m * 1e6:.6f}")
        _avance(f"repetición {rep + 1}/{cfg.repeticiones} lista", inicio)
    out.cerrar()


# ---------------------------------------------------------------------------
# C. Efecto del orden del B+ (hijos por nodo)
# ---------------------------------------------------------------------------
COLUMNAS_C = ["estructura", "orden", "n", "repeticion", "semilla", "us_por_busqueda",
              "us_por_insercion", "altura", "ocupacion_hojas_pct"]


def experimento_orden_bmas(cfg, carpeta_datos):
    print("\nExperimento C: orden del árbol B+")
    out = _EscritorCSV(os.path.join(carpeta_datos, "C_orden_bmas.csv"), COLUMNAS_C)
    inicio = time.perf_counter()
    n = cfg.n_orden_bmas

    for rep in range(cfg.repeticiones):
        semilla = _semilla(cfg, n, rep) + 2
        rng = nuevo_generador(semilla)
        estudiantes = generar_estudiantes(n, rng, "aleatorio")
        busquedas = generar_busquedas(estudiantes, cfg.m_fijo, rng)

        # El ABB se mide en la misma repetición como línea de referencia.
        casos = [(ArbolBinarioBusqueda, {}, "")] + [(ArbolBMas, {"orden": o}, o) for o in cfg.ordenes_bmas]
        rng.shuffle(casos)
        for clase, kw, orden in casos:
            e, us_ins = medicion.construir_y_medir(clase, estudiantes, cfg.ventana_construccion_s, **kw)
            us_bus, _, _ = medicion.medir_busquedas(e, busquedas, cfg.ventana_busqueda_s, cfg.calentamiento)
            out.fila(estructura=clase.nombre, orden=orden, n=n, repeticion=rep, semilla=semilla,
                     us_por_busqueda=f"{us_bus:.6f}", us_por_insercion=f"{us_ins:.6f}",
                     altura=e.altura(),
                     ocupacion_hojas_pct=f"{e.ocupacion_hojas():.2f}" if isinstance(e, ArbolBMas) else "")
        _avance(f"repetición {rep + 1}/{cfg.repeticiones} lista", inicio)
    out.cerrar()
