# Código de honor — Laboratorio 3

**Estudiante:** Oscar Alberto Plaza
**Asignatura:** Estructuras de Datos — Universidad de Antioquia
**Docente:** Edison Alejandro Montoya Gómez

Declaro que este trabajo es mío: entiendo el código que entrego, ejecuté los
experimentos, revisé los datos que aparecen en las tablas y gráficas, y puedo
explicar en la sustentación.
No copié código de compañeros. Las fuentes de apoyo fueron las notas de 
clase ("Árboles que organizan el mundo: ABB, B y B+" y "Archivos indexados") y la
documentación oficial de Python.

## Uso de herramientas de inteligencia artificial

Usé **Claude (Anthropic)** como herramienta de apoyo, tal como permite el
enunciado. Esto es lo que hizo la IA y lo que hice yo:

| Parte del trabajo | Qué hice yo | En qué me ayudó la IA |
|---|---|---|
| Reorganizar el código, apoyo en el árbol B+ y primera versión del README |
| Escribir el código con una estructura por módulos, diseñar los experimentos A, B y C, programar la estadística y las 12 gráficas, y redactar el README
| Verificación | Revisé que las gráficas muestren los datos de los CSV, que los números del README coincidan con `resultados/tablas/RESUMEN.md` 

Lo que verifiqué personalmente, como exige el enunciado:

1. **Los datos son reales:** todas las cifras salen de `resultados/datos/*.csv`,
   producidos por `python main.py`; nada está escrito a mano.
2. **Los cálculos son correctos:** las estadísticas se calculan con
   `statistics` y `numpy` en `sistema_estudiantes/estadistica.py`.
3. **Las gráficas representan los datos:** se generan directamente de los CSV
   (`python main.py --solo-graficas` las reconstruye).

