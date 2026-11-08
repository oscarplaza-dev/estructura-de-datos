"""
analisis.py — Métricas de rendimiento: Quadtree vs fuerza bruta.

Ejecutar (desde la carpeta Lab4):
    python analisis.py                  # experimento completo (gráficas del repositorio)
    python analisis.py --rapido         # prueba de humo, guarda en resultados_rapido/
    python analisis.py --solo-graficas  # regenera tablas y gráficas desde los CSV

Experimentos (todos los parámetros están en config.py):
  A. Tiempo por consulta vs n en un rango PEQUEÑO (1 a 1.024): ubica el cruce.
  B. Tiempo por consulta y de construcción vs n en un rango GRANDE (10^3 a 10^5):
     tendencias y pendientes en log-log; amortización de la construcción.
  C. Capacidad por nodo (1 a 64): construcción, consulta, profundidad y cruce.
  D. Datos uniformes vs agrupados: tiempo, profundidad máxima y puntos devueltos.
  E. Radio variable con n fijo (10.000).
  F. Tres dimensiones (octree).

Salidas:
  resultados/datos/*.csv     mediciones CRUDAS (una fila por medición)
  resultados/tablas/         resumen estadístico (resumen.csv) y RESUMEN.md
  resultados/graficas/       gráficas 04 a 11
  resultados/entorno.txt     hardware, software y parámetros usados

Las gráficas se hacen LEYENDO los CSV: por eso se pueden regenerar sin repetir
el experimento, y el código de las gráficas no puede modificar las mediciones.
"""

import argparse
import csv
import math
import os
import random
import sys
from collections import defaultdict
from time import perf_counter

import config
import datos
import medicion
from Quadtreetree import (Quadtree, fuerza_bruta_radio, fuerza_bruta_vecino)

CAMPOS = ["experimento", "distribucion", "k", "n", "capacidad", "radio", "rep", "metrica", "valor"]
METODOS = ("arbol_radio", "fb_radio", "arbol_vecino", "fb_vecino")
NOMBRES = {"arbol_radio": "Quadtree", "fb_radio": "Fuerza bruta",
           "arbol_vecino": "Quadtree", "fb_vecino": "Fuerza bruta"}


# ---------------------------------------------------------------------------
# Utilidades de medición
# ---------------------------------------------------------------------------

def num_consultas(n, perfil):
    """Consultas por bloque: 200, pero menos si n es grande (la fuerza bruta tarda n por consulta)."""
    return max(10, min(perfil["consultas_max"], perfil["presupuesto_fb"] // max(n, 1)))


def funciones(arbol, puntos, radio):
    """Las cuatro formas de responder, con la misma firma f(consulta)."""
    return {
        "arbol_radio": lambda c: arbol.buscar_radio(c, radio),
        "fb_radio": lambda c: fuerza_bruta_radio(puntos, c, radio),
        "arbol_vecino": lambda c: arbol.vecino_mas_cercano(c),
        "fb_vecino": lambda c: fuerza_bruta_vecino(puntos, c),
    }


def hojas_tocadas(arbol, consulta, radio2):
    """Instrumentación (NO es parte del árbol): recorre el árbol con la misma poda que
    buscar_radio y devuelve cuántos puntos se miden (puntos de las hojas revisadas)."""
    medidos, pila = 0, [arbol.raiz]
    while pila:
        nodo = pila.pop()
        if nodo.caja.distancia2_minima(consulta) > radio2:
            continue
        if nodo.es_hoja():
            medidos += len(nodo.puntos)
        else:
            pila.extend(nodo.hijos.values())
    return medidos


def fila(experimento, n, rep, metrica, valor, distribucion="uniforme", k=2,
         capacidad=config.CAPACIDAD, radio=config.RADIO):
    return {"experimento": experimento, "distribucion": distribucion, "k": k, "n": n,
            "capacidad": capacidad, "radio": radio, "rep": rep, "metrica": metrica, "valor": valor}


def progreso(texto):
    print(f"  {texto}", flush=True)


# ---------------------------------------------------------------------------
# Experimentos
# ---------------------------------------------------------------------------

def experimento_n(nombre, ns, ventana, perfil, capacidad=config.CAPACIDAD,
                  metodos=METODOS, k=2):
    """A, B, C2 y F: para cada n y repetición, construye y mide las consultas."""
    filas = []
    for n in ns:
        for rep in range(perfil["repeticiones"]):
            semilla = config.SEMILLA + 1_000 * rep + n
            puntos = datos.uniformes(n, k=k, semilla=semilla)
            consultas = datos.consultas(num_consultas(n, perfil), k=k, semilla=semilla + 1)
            t_constr, arbol = medicion.segundos_construccion(
                lambda: Quadtree(datos.caja_mapa(k), capacidad, puntos), ventana)
            base = dict(k=k, capacidad=capacidad)
            filas.append(fila(nombre, n, rep, "construir", t_constr, **base))
            filas.append(fila(nombre, n, rep, "profundidad", arbol.profundidad_maxima(), **base))
            f = funciones(arbol, puntos, config.RADIO)
            orden = list(metodos)
            random.Random(semilla).shuffle(orden)        # el orden de medición se baraja
            for metodo in orden:
                t = medicion.segundos_por_consulta(f[metodo], consultas, ventana)
                filas.append(fila(nombre, n, rep, metodo, t, **base))
        extra = f" (capacidad {capacidad})" if nombre == "C2" else ""
        progreso(f"{nombre}{extra}: n = {n:>7,} listo".replace(",", "."))
    return filas


def experimento_capacidad(perfil):
    """C: n fijo (10.000), capacidad variable."""
    filas = []
    for capacidad in perfil["capacidades"]:
        for rep in range(perfil["repeticiones"]):
            semilla = config.SEMILLA + 1_000 * rep          # mismos datos para todas las capacidades
            puntos = datos.uniformes(config.N, semilla=semilla)
            consultas = datos.consultas(num_consultas(config.N, perfil), semilla=semilla + 1)
            t_constr, arbol = medicion.segundos_construccion(
                lambda: Quadtree(datos.caja_mapa(), capacidad, puntos), perfil["ventana_s"])
            hojas = sum(1 for _ in _hojas(arbol.raiz))
            for metrica, valor in (("construir", t_constr), ("profundidad", arbol.profundidad_maxima()),
                                   ("hojas", hojas)):
                filas.append(fila("C", config.N, rep, metrica, valor, capacidad=capacidad))
            f = funciones(arbol, puntos, config.RADIO)
            orden = ["arbol_radio", "arbol_vecino"]
            random.Random(semilla + capacidad).shuffle(orden)
            for metodo in orden:
                t = medicion.segundos_por_consulta(f[metodo], consultas, perfil["ventana_s"])
                filas.append(fila("C", config.N, rep, metodo, t, capacidad=capacidad))
        progreso(f"C: capacidad = {capacidad} lista")
    return filas


def _hojas(nodo):
    pila = [nodo]
    while pila:
        actual = pila.pop()
        if actual.es_hoja():
            yield actual
        else:
            pila.extend(actual.hijos.values())


def experimento_distribucion(perfil):
    """D: uniforme vs agrupado. Las consultas siguen la MISMA distribución que los datos
    (los clientes piden entregas donde vive la gente)."""
    filas = []
    generadores = {"uniforme": datos.uniformes, "agrupado": datos.agrupados}
    radio2 = config.RADIO ** 2
    for distribucion, generar in generadores.items():
        for n in perfil["n_distribucion"]:
            for rep in range(perfil["repeticiones"]):
                semilla = config.SEMILLA + 1_000 * rep + n
                m = num_consultas(n, perfil)
                todos = generar(n + m, semilla=semilla)
                puntos, consultas = todos[:n], todos[n:]
                t_constr, arbol = medicion.segundos_construccion(
                    lambda: Quadtree(datos.caja_mapa(), config.CAPACIDAD, puntos), perfil["ventana_s"])
                devueltos = sum(len(arbol.buscar_radio(c, config.RADIO)) for c in consultas) / m
                medidos = sum(hojas_tocadas(arbol, c, radio2) for c in consultas) / m
                base = dict(distribucion=distribucion)
                for metrica, valor in (("construir", t_constr), ("profundidad", arbol.profundidad_maxima()),
                                       ("devueltos", devueltos), ("medidos", medidos)):
                    filas.append(fila("D", n, rep, metrica, valor, **base))
                f = funciones(arbol, puntos, config.RADIO)
                orden = ["arbol_radio", "arbol_vecino"]
                random.Random(semilla).shuffle(orden)
                for metodo in orden:
                    t = medicion.segundos_por_consulta(f[metodo], consultas, perfil["ventana_s"])
                    filas.append(fila("D", n, rep, metodo, t, **base))
            progreso(f"D: {distribucion}, n = {n:>7,} listo".replace(",", "."))
    return filas


def experimento_radio(perfil):
    """E: n fijo (10.000), radio variable."""
    filas = []
    for rep in range(perfil["repeticiones"]):
        semilla = config.SEMILLA + 1_000 * rep
        puntos = datos.uniformes(config.N, semilla=semilla)
        consultas = datos.consultas(num_consultas(config.N, perfil), semilla=semilla + 1)
        arbol = Quadtree(datos.caja_mapa(), config.CAPACIDAD, puntos)
        for radio in perfil["radios"]:
            devueltos = sum(len(arbol.buscar_radio(c, radio)) for c in consultas) / len(consultas)
            filas.append(fila("E", config.N, rep, "devueltos", devueltos, radio=radio))
            f = funciones(arbol, puntos, radio)
            orden = ["arbol_radio", "fb_radio"]
            random.Random(semilla + radio).shuffle(orden)
            for metodo in orden:
                t = medicion.segundos_por_consulta(f[metodo], consultas, perfil["ventana_s"])
                filas.append(fila("E", config.N, rep, metodo, t, radio=radio))
        progreso(f"E: repetición {rep + 1} lista")
    return filas


# ---------------------------------------------------------------------------
# CSV y resumen estadístico
# ---------------------------------------------------------------------------

def guardar_csv(ruta, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=CAMPOS)
        escritor.writeheader()
        escritor.writerows(filas)


def leer_csv(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    for f in filas:
        for campo in ("k", "n", "capacidad", "radio", "rep"):
            f[campo] = int(f[campo])
        f["valor"] = float(f["valor"])
    return filas


def resumir(filas):
    """Agrupa las repeticiones: clave -> {media, desv, cv, ic95, ...}."""
    grupos = defaultdict(list)
    for f in filas:
        clave = (f["experimento"], f["distribucion"], f["k"], f["n"], f["capacidad"], f["radio"], f["metrica"])
        grupos[clave].append(f["valor"])
    return {clave: medicion.resumen(valores) for clave, valores in grupos.items()}


def serie(res, experimento, metrica, x="n", distribucion="uniforme", k=2,
          capacidad=config.CAPACIDAD, radio=config.RADIO, n=None):
    """Extrae (xs, medias, desvs) de un experimento, ordenado por x."""
    puntos = []
    for (e, d, kk, nn, cap, r, m), s in res.items():
        if e != experimento or m != metrica or d != distribucion or kk != k:
            continue
        if x != "capacidad" and cap != capacidad:
            continue
        if x != "radio" and r != radio:
            continue
        if n is not None and nn != n:
            continue
        valor_x = {"n": nn, "capacidad": cap, "radio": r}[x]
        puntos.append((valor_x, s["media"], s["desv"]))
    puntos.sort()
    return [p[0] for p in puntos], [p[1] for p in puntos], [p[2] for p in puntos]


def cruce(ns, arbol, bruta):
    """Menor n desde el cual el árbol es más rápido en TODOS los n medidos de ahí en adelante."""
    n_cruce = None
    for n, a, b in zip(ns, arbol, bruta):
        if a < b:
            if n_cruce is None:
                n_cruce = n
        else:
            n_cruce = None
    return n_cruce


# ---------------------------------------------------------------------------
# Gráficas (solo LEEN el resumen)
# ---------------------------------------------------------------------------

AZUL, NARANJA, AGUAMARINA = "#2a78d6", "#eb6834", "#1baf7a"
TINTA, GRIS, GRIS_CLARO, REJILLA = "#0b0b0b", "#898781", "#c3c2b7", "#e1e0d9"
COLOR = {"arbol_radio": AZUL, "arbol_vecino": AZUL, "fb_radio": NARANJA, "fb_vecino": NARANJA}
RAMPA_CAP = {1: "#9ec5f4", 4: "#3987e5", 16: "#184f95", 64: "#0d366b"}


def estilo(ax, titulo, xlabel, ylabel, log_x=False, log_y=False):
    ax.set_title(titulo, fontsize=10, color=TINTA, loc="left")
    ax.set_xlabel(xlabel, color=GRIS)
    ax.set_ylabel(ylabel, color=GRIS)
    if log_x:
        ax.set_xscale("log")
    if log_y:
        ax.set_yscale("log")
    ax.grid(True, which="major", color=REJILLA, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(colors=GRIS, labelsize=8)
    for lado in ax.spines.values():
        lado.set_color(GRIS_CLARO)


def linea(ax, xs, ys, es, color, etiqueta, escala=1.0, estilo_linea="-", marcador="o"):
    ys = [y * escala for y in ys]
    es = [e * escala for e in es]
    ax.errorbar(xs, ys, yerr=es, color=color, linestyle=estilo_linea, marker=marcador,
                markersize=4.5, linewidth=1.6, capsize=2, label=etiqueta)


def graficar(res, carpeta, perfil):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(carpeta, exist_ok=True)
    ruta = lambda nombre: os.path.join(carpeta, nombre)
    reps = perfil["repeticiones"]
    nota = f"media de {reps} repeticiones ± 1 desviación estándar"
    US, MS = 1e6, 1e3

    # ---- 04. Construcción vs n -------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), constrained_layout=True)
    xa, ya, ea = serie(res, "A", "construir")
    xb, yb, eb = serie(res, "B", "construir")
    linea(ax1, xa, ya, ea, AZUL, "rango pequeño (A)", MS, marcador="s")
    linea(ax1, xb, yb, eb, AZUL, "rango grande (B)", MS)
    a, b, r2 = medicion.ajuste_potencia(xb, yb)
    ax1.plot(xb, [a * x ** b * MS for x in xb], color=TINTA, linestyle=":", linewidth=1.2,
             label=f"ajuste en B: t ∝ n^{b:.2f} (R² = {r2:.3f})")
    estilo(ax1, "Construcción del Quadtree (ejes log-log)", "n (puntos)", "tiempo de construcción (ms)",
           True, True)
    ax1.legend(fontsize=8)
    xs = xa + xb
    por_punto = [y / x * US for x, y in zip(xs, ya + yb)]
    ax2.plot(xs, por_punto, color=AZUL, marker="o", markersize=4.5, linewidth=1.6)
    estilo(ax2, "Costo promedio de insertar UN punto (eje x log)", "n (puntos)",
           "tiempo por punto insertado (µs)", log_x=True)
    fig.suptitle(f"Gráfica 4 · Construcción vs n · datos uniformes, capacidad {config.CAPACIDAD} · {nota}",
                 fontsize=11, color=TINTA)
    fig.savefig(ruta("04_construccion_vs_n.png"), dpi=150)
    plt.close(fig)

    # ---- 05. Consulta vs n, dos rangos, cruce marcado ---------------------
    fig, ejes = plt.subplots(2, 2, figsize=(13, 9.5), constrained_layout=True)
    for fila_ax, (arb, fb, nombre) in zip(ejes, (("arbol_radio", "fb_radio", "Búsqueda por radio (500 m)"),
                                                 ("arbol_vecino", "fb_vecino", "Vecino más cercano"))):
        for ax, exp, rango in zip(fila_ax, ("A", "B"), ("rango pequeño", "rango grande")):
            xs, ya, ea = serie(res, exp, arb)
            _, yb, eb = serie(res, exp, fb)
            if exp == "B":
                _, pa, ra = medicion.ajuste_potencia(xs, ya)
                _, pb, rb = medicion.ajuste_potencia(xs, yb)
                linea(ax, xs, ya, ea, AZUL, f"Quadtree (pendiente {pa:.2f})", US)
                linea(ax, xs, yb, eb, NARANJA, f"Fuerza bruta (pendiente {pb:.2f})", US)
            else:
                linea(ax, xs, ya, ea, AZUL, "Quadtree", US)
                linea(ax, xs, yb, eb, NARANJA, "Fuerza bruta", US)
                nc = cruce(xs, ya, yb)
                if nc is not None:
                    ax.axvline(nc, color=GRIS, linestyle="--", linewidth=1)
                    ax.annotate(f"cruce: n = {nc}", (nc, ax.get_ylim()[1]), xytext=(4, -14),
                                textcoords="offset points", fontsize=8, color=TINTA)
            estilo(ax, f"{nombre} · {rango}", "n (puntos)", "tiempo por consulta (µs)", True, True)
            ax.legend(fontsize=8, loc="upper left")
    fig.suptitle(f"Gráfica 5 · Tiempo por consulta vs n (ejes log-log) · {nota}", fontsize=11, color=TINTA)
    fig.savefig(ruta("05_consulta_vs_n_cruce.png"), dpi=150)
    plt.close(fig)

    # ---- 06. La misma información en escala LINEAL (rango grande) --------
    fig, ejes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for ax, (arb, fb, nombre) in zip(ejes, (("arbol_radio", "fb_radio", "Búsqueda por radio (500 m)"),
                                            ("arbol_vecino", "fb_vecino", "Vecino más cercano"))):
        xs, ya, ea = serie(res, "B", arb)
        _, yb, eb = serie(res, "B", fb)
        linea(ax, xs, ya, ea, AZUL, "Quadtree", MS)
        linea(ax, xs, yb, eb, NARANJA, "Fuerza bruta", MS)
        estilo(ax, f"{nombre} · ejes lineales", "n (puntos)", "tiempo por consulta (ms)")
        ax.legend(fontsize=8, loc="upper left")
    fig.suptitle("Gráfica 6 · Mismos datos que la gráfica 5 (rango grande) en escala lineal: "
                 "la curva del Quadtree casi no se separa del cero", fontsize=11, color=TINTA)
    fig.savefig(ruta("06_consulta_vs_n_lineal.png"), dpi=150)
    plt.close(fig)

    # ---- 07. Capacidad por nodo ------------------------------------------
    fig, ejes = plt.subplots(2, 2, figsize=(13, 9.5), constrained_layout=True)
    caps, yc, ec = serie(res, "C", "construir", x="capacidad", n=config.N)
    linea(ejes[0][0], caps, yc, ec, AZUL, "construcción", MS)
    estilo(ejes[0][0], f"Construcción con n = {config.N:,}".replace(",", "."), "capacidad por nodo",
           "tiempo de construcción (ms)", log_x=True)
    for metodo, color, etiqueta, marcador in (("arbol_radio", AZUL, "radio 500 m", "o"),
                                              ("arbol_vecino", AGUAMARINA, "vecino más cercano", "s")):
        _, y, e = serie(res, "C", metodo, x="capacidad", n=config.N)
        linea(ejes[0][1], caps, y, e, color, etiqueta, US, marcador=marcador)
    estilo(ejes[0][1], f"Consulta en el Quadtree con n = {config.N:,}".replace(",", "."),
           "capacidad por nodo", "tiempo por consulta (µs)", log_x=True)
    ejes[0][1].legend(fontsize=8)
    _, yp, _ = serie(res, "C", "profundidad", x="capacidad", n=config.N)
    _, yh, _ = serie(res, "C", "hojas", x="capacidad", n=config.N)
    ejes[1][0].plot(caps, yp, color=AZUL, marker="o", linewidth=1.6, label="profundidad máxima")
    estilo(ejes[1][0], "Profundidad máxima y número de hojas", "capacidad por nodo",
           "profundidad máxima (niveles)", log_x=True)
    for c, p, h in zip(caps, yp, yh):
        ejes[1][0].annotate(f"{h:,.0f} hojas".replace(",", "."), (c, p), xytext=(4, 6),
                            textcoords="offset points", fontsize=7, color=GRIS)
    ax = ejes[1][1]
    xs_fb, fb_r, _ = serie(res, "A", "fb_radio")
    _, fb_v, _ = serie(res, "A", "fb_vecino")
    cruces = {}
    for cap in perfil["capacidades_cruce"]:
        xs, ar, _ = serie(res, "C2", "arbol_radio", capacidad=cap)
        _, av, _ = serie(res, "C2", "arbol_vecino", capacidad=cap)
        cruces[cap] = (cruce(xs, ar, fb_r), cruce(xs, av, fb_v))
        ax.plot(xs, [y * US for y in av], color=RAMPA_CAP.get(cap, AZUL), marker="o", markersize=4,
                linewidth=1.4, label=f"Quadtree, capacidad {cap}")
    ax.plot(xs_fb, [y * US for y in fb_v], color=NARANJA, marker="o", markersize=4, linewidth=1.8,
            label="Fuerza bruta")
    texto = "\n".join(f"cap. {c}: cruce radio n = {r}, vecino n = {v}" for c, (r, v) in cruces.items())
    ax.text(0.98, 0.04, texto, transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5, color=TINTA,
            bbox=dict(facecolor="white", edgecolor=GRIS_CLARO, boxstyle="round,pad=0.4"))
    estilo(ax, "Vecino más cercano: el cruce se mueve con la capacidad (ejes log-log)", "n (puntos)",
           "tiempo por consulta (µs)", True, True)
    ax.legend(fontsize=8, loc="upper left")
    fig.suptitle(f"Gráfica 7 · Efecto de la capacidad por nodo · datos uniformes · {nota}",
                 fontsize=11, color=TINTA)
    fig.savefig(ruta("07_capacidad.png"), dpi=150)
    plt.close(fig)

    # ---- 08. Uniforme vs agrupado ----------------------------------------
    fig, ejes = plt.subplots(2, 2, figsize=(13, 9.5), constrained_layout=True)
    colores_d = {"uniforme": AZUL, "agrupado": AGUAMARINA}
    for ax, metodo, titulo in ((ejes[0][0], "arbol_radio", "Quadtree · búsqueda por radio (500 m)"),
                               (ejes[0][1], "arbol_vecino", "Quadtree · vecino más cercano")):
        for d, color in colores_d.items():
            xs, y, e = serie(res, "D", metodo, distribucion=d)
            linea(ax, xs, y, e, color, d, US)
        estilo(ax, titulo, "n (puntos)", "tiempo por consulta (µs)", True, True)
        ax.legend(fontsize=8, loc="upper left")
    for d, color in colores_d.items():
        xs, y, e = serie(res, "D", "profundidad", distribucion=d)
        linea(ejes[1][0], xs, y, e, color, d)
    estilo(ejes[1][0], "Profundidad máxima del árbol", "n (puntos)", "profundidad máxima (niveles)", log_x=True)
    ejes[1][0].legend(fontsize=8, loc="upper left")
    for d, color in colores_d.items():
        xs, y, e = serie(res, "D", "devueltos", distribucion=d)
        linea(ejes[1][1], xs, y, e, color, f"{d}: puntos devueltos")
        xs, y, e = serie(res, "D", "medidos", distribucion=d)
        linea(ejes[1][1], xs, y, e, color, f"{d}: puntos medidos", estilo_linea="--", marcador="s")
    estilo(ejes[1][1], "Puntos por consulta de radio 500 m", "n (puntos)", "puntos por consulta", True, True)
    ejes[1][1].legend(fontsize=8, loc="upper left")
    fig.suptitle(f"Gráfica 8 · Uniforme vs agrupado (consultas con la misma distribución que los datos) · {nota}",
                 fontsize=11, color=TINTA)
    fig.savefig(ruta("08_uniforme_vs_agrupado.png"), dpi=150)
    plt.close(fig)

    # ---- 09. Tiempo vs radio, n fijo --------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), constrained_layout=True)
    xs, ya, ea = serie(res, "E", "arbol_radio", x="radio", n=config.N)
    _, yb, eb = serie(res, "E", "fb_radio", x="radio", n=config.N)
    linea(ax1, xs, ya, ea, AZUL, "Quadtree", US)
    linea(ax1, xs, yb, eb, NARANJA, "Fuerza bruta", US)
    estilo(ax1, f"Tiempo por consulta vs radio, n = {config.N:,}".replace(",", "."), "radio (m)",
           "tiempo por consulta (µs)", True, True)
    ax1.legend(fontsize=8, loc="upper left")
    _, yd, ed = serie(res, "E", "devueltos", x="radio", n=config.N)
    linea(ax2, xs, yd, ed, AZUL, "medido")
    teorico = [config.N * math.pi * r * r / config.LADO ** 2 for r in xs]
    ax2.plot(xs, teorico, color=GRIS, linestyle=":", linewidth=1.4, label="n·πr²/área (sin efecto de bordes)")
    estilo(ax2, "Puntos devueltos por consulta vs radio", "radio (m)", "puntos devueltos", True, True)
    ax2.legend(fontsize=8, loc="upper left")
    fig.suptitle(f"Gráfica 9 · Radio variable con n fijo (ejes log-log) · {nota}", fontsize=11, color=TINTA)
    fig.savefig(ruta("09_tiempo_vs_radio.png"), dpi=150)
    plt.close(fig)

    # ---- 10. Tres dimensiones ---------------------------------------------
    fig, ejes = plt.subplots(1, 2, figsize=(13, 5.2), constrained_layout=True)
    for ax, (arb, fb, nombre) in zip(ejes, (("arbol_radio", "fb_radio", "Búsqueda por radio (500 m)"),
                                            ("arbol_vecino", "fb_vecino", "Vecino más cercano"))):
        xs, ya, ea = serie(res, "F", arb, k=3)
        _, yb, eb = serie(res, "F", fb, k=3)
        linea(ax, xs, ya, ea, AZUL, "Octree (3D)", US)
        linea(ax, xs, yb, eb, NARANJA, "Fuerza bruta (3D)", US)
        x2, y2, e2 = serie(res, "B", arb)
        linea(ax, x2, y2, e2, GRIS, "Quadtree (2D), referencia", US, estilo_linea="--", marcador="s")
        estilo(ax, f"{nombre} · 3D", "n (puntos)", "tiempo por consulta (µs)", True, True)
        ax.legend(fontsize=8, loc="upper left")
    fig.suptitle(f"Gráfica 10 · Tres dimensiones (cubo de 10 km de lado, 8 hijos por nodo) · {nota}",
                 fontsize=11, color=TINTA)
    fig.savefig(ruta("10_tres_dimensiones.png"), dpi=150)
    plt.close(fig)

    # ---- 11. Amortización de la construcción -------------------------------
    fig, ax = plt.subplots(figsize=(7.5, 5.2), constrained_layout=True)
    for arb, fb, color, etiqueta, marcador in (("arbol_radio", "fb_radio", AZUL, "radio 500 m", "o"),
                                               ("arbol_vecino", "fb_vecino", AGUAMARINA, "vecino más cercano", "s")):
        filas_am = amortizacion(res, arb, fb)
        ax.plot([f[0] for f in filas_am], [f[1] for f in filas_am], color=color, marker=marcador,
                linewidth=1.6, label=etiqueta)
    estilo(ax, "Consultas necesarias para pagar la construcción\n= construir ÷ (t fuerza bruta − t Quadtree)",
           "n (puntos)", "consultas", log_x=True)
    ax.set_ylim(bottom=0)
    ax.legend(fontsize=8)
    fig.suptitle("Gráfica 11 · Amortización (rango grande, eje x log)", fontsize=11, color=TINTA)
    fig.savefig(ruta("11_amortizacion.png"), dpi=150)
    plt.close(fig)


def amortizacion(res, arb, fb, experimento="B"):
    xs, construir, _ = serie(res, experimento, "construir")
    _, ta, _ = serie(res, experimento, arb)
    _, tb, _ = serie(res, experimento, fb)
    filas = []
    for n, c, a, b in zip(xs, construir, ta, tb):
        if b > a:
            filas.append((n, c / (b - a), c, a, b))
    return filas


# ---------------------------------------------------------------------------
# Tablas y discusión
# ---------------------------------------------------------------------------

def num(valor, decimales=2):
    """Número en formato español: punto de miles y coma decimal (12.345,67)."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def tablas(res, carpeta, perfil):
    os.makedirs(carpeta, exist_ok=True)
    with open(os.path.join(carpeta, "resumen.csv"), "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["experimento", "distribucion", "k", "n", "capacidad", "radio", "metrica",
                           "media", "desv", "cv_%", "ic95", "min", "max", "reps"])
        for clave in sorted(res):
            s = res[clave]
            escritor.writerow(list(clave) + [f"{s['media']:.6g}", f"{s['desv']:.3g}", f"{s['cv']:.1f}",
                                             f"{s['ic95']:.3g}", f"{s['min']:.6g}", f"{s['max']:.6g}", s["reps"]])

    L = []
    us = lambda v: num(v * 1e6, 2)
    ms = lambda v: num(v * 1e3, 2)
    L.append(f"# Resumen de resultados (perfil: {perfil['nombre']}, {perfil['repeticiones']} repeticiones)\n")

    L.append("## 1. ¿Desde qué n el Quadtree es más rápido que la fuerza bruta? (solo consulta)\n")
    xs, ar, _ = serie(res, "A", "arbol_radio")
    _, br, _ = serie(res, "A", "fb_radio")
    _, av, _ = serie(res, "A", "arbol_vecino")
    _, bv, _ = serie(res, "A", "fb_vecino")
    L.append(f"- Radio 500 m: desde **n = {cruce(xs, ar, br)}**")
    L.append(f"- Vecino más cercano: desde **n = {cruce(xs, av, bv)}**\n")
    L.append("| n | Quadtree radio (µs) | FB radio (µs) | Quadtree vecino (µs) | FB vecino (µs) |")
    L.append("|---:|---:|---:|---:|---:|")
    for i, n in enumerate(xs):
        L.append(f"| {n} | {us(ar[i])} | {us(br[i])} | {us(av[i])} | {us(bv[i])} |")

    L.append("\n## 2. Rango grande: tiempos y pendientes (t ≈ a·n^b)\n")
    xs, constr, _ = serie(res, "B", "construir")
    L.append("| n | construir (ms) | Quadtree radio (µs) | FB radio (µs) | Quadtree vecino (µs) | FB vecino (µs) |")
    L.append("|---:|---:|---:|---:|---:|---:|")
    series_b = {m: serie(res, "B", m)[1] for m in METODOS}
    for i, n in enumerate(xs):
        L.append(f"| {num(n, 0)} | {ms(constr[i])} | {us(series_b['arbol_radio'][i])} | {us(series_b['fb_radio'][i])} | "
                 f"{us(series_b['arbol_vecino'][i])} | {us(series_b['fb_vecino'][i])} |")
    L.append("\n| Medida | pendiente b | R² |")
    L.append("|---|---:|---:|")
    for etiqueta, ys in (("construir", constr), ("Quadtree radio", series_b["arbol_radio"]),
                         ("FB radio", series_b["fb_radio"]), ("Quadtree vecino", series_b["arbol_vecino"]),
                         ("FB vecino", series_b["fb_vecino"])):
        _, b, r2 = medicion.ajuste_potencia(xs, ys)
        L.append(f"| {etiqueta} | {num(b, 3)} | {num(r2, 4)} |")
    if config.N in xs:
        i = xs.index(config.N)
        L.append(f"\nCon n = {num(config.N, 0)} el Quadtree es **{num(series_b['fb_radio'][i] / series_b['arbol_radio'][i], 0)}×** "
                 f"más rápido en radio y **{num(series_b['fb_vecino'][i] / series_b['arbol_vecino'][i], 0)}×** en vecino."
                 )

    L.append("\n## 3. Construcción + consulta: ¿cuántas consultas pagan la construcción?\n")
    L.append("| n | construir (ms) | consultas para amortizar (radio) | consultas para amortizar (vecino) |")
    L.append("|---:|---:|---:|---:|")
    am_r = {f[0]: f[1] for f in amortizacion(res, "arbol_radio", "fb_radio")}
    am_v = {f[0]: f[1] for f in amortizacion(res, "arbol_vecino", "fb_vecino")}
    for i, n in enumerate(xs):
        L.append(f"| {num(n, 0)} | {ms(constr[i])} | {num(am_r[n], 1) if n in am_r else 'nunca'} | {num(am_v[n], 1) if n in am_v else 'nunca'} |"
                 )
    xs_a, ca, _ = serie(res, "A", "construir")
    L.append("\nRango pequeño (construcción + Q consultas vs Q consultas de fuerza bruta):\n")
    L.append("| n | construir (µs) | consultas para amortizar (radio) | consultas para amortizar (vecino) |")
    L.append("|---:|---:|---:|---:|")
    am_ra = {f[0]: f[1] for f in amortizacion(res, "arbol_radio", "fb_radio", "A")}
    am_va = {f[0]: f[1] for f in amortizacion(res, "arbol_vecino", "fb_vecino", "A")}
    for i, n in enumerate(xs_a):
        r = num(am_ra[n], 1) if n in am_ra else "nunca"
        v = num(am_va[n], 1) if n in am_va else "nunca"
        L.append(f"| {n} | {us(ca[i])} | {r} | {v} |")

    L.append(f"\n## 4. Capacidad por nodo (n = {num(config.N, 0)})\n")
    caps, cc, _ = serie(res, "C", "construir", x="capacidad", n=config.N)
    _, cr, _ = serie(res, "C", "arbol_radio", x="capacidad", n=config.N)
    _, cv, _ = serie(res, "C", "arbol_vecino", x="capacidad", n=config.N)
    _, cp, _ = serie(res, "C", "profundidad", x="capacidad", n=config.N)
    _, ch, _ = serie(res, "C", "hojas", x="capacidad", n=config.N)
    L.append("| capacidad | construir (ms) | radio (µs) | vecino (µs) | profundidad máx. | hojas |")
    L.append("|---:|---:|---:|---:|---:|---:|")
    for i, c in enumerate(caps):
        L.append(f"| {c} | {ms(cc[i])} | {us(cr[i])} | {us(cv[i])} | {num(cp[i], 1)} | {num(ch[i], 0)} |")
    L.append("\nCruce según la capacidad (solo consulta):\n")
    L.append("| capacidad | cruce radio | cruce vecino |")
    L.append("|---:|---:|---:|")
    xs_fb, fb_r, _ = serie(res, "A", "fb_radio")
    _, fb_v, _ = serie(res, "A", "fb_vecino")
    for cap in perfil["capacidades_cruce"]:
        x2, a2, _ = serie(res, "C2", "arbol_radio", capacidad=cap)
        _, v2, _ = serie(res, "C2", "arbol_vecino", capacidad=cap)
        L.append(f"| {cap} | n = {cruce(x2, a2, fb_r)} | n = {cruce(x2, v2, fb_v)} |")

    L.append("\n## 5. Uniforme vs agrupado (radio 500 m)\n")
    L.append("| distribución | n | profundidad máx. | puntos devueltos | puntos medidos | radio (µs) | vecino (µs) |")
    L.append("|---|---:|---:|---:|---:|---:|---:|")
    for d in ("uniforme", "agrupado"):
        xs_d, p, _ = serie(res, "D", "profundidad", distribucion=d)
        _, dv, _ = serie(res, "D", "devueltos", distribucion=d)
        _, md, _ = serie(res, "D", "medidos", distribucion=d)
        _, tr, _ = serie(res, "D", "arbol_radio", distribucion=d)
        _, tv, _ = serie(res, "D", "arbol_vecino", distribucion=d)
        for i, n in enumerate(xs_d):
            L.append(f"| {d} | {num(n, 0)} | {num(p[i], 1)} | {num(dv[i], 1)} | {num(md[i], 1)} | {us(tr[i])} | {us(tv[i])} |"
                     )

    L.append(f"\n## 6. Radio variable (n = {num(config.N, 0)})\n")
    rs, ra, _ = serie(res, "E", "arbol_radio", x="radio", n=config.N)
    _, rb, _ = serie(res, "E", "fb_radio", x="radio", n=config.N)
    _, rd, _ = serie(res, "E", "devueltos", x="radio", n=config.N)
    L.append("| radio (m) | puntos devueltos | Quadtree (µs) | FB (µs) | FB ÷ Quadtree |")
    L.append("|---:|---:|---:|---:|---:|")
    for i, r in enumerate(rs):
        L.append(f"| {num(r, 0)} | {num(rd[i], 1)} | {us(ra[i])} | {us(rb[i])} | {num(rb[i] / ra[i], 1)}× |")

    L.append("\n## 7. Tres dimensiones\n")
    xs3, a3, _ = serie(res, "F", "arbol_radio", k=3)
    _, b3, _ = serie(res, "F", "fb_radio", k=3)
    _, v3, _ = serie(res, "F", "arbol_vecino", k=3)
    _, w3, _ = serie(res, "F", "fb_vecino", k=3)
    L.append("| n | Octree radio (µs) | FB radio (µs) | Octree vecino (µs) | FB vecino (µs) |")
    L.append("|---:|---:|---:|---:|---:|")
    for i, n in enumerate(xs3):
        L.append(f"| {num(n, 0)} | {us(a3[i])} | {us(b3[i])} | {us(v3[i])} | {us(w3[i])} |")

    cvs = [s["cv"] for (e, *_r, m), s in res.items() if m in METODOS and s["reps"] > 1]
    if cvs:
        cvs.sort()
        L.append(f"\n## 8. Ruido de las mediciones\n\nCV de los tiempos de consulta: mediana "
                 f"{num(cvs[len(cvs) // 2], 1)} %, máximo {num(cvs[-1], 1)} % ({len(cvs)} grupos).")

    texto = "\n".join(L) + "\n"
    with open(os.path.join(carpeta, "RESUMEN.md"), "w", encoding="utf-8") as archivo:
        archivo.write(texto)
    return texto


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

ARCHIVOS = {"A": "A_cruce.csv", "B": "B_tendencia.csv", "C": "C_capacidad.csv",
            "C2": "C2_cruce_capacidad.csv", "D": "D_distribucion.csv", "E": "E_radio.csv", "F": "F_3d.csv"}


def main():
    parser = argparse.ArgumentParser(description="Quadtree vs fuerza bruta: experimentos de rendimiento")
    parser.add_argument("--rapido", action="store_true", help="prueba de humo (~1-2 min)")
    parser.add_argument("--solo-graficas", action="store_true", help="regenera tablas y gráficas desde los CSV")
    args = parser.parse_args()

    perfil = config.RAPIDO if args.rapido else config.COMPLETO
    base = "resultados_rapido" if args.rapido else "resultados"
    carpeta_datos = os.path.join(base, "datos")
    os.makedirs(carpeta_datos, exist_ok=True)

    if not args.solo_graficas:
        inicio = perf_counter()
        print(f"Perfil: {perfil['nombre']} · {perfil['repeticiones']} repeticiones")
        trabajos = {
            "A": lambda: experimento_n("A", perfil["n_cruce"], perfil["ventana_corta_s"], perfil),
            "B": lambda: experimento_n("B", perfil["n_tendencia"], perfil["ventana_s"], perfil),
            "C": lambda: experimento_capacidad(perfil),
            "C2": lambda: [f for cap in perfil["capacidades_cruce"]
                           for f in experimento_n("C2", perfil["n_cruce"], perfil["ventana_corta_s"], perfil,
                                                  capacidad=cap, metodos=("arbol_radio", "arbol_vecino"))],
            "D": lambda: experimento_distribucion(perfil),
            "E": lambda: experimento_radio(perfil),
            "F": lambda: experimento_n("F", perfil["n_3d"], perfil["ventana_s"], perfil, k=3),
        }
        for clave, trabajo in trabajos.items():
            print(f"Experimento {clave}...", flush=True)
            guardar_csv(os.path.join(carpeta_datos, ARCHIVOS[clave]), trabajo())
        minutos = (perf_counter() - inicio) / 60
        with open(os.path.join(base, "entorno.txt"), "w", encoding="utf-8") as archivo:
            archivo.write(medicion.describir_entorno())
            archivo.write(f"\nDuración del experimento: {minutos:.1f} min\n\nPerfil de configuración:\n")
            for clave, valor in perfil.items():
                archivo.write(f"  {clave} = {valor}\n")
            archivo.write(f"  N = {config.N}, RADIO = {config.RADIO} m, LADO = {config.LADO} m, "
                          f"CAPACIDAD = {config.CAPACIDAD}, SEMILLA = {config.SEMILLA}\n")
        print(f"Experimentos terminados en {minutos:.1f} min.")

    filas = [f for nombre in ARCHIVOS.values() for f in leer_csv(os.path.join(carpeta_datos, nombre))]
    res = resumir(filas)
    texto = tablas(res, os.path.join(base, "tablas"), perfil)
    graficar(res, os.path.join(base, "graficas"), perfil)
    print("\n" + texto)
    print(f"Tablas en {base}/tablas · gráficas en {base}/graficas")


if __name__ == "__main__":
    main()
