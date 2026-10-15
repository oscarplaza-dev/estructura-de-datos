"""
Laboratorio 3 — Sistema de búsqueda de estudiantes (Lista vs ABB vs B+).

Uso (desde la carpeta Lab3):
    python main.py                  # corre TODO: experimentos + tablas + gráficas (≈ 20 min)
    python main.py --rapido         # versión corta para probar que todo funciona (≈ 1 min)
    python main.py --solo-graficas  # NO mide nada: regenera tablas y gráficas desde los CSV
    python main.py --experimentos A C   # corre solo algunos experimentos (A, B, C)

Resultados:
    resultados/datos/     mediciones crudas (una fila por medición)
    resultados/tablas/    resúmenes estadísticos (.csv y .md)
    resultados/graficas/  figuras .png
    resultados/entorno.txt  hardware y software usados
"""

import argparse
import os
import time

from sistema_estudiantes.config import COMPLETO, RAPIDO
from sistema_estudiantes import experimentos, medicion

AQUI = os.path.dirname(os.path.abspath(__file__))


def carpetas(nombre_resultados):
    base = os.path.join(AQUI, nombre_resultados)
    rutas = {k: os.path.join(base, k) for k in ("datos", "tablas", "graficas")}
    rutas["base"] = base
    for r in rutas.values():
        os.makedirs(r, exist_ok=True)
    return rutas


def guardar_entorno(cfg, ruta):
    entorno = medicion.describir_entorno()
    with open(ruta, "w", encoding="utf-8") as f:
        for k, v in entorno.items():
            f.write(f"{k}: {v}\n")
        f.write(f"\nPerfil de configuración: {cfg.nombre}\n")
        for campo, valor in vars(cfg).items():
            f.write(f"  {campo} = {valor}\n")
    print("\n".join(f"{k}: {v}" for k, v in entorno.items()))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rapido", action="store_true", help="perfil corto de prueba")
    p.add_argument("--solo-graficas", action="store_true", help="no medir; solo tablas y gráficas")
    p.add_argument("--experimentos", nargs="+", choices=["A", "B", "C"], default=["A", "B", "C"])
    args = p.parse_args()

    cfg = RAPIDO if args.rapido else COMPLETO
    rutas = carpetas("resultados_rapido" if args.rapido else "resultados")

    if not args.solo_graficas:
        guardar_entorno(cfg, os.path.join(rutas["base"], "entorno.txt"))
        inicio = time.perf_counter()
        if "A" in args.experimentos:
            experimentos.experimento_busqueda_vs_n(cfg, rutas["datos"])
        if "B" in args.experimentos:
            experimentos.experimento_busqueda_vs_m(cfg, rutas["datos"])
        if "C" in args.experimentos:
            experimentos.experimento_orden_bmas(cfg, rutas["datos"])
        print(f"\nMediciones terminadas en {(time.perf_counter() - inicio) / 60:.1f} min")

    from sistema_estudiantes import tablas, graficas     # solo se necesitan aquí
    tablas.generar_todas(rutas["datos"], rutas["tablas"])
    graficas.generar_todas(rutas["datos"], rutas["graficas"])
    print(f"\nListo. Revise la carpeta: {rutas['base']}")


if __name__ == "__main__":
    main()
