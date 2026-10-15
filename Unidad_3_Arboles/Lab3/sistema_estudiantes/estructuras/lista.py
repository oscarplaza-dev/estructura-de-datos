"""
Estrategia 1: LISTA de Python (el objeto `list` que trae el lenguaje).

Siguiendo la indicación del profesor, aquí no se construye una lista enlazada
"artesanal": se usa la lista nativa de Python, que es la estructura más simple
que ya ofrece el lenguaje (internamente es un arreglo dinámico escrito en C).

    insertar -> append al final .................. O(1) amortizado
    buscar   -> recorrido secuencial ............. O(N)  (en promedio revisa N/2)
    listar   -> sorted(...) por ID ............... O(N log N)
"""


class ListaPython:
    nombre = "Lista"

    def __init__(self):
        self._datos = []          # list de Python con objetos Estudiante

    def __len__(self):
        return len(self._datos)

    # --- Operación 2: insertar --------------------------------------------
    def insertar(self, estudiante):
        # Los IDs son únicos por construcción (ver modelo.py). Verificar
        # duplicados aquí haría que cada inserción costara O(N).
        self._datos.append(estudiante)

    # --- Operación 1: buscar por ID ---------------------------------------
    def buscar(self, id_buscado):
        for estudiante in self._datos:        # uno por uno, desde el inicio
            if estudiante.id == id_buscado:
                return estudiante
        return None

    # --- Operación 3: listar en orden ascendente de ID ---------------------
    def listar(self):
        # La lista guarda en orden de llegada, así que hay que ordenar.
        return sorted(self._datos, key=lambda e: e.id)

    # --- Instrumentación (solo para el análisis, no se cronometra) --------
    def costo_busqueda(self, id_buscado):
        """Cuántos elementos se revisan para encontrar `id_buscado`."""
        for posicion, estudiante in enumerate(self._datos, start=1):
            if estudiante.id == id_buscado:
                return posicion
        return len(self._datos)

    def altura(self):
        return None               # una lista no tiene altura
