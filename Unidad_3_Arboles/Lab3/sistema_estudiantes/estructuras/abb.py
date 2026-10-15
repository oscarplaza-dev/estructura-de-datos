"""
Estrategia 2: ÁRBOL BINARIO DE BÚSQUEDA (ABB), sin balanceo.

Regla: en cada nodo, los IDs menores van a la izquierda y los mayores a la
derecha. Cada nodo guarda el estudiante completo.

    insertar -> bajar comparando hasta un espacio vacío ... O(h)
    buscar   -> bajar comparando .......................... O(h)
    listar   -> recorrido in-orden (izq, raíz, der) ....... O(N)

h = altura del árbol:
  * IDs aleatorios -> h crece como log2(N)  (≈ 2.5–3 · log2 N en la práctica)
  * IDs ordenados  -> cada nodo nuevo cae siempre a la derecha, h = N
                      ("una lista enlazada disfrazada")

Todo se hace de forma ITERATIVA (con ciclos y una lista de Python como pila).
Con IDs ordenados el árbol puede tener miles de niveles y la recursión de
Python se desbordaría (límite ≈ 1000 llamadas).
"""


class _Nodo:
    __slots__ = ("clave", "estudiante", "izquierdo", "derecho")

    def __init__(self, estudiante):
        self.clave = estudiante.id
        self.estudiante = estudiante
        self.izquierdo = None
        self.derecho = None


class ArbolBinarioBusqueda:
    nombre = "ABB"

    def __init__(self):
        self.raiz = None
        self._cantidad = 0

    def __len__(self):
        return self._cantidad

    # --- Operación 2: insertar --------------------------------------------
    def insertar(self, estudiante):
        nuevo = _Nodo(estudiante)
        if self.raiz is None:
            self.raiz = nuevo
            self._cantidad = 1
            return

        actual = self.raiz
        while True:
            if nuevo.clave < actual.clave:
                if actual.izquierdo is None:
                    actual.izquierdo = nuevo
                    break
                actual = actual.izquierdo
            elif nuevo.clave > actual.clave:
                if actual.derecho is None:
                    actual.derecho = nuevo
                    break
                actual = actual.derecho
            else:                        # ID repetido: se actualiza el registro
                actual.estudiante = estudiante
                return
        self._cantidad += 1

    # --- Operación 1: buscar por ID ---------------------------------------
    def buscar(self, id_buscado):
        actual = self.raiz
        while actual is not None:
            if id_buscado == actual.clave:
                return actual.estudiante
            actual = actual.izquierdo if id_buscado < actual.clave else actual.derecho
        return None

    # --- Operación 3: listar en orden ascendente de ID ---------------------
    def listar(self):
        """Recorrido in-orden iterativo. La pila es una lista de Python."""
        resultado = []
        pila = []
        actual = self.raiz
        while pila or actual is not None:
            while actual is not None:        # bajar todo a la izquierda
                pila.append(actual)
                actual = actual.izquierdo
            actual = pila.pop()
            resultado.append(actual.estudiante)
            actual = actual.derecho
        return resultado

    # --- Instrumentación ---------------------------------------------------
    def costo_busqueda(self, id_buscado):
        """Cuántos nodos se visitan para encontrar `id_buscado`."""
        visitados = 0
        actual = self.raiz
        while actual is not None:
            visitados += 1
            if id_buscado == actual.clave:
                break
            actual = actual.izquierdo if id_buscado < actual.clave else actual.derecho
        return visitados

    def altura(self):
        """Número de niveles (un árbol con solo la raíz tiene altura 1)."""
        if self.raiz is None:
            return 0
        niveles = 0
        nivel_actual = [self.raiz]           # recorrido por niveles con listas
        while nivel_actual:
            niveles += 1
            siguiente = []
            for nodo in nivel_actual:
                if nodo.izquierdo is not None:
                    siguiente.append(nodo.izquierdo)
                if nodo.derecho is not None:
                    siguiente.append(nodo.derecho)
            nivel_actual = siguiente
        return niveles
