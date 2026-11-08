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

# --- Experimentos de rendimiento (analisis.py) ------------------------------
# Dos perfiles: COMPLETO (el de las gráficas del repositorio) y RAPIDO (prueba
# de humo de ~1-2 min para verificar que todo corre: python analisis.py --rapido).
COMPLETO = {
    "nombre": "completo",
    "repeticiones": 5,                 # ejecuciones independientes por punto (datos nuevos)
    # A. Rango PEQUEÑO, para ubicar el cruce (potencias de 2: parejas en escala log)
    "n_cruce": (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1_024),
    # B. Rango GRANDE, para tendencias limpias y pendientes (10^3 a 10^5)
    "n_tendencia": (1_000, 2_000, 5_000, 10_000, 20_000, 50_000, 100_000),
    # C. Capacidad por nodo
    "capacidades": (1, 2, 4, 8, 16, 32, 64),
    "capacidades_cruce": (1, 4, 16, 64),
    # D. Uniforme vs agrupado
    "n_distribucion": (1_000, 3_000, 10_000, 30_000, 100_000),
    # E. Radio variable con n fijo (= N del enunciado)
    "radios": (25, 50, 100, 200, 500, 1_000, 2_000, 5_000),
    # F. Tres dimensiones (cubo de 10 km de lado)
    "n_3d": (1_000, 3_000, 10_000, 30_000),
    # Medición
    "consultas_max": 200,              # consultas por bloque...
    "presupuesto_fb": 400_000,         # ...pero si n es grande se usan max(10, presupuesto/n)
    "ventana_corta_s": 0.1,            # ventana para n pequeños (rango A y cruce por capacidad)
    "ventana_s": 0.2,                  # ventana para el resto
}

RAPIDO = {
    **COMPLETO,
    "nombre": "rapido",
    "repeticiones": 2,
    "n_cruce": (1, 4, 16, 64, 256, 1_024),
    "n_tendencia": (1_000, 5_000, 20_000),
    "capacidades": (1, 4, 16, 64),
    "capacidades_cruce": (1, 16),
    "n_distribucion": (1_000, 10_000),
    "radios": (50, 500, 2_000),
    "n_3d": (1_000, 5_000),
    "ventana_corta_s": 0.01,
    "ventana_s": 0.02,
}
