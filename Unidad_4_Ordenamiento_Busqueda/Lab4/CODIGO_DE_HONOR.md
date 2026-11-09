# Código de honor — Laboratorio 4

**Estudiante:** Oscar Alberto Plaza Laverde
**Asignatura:** Estructuras de Datos — Universidad de Antioquia
**Docente:** Edison Alejandro Montoya Gómez

Declaro que entiendo el código que entrego, que ejecuté las pruebas y los experimentos en mi computador,
que revisé los datos que aparecen en las tablas y gráficas, y que puedo explicarlos en la sustentación.


Las fuentes del árbol están citadas en el docstring de `Quadtreetree.py` y en la sección 4 del README:
Wikipedia, *Quadtree* (point-region quadtree y pseudocódigo), *K-d tree* (búsqueda del vecino más cercano),
*Octree* y *Árbol kd*.

## Uso de herramientas de inteligencia artificial

Usé **Claude (Anthropic)** como tutor y herramienta de apoyo, tal como permite el enunciado. Esto es lo que
hice yo y lo que hizo la IA:

| Parte del trabajo | Qué hice yo | En qué me ayudó la IA |
|---|---|---|
| **Árbol** (`Quadtreetree.py`) | Lo construí paso a paso (caja, nodo, inserción, radio, vecinos). En cada paso escribí el código en mi archivo, lo ejecuté, corregí los errores que me salieron y respondí preguntas de comprobación sobre cada línea | Me explicó qué dice la fuente en cada paso, propuso el fragmento de código derivado de ella y lo explicó línea por línea; me ayudó a distinguir qué viene de Wikipedia y qué es adaptación |
| **Pruebas** (`test.py`) | Las ejecuté, revisé qué verifica cada una y respondí preguntas sobre por qué son necesarias | Escribió las 18 pruebas y el código de las gráficas 01–03 |
| **Datos y medición** (`datos.py`, `config.py`, `medicion.py`) | Elegí datos aleatorios en metros (uniformes y agrupados) | Escribió la generación de datos, el cronómetro y la estadística|
| **Experimentos** (`analisis.py`) | Corrí el experimento oficial en mi computador (5,9 min) y revisé las tablas | Diseñó los 7 experimentos y escribió el código de las gráficas 04–11 |
| **Interpretación y README** | Revisé cada gráfica y las respuestas a las preguntas del enunciado; escribí mi registro de dudas |Redactó el borrador del README con mis resultados |

Lo que verifiqué personalmente:

1. **Los resultados son correctos:** las 18 pruebas comparan el árbol con la fuerza bruta (mismos puntos y
   mismas distancias) y pasan en mi computador.
2. **Los datos son reales:** todas las cifras salen de `resultados/datos/*.csv`, producidos por
   `python analisis.py` en mi equipo; nada está escrito a mano.
3. **Las gráficas representan los datos:** se generan leyendo los CSV (`python analisis.py --solo-graficas`
   las reconstruye), y `test.py` comprueba que graficar no modifica los datos.
