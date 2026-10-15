"""
Convierte las mediciones crudas en tablas resumen:

  resultados/tablas/A_resumen.csv    estadística por (orden de datos, estructura, N, medida)
  resultados/tablas/B_resumen.csv    estadística por (estructura, M)
  resultados/tablas/C_resumen.csv    estadística por (estructura, orden del B+, medida)
  resultados/tablas/ajustes.csv      curvas ajustadas (comparación con la teoría)
  resultados/tablas/RESUMEN.md       las tablas más importantes, listas para leer
"""

import csv
import os

from . import estadistica as est

ESTRUCTURAS = ["Lista", "ABB", "B+"]


# ---------------------------------------------------------------------------
# Lectura / escritura
# ---------------------------------------------------------------------------
def leer_csv(ruta):
    with open(ruta, encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    for f in filas:
        for k, v in f.items():
            if k in ("orden_datos", "estructura"):
                continue
            try:
                f[k] = float(v) if v != "" else None
                if f[k] is not None and f[k].is_integer() and k in ("n", "m", "repeticion", "orden", "altura", "lotes", "semilla"):
                    f[k] = int(f[k])
            except ValueError:
                pass
    return filas


def escribir_csv(ruta, filas):
    if not filas:
        return
    columnas = list(filas[0].keys())
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        for fila in filas:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in fila.items()})


def buscar(resumen, **filtro):
    for r in resumen:
        if all(r.get(k) == v for k, v in filtro.items()):
            return r
    return None


def serie(resumen, xcampo, **filtro):
    """Puntos (x, media, desv) ordenados por x que cumplen el filtro."""
    pts = sorted((r[xcampo], r["media"], r["desv_est"]) for r in resumen
                 if all(r.get(k) == v for k, v in filtro.items()))
    return [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]


# ---------------------------------------------------------------------------
# Resúmenes
# ---------------------------------------------------------------------------
MEDIDAS_A = ["us_por_busqueda", "us_por_insercion", "ms_listado", "altura",
             "nodos_visitados", "ocupacion_hojas_pct"]


def resumen_a(filas):
    salida = []
    for medida in MEDIDAS_A:
        salida += est.agrupar_y_resumir(filas, ["orden_datos", "estructura", "n"], medida)
    return salida


def resumen_b(filas):
    return (est.agrupar_y_resumir(filas, ["estructura", "m"], "segundos_total")
            + est.agrupar_y_resumir(filas, ["estructura", "m"], "us_por_busqueda"))


def resumen_c(filas):
    for f in filas:
        if f["orden"] is None:
            f["orden"] = 0          # 0 = ABB (no tiene orden)
    salida = []
    for medida in ("us_por_busqueda", "us_por_insercion", "altura", "ocupacion_hojas_pct"):
        salida += est.agrupar_y_resumir(filas, ["estructura", "orden"], medida)
    return salida


def ajustes(res_a, res_b):
    """Ajusta curvas a las medias para contrastar con la complejidad teórica."""
    filas = []
    teoria = {"Lista": "O(N)", "ABB": "O(log N) promedio / O(N) peor caso", "B+": "O(log N)"}
    for orden_datos in ("aleatorio", "ordenado"):
        for e in ESTRUCTURAS:
            xs, ys, _ = serie(res_a, "n", orden_datos=orden_datos, estructura=e, medida="us_por_busqueda")
            if len(xs) < 3:
                continue
            # El ajuste se hace en la zona "grande" (N >= 1024) para evitar la
            # región cercana a 0 donde dominan los costos constantes.
            grandes = [(x, y) for x, y in zip(xs, ys) if x >= 1024]
            gx, gy = zip(*grandes)
            a, b, r2 = est.ajuste_potencia(gx, gy)
            la, lb, lr2 = est.ajuste_logaritmico(gx, gy)
            filas.append({
                "experimento": "A búsqueda vs N", "orden_datos": orden_datos, "estructura": e,
                "teoria": teoria[e], "rango_N": f"{_fmt(gx[0])}–{_fmt(gx[-1])}",
                "exponente_b": b, "R2_potencia": r2,
                "modelo_pendiente": "t = a + b·log2(N)  [µs al duplicar N]",
                "pendiente": lb, "R2_pendiente": lr2,
            })
    for e in ESTRUCTURAS:
        xs, ys, _ = serie(res_b, "m", estructura=e, medida="segundos_total")
        a, b, r2 = est.ajuste_lineal(xs, ys)
        filas.append({
            "experimento": "B tiempo total vs M", "orden_datos": "aleatorio", "estructura": e,
            "teoria": "O(M) para todas", "rango_N": f"M {int(xs[0])}–{int(xs[-1])}",
            "exponente_b": est.ajuste_potencia(xs, ys)[1], "R2_potencia": est.ajuste_potencia(xs, ys)[2],
            "modelo_pendiente": "t = a + b·M  [µs por búsqueda]",
            "pendiente": b * 1e6, "R2_pendiente": r2,
        })
    return filas


# ---------------------------------------------------------------------------
# Markdown legible
# ---------------------------------------------------------------------------
def _fmt(v, dec=2):
    """Formato colombiano: punto de miles y coma decimal (2026.5 -> '2.026,50')."""
    if v is None:
        return "—"
    if abs(v) >= 1000:
        dec = 0
    texto = f"{v:,.{dec}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def _tabla(encabezados, filas):
    lineas = ["| " + " | ".join(encabezados) + " |",
              "|" + "|".join(["---:"] * len(encabezados)) + "|"]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def markdown(res_a, res_b, res_c, ajus, m_fijo):
    md = ["# Resumen de resultados (generado automáticamente)\n",
          "Todas las cifras son **media ± desviación estándar** de las repeticiones "
          "independientes (columna *ejec.* = número de ejecuciones). CV = desviación/media.\n"]

    for orden_datos in ("aleatorio", "ordenado"):
        md.append(f"\n## Búsqueda por ID — IDs insertados en orden **{orden_datos}** (µs por búsqueda, M = {_fmt(m_fijo)})\n")
        ns = sorted({r["n"] for r in res_a if r["orden_datos"] == orden_datos})
        filas = []
        for n in ns:
            fila = [f"{n:,}".replace(",", ".")]
            for e in ESTRUCTURAS:
                r = buscar(res_a, orden_datos=orden_datos, estructura=e, n=n, medida="us_por_busqueda")
                fila.append(f"{_fmt(r['media'])} ± {_fmt(r['desv_est'])} (CV {_fmt(r['cv_pct'], 1)} %)" if r else "—")
            r = buscar(res_a, orden_datos=orden_datos, estructura="Lista", n=n, medida="us_por_busqueda")
            fila.append(str(r["ejecuciones"]) if r else "—")
            atip = sum(buscar(res_a, orden_datos=orden_datos, estructura=e, n=n, medida="us_por_busqueda")["atipicos"]
                       for e in ESTRUCTURAS)
            fila.append(str(atip))
            filas.append(fila)
        md.append(_tabla(["N", "Lista", "ABB", "B+", "ejec.", "atípicos (Tukey)"], filas))

        md.append(f"\n\n**Altura del árbol (niveles) y nodos visitados por búsqueda — orden {orden_datos}**\n")
        filas = []
        for n in ns:
            fila = [f"{n:,}".replace(",", ".")]
            for e in ("ABB", "B+"):
                h = buscar(res_a, orden_datos=orden_datos, estructura=e, n=n, medida="altura")
                fila.append(_fmt(h["media"], 1))
            for e in ESTRUCTURAS:
                v = buscar(res_a, orden_datos=orden_datos, estructura=e, n=n, medida="nodos_visitados")
                fila.append(_fmt(v["media"], 1))
            oc = buscar(res_a, orden_datos=orden_datos, estructura="B+", n=n, medida="ocupacion_hojas_pct")
            fila.append(_fmt(oc["media"], 1))
            filas.append(fila)
        md.append(_tabla(["N", "altura ABB", "altura B+", "visitados Lista", "visitados ABB",
                          "visitados B+", "ocupación hojas B+ (%)"], filas))

        md.append(f"\n\n**Construcción (µs por inserción) y listado ordenado (ms) — orden {orden_datos}**\n")
        filas = []
        for n in ns:
            fila = [f"{n:,}".replace(",", ".")]
            for medida in ("us_por_insercion", "ms_listado"):
                for e in ESTRUCTURAS:
                    r = buscar(res_a, orden_datos=orden_datos, estructura=e, n=n, medida=medida)
                    fila.append(_fmt(r["media"], 3))
            filas.append(fila)
        md.append(_tabla(["N", "insertar Lista", "insertar ABB", "insertar B+",
                          "listar Lista", "listar ABB", "listar B+"], filas))

    md.append("\n\n## Tiempo total de M búsquedas con N fijo (segundos)\n")
    ms = sorted({r["m"] for r in res_b})
    filas = []
    for m in ms:
        fila = [f"{m:,}".replace(",", ".")]
        for e in ESTRUCTURAS:
            r = buscar(res_b, estructura=e, m=m, medida="segundos_total")
            fila.append(f"{_fmt(r['media'], 5)} ± {_fmt(r['desv_est'], 5)}")
        filas.append(fila)
    md.append(_tabla(["M", "Lista (s)", "ABB (s)", "B+ (s)"], filas))

    md.append("\n\n## Efecto del orden del árbol B+\n")
    ordenes = sorted({r["orden"] for r in res_c if r["estructura"] == "B+"})
    filas = []
    abb = buscar(res_c, estructura="ABB", medida="us_por_busqueda")
    abb_h = buscar(res_c, estructura="ABB", medida="altura")
    filas.append(["ABB (referencia)", f"{_fmt(abb['media'])} ± {_fmt(abb['desv_est'])}", _fmt(abb_h["media"], 1), "—"])
    for o in ordenes:
        r = buscar(res_c, estructura="B+", orden=o, medida="us_por_busqueda")
        h = buscar(res_c, estructura="B+", orden=o, medida="altura")
        oc = buscar(res_c, estructura="B+", orden=o, medida="ocupacion_hojas_pct")
        filas.append([f"B+ orden {o}", f"{_fmt(r['media'])} ± {_fmt(r['desv_est'])}", _fmt(h["media"], 1), _fmt(oc["media"], 1)])
    md.append(_tabla(["estructura", "µs por búsqueda", "altura", "ocupación hojas (%)"], filas))

    md.append("\n\n## Ajuste de curvas (comparación con la teoría)\n")
    md.append("*b* es el exponente de t ≈ a·N^b ajustado en log-log con N ≥ 1.024: "
              "b ≈ 1 significa crecimiento lineal; b cercano a 0 significa crecimiento muy lento "
              "(logarítmico). La pendiente log indica cuántos µs aumenta la búsqueda cada vez que N se duplica.\n")
    filas = []
    for a in ajus:
        if a["experimento"].startswith("A"):
            filas.append([a["estructura"], a["orden_datos"], a["teoria"], a["rango_N"],
                          _fmt(a['exponente_b'], 3), _fmt(a['R2_potencia'], 4),
                          _fmt(a['pendiente'], 3), _fmt(a['R2_pendiente'], 4)])
    md.append(_tabla(["estructura", "IDs", "teoría", "rango N", "exponente b", "R² potencia",
                      "µs extra al duplicar N", "R² log"], filas))
    md.append("\n\n**Tiempo total vs M** (ajuste t = a + b·M): b = costo de cada búsqueda adicional.\n")
    filas = [[a["estructura"], _fmt(a['exponente_b'], 3), _fmt(a['pendiente'], 3), _fmt(a['R2_pendiente'], 5)]
             for a in ajus if a["experimento"].startswith("B")]
    md.append(_tabla(["estructura", "exponente de M", "µs por búsqueda (pendiente)", "R² lineal"], filas))
    return "\n".join(md) + "\n"


def generar_todas(carpeta_datos, carpeta_tablas):
    print("\nGenerando tablas...")
    a = leer_csv(os.path.join(carpeta_datos, "A_busqueda_vs_n.csv"))
    b = leer_csv(os.path.join(carpeta_datos, "B_busqueda_vs_m.csv"))
    c = leer_csv(os.path.join(carpeta_datos, "C_orden_bmas.csv"))
    res_a, res_b, res_c = resumen_a(a), resumen_b(b), resumen_c(c)
    ajus = ajustes(res_a, res_b)
    escribir_csv(os.path.join(carpeta_tablas, "A_resumen.csv"), res_a)
    escribir_csv(os.path.join(carpeta_tablas, "B_resumen.csv"), res_b)
    escribir_csv(os.path.join(carpeta_tablas, "C_resumen.csv"), res_c)
    escribir_csv(os.path.join(carpeta_tablas, "ajustes.csv"), ajus)
    m_fijo = int(a[0]["m"])
    with open(os.path.join(carpeta_tablas, "RESUMEN.md"), "w", encoding="utf-8") as f:
        f.write(markdown(res_a, res_b, res_c, ajus, m_fijo))
    print(f"  tablas en {carpeta_tablas}")
    return res_a, res_b, res_c
