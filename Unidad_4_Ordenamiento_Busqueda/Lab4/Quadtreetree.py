"""
Quadtreetree.py — Quadtree PR (point-region) por buckets, en K dimensiones.

Autor: Oscar Alberto Plaza — Estructuras de Datos (UdeA), Laboratorio 4.

Fuentes (consultadas en noviembre de 2026):
  [1] Wikipedia, "Quadtree", secciones "Point-region (PR) quadtree" y "Pseudocode".
      https://en.wikipedia.org/wiki/Quadtree
  [2] Wikipedia, "K-d tree", sección "Nearest neighbour search".
      https://en.wikipedia.org/wiki/K-d_tree
  [3] Wikipedia, "Octree". https://en.wikipedia.org/wiki/Octree

Qué viene de la fuente y qué es adaptación mía:
  - Caja (centro + semilado) y contiene(): AABB y containsPoint de [1].
  - Nodo con capacidad, lista de puntos, hijos y subdividir(): QT_NODE_CAPACITY
    y subdivide de [1].
  - insertar(): insert de [1]. Adaptaciones mías: al subdividir reparto los puntos
    entre los hijos (solo las hojas guardan puntos); elijo el hijo comparando con
    el centro; un punto fuera del mapa lanza ValueError en vez de ignorarse; y
    PROFUNDIDAD_MAXIMA evita la recursión infinita con puntos repetidos.
  - 2^K hijos con una clave de K valores True/False (un bit por dimensión):
    adaptación mía; [3] solo describe los 8 hijos del caso 3D.
  - buscar_radio(): queryRange de [1]. Adaptación mía: el rango es un círculo y
    "¿el rango toca la caja?" se responde con distancia2_minima.
  - buscar_vecinos() / k_vecinos(): vecino más cercano y extensión a k vecinos
    de [2], adaptados a las cajas del quadtree; visito primero el hijo más cercano.
  - Distancias al cuadrado para no calcular raíces: [2].
  - Funciones de fuerza bruta: referencia sin árbol pedida por el enunciado.
"""

from itertools import product

PROFUNDIDAD_MAXIMA = 20


def distancia2(a, b):
    total = 0.0
    for x, y in zip(a, b):
        total += (x - y) * (x - y)
    return total


class Caja:
    def __init__(self, centro, semilado):
        self.centro = tuple(centro)
        self.semilado = semilado

    def contiene(self, punto):
        for c, p in zip(self.centro, punto):
            if p < c - self.semilado or p > c + self.semilado:
                return False
        return True

    def distancia2_minima(self, punto):
        total = 0.0
        for c, p in zip(self.centro, punto):
            exceso = abs(p - c) - self.semilado
            if exceso > 0:
                total += exceso * exceso
        return total


class Nodo:
    def __init__(self, caja, capacidad, profundidad=0):
        self.caja = caja
        self.capacidad = capacidad
        self.profundidad = profundidad
        self.puntos = []
        self.hijos = None

    def es_hoja(self):
        return self.hijos is None

    def subdividir(self):
        mitad = self.caja.semilado / 2
        k = len(self.caja.centro)
        self.hijos = {}
        for lados in product((False, True), repeat=k):
            centro_hijo = []
            for c, alto in zip(self.caja.centro, lados):
                if alto:
                    centro_hijo.append(c + mitad)
                else:
                    centro_hijo.append(c - mitad)
            self.hijos[lados] = Nodo(Caja(centro_hijo, mitad), self.capacidad, self.profundidad + 1)

    def hijo_para(self, punto):
        lados = tuple(p >= c for c, p in zip(self.caja.centro, punto))
        return self.hijos[lados]

    def insertar(self, punto):
        if not self.es_hoja():
            self.hijo_para(punto).insertar(punto)
            return
        self.puntos.append(punto)
        if len(self.puntos) > self.capacidad and self.profundidad < PROFUNDIDAD_MAXIMA:
            self.subdividir()
            for p in self.puntos:
                self.hijo_para(p).insertar(p)
            self.puntos = []

    def profundidad_maxima(self):
        if self.es_hoja():
            return self.profundidad
        return max(hijo.profundidad_maxima() for hijo in self.hijos.values())

    def buscar_radio(self, consulta, radio2, encontrados):
        if self.caja.distancia2_minima(consulta) > radio2:
            return
        if self.es_hoja():
            for p in self.puntos:
                if distancia2(p, consulta) <= radio2:
                    encontrados.append(p)
        else:
            for hijo in self.hijos.values():
                hijo.buscar_radio(consulta, radio2, encontrados)

    def buscar_vecinos(self, consulta, k, mejores):
        if len(mejores) == k and self.caja.distancia2_minima(consulta) > mejores[-1][0]:
            return
        if self.es_hoja():
            for p in self.puntos:
                candidato = (distancia2(p, consulta), p)
                if len(mejores) < k or candidato < mejores[-1]:
                    mejores.append(candidato)
                    mejores.sort()
                    del mejores[k:]
        else:
            hijos = sorted(self.hijos.values(), key=lambda h: h.caja.distancia2_minima(consulta))
            for hijo in hijos:
                hijo.buscar_vecinos(consulta, k, mejores)


class Quadtree:
    def __init__(self, caja, capacidad=4, puntos=()):
        self.raiz = Nodo(caja, capacidad)
        self.n = 0
        for p in puntos:
            self.insertar(p)

    def insertar(self, punto):
        if not self.raiz.caja.contiene(punto):
            raise ValueError(f"El punto {punto} está fuera del mapa")
        self.raiz.insertar(tuple(punto))
        self.n += 1

    def profundidad_maxima(self):
        return self.raiz.profundidad_maxima()

    def buscar_radio(self, consulta, radio):
        encontrados = []
        self.raiz.buscar_radio(tuple(consulta), radio * radio, encontrados)
        return encontrados

    def k_vecinos(self, consulta, k):
        mejores = []
        if k > 0:
            self.raiz.buscar_vecinos(tuple(consulta), k, mejores)
        return [(d2 ** 0.5, p) for d2, p in mejores]

    def vecino_mas_cercano(self, consulta):
        vecinos = self.k_vecinos(consulta, 1)
        if not vecinos:
            return None
        return vecinos[0]


def fuerza_bruta_radio(puntos, consulta, radio):
    radio2 = radio * radio
    return [p for p in puntos if distancia2(p, consulta) <= radio2]


def fuerza_bruta_vecino(puntos, consulta):
    if not puntos:
        return None
    d2, p = min((distancia2(p, consulta), p) for p in puntos)
    return (d2 ** 0.5, p)


def fuerza_bruta_k_vecinos(puntos, consulta, k):
    todos = sorted((distancia2(p, consulta), p) for p in puntos)
    return [(d2 ** 0.5, p) for d2, p in todos[:k]]


if __name__ == "__main__":
    import random

    rng = random.Random(4)
    puntos = [(rng.uniform(0, 10000), rng.uniform(0, 10000)) for _ in range(10000)]
    arbol = Quadtree(Caja((5000, 5000), 5000), capacidad=4, puntos=puntos)

    print("vecino más cercano:", arbol.vecino_mas_cercano((1234, 5678)))
    print("fuerza bruta:      ", fuerza_bruta_vecino(puntos, (1234, 5678)))
    for d, p in arbol.k_vecinos((1234, 5678), 5):
        print(f"  {d:8.2f} m  {p}")

    iguales = 0
    for _ in range(200):
        c = (rng.uniform(0, 10000), rng.uniform(0, 10000))
        if (arbol.vecino_mas_cercano(c) == fuerza_bruta_vecino(puntos, c)
                and arbol.k_vecinos(c, 5) == fuerza_bruta_k_vecinos(puntos, c, 5)):
            iguales += 1
    print("consultas aleatorias iguales (1 y 5 vecinos):", iguales, "de 200")

    pocos = Quadtree(Caja((5000, 5000), 5000), puntos=[(100, 100), (200, 200), (300, 300)])
    print("k = 10 con 3 puntos:", len(pocos.k_vecinos((0, 0), 10)))
    print("árbol vacío:", Quadtree(Caja((5000, 5000), 5000)).vecino_mas_cercano((5000, 5000)))
    print("consulta fuera del mapa:", arbol.vecino_mas_cercano((-3000, 20000)) == fuerza_bruta_vecino(puntos, (-3000, 20000)))