"""
TODOS los parámetros del experimento en un solo lugar.

Si alguien quiere repetir el estudio, solo necesita mirar este archivo.
Hay dos perfiles:
  * COMPLETO: el que se usó para las gráficas del repositorio (≈ 20 min).
  * RAPIDO  : prueba de humo para verificar que todo corre (≈ 1 min).
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Configuracion:
    nombre: str
    semilla: int = 2026
    repeticiones: int = 10            # ejecuciones independientes por punto

    # --- Experimento A: búsqueda vs N (tamaño de la base de datos) ---------
    # Potencias de 4 (y 2 al final): cubren desde 16 hasta 131 072
    # estudiantes, cuatro órdenes de magnitud, con puntos parejos en escala log.
    n_aleatorio: tuple = (16, 64, 256, 1_024, 4_096, 16_384, 65_536, 131_072)
    # Con IDs ordenados el ABB se vuelve una lista: construirlo cuesta N²/2
    # comparaciones (16 384 estudiantes ≈ 10 s por construcción). Por eso
    # este caso se detiene en 16 384: ya ahí la degeneración es evidente.
    n_ordenado: tuple = (16, 64, 256, 1_024, 2_048, 4_096, 8_192, 16_384)
    m_fijo: int = 1_000               # búsquedas por lote

    # --- Experimento B: búsqueda vs M (cantidad de búsquedas) -------------
    n_fijo: int = 10_000              # el tamaño del enunciado original
    m_valores: tuple = (100, 200, 400, 800, 1_600, 3_200, 6_400, 12_800, 25_600)

    # --- Experimento C: efecto del orden del árbol B+ ----------------------
    n_orden_bmas: int = 65_536
    ordenes_bmas: tuple = (4, 8, 16, 32, 64, 128, 256)
    orden_bmas: int = 32              # orden usado en los experimentos A y B

    # --- Medición -----------------------------------------------------------
    # Regla del profesor: no medir ventanas de milisegundos (el ruido del
    # sistema operativo pesa demasiado). Cada medición de búsqueda repite el
    # lote de M búsquedas hasta acumular al menos `ventana_busqueda_s`.
    ventana_busqueda_s: float = 1.0
    ventana_construccion_s: float = 0.2
    ventana_listado_s: float = 0.2
    calentamiento: int = 50           # búsquedas previas que no se miden


COMPLETO = Configuracion(nombre="completo")

RAPIDO = Configuracion(
    nombre="rapido",
    repeticiones=3,
    n_aleatorio=(16, 256, 4_096, 16_384),
    n_ordenado=(16, 256, 1_024, 2_048),
    m_valores=(100, 400, 1_600),
    n_fijo=2_000,
    n_orden_bmas=4_096,
    ordenes_bmas=(4, 32, 128),
    ventana_busqueda_s=0.05,
    ventana_construccion_s=0.02,
    ventana_listado_s=0.02,
)
