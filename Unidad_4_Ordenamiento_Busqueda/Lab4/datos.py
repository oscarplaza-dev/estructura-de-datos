"""
Generación de los puntos de entrega (todo en METROS).

  * uniformes(): puntos repartidos al azar en todo el mapa.
  * agrupados(): la mayoría alrededor de unos pocos núcleos densos (como el
    centro de una ciudad) y una fracción repartida uniforme como "fondo".
  * consultas(): ubicaciones de clientes al azar, para buscar.

Todas reciben una semilla, así los mismos datos salen en cada ejecución.
"""

import random

import config
from Quadtreetree import Caja


def caja_mapa(k=2, lado=config.LADO):
    """La caja de la raíz: el cuadrado (o cubo, o hipercubo) [0, lado]^k."""
    return Caja([lado / 2] * k, lado / 2)


def uniformes(n, k=2, semilla=config.SEMILLA, lado=config.LADO):
    rng = random.Random(semilla)
    return [tuple(rng.uniform(0, lado) for _ in range(k)) for _ in range(n)]


def agrupados(n, k=2, semilla=config.SEMILLA, lado=config.LADO,
              centros=config.CENTROS_AGRUPADOS, dispersion=config.DISPERSION,
              fraccion_fondo=config.FRACCION_FONDO):
    rng = random.Random(semilla)
    nucleos = [tuple(rng.uniform(0.15 * lado, 0.85 * lado) for _ in range(k))
               for _ in range(centros)]
    puntos = []
    while len(puntos) < n:
        if rng.random() < fraccion_fondo:
            p = tuple(rng.uniform(0, lado) for _ in range(k))
        else:
            nucleo = rng.choice(nucleos)
            p = tuple(rng.gauss(c, dispersion) for c in nucleo)
        if all(0 <= x <= lado for x in p):      # se descartan los que caen fuera del mapa
            puntos.append(p)
    return puntos


def consultas(m, k=2, semilla=config.SEMILLA + 1, lado=config.LADO):
    rng = random.Random(semilla)
    return [tuple(rng.uniform(0, lado) for _ in range(k)) for _ in range(m)]
