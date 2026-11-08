"""
TODOS los parámetros del laboratorio en un solo lugar.
Si alguien quiere repetir el estudio, solo necesita mirar este archivo.
"""

# --- El problema del enunciado -------------------------------------------
LADO = 10_000          # metros: el mapa es un cuadrado de 10 km × 10 km
N = 10_000             # puntos de entrega
RADIO = 500            # metros
SEMILLA = 4            # semilla fija: mismos datos en cada ejecución ("Lab 4")

# --- El árbol --------------------------------------------------------------
CAPACIDAD = 4          # puntos por hoja antes de dividirse (QT_NODE_CAPACITY de Wikipedia)

# --- Datos agrupados (simulan zonas densas de una ciudad) ------------------
CENTROS_AGRUPADOS = 5      # núcleos densos
DISPERSION = 300           # metros: desviación estándar alrededor de cada núcleo
FRACCION_FONDO = 0.2       # 20 % de los puntos repartidos uniforme en todo el mapa

# --- Pruebas ----------------------------------------------------------------
CONSULTAS_PRUEBA = 300     # consultas aleatorias en cada prueba contra fuerza bruta

# --- Carpetas ---------------------------------------------------------------
CARPETA_GRAFICAS = "resultados/graficas"
CARPETA_DATOS = "resultados/datos"
CARPETA_TABLAS = "resultados/tablas"
