"""
Estrategia 3: ÁRBOL B+.

Idea (como la vimos en clase):
  * Nodos INTERNOS: solo guardan claves "guía" y punteros a hijos. Son el mapa
    de navegación; no guardan estudiantes.
  * HOJAS: guardan las claves y los estudiantes. Todas están al mismo nivel y
    están ENLAZADAS de izquierda a derecha (la "autopista" de las hojas).
  * Cada nodo tiene hasta `orden` hijos (orden - 1 claves). Cuando un nodo se
    llena, se parte en dos y una clave sube al padre. Si la raíz se parte, el
    árbol crece hacia ARRIBA, por eso nunca se desbalancea.

Las claves, los hijos y los registros de cada nodo son LISTAS de Python que se
mantienen ordenadas. Para ubicar una clave dentro de un nodo se usa búsqueda
binaria (`bisect`, de la librería estándar), que trabaja sobre esas listas.

    insertar -> bajar hasta la hoja + insertar ordenado (+ partir si se llena)  O(log N)
    buscar   -> bajar por la altura del árbol ................................. O(log N)
    listar   -> ir a la hoja más a la izquierda y caminar por los enlaces ..... O(N)

Convención de las claves guía de un nodo interno con claves [k1, k2, ...]:
    hijo 0 : IDs <  k1
    hijo 1 : k1 <= IDs < k2      ... y así sucesivamente.
"""

from bisect import bisect_left, bisect_right


class _Hoja:
    __slots__ = ("claves", "registros", "siguiente")

    def __init__(self, claves=None, registros=None, siguiente=None):
        self.claves = claves if claves is not None else []        # IDs ordenados
        self.registros = registros if registros is not None else []  # estudiantes
        self.siguiente = siguiente                                 # hoja de la derecha


class _Interno:
    __slots__ = ("claves", "hijos")

    def __init__(self, claves, hijos):
        self.claves = claves      # claves guía (lista de Python)
        self.hijos = hijos        # len(hijos) == len(claves) + 1


class ArbolBMas:
    nombre = "B+"

    def __init__(self, orden=32):
        if orden < 3:
            raise ValueError("El orden de un árbol B+ debe ser al menos 3")
        self.orden = orden
        self.max_claves = orden - 1
        self.raiz = _Hoja()
        self._cantidad = 0

    def __len__(self):
        return self._cantidad

    # --- Navegación común --------------------------------------------------
    def _bajar_hasta_hoja(self, id_buscado, camino=None):
        """Baja desde la raíz hasta la hoja donde debe estar `id_buscado`.
        Si se pasa `camino` (lista), guarda (nodo_interno, posición_hijo)."""
        nodo = self.raiz
        while type(nodo) is _Interno:
            posicion = bisect_right(nodo.claves, id_buscado)
            if camino is not None:
                camino.append((nodo, posicion))
            nodo = nodo.hijos[posicion]
        return nodo

    # --- Operación 1: buscar por ID ---------------------------------------
    def buscar(self, id_buscado):
        hoja = self._bajar_hasta_hoja(id_buscado)
        i = bisect_left(hoja.claves, id_buscado)
        if i < len(hoja.claves) and hoja.claves[i] == id_buscado:
            return hoja.registros[i]
        return None

    # --- Operación 2: insertar --------------------------------------------
    def insertar(self, estudiante):
        clave = estudiante.id
        camino = []                                   # pila de padres
        hoja = self._bajar_hasta_hoja(clave, camino)

        i = bisect_left(hoja.claves, clave)
        if i < len(hoja.claves) and hoja.claves[i] == clave:   # ID repetido
            hoja.registros[i] = estudiante
            return
        hoja.claves.insert(i, clave)
        hoja.registros.insert(i, estudiante)
        self._cantidad += 1

        if len(hoja.claves) <= self.max_claves:
            return                                    # cabe: terminamos

        # 1) La hoja se desbordó: partirla en dos mitades.
        mitad = len(hoja.claves) // 2
        nueva = _Hoja(hoja.claves[mitad:], hoja.registros[mitad:], hoja.siguiente)
        del hoja.claves[mitad:]
        del hoja.registros[mitad:]
        hoja.siguiente = nueva                        # mantener la autopista
        clave_que_sube = nueva.claves[0]              # en B+ se COPIA hacia arriba
        izquierdo, derecho = hoja, nueva

        # 2) Subir la clave a los padres; partir los que se desborden.
        while camino:
            padre, posicion = camino.pop()
            padre.claves.insert(posicion, clave_que_sube)
            padre.hijos.insert(posicion + 1, derecho)
            if len(padre.claves) <= self.max_claves:
                return
            mitad = len(padre.claves) // 2
            clave_que_sube = padre.claves[mitad]      # en internos se MUEVE hacia arriba
            nuevo = _Interno(padre.claves[mitad + 1:], padre.hijos[mitad + 1:])
            del padre.claves[mitad:]
            del padre.hijos[mitad + 1:]
            izquierdo, derecho = padre, nuevo

        # 3) Se partió la raíz: el árbol crece un nivel hacia arriba.
        self.raiz = _Interno([clave_que_sube], [izquierdo, derecho])

    # --- Operación 3: listar en orden ascendente de ID ---------------------
    def listar(self):
        resultado = []
        hoja = self._hoja_mas_izquierda()
        while hoja is not None:                       # caminar por la autopista
            resultado.extend(hoja.registros)
            hoja = hoja.siguiente
        return resultado

    def listar_rango(self, id_desde, id_hasta):
        """Bonus: estudiantes con ID en [id_desde, id_hasta] (consulta por rango)."""
        resultado = []
        hoja = self._bajar_hasta_hoja(id_desde)
        i = bisect_left(hoja.claves, id_desde)
        while hoja is not None:
            while i < len(hoja.claves):
                if hoja.claves[i] > id_hasta:
                    return resultado
                resultado.append(hoja.registros[i])
                i += 1
            hoja, i = hoja.siguiente, 0
        return resultado

    def _hoja_mas_izquierda(self):
        nodo = self.raiz
        while type(nodo) is _Interno:
            nodo = nodo.hijos[0]
        return nodo

    # --- Instrumentación ---------------------------------------------------
    def costo_busqueda(self, id_buscado):
        """Nodos visitados en una búsqueda = altura (todas las hojas al mismo nivel)."""
        return self.altura()

    def altura(self):
        niveles = 1
        nodo = self.raiz
        while type(nodo) is _Interno:
            nodo = nodo.hijos[0]
            niveles += 1
        return niveles

    def ocupacion_hojas(self):
        """Porcentaje promedio de llenado de las hojas (100 % = hojas llenas)."""
        hojas, claves = 0, 0
        hoja = self._hoja_mas_izquierda()
        while hoja is not None:
            hojas += 1
            claves += len(hoja.claves)
            hoja = hoja.siguiente
        return 100.0 * claves / (hojas * self.max_claves)
