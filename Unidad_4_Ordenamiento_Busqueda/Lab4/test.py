"""
test.py — Pruebas unitarias, verificación visual y análisis de las pruebas.

Ejecutar:  python test.py
  1) Corre las pruebas unitarias (unittest). Cada búsqueda del Quadtree se compara
     contra la fuerza bruta: el resultado debe ser EXACTAMENTE el mismo.
  2) Si todas pasan, genera las gráficas de verificación en resultados/graficas:
       01_estructura_uniforme_vs_agrupado.png
       02_busqueda_radio.png
       03_vecinos_mas_cercanos.png
  3) Imprime un resumen (análisis de las pruebas).

Las gráficas solo LEEN el árbol y las listas de puntos. Al final se comprueba que
los datos siguen idénticos después de graficar (verificar_que_graficar_no_modifica).
"""

import os
import random
import sys
import unittest

import config
import datos
from Quadtreetree import (PROFUNDIDAD_MAXIMA, Caja, Quadtree, distancia2,
                          fuerza_bruta_k_vecinos, fuerza_bruta_radio,
                          fuerza_bruta_vecino)


# ---------------------------------------------------------------------------
# Ayudas para recorrer el árbol (no son parte del árbol: solo lo inspeccionan)
# ---------------------------------------------------------------------------

def nodos(nodo):
    """Todos los nodos del árbol, recorriéndolo desde `nodo`."""
    pila = [nodo]
    while pila:
        actual = pila.pop()
        yield actual
        if not actual.es_hoja():
            pila.extend(actual.hijos.values())


def hojas(nodo):
    return [n for n in nodos(nodo) if n.es_hoja()]


def puntos_guardados(arbol):
    return [p for h in hojas(arbol.raiz) for p in h.puntos]


def mismos_puntos(a, b):
    """Compara dos resultados de búsqueda por radio sin importar el orden."""
    return sorted(a) == sorted(b)


# ---------------------------------------------------------------------------
# 1. Pruebas de estructura: ¿el árbol se construye bien?
# ---------------------------------------------------------------------------

class PruebasEstructura(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.puntos = datos.uniformes(config.N)
        cls.arbol = Quadtree(datos.caja_mapa(), config.CAPACIDAD, cls.puntos)

    def test_01_ningun_punto_se_pierde_ni_se_duplica(self):
        self.assertEqual(self.arbol.n, config.N)
        self.assertEqual(sorted(puntos_guardados(self.arbol)), sorted(self.puntos))

    def test_02_el_arbol_realmente_se_divide(self):
        # Si el árbol nunca se dividiera (una sola hoja con todo), las búsquedas
        # darían el resultado correcto ... pero serían fuerza bruta. Esta prueba lo detecta.
        self.assertFalse(self.arbol.raiz.es_hoja())
        self.assertGreater(self.arbol.profundidad_maxima(), 3)
        for nodo in nodos(self.arbol.raiz):
            if not nodo.es_hoja():
                self.assertEqual(nodo.puntos, [], "un nodo interno no debe guardar puntos")
                self.assertEqual(len(nodo.hijos), 4, "en 2D cada nodo interno tiene 4 hijos")

    def test_03_hojas_respetan_capacidad_y_cada_punto_esta_en_su_caja(self):
        for hoja in hojas(self.arbol.raiz):
            self.assertLessEqual(len(hoja.puntos), config.CAPACIDAD)
            for p in hoja.puntos:
                self.assertTrue(hoja.caja.contiene(p))

    def test_04_puntos_en_los_bordes_y_en_la_linea_del_centro(self):
        bordes = [(0, 0), (10_000, 10_000), (0, 10_000), (10_000, 0),
                  (5_000, 5_000), (5_000, 0), (0, 5_000), (10_000, 5_000)]
        arbol = Quadtree(datos.caja_mapa(), 1, bordes)       # capacidad 1: se divide mucho
        self.assertEqual(sorted(puntos_guardados(arbol)), sorted(bordes))
        for p in bordes:
            self.assertEqual(arbol.buscar_radio(p, 0), [p])


# ---------------------------------------------------------------------------
# 2. Correctitud: el Quadtree debe dar EXACTAMENTE lo mismo que fuerza bruta
# ---------------------------------------------------------------------------

class PruebasContraFuerzaBruta(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conjuntos = {
            "uniforme": datos.uniformes(config.N),
            "agrupado": datos.agrupados(config.N),
        }
        cls.arboles = {nombre: Quadtree(datos.caja_mapa(), config.CAPACIDAD, pts)
                       for nombre, pts in cls.conjuntos.items()}
        cls.consultas = datos.consultas(config.CONSULTAS_PRUEBA)

    def test_05_radio_500m_igual_a_fuerza_bruta(self):
        for nombre, puntos in self.conjuntos.items():
            arbol = self.arboles[nombre]
            for c in self.consultas:
                with self.subTest(datos=nombre, consulta=c):
                    self.assertTrue(mismos_puntos(arbol.buscar_radio(c, config.RADIO),
                                                  fuerza_bruta_radio(puntos, c, config.RADIO)))

    def test_06_varios_radios_igual_a_fuerza_bruta(self):
        puntos, arbol = self.conjuntos["agrupado"], self.arboles["agrupado"]
        for radio in (10, 100, 1_000, 3_000):
            for c in self.consultas[:60]:
                with self.subTest(radio=radio, consulta=c):
                    self.assertTrue(mismos_puntos(arbol.buscar_radio(c, radio),
                                                  fuerza_bruta_radio(puntos, c, radio)))

    def test_07_vecino_mas_cercano_igual_a_fuerza_bruta(self):
        for nombre, puntos in self.conjuntos.items():
            arbol = self.arboles[nombre]
            for c in self.consultas:
                with self.subTest(datos=nombre, consulta=c):
                    self.assertEqual(arbol.vecino_mas_cercano(c), fuerza_bruta_vecino(puntos, c))

    def test_08_k_vecinos_igual_a_fuerza_bruta(self):
        for nombre, puntos in self.conjuntos.items():
            arbol = self.arboles[nombre]
            for k in (1, 3, 10, 50):
                for c in self.consultas[:60]:
                    with self.subTest(datos=nombre, k=k, consulta=c):
                        self.assertEqual(arbol.k_vecinos(c, k), fuerza_bruta_k_vecinos(puntos, c, k))

    def test_09_distintas_capacidades_dan_el_mismo_resultado(self):
        puntos = datos.uniformes(3_000)
        for capacidad in (1, 4, 16, 64):
            arbol = Quadtree(datos.caja_mapa(), capacidad, puntos)
            for c in self.consultas[:40]:
                with self.subTest(capacidad=capacidad, consulta=c):
                    self.assertTrue(mismos_puntos(arbol.buscar_radio(c, config.RADIO),
                                                  fuerza_bruta_radio(puntos, c, config.RADIO)))
                    self.assertEqual(arbol.k_vecinos(c, 5), fuerza_bruta_k_vecinos(puntos, c, 5))


# ---------------------------------------------------------------------------
# 3. Casos borde
# ---------------------------------------------------------------------------

class PruebasCasosBorde(unittest.TestCase):

    def test_10_punto_exactamente_en_el_limite_del_radio(self):
        arbol = Quadtree(datos.caja_mapa(), puntos=[(5_500, 5_000), (5_500.001, 5_000), (5_000, 4_500)])
        self.assertEqual(sorted(arbol.buscar_radio((5_000, 5_000), 500)),
                         [(5_000, 4_500), (5_500, 5_000)])        # a 500 m exactos sí entra

    def test_11_radio_cero_y_radio_gigante(self):
        puntos = datos.uniformes(2_000)
        arbol = Quadtree(datos.caja_mapa(), config.CAPACIDAD, puntos)
        self.assertEqual(arbol.buscar_radio(puntos[7], 0), [puntos[7]])   # solo el mismo punto
        self.assertEqual(arbol.buscar_radio((5_000.5, 5_000.5), 0), [])    # donde no hay punto
        self.assertTrue(mismos_puntos(arbol.buscar_radio((5_000, 5_000), 20_000), puntos))

    def test_12_consulta_fuera_del_mapa(self):
        puntos = datos.uniformes(2_000)
        arbol = Quadtree(datos.caja_mapa(), config.CAPACIDAD, puntos)
        for c in [(-3_000, 20_000), (15_000, 5_000), (-1, -1)]:
            with self.subTest(consulta=c):
                self.assertEqual(arbol.vecino_mas_cercano(c), fuerza_bruta_vecino(puntos, c))
                self.assertEqual(arbol.k_vecinos(c, 4), fuerza_bruta_k_vecinos(puntos, c, 4))
                self.assertTrue(mismos_puntos(arbol.buscar_radio(c, 3_000),
                                              fuerza_bruta_radio(puntos, c, 3_000)))

    def test_13_k_mayor_que_n_y_k_cero(self):
        arbol = Quadtree(datos.caja_mapa(), puntos=[(100, 100), (200, 200), (300, 300)])
        self.assertEqual(len(arbol.k_vecinos((0, 0), 10)), 3)
        self.assertEqual(arbol.k_vecinos((0, 0), 0), [])

    def test_14_arbol_vacio(self):
        arbol = Quadtree(datos.caja_mapa())
        self.assertIsNone(arbol.vecino_mas_cercano((5_000, 5_000)))
        self.assertEqual(arbol.k_vecinos((5_000, 5_000), 3), [])
        self.assertEqual(arbol.buscar_radio((5_000, 5_000), 500), [])
        self.assertEqual(arbol.profundidad_maxima(), 0)

    def test_15_puntos_duplicados_no_causan_recursion_infinita(self):
        repetidos = [(3_000.0, 3_000.0)] * 50 + [(7_000.0, 7_000.0)]
        arbol = Quadtree(datos.caja_mapa(), 4, repetidos)
        self.assertEqual(arbol.n, 51)
        self.assertEqual(arbol.profundidad_maxima(), PROFUNDIDAD_MAXIMA)  # se detuvo en el límite
        self.assertEqual(len(arbol.buscar_radio((3_000, 3_000), 0)), 50)
        self.assertEqual(arbol.vecino_mas_cercano((7_000, 7_001)), (1.0, (7_000.0, 7_000.0)))

    def test_16_punto_fuera_del_mapa_se_rechaza(self):
        # Decisión de diseño: rechazar con un error claro. Si se guardara en una caja
        # que no lo contiene, la poda nunca lo encontraría (búsqueda incorrecta).
        arbol = Quadtree(datos.caja_mapa(), puntos=[(1, 1)])
        for p in [(-50, 20_000), (10_000.01, 5), (5, -0.01)]:
            with self.subTest(punto=p):
                with self.assertRaises(ValueError):
                    arbol.insertar(p)
        self.assertEqual(arbol.n, 1)


# ---------------------------------------------------------------------------
# 4. K dimensiones: el mismo código en 3D (octree) y 4D
# ---------------------------------------------------------------------------

class PruebasKDimensiones(unittest.TestCase):

    def test_17_tres_dimensiones_octree(self):
        puntos = datos.uniformes(5_000, k=3)
        arbol = Quadtree(datos.caja_mapa(k=3), config.CAPACIDAD, puntos)
        self.assertEqual(len(arbol.raiz.hijos), 8)                          # 2^3 hijos
        for c in datos.consultas(200, k=3):
            with self.subTest(consulta=c):
                self.assertTrue(mismos_puntos(arbol.buscar_radio(c, 1_000),
                                              fuerza_bruta_radio(puntos, c, 1_000)))
                self.assertEqual(arbol.vecino_mas_cercano(c), fuerza_bruta_vecino(puntos, c))
                self.assertEqual(arbol.k_vecinos(c, 5), fuerza_bruta_k_vecinos(puntos, c, 5))

    def test_18_cuatro_dimensiones(self):
        puntos = datos.uniformes(3_000, k=4)
        arbol = Quadtree(datos.caja_mapa(k=4), config.CAPACIDAD, puntos)
        self.assertEqual(len(arbol.raiz.hijos), 16)                         # 2^4 hijos
        for c in datos.consultas(100, k=4):
            with self.subTest(consulta=c):
                self.assertEqual(arbol.k_vecinos(c, 3), fuerza_bruta_k_vecinos(puntos, c, 3))


# ---------------------------------------------------------------------------
# Verificación visual
# ---------------------------------------------------------------------------

AZUL, NARANJA = "#2a78d6", "#eb6834"          # paleta categórica (consulta / encontrados)
TINTA, GRIS, GRIS_CLARO = "#0b0b0b", "#898781", "#c3c2b7"
RAMPA_PROFUNDIDAD = ["#f3f8fe", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5",
                     "#256abf", "#184f95", "#0d366b"]  # secuencial azul: claro = poco profundo


def _estilo(ax, titulo):
    ax.set_title(titulo, fontsize=10, color=TINTA, loc="left")
    ax.set_xlabel("x (m)", color=GRIS)
    ax.set_ylabel("y (m)", color=GRIS)
    ax.set_aspect("equal")
    ax.tick_params(colors=GRIS, labelsize=8)
    for lado in ax.spines.values():
        lado.set_color(GRIS_CLARO)


def grafica_estructura(plt, ruta):
    """01: hojas del árbol coloreadas por profundidad, uniforme vs agrupado."""
    from matplotlib.collections import PatchCollection
    from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap
    from matplotlib.patches import Rectangle

    casos = {}
    for nombre, pts in (("Uniforme", datos.uniformes(config.N)),
                        ("Agrupado", datos.agrupados(config.N))):
        casos[nombre] = (pts, Quadtree(datos.caja_mapa(), config.CAPACIDAD, pts))
    prof_max = max(a.profundidad_maxima() for _, a in casos.values())
    prof_min = min(h.profundidad for _, a in casos.values() for h in hojas(a.raiz))
    niveles = list(range(prof_min, prof_max + 1))
    cmap = LinearSegmentedColormap.from_list("prof", RAMPA_PROFUNDIDAD, N=len(niveles))
    norma = BoundaryNorm([d - 0.5 for d in niveles + [prof_max + 1]], cmap.N)

    fig, ejes = plt.subplots(1, 2, figsize=(13, 6.4), constrained_layout=True)
    for ax, (nombre, (pts, arbol)) in zip(ejes, casos.items()):
        lista = hojas(arbol.raiz)
        rects = [Rectangle((h.caja.centro[0] - h.caja.semilado, h.caja.centro[1] - h.caja.semilado),
                           2 * h.caja.semilado, 2 * h.caja.semilado) for h in lista]
        col = PatchCollection(rects, cmap=cmap, norm=norma, edgecolor="white", linewidth=0.15)
        col.set_array([h.profundidad for h in lista])
        ax.add_collection(col)
        ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=0.3, color=TINTA, alpha=0.25, linewidths=0)
        ax.set_xlim(0, config.LADO)
        ax.set_ylim(0, config.LADO)
        _estilo(ax, f"{nombre}: {len(pts):,} puntos · {len(lista):,} hojas · "
                    f"profundidad máxima {arbol.profundidad_maxima()}".replace(",", "."))
    barra = fig.colorbar(col, ax=ejes, ticks=niveles, shrink=0.8)
    barra.set_label("profundidad de la hoja (nivel)", color=GRIS)
    fig.suptitle(f"Quadtree con capacidad {config.CAPACIDAD}: las cajas son más pequeñas "
                 "(y el árbol más profundo) donde hay más puntos", fontsize=11, color=TINTA)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return {n: (len(hojas(a.raiz)), a.profundidad_maxima()) for n, (_, a) in casos.items()}


def grafica_radio(plt, puntos, arbol, consulta, ruta):
    """02: círculo de 500 m, puntos dentro/fuera, y hojas revisadas vs descartadas."""
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import Circle, Rectangle

    encontrados = arbol.buscar_radio(consulta, config.RADIO)
    assert mismos_puntos(encontrados, fuerza_bruta_radio(puntos, consulta, config.RADIO))
    dentro = set(encontrados)
    todas = hojas(arbol.raiz)
    # Una hoja se revisa si su caja toca el círculo (sus ancestros, que la contienen, también lo tocan).
    revisadas = [h for h in todas if h.caja.distancia2_minima(consulta) <= config.RADIO ** 2]
    puntos_medidos = sum(len(h.puntos) for h in revisadas)
    ventana = 1_200

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.4), constrained_layout=True)
    fuera = [p for p in puntos if p not in dentro]
    for ax in (ax1, ax2):
        ax.scatter([p[0] for p in fuera], [p[1] for p in fuera], s=6, color=GRIS_CLARO,
                   linewidths=0, label="fuera del radio")
        ax.scatter([p[0] for p in encontrados], [p[1] for p in encontrados], s=14, color=NARANJA,
                   linewidths=0, label=f"dentro del radio ({len(encontrados)})")
        ax.add_patch(Circle(consulta, config.RADIO, fill=False, edgecolor=AZUL, linewidth=1.5,
                            linestyle="--", label="radio de 500 m"))
        ax.scatter(*consulta, marker="X", s=90, color=AZUL, edgecolors="white", linewidths=1,
                   zorder=5, label="consulta")
        ax.set_xlim(consulta[0] - ventana, consulta[0] + ventana)
        ax.set_ylim(consulta[1] - ventana, consulta[1] + ventana)
    _estilo(ax1, f"Búsqueda por radio desde ({consulta[0]:.0f}, {consulta[1]:.0f}) m: "
                 f"{len(encontrados)} puntos (= fuerza bruta)")
    ax1.legend(loc="upper right", fontsize=8, framealpha=0.9)

    def cajas(lista):
        return [Rectangle((h.caja.centro[0] - h.caja.semilado, h.caja.centro[1] - h.caja.semilado),
                          2 * h.caja.semilado, 2 * h.caja.semilado) for h in lista]
    conjunto_revisadas = set(revisadas)
    descartadas = [h for h in todas if h not in conjunto_revisadas]
    ax2.add_collection(PatchCollection(cajas(descartadas), facecolor="none", edgecolor=GRIS_CLARO,
                                       linewidth=0.5))
    ax2.add_collection(PatchCollection(cajas(revisadas), facecolor=AZUL, alpha=0.12,
                                       edgecolor=AZUL, linewidth=1.0))
    ax2.plot([], [], color=AZUL, linewidth=6, alpha=0.3, label=f"hojas revisadas ({len(revisadas)})")
    ax2.plot([], [], color=GRIS_CLARO, linewidth=1, label=f"hojas descartadas ({len(todas) - len(revisadas):,})".replace(",", "."))
    _estilo(ax2, f"Poda: se revisan {len(revisadas)} de {len(todas):,} hojas → se miden "
                 f"{puntos_medidos} de {len(puntos):,} puntos".replace(",", "."))
    ax2.legend(loc="upper right", fontsize=8, framealpha=0.9)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return len(encontrados), len(revisadas), len(todas), puntos_medidos


def grafica_vecinos(plt, puntos, arbol, consulta, k, ruta):
    """03: vecino más cercano y k vecinos, verificados contra fuerza bruta."""
    from matplotlib.patches import Circle

    vecinos = arbol.k_vecinos(consulta, k)
    assert vecinos == fuerza_bruta_k_vecinos(puntos, consulta, k)
    assert vecinos[0] == fuerza_bruta_vecino(puntos, consulta)
    radio_k = vecinos[-1][0]
    ventana = max(250, radio_k * 1.6)

    fig, ax = plt.subplots(figsize=(7.4, 7.2), constrained_layout=True)
    ax.scatter([p[0] for p in puntos], [p[1] for p in puntos], s=6, color=GRIS_CLARO, linewidths=0,
               label="puntos de entrega")
    ax.add_patch(Circle(consulta, radio_k, fill=False, edgecolor=AZUL, linestyle="--", linewidth=1.2,
                        label=f"círculo hasta el {k}.º vecino ({radio_k:.1f} m)"))
    for i, (d, p) in enumerate(vecinos, start=1):
        ax.plot([consulta[0], p[0]], [consulta[1], p[1]], color=NARANJA if i == 1 else GRIS,
                linewidth=2 if i == 1 else 0.8, zorder=3)
        ax.annotate(f"{i}: {d:.1f} m", p, textcoords="offset points", xytext=(5, 5),
                    fontsize=8, color=TINTA)
    ax.scatter([p[0] for _, p in vecinos[1:]], [p[1] for _, p in vecinos[1:]], s=30, color=GRIS,
               zorder=4, label=f"vecinos 2 a {k}")
    ax.scatter(*vecinos[0][1], s=60, color=NARANJA, zorder=4, label="vecino más cercano")
    ax.scatter(*consulta, marker="X", s=90, color=AZUL, edgecolors="white", linewidths=1, zorder=5,
               label="consulta")
    ax.set_xlim(consulta[0] - ventana, consulta[0] + ventana)
    ax.set_ylim(consulta[1] - ventana, consulta[1] + ventana)
    _estilo(ax, f"{k} vecinos más cercanos a ({consulta[0]:.0f}, {consulta[1]:.0f}) m\n"
                "idénticos a fuerza bruta (puntos y distancias)")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return vecinos


def generar_graficas():
    import matplotlib
    matplotlib.use("Agg")                     # solo guarda archivos, no abre ventanas
    import matplotlib.pyplot as plt

    os.makedirs(config.CARPETA_GRAFICAS, exist_ok=True)
    puntos = datos.uniformes(config.N)
    arbol = Quadtree(datos.caja_mapa(), config.CAPACIDAD, puntos)
    copia = list(puntos)
    antes = arbol.buscar_radio((5_000, 5_000), config.RADIO)

    ruta = lambda nombre: os.path.join(config.CARPETA_GRAFICAS, nombre)
    estructura = grafica_estructura(plt, ruta("01_estructura_uniforme_vs_agrupado.png"))
    radio = grafica_radio(plt, puntos, arbol, (5_000, 5_000), ruta("02_busqueda_radio.png"))
    vecinos = grafica_vecinos(plt, puntos, arbol, (1_234, 5_678), 5, ruta("03_vecinos_mas_cercanos.png"))

    # Verificar que graficar no modificó los datos ni el árbol
    assert puntos == copia, "graficar modificó la lista de puntos"
    assert arbol.buscar_radio((5_000, 5_000), config.RADIO) == antes, "graficar modificó el árbol"
    return estructura, radio, vecinos


if __name__ == "__main__":
    programa = unittest.main(exit=False, verbosity=2)
    resultado = programa.result
    if not resultado.wasSuccessful():
        sys.exit(1)

    estructura, radio, vecinos = generar_graficas()
    n_enc, n_rev, n_hojas, medidos = radio
    print("\n=== Análisis de las pruebas ===")
    print(f"Pruebas: {resultado.testsRun} ejecutadas, todas correctas.")
    print(f"Cada búsqueda se comparó con fuerza bruta ({config.CONSULTAS_PRUEBA} consultas por "
          "conjunto, datos uniformes y agrupados, 2D, 3D y 4D): resultados idénticos.")
    for nombre, (h, p) in estructura.items():
        print(f"Estructura {nombre.lower():9s}: {h:5d} hojas, profundidad máxima {p}")
    print(f"Radio 500 m desde (5000, 5000): {n_enc} puntos; se revisaron {n_rev} de {n_hojas} hojas "
          f"y se midieron {medidos} de {config.N} puntos ({100 * medidos / config.N:.1f} %).")
    print(f"Vecino más cercano a (1234, 5678): {vecinos[0][0]:.2f} m; 5.º vecino a {vecinos[-1][0]:.2f} m.")
    print("Graficar no modificó los datos (verificado). Gráficas en", config.CARPETA_GRAFICAS)
