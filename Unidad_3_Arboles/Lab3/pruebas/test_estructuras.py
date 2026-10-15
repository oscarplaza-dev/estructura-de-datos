"""
Pruebas de corrección: antes de medir tiempos hay que estar seguros de que las
tres estructuras devuelven lo mismo y lo correcto.

Ejecutar desde la carpeta Lab3:   python -m unittest discover -s pruebas -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sistema_estudiantes.modelo import Estudiante, generar_estudiantes, nuevo_generador
from sistema_estudiantes.estructuras import ListaPython, ArbolBinarioBusqueda, ArbolBMas
from sistema_estudiantes.estructuras.arbol_bmas import _Interno


def construir(clase, estudiantes, **kw):
    e = clase(**kw)
    for est in estudiantes:
        e.insertar(est)
    return e


class PruebasComunes(unittest.TestCase):
    """Las tres estructuras deben comportarse igual que un dict + sorted."""

    def revisar(self, orden_datos, n, **kw_bmas):
        rng = nuevo_generador(7)
        datos = generar_estudiantes(n, rng, orden_datos)
        referencia = {e.id: e for e in datos}
        esperado = sorted(datos, key=lambda e: e.id)

        for clase, kw in ((ListaPython, {}), (ArbolBinarioBusqueda, {}), (ArbolBMas, kw_bmas)):
            with self.subTest(estructura=clase.__name__, datos=orden_datos, n=n, **kw):
                e = construir(clase, datos, **kw)
                self.assertEqual(len(e), n)
                # buscar: todos los existentes
                for id_ in referencia:
                    self.assertIs(e.buscar(id_), referencia[id_])
                # buscar: IDs que no existen
                for id_ in (0, 999_999, 10_000_001, datos[0].id + 1 if datos[0].id + 1 not in referencia else -5):
                    self.assertIsNone(e.buscar(id_))
                # listar: orden ascendente y completo
                self.assertEqual(e.listar(), esperado)

    def test_aleatorio(self):
        for n in (1, 2, 10, 500, 3000):
            self.revisar("aleatorio", n)

    def test_ordenado(self):
        for n in (1, 2, 10, 500, 3000):
            self.revisar("ordenado", n)

    def test_bmas_varios_ordenes(self):
        for orden in (3, 4, 5, 16, 128):
            self.revisar("aleatorio", 2000, orden=orden)
            self.revisar("ordenado", 2000, orden=orden)


class PruebasAltura(unittest.TestCase):

    def test_abb_ordenado_degenera(self):
        datos = generar_estudiantes(300, nuevo_generador(1), "ordenado")
        abb = construir(ArbolBinarioBusqueda, datos)
        self.assertEqual(abb.altura(), 300)        # es una "lista" de 300 niveles

    def test_abb_aleatorio_es_bajo(self):
        datos = generar_estudiantes(4096, nuevo_generador(1), "aleatorio")
        abb = construir(ArbolBinarioBusqueda, datos)
        self.assertLess(abb.altura(), 4 * 12)      # muy lejos de 4096

    def test_bmas_hojas_mismo_nivel_y_ordenado(self):
        for orden_datos in ("aleatorio", "ordenado"):
            datos = generar_estudiantes(5000, nuevo_generador(3), orden_datos)
            arbol = construir(ArbolBMas, datos, orden=4)
            profundidades = set()

            def recorrer(nodo, nivel, minimo, maximo):
                self.assertEqual(nodo.claves, sorted(nodo.claves))
                self.assertLessEqual(len(nodo.claves), arbol.max_claves)
                for c in nodo.claves:
                    self.assertTrue(minimo <= c < maximo)
                if type(nodo) is _Interno:
                    self.assertEqual(len(nodo.hijos), len(nodo.claves) + 1)
                    limites = [minimo] + nodo.claves + [maximo]
                    for i, hijo in enumerate(nodo.hijos):
                        recorrer(hijo, nivel + 1, limites[i], limites[i + 1])
                else:
                    profundidades.add(nivel)

            recorrer(arbol.raiz, 1, float("-inf"), float("inf"))
            self.assertEqual(len(profundidades), 1)              # todas al mismo nivel
            self.assertEqual(profundidades.pop(), arbol.altura())

    def test_rango_bmas(self):
        datos = generar_estudiantes(3000, nuevo_generador(5), "aleatorio")
        arbol = construir(ArbolBMas, datos, orden=8)
        ids = sorted(e.id for e in datos)
        desde, hasta = ids[100], ids[250]
        self.assertEqual([e.id for e in arbol.listar_rango(desde, hasta)], ids[100:251])


class PruebaDuplicados(unittest.TestCase):

    def test_arboles_actualizan_duplicado(self):
        a = Estudiante(5, "A", 20, 3.0)
        b = Estudiante(5, "B", 21, 4.0)
        for clase in (ArbolBinarioBusqueda, ArbolBMas):
            e = construir(clase, [a, b])
            self.assertEqual(len(e), 1)
            self.assertIs(e.buscar(5), b)


if __name__ == "__main__":
    unittest.main()
