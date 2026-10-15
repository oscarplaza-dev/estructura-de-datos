"""
Gráficas del laboratorio. Principio: UNA idea por gráfica.

Convenciones que se repiten en todas:
  * Color = estructura (siempre el mismo): Lista naranja, ABB azul, B+ verde.
  * Línea continua y punto relleno  = IDs insertados en orden ALEATORIO.
    Línea punteada y punto hueco    = IDs insertados en orden ORDENADO.
  * Cada punto es la MEDIA de las repeticiones; la barra vertical es ±1
    desviación estándar (si no se ve es porque es más pequeña que el punto).
  * El subtítulo dice exactamente qué se fijó y qué se varió.
"""

import os

import matplotlib

matplotlib.use("Agg")                     # genera archivos sin abrir ventanas
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, NullFormatter, NullLocator
import numpy as np

from .tablas import leer_csv, resumen_a, resumen_b, resumen_c, serie, buscar
from . import estadistica as est

COLOR = {"Lista": "#eb6834", "ABB": "#2a78d6", "B+": "#1baf7a"}
NOMBRE = {"Lista": "Lista de Python", "ABB": "Árbol binario de búsqueda (ABB)", "B+": "Árbol B+ (orden 32)"}
GRIS = "#8a8984"
TEXTO = "#0b0b0b"
TEXTO_2 = "#52514e"

plt.rcParams.update({
    "figure.figsize": (9, 5.6),
    "figure.dpi": 110,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 11.5,
    "axes.edgecolor": "#c3c2b7",
    "axes.labelcolor": TEXTO,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#e6e5e0",
    "grid.linewidth": 0.8,
    "xtick.color": TEXTO_2,
    "ytick.color": TEXTO_2,
    "legend.frameon": False,
    "legend.fontsize": 10.5,
    "lines.linewidth": 2,
    "lines.markersize": 7,
})


def _miles(x, _pos=None):
    """16384 -> '16.384' (formato colombiano)."""
    if x >= 1:
        return f"{x:,.0f}".replace(",", ".")
    return f"{x:g}".replace(".", ",")


def _numero(x, _pos=None):
    if x >= 100:
        return _miles(x)
    if x >= 1:
        return f"{x:g}".replace(".", ",")
    return f"{x:.2g}".replace(".", ",")


def _dec(texto):
    """Coma decimal en los textos de las leyendas (1.07 -> 1,07)."""
    import re
    return re.sub(r"(?<=\d)\.(?=\d)", ",", texto)


def _titulos(ax, titulo, subtitulo):
    ax.set_title(titulo, loc="left", pad=26, color=TEXTO)
    ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=10, color=TEXTO_2, va="bottom")


def _eje_n(ax, valores, log=True, etiqueta="N = número de estudiantes en la estructura"):
    if log:
        ax.set_xscale("log", base=2)
    ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(valores))
    ax.xaxis.set_major_formatter(FuncFormatter(_miles))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xlabel(etiqueta)
    ax.tick_params(axis="x", labelrotation=35, labelsize=9.5)


def _eje_y_log(ax, etiqueta):
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(_numero))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_ylabel(etiqueta)


def _linea(ax, xs, ys, desv, estructura, ordenado=False, etiqueta=None, barras=True):
    color = COLOR[estructura]
    estilo = dict(color=color, linestyle="--" if ordenado else "-", marker="o",
                  markerfacecolor="white" if ordenado else color, markeredgecolor=color,
                  markeredgewidth=1.8, label=etiqueta or NOMBRE[estructura], zorder=3)
    if barras and desv is not None:
        ax.errorbar(xs, ys, yerr=desv, capsize=3, elinewidth=1.2, **estilo)
    else:
        ax.plot(xs, ys, **estilo)


def _guardar(fig, carpeta, nombre):
    ruta = os.path.join(carpeta, nombre)
    fig.savefig(ruta, facecolor="white")
    plt.close(fig)
    print(f"  {nombre}")


# ---------------------------------------------------------------------------
# Figuras del experimento A (búsqueda vs N)
# ---------------------------------------------------------------------------
def fig_busqueda_lineal(res, rep, m, carpeta):
    fig, ax = plt.subplots()
    for e in ("Lista", "ABB", "B+"):
        xs, ys, ds = serie(res, "n", orden_datos="aleatorio", estructura=e, medida="us_por_busqueda")
        _linea(ax, xs, ys, ds, e)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_formatter(FuncFormatter(_miles))
    ax.yaxis.set_major_formatter(FuncFormatter(_miles))
    ax.set_xlabel("N = número de estudiantes en la estructura")
    ax.set_ylabel("Tiempo promedio de UNA búsqueda (µs)")
    _titulos(ax, "1. Búsqueda vs N en escala normal: la lista crece en línea recta",
             f"IDs insertados al azar · M = {m:,} búsquedas por lote · media de {rep} repeticiones".replace(",", "."))
    ax.legend(loc="upper left")
    ax.annotate("Los dos árboles quedan pegados al piso:\nen esta escala no se pueden comparar\n(ver gráfica 2)",
                xy=(110_000, 15), xytext=(78_000, 330), fontsize=10, color=TEXTO_2,
                arrowprops=dict(arrowstyle="->", color=GRIS))
    _guardar(fig, carpeta, "01_busqueda_vs_n_escala_normal.png")


def fig_busqueda_loglog(res, rep, m, ajus, carpeta):
    fig, ax = plt.subplots()
    for e in ("Lista", "ABB", "B+"):
        xs, ys, ds = serie(res, "n", orden_datos="aleatorio", estructura=e, medida="us_por_busqueda")
        b = next(a["exponente_b"] for a in ajus if a["experimento"].startswith("A")
                 and a["estructura"] == e and a["orden_datos"] == "aleatorio")
        _linea(ax, xs, ys, ds, e, etiqueta=_dec(f"{NOMBRE[e]}  — pendiente b = {b:.2f}"))
    _eje_n(ax, xs)
    _eje_y_log(ax, "Tiempo promedio de UNA búsqueda (µs, escala log)")
    _titulos(ax, "2. Búsqueda vs N en escala log-log: lineal vs logarítmico",
             f"IDs al azar · M = {m:,} · media ± desv. est. de {rep} repeticiones · "
             "b = pendiente ajustada para N ≥ 1.024 (1 = lineal)".replace(",", "."))
    ax.legend(loc="upper left")
    _guardar(fig, carpeta, "02_busqueda_vs_n_loglog.png")


def fig_arboles_log2(res, rep, ajus, carpeta):
    fig, ax = plt.subplots()
    for e in ("ABB", "B+"):
        xs, ys, ds = serie(res, "n", orden_datos="aleatorio", estructura=e, medida="us_por_busqueda")
        a = next(a for a in ajus if a["experimento"].startswith("A") and a["estructura"] == e
                 and a["orden_datos"] == "aleatorio")
        _linea(ax, xs, ys, ds, e, etiqueta=_dec(f"{NOMBRE[e]}  (+{a['pendiente']:.2f} µs cada vez que N se duplica)"))
        # recta de referencia t = a + b log2 N ajustada con N >= 1024
        ia, ib, _ = est.ajuste_logaritmico([x for x in xs if x >= 1024], [y for x, y in zip(xs, ys) if x >= 1024])
        xx = np.array([1024, xs[-1]], float)
        ax.plot(xx, ia + ib * np.log2(xx), color=COLOR[e], alpha=0.35, linewidth=6, zorder=1)
    _eje_n(ax, xs)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Tiempo promedio de UNA búsqueda (µs)")
    _titulos(ax, "3. Zoom a los árboles: con el eje N logarítmico se ven como rectas",
             f"IDs al azar · eje x en escala log2 (cada marca duplica o cuadruplica N) · "
             f"franja clara = recta t = a + b·log2(N) ajustada con N ≥ 1.024 · {rep} repeticiones")
    ax.legend(loc="upper left")
    _guardar(fig, carpeta, "03_arboles_crecen_como_log.png")


def fig_aleatorio_vs_ordenado(res, rep, m, carpeta):
    fig, ax = plt.subplots()
    casos = [("Lista", "ordenado", "Lista de Python (IDs ordenados)"),
             ("ABB", "aleatorio", "ABB con IDs aleatorios"),
             ("ABB", "ordenado", "ABB con IDs ORDENADOS  ← degenerado"),
             ("B+", "ordenado", "B+ con IDs ordenados")]
    nmax = max(r["n"] for r in res if r["orden_datos"] == "ordenado")
    for e, orden, etq in casos:
        xs, ys, ds = serie(res, "n", orden_datos=orden, estructura=e, medida="us_por_busqueda")
        pares = [(x, y, d) for x, y, d in zip(xs, ys, ds) if x <= nmax]
        xs, ys, ds = zip(*pares)
        _linea(ax, xs, ys, ds, e, ordenado=(orden == "ordenado"), etiqueta=etq)
    _eje_n(ax, xs)
    _eje_y_log(ax, "Tiempo promedio de UNA búsqueda (µs, escala log)")
    _titulos(ax, "4. Si los IDs llegan ordenados, el ABB se vuelve una lista",
             f"Mismos IDs en ambos casos; solo cambia el orden de inserción · M = {m:,} · {rep} repeticiones".replace(",", "."))
    ax.legend(loc="upper left")
    _guardar(fig, carpeta, "04_aleatorio_vs_ordenado.png")


def fig_altura(res, rep, carpeta):
    fig, ax = plt.subplots()
    xs_r, h_r, _ = serie(res, "n", orden_datos="aleatorio", estructura="ABB", medida="altura")
    xs_o, h_o, _ = serie(res, "n", orden_datos="ordenado", estructura="ABB", medida="altura")
    xs_b, h_b, _ = serie(res, "n", orden_datos="aleatorio", estructura="B+", medida="altura")
    xs_bo, h_bo, _ = serie(res, "n", orden_datos="ordenado", estructura="B+", medida="altura")
    xx = np.array(xs_r, float)
    ax.plot(xx, xx, color=GRIS, linestyle=":", linewidth=1.5, label="Referencia: altura = N (una lista)")
    ax.plot(xx, np.log2(xx) + 1, color=GRIS, linestyle="-.", linewidth=1.5, label="Referencia: log2(N) (árbol perfecto)")
    _linea(ax, xs_o, h_o, None, "ABB", ordenado=True, etiqueta="ABB con IDs ordenados", barras=False)
    _linea(ax, xs_r, h_r, None, "ABB", etiqueta="ABB con IDs aleatorios", barras=False)
    _linea(ax, xs_bo, h_bo, None, "B+", ordenado=True, etiqueta="B+ con IDs ordenados", barras=False)
    _linea(ax, xs_b, h_b, None, "B+", etiqueta="B+ con IDs aleatorios", barras=False)
    _eje_n(ax, xs_r)
    _eje_y_log(ax, "Altura del árbol (número de niveles, escala log)")
    _titulos(ax, "5. Altura del árbol vs N",
             f"Media de {rep} árboles construidos con datos distintos")
    ax.legend(loc="upper left")
    _guardar(fig, carpeta, "05_altura_vs_n.png")


def fig_tiempo_vs_visitados(res, carpeta):
    """Pregunta del enunciado: ¿qué relación hay entre la altura del ABB y el tiempo?"""
    fig, ax = plt.subplots()
    todos_x, todos_y = [], []
    for orden in ("aleatorio", "ordenado"):
        ns = sorted({r["n"] for r in res if r["orden_datos"] == orden})
        xs = [buscar(res, orden_datos=orden, estructura="ABB", n=n, medida="nodos_visitados")["media"] for n in ns]
        ys = [buscar(res, orden_datos=orden, estructura="ABB", n=n, medida="us_por_busqueda")["media"] for n in ns]
        todos_x += xs
        todos_y += ys
        ax.scatter(xs, ys, s=70, color="white" if orden == "ordenado" else COLOR["ABB"],
                   edgecolors=COLOR["ABB"], linewidths=2, zorder=3,
                   label=f"ABB con IDs {'ordenados (árbol degenerado)' if orden == 'ordenado' else 'aleatorios (árbol bajo)'}")
    a, b, r2 = est.ajuste_potencia(todos_x, todos_y)
    xx = np.logspace(np.log10(min(todos_x)), np.log10(max(todos_x)), 50)
    ax.plot(xx, a * xx ** b, color=GRIS, linestyle="--", linewidth=1.5,
            label=_dec(f"Ajuste: tiempo ∝ (nodos visitados)^{b:.2f}   R² = {r2:.3f}"))
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(_numero))
    ax.set_xlabel("Nodos visitados en promedio por búsqueda (≈ profundidad del nodo, escala log)")
    _eje_y_log(ax, "Tiempo promedio de UNA búsqueda (µs, escala log)")
    _titulos(ax, "6. ABB: el tiempo es proporcional a la profundidad recorrida",
             "Cada punto es un N del experimento A · árbol alto = más nodos por búsqueda = más tiempo")
    ax.legend(loc="upper left")
    _guardar(fig, carpeta, "06_tiempo_vs_nodos_visitados.png")


def fig_aceleracion(res, rep, carpeta):
    fig, ax = plt.subplots()
    xs, lista, _ = serie(res, "n", orden_datos="aleatorio", estructura="Lista", medida="us_por_busqueda")
    for e in ("ABB", "B+"):
        _, arbol, _ = serie(res, "n", orden_datos="aleatorio", estructura=e, medida="us_por_busqueda")
        _linea(ax, xs, [l / t for l, t in zip(lista, arbol)], None, e,
               etiqueta=f"Lista ÷ {e}", barras=False)
    ax.axhline(1, color=GRIS, linestyle=":", linewidth=1.5)
    ax.text(xs[-1], 1.15, "1 = igual de rápidos", ha="right", color=TEXTO_2, fontsize=10)
    _eje_n(ax, xs)
    _eje_y_log(ax, "¿Cuántas veces más rápido que la lista? (escala log)")
    _titulos(ax, "7. ¿Desde qué N vale la pena un árbol?",
             f"Tiempo de búsqueda de la lista dividido por el del árbol · IDs al azar · medias de {rep} repeticiones")
    ax.legend(loc="upper left")
    _guardar(fig, carpeta, "07_cuantas_veces_mas_rapido.png")


def fig_insercion(res, rep, carpeta):
    fig, ax = plt.subplots()
    nmax = max(r["n"] for r in res if r["orden_datos"] == "ordenado")
    for e in ("Lista", "ABB", "B+"):
        xs, ys, ds = serie(res, "n", orden_datos="aleatorio", estructura=e, medida="us_por_insercion")
        _linea(ax, xs, ys, ds, e, etiqueta=f"{e} — IDs aleatorios")
    xs, ys, ds = serie(res, "n", orden_datos="ordenado", estructura="ABB", medida="us_por_insercion")
    _linea(ax, xs, ys, ds, "ABB", ordenado=True, etiqueta="ABB — IDs ORDENADOS")
    xs, _, _ = serie(res, "n", orden_datos="aleatorio", estructura="ABB", medida="us_por_insercion")
    _eje_n(ax, xs)
    _eje_y_log(ax, "Tiempo promedio de UNA inserción (µs, escala log)")
    _titulos(ax, "8. Insertar: la lista solo agrega al final; el ABB ordenado recorre todo",
             f"Tiempo de construir la estructura completa ÷ N · {rep} repeticiones · ABB ordenado medido hasta N = {_miles(nmax)}")
    ax.legend(loc="upper left")
    _guardar(fig, carpeta, "08_insercion_vs_n.png")


def fig_listado(res, rep, carpeta):
    fig, ax = plt.subplots()
    for e in ("Lista", "ABB", "B+"):
        xs, ys, ds = serie(res, "n", orden_datos="aleatorio", estructura=e, medida="ms_listado")
        _linea(ax, xs, [y * 1000 / x for x, y in zip(xs, ys)], [d * 1000 / x for x, d in zip(xs, ds)], e)
    _eje_n(ax, xs)
    _eje_y_log(ax, "Tiempo de listar ÷ N  (µs por estudiante, escala log)")
    _titulos(ax, "9. Listar todos en orden de ID: costo por estudiante",
             "IDs al azar · Lista = sorted() O(N log N) · ABB = in-orden O(N) · B+ = recorrer hojas enlazadas O(N)")
    ax.legend(loc="upper left")
    _guardar(fig, carpeta, "09_listado_ordenado.png")


def fig_variabilidad(filas_a, carpeta):
    """Cada repetición expresada como % de la media de su grupo: así las tres
    estructuras (que tienen tiempos muy distintos) se comparan en la misma escala."""
    n = 16_384
    fig, ax = plt.subplots()
    datos, etiquetas, colores = [], [], []
    for e in ("Lista", "ABB", "B+"):
        vals = [f["us_por_busqueda"] for f in filas_a
                if f["orden_datos"] == "aleatorio" and f["estructura"] == e and f["n"] == n]
        r = est.resumir(vals)
        datos.append([100 * v / r["media"] for v in vals])
        etiquetas.append(_dec(f"{NOMBRE[e]}\nmedia {r['media']:.2f} µs · CV {r['cv_pct']:.1f} %"))
        colores.append(COLOR[e])
    ax.axhline(100, color=GRIS, linestyle=":", linewidth=1.5)
    caja = ax.boxplot(datos, tick_labels=etiquetas, widths=0.45, patch_artist=True,
                      medianprops=dict(color=TEXTO, linewidth=2), showfliers=False)
    for parche, c in zip(caja["boxes"], colores):
        parche.set_facecolor(c)
        parche.set_alpha(0.3)
        parche.set_edgecolor(c)
    for i, (vals, c) in enumerate(zip(datos, colores), start=1):
        jitter = np.linspace(-0.12, 0.12, len(vals))
        ax.scatter(np.full(len(vals), i) + jitter, vals, color=c, s=34, zorder=3,
                   edgecolors="white", linewidths=0.8)
    ax.set_ylabel("Cada repetición como % de la media de su estructura")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: f"{v:.0f} %"))
    ax.grid(axis="x", visible=False)
    _titulos(ax, f"10. ¿Qué tan repetibles son las mediciones? (N = {_miles(n)})",
             f"Cada punto = una repetición independiente ({len(datos[0])}) · caja = Q1–Q3 · "
             "línea negra = mediana · 100 % = la media")
    _guardar(fig, carpeta, "10_variabilidad_repeticiones.png")


# ---------------------------------------------------------------------------
# Experimento B (vs M) y C (orden del B+)
# ---------------------------------------------------------------------------
def fig_busqueda_vs_m(res_b, rep, n, carpeta):
    fig, ax = plt.subplots()
    for e in ("Lista", "ABB", "B+"):
        xs, ys, ds = serie(res_b, "m", estructura=e, medida="segundos_total")
        _linea(ax, xs, ys, ds, e)
    ax.axhline(1, color=GRIS, linestyle=":", linewidth=1.5)
    ax.text(xs[-1], 1.25, "1 segundo", ha="right", color=TEXTO_2, fontsize=10)
    _eje_n(ax, xs, etiqueta="M = número de búsquedas realizadas")
    _eje_y_log(ax, "Tiempo TOTAL de las M búsquedas (s, escala log)")
    _titulos(ax, "11. Más búsquedas = más tiempo, en proporción directa (las 3 son rectas)",
             f"N fijo = {_miles(n)} estudiantes (IDs al azar) · M se duplica en cada punto · {rep} repeticiones")
    ax.legend(loc="lower right")
    _guardar(fig, carpeta, "11_busqueda_vs_m.png")


def fig_orden_bmas(res_c, rep, n, carpeta):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7.4), sharex=True,
                                   gridspec_kw=dict(height_ratios=[1.4, 1], hspace=0.12))
    ordenes, ys, ds = serie(res_c, "orden", estructura="B+", medida="us_por_busqueda")
    _, hs, _ = serie(res_c, "orden", estructura="B+", medida="altura")
    pos = list(range(len(ordenes)))                 # eje x categórico

    _linea(ax1, pos, ys, ds, "B+", etiqueta="Árbol B+")
    abb = buscar(res_c, estructura="ABB", medida="us_por_busqueda")
    ax1.axhline(abb["media"], color=COLOR["ABB"], linestyle="--", linewidth=1.8,
                label=f"ABB (referencia): {abb['media']:.2f} µs".replace(".", ","))
    ax1.set_ylim(bottom=0)
    ax1.set_ylabel("Tiempo de UNA búsqueda (µs)")
    ax1.legend(loc="upper right")
    _titulos(ax1, "12. Árbol B+: ¿cuántos hijos por nodo conviene?",
             f"N = {_miles(n)} estudiantes al azar · {rep} repeticiones · orden = máximo de hijos por nodo")

    ax2.bar(pos, hs, color=COLOR["B+"], alpha=0.85, width=0.55)
    for i, h in enumerate(hs):
        ax2.text(i, h + 0.2, f"{h:.0f} niveles", ha="center", color=TEXTO, fontsize=9.5)
    ax2.set_ylabel("Altura del B+")
    ax2.set_ylim(0, max(hs) + 2)
    ax2.grid(axis="x", visible=False)
    ax2.set_xticks(pos)
    ax2.set_xticklabels([str(int(o)) for o in ordenes])
    ax2.set_xlabel("Orden del árbol B+ (máximo de hijos por nodo)")
    _guardar(fig, carpeta, "12_orden_del_bmas.png")


def generar_todas(carpeta_datos, carpeta_graficas):
    print("\nGenerando gráficas...")
    filas_a = leer_csv(os.path.join(carpeta_datos, "A_busqueda_vs_n.csv"))
    filas_b = leer_csv(os.path.join(carpeta_datos, "B_busqueda_vs_m.csv"))
    filas_c = leer_csv(os.path.join(carpeta_datos, "C_orden_bmas.csv"))
    res_a, res_b, res_c = resumen_a(filas_a), resumen_b(filas_b), resumen_c(filas_c)
    from .tablas import ajustes
    ajus = ajustes(res_a, res_b)
    rep = max(f["repeticion"] for f in filas_a) + 1
    m = int(filas_a[0]["m"])

    fig_busqueda_lineal(res_a, rep, m, carpeta_graficas)
    fig_busqueda_loglog(res_a, rep, m, ajus, carpeta_graficas)
    fig_arboles_log2(res_a, rep, ajus, carpeta_graficas)
    fig_aleatorio_vs_ordenado(res_a, rep, m, carpeta_graficas)
    fig_altura(res_a, rep, carpeta_graficas)
    fig_tiempo_vs_visitados(res_a, carpeta_graficas)
    fig_aceleracion(res_a, rep, carpeta_graficas)
    fig_insercion(res_a, rep, carpeta_graficas)
    fig_listado(res_a, rep, carpeta_graficas)
    fig_variabilidad(filas_a, carpeta_graficas)
    fig_busqueda_vs_m(res_b, rep, int(filas_b[0]["n"]), carpeta_graficas)
    fig_orden_bmas(res_c, rep, int(filas_c[0]["n"]), carpeta_graficas)
