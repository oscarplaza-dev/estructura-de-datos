# Laboratorio 1: Matriz Binaria (100,000 x 100,000)

**Asignatura:** Estructuras de Datos  
**Docente:** Edison Alejandro Montoya  

---

## 1. Justificación Técnica y Optimización
Para representar y manipular una matriz de $100,000 \times 100,000$ ($10^{10}$ celdas) sin saturar la memoria RAM ni agotar el disco de la máquina:
* **Representación Bidimensional Real:** Se define una cabecera binaria `MatrixHeader` (16 bytes) al inicio del archivo que contiene explícitamente el número de filas, columnas y el tamaño en bits por elemento.
* **Bit-Packing (1 bit/celda):** En lugar de usar enteros (`int` de 4 bytes = 40 GB), se almacena cada celda como un único bit. Esto comprime la representación a solo **1.16 GB** en disco.
* **Acceso por Streaming (`seekg`):** Las lecturas y consultas de subregiones se realizan leyendo directamente desde la posición física en el archivo binario usando aritmética de punteros en disco, consumiendo un espacio de RAM insignificante (< 1 MB).

---

## 2. Estructura del Repositorio
* `main.cpp`: Código fuente completo en C++ que genera el archivo binario, escribe la cabecera y realiza consultas mediante streaming.
* `.gitignore`: Configuración para evitar subir el archivo de datos binario (`.bin`) y compilados (`.exe`).
* `README.md`: Documentación del laboratorio.

---

## 3. Instrucciones de Compilación y Ejecución

### Compilación:
```bash
g++ -O3 main.cpp -o lab1.exe