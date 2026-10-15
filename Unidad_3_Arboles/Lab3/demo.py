"""
Demostración de las tres operaciones del sistema (ideal para la sustentación):

    1. Buscar un estudiante por su ID
    2. Insertar un estudiante nuevo
    3. Listar todos los estudiantes en orden ascendente de ID

Uso:  python demo.py            (10 000 estudiantes, como el enunciado)
      python demo.py 50000      (otro tamaño)
"""

import sys
import time

from sistema_estudiantes.modelo import Estudiante, generar_estudiantes, nuevo_generador
from sistema_estudiantes.estructuras import ListaPython, ArbolBinarioBusqueda, ArbolBMas


def linea(titulo=""):
    print("\n" + "─" * 78)
    if titulo:
        print(titulo)
        print("─" * 78)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    rng = nuevo_generador(2026)

    for orden in ("aleatorio", "ordenado"):
        estudiantes = generar_estudiantes(n, rng, orden)
        linea(f"{n:,} estudiantes con IDs en orden {orden.upper()}".replace(",", "."))

        estructuras = [ListaPython(), ArbolBinarioBusqueda(), ArbolBMas(orden=32)]
        for e in estructuras:
            t = time.perf_counter()
            for est in estudiantes:
                e.insertar(est)
            t = time.perf_counter() - t
            altura = e.altura()
            print(f"  {e.nombre:<6} construida en {t * 1000:9.1f} ms"
                  + (f"   | altura = {altura} niveles" if altura else ""))

        # 1. BUSCAR -----------------------------------------------------------
        objetivo = rng.choice(estudiantes).id
        print(f"\n  1) Buscar ID {objetivo} (100 veces cada estructura):")
        for e in estructuras:
            t = time.perf_counter()
            for _ in range(100):
                encontrado = e.buscar(objetivo)
            t = (time.perf_counter() - t) / 100 * 1e6
            print(f"     {e.nombre:<6} {t:10.2f} µs  ->  {encontrado}")
        print(f"     Buscar un ID que no existe (5): {[e.buscar(5) for e in estructuras]}")

        # 2. INSERTAR ---------------------------------------------------------
        nuevo = Estudiante(id=999, nombre="Oscar Plaza", edad=25, promedio=4.9)
        print(f"\n  2) Insertar al estudiante nuevo: {nuevo}")
        for e in estructuras:
            e.insertar(nuevo)
            print(f"     {e.nombre:<6} ahora tiene {len(e):,} estudiantes; buscar(999) -> "
                  f"{e.buscar(999).nombre}".replace(",", "."))

        # 3. LISTAR -----------------------------------------------------------
        print("\n  3) Listar en orden de ID (primeros 5 de cada estructura):")
        listados = []
        for e in estructuras:
            t = time.perf_counter()
            listado = e.listar()
            t = (time.perf_counter() - t) * 1000
            listados.append([x.id for x in listado])
            print(f"     {e.nombre:<6} {t:8.2f} ms   primeros IDs: {[x.id for x in listado[:5]]}")
        iguales = all(lst == listados[0] for lst in listados)
        print(f"     ¿Las tres estructuras devuelven exactamente el mismo listado? {'Sí' if iguales else 'NO'}")

    # Bonus: consulta por rango (la "autopista" de hojas del B+)
    linea("Bonus: consulta por rango en el B+ (recorre las hojas enlazadas)")
    arbol = estructuras[2]
    ids = sorted(e.id for e in estudiantes)
    desde, hasta = ids[100], ids[104]
    for est in arbol.listar_rango(desde, hasta):
        print("  ", est)
    print()


if __name__ == "__main__":
    main()
