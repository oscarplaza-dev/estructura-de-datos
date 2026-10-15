"""
El "modelo" del problema: qué es un estudiante y cómo se generan los datos.

Aquí NO hay estructuras de datos ni mediciones; solo:
  * la clase Estudiante (el registro que guardamos),
  * el generador de estudiantes (IDs únicos, en orden aleatorio u ordenado),
  * el generador de búsquedas (los M IDs que se van a buscar).
"""

from dataclasses import dataclass
import random

NOMBRES = ["Ana", "Carlos", "María", "Juan", "Laura", "Pedro", "Sofía", "Luis",
           "Valentina", "Andrés", "Camila", "Diego", "Isabella", "Mateo"]
APELLIDOS = ["García", "Rodríguez", "Martínez", "Hernández", "López", "González",
             "Pérez", "Sánchez", "Ramírez", "Torres", "Restrepo", "Gómez"]

# Rango de los números de matrícula. Es mucho más grande que el número de
# estudiantes, así los IDs quedan "salteados" como en la vida real.
ID_MIN = 1_000_000
ID_MAX = 9_999_999


@dataclass(frozen=True, slots=True)
class Estudiante:
    """Un registro: ID (clave de búsqueda), nombre, edad y promedio."""
    id: int
    nombre: str
    edad: int
    promedio: float

    def __str__(self):
        return (f"ID {self.id} | {self.nombre:<22} | edad {self.edad:>2} | "
                f"promedio {self.promedio:.2f}")


def generar_estudiantes(n, rng, orden="aleatorio"):
    """
    Devuelve una lista de Python con `n` estudiantes de IDs únicos.

    orden = "aleatorio": los IDs llegan en cualquier orden (caso típico).
    orden = "ordenado" : los IDs llegan de menor a mayor (peor caso del ABB).
    """
    ids = rng.sample(range(ID_MIN, ID_MAX + 1), n)   # sin repetir
    if orden == "ordenado":
        ids.sort()
    elif orden != "aleatorio":
        raise ValueError("orden debe ser 'aleatorio' u 'ordenado'")

    return [
        Estudiante(
            id=i,
            nombre=f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)}",
            edad=rng.randint(16, 30),
            promedio=round(rng.uniform(0.0, 5.0), 2),
        )
        for i in ids
    ]


def generar_busquedas(estudiantes, m, rng):
    """
    Devuelve M IDs a buscar, tomados al azar entre los estudiantes que existen.
    Se toman con reemplazo, así M puede ser mayor que N.
    Todas las estructuras reciben exactamente la misma lista de búsquedas.
    """
    return [rng.choice(estudiantes).id for _ in range(m)]


def nuevo_generador(semilla):
    """Generador aleatorio propio (no global) para que todo sea reproducible."""
    return random.Random(semilla)
