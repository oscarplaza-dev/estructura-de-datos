#include <iostream>
#include <fstream>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <ctime>

// Cabecera de metadatos obligatoria para definir la bidimensionalidad
struct MatrixHeader {
    uint32_t rows;
    uint32_t cols;
    uint8_t element_size_bits; // 1 bit por elemento
};

const std::string FILENAME = "matriz_gigante.bin";
const uint32_t ROWS = 100000;
const uint32_t COLS = 100000;

void generarYMostrarMatriz() {
    std::srand(static_cast<unsigned int>(std::time(0)));

    // 1. Crear y preparar archivo
    std::ofstream outfile(FILENAME, std::ios::binary);
    if (!outfile) {
        std::cerr << "Error al crear el archivo binario." << std::endl;
        return;
    }

    std::cout << "Inicializando y escribiendo 1.16 GB en disco..." << std::endl;

    // 2. Escribir Cabecera de Metadatos (16 bytes al inicio)
    MatrixHeader header = {ROWS, COLS, 1};
    outfile.write(reinterpret_cast<const char*>(&header), sizeof(header));

    // 3. Escritura optimizada por Chunks/Filas (Evita satura RAM)
    size_t bytes_per_row = COLS / 8; // 12,500 bytes por fila
    std::vector<uint8_t> row_buffer(bytes_per_row);

    for (uint32_t r = 0; r < ROWS; ++r) {
        for (size_t byte_idx = 0; byte_idx < bytes_per_row; ++byte_idx) {
            row_buffer[byte_idx] = static_cast<uint8_t>(std::rand() % 256);
        }
        outfile.write(reinterpret_cast<const char*>(row_buffer.data()), bytes_per_row);
    }
    outfile.close();
    std::cout << "¡Escritura completada con exito!\n" << std::endl;

    // =========================================================================
    // LECTURA DE SECCIÓN ESPECÍFICA MEDIANTE SEEK (SIN CARGAR RAM)
    // =========================================================================
    std::ifstream infile(FILENAME, std::ios::binary);
    if (!infile) {
        std::cerr << "Error al abrir el archivo para lectura." << std::endl;
        return;
    }

    // Leer cabecera para verificar
    MatrixHeader read_header;
    infile.read(reinterpret_cast<char*>(&read_header), sizeof(read_header));

    uint32_t f_inicio = 5000, f_fin = 5005;
    uint32_t c_inicio = 5000, c_fin = 5005;

    std::cout << "--- MOSTRANDO SECCIÓN (" << f_inicio << "x" << c_inicio << ") SIN USAR RAM ---" << std::endl;

    for (uint32_t f = f_inicio; f < f_fin; f++) {
        for (uint32_t c = c_inicio; c < c_fin; c++) {
            
            // Cálculo del offset posicional en el archivo binario
            uint64_t bit_global = (static_cast<uint64_t>(f) * read_header.cols) + c;
            uint64_t byte_index = bit_global / 8;
            int bit_offset = bit_global % 8;

            // Posicionar el puntero del archivo ignorando el tamaño del Header
            infile.seekg(sizeof(MatrixHeader) + byte_index, std::ios::beg);

            uint8_t byte_leido;
            infile.read(reinterpret_cast<char*>(&byte_leido), 1);

            bool bit_valor = (byte_leido >> (7 - bit_offset)) & 1;
            std::cout << bit_valor << "\t";
        }
        std::cout << "\n";
    }

    // =========================================================================
    // CONSULTA INDIVIDUAL
    // =========================================================================
    uint32_t consulta_f = 99999;
    uint32_t consulta_c = 99999;

    uint64_t bit_buscado = (static_cast<uint64_t>(consulta_f) * read_header.cols) + consulta_c;
    uint64_t byte_b = bit_buscado / 8;
    int offset_b = bit_buscado % 8;

    infile.seekg(sizeof(MatrixHeader) + byte_b, std::ios::beg);
    uint8_t byte_individual;
    infile.read(reinterpret_cast<char*>(&byte_individual), 1);
    bool resultado_bit = (byte_individual >> (7 - offset_b)) & 1;

    std::cout << "\n[CONSULTA] El elemento en posicion [" << consulta_f << "][" << consulta_c << "] es: " 
              << resultado_bit << std::endl;

    infile.close();
}

int main() {
    generarYMostrarMatriz();
    return 0;
}