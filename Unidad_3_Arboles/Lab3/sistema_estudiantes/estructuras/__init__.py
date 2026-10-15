"""Las tres estrategias de almacenamiento y búsqueda. Todas tienen la misma
interfaz: insertar(estudiante), buscar(id), listar(), altura(), costo_busqueda(id)."""

from .lista import ListaPython
from .abb import ArbolBinarioBusqueda
from .arbol_bmas import ArbolBMas

__all__ = ["ListaPython", "ArbolBinarioBusqueda", "ArbolBMas"]
