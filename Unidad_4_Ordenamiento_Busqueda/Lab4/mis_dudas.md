# Dudas que tuve y cómo las resolví — Laboratorio 4

## Sesión 1 (8 de noviembre de 2026): la idea del quadtree y la caja

### Duda 1: ¿construir el árbol cuesta lo mismo que buscar?
**Lo que pensaba:** que construir el árbol era rápido, como una búsqueda (O(log n)),
porque el árbol "solo tiene dos niveles".
**Lo que entendí:** con 10.000 puntos el árbol tiene varios niveles (cada nivel
multiplica las cajas por 4). Buscar es bajar una vez por esos niveles. Construir
es insertar los 10.000 puntos, y cada uno baja hasta su hoja, así que cuesta
aproximadamente n × profundidad. Construir es mucho más caro que una búsqueda.
**Por qué igual vale la pena:** los puntos de entrega no cambian. El árbol se
construye una sola vez y luego responde muchas consultas; lo que se ahorra en
cada consulta termina pagando la construcción.

### Duda 2: ¿la distancia mínima a la caja es la distancia al borde?
**Lo que pensaba:** que si la consulta está dentro de la caja, la distancia
mínima era la distancia al borde más cercano.
**Lo que entendí:** la distancia mínima es la distancia al punto de la caja más
cercano a la consulta. Si la consulta está dentro, ese punto es la consulta
misma, así que la distancia es 0 (podría haber una entrega justo ahí).
**Cómo lo comprobé:** con mi clase `Caja` (centro 5000, semilado 1000):
- consulta (5000, 5000), dentro de la caja → `0.0` → la caja se revisa.
- consulta (7000, 5000), fuera → `1000000.0` = 1000² → la caja está a 1000 m;
  como 1.000.000 > 250.000 (500²), la caja se descarta completa. Eso es la poda.
**Por qué importa:** si usara la distancia al borde, una consulta en el centro
del mapa daría 5000 m > 500 m y descartaría la caja, perdiendo todas las
entregas cercanas.


