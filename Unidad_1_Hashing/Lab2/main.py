import hashlib

def calcular_sha256(texto: str) -> str:
    
    # Entra SHA-256 a un texto y devuelve el hash en hexadecimal.
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()


class MotorArbolMerkle:
 
    @staticmethod
    def _nivel_completo(nivel: list[str]) -> list[str]:
 
        return nivel + nivel[-1:] if len(nivel) % 2 else nivel

    @classmethod
    def construir_niveles_arbol(cls, bloques_datos: list[str]) -> list[list[str]]:
    
        if not bloques_datos:
            return []

        # Nivel 0 = las hojas, o sea el hash de cada transacción
        niveles = [[calcular_sha256(bloque) for bloque in bloques_datos]]

        while len(niveles[-1]) > 1:
            nivel = cls._nivel_completo(niveles[-1])
            # Combinamos de a pares (izquierda + derecha) y sacamos el hash
            niveles.append([
                calcular_sha256(nivel[i] + nivel[i + 1])
                for i in range(0, len(nivel), 2)
            ])

        return niveles

    @classmethod
    def obtener_raiz(cls, bloques_datos: list[str]) -> str:
 
        niveles = cls.construir_niveles_arbol(bloques_datos)
        return niveles[-1][0] if niveles else ""

    @classmethod
    def obtener_prueba_inclusion(
        cls, bloques_datos: list[str], indice: int
    ) -> list[tuple[str, str]]:
     
        prueba = []
        for nivel in cls.construir_niveles_arbol(bloques_datos)[:-1]:
            nivel = cls._nivel_completo(nivel)

            # Si el índice es impar, estamos a la derecha, entonces el hermano
            # está a la izquierda (y viceversa)
            es_hijo_derecho = indice % 2 == 1
            indice_hermano = indice - 1 if es_hijo_derecho else indice + 1
            direccion = "IZQUIERDA" if es_hijo_derecho else "DERECHA"

            prueba.append((nivel[indice_hermano], direccion))
            indice //= 2  # subimos un nivel

        return prueba

    @staticmethod
    def verificar_prueba_inclusion(
        bloque_datos: str,
        prueba: list[tuple[str, str]],
        raiz_esperada: str,
    ) -> bool:
     
        hash_actual = calcular_sha256(bloque_datos)
        for hash_hermano, direccion in prueba:
            if direccion == "IZQUIERDA":
                hash_actual = calcular_sha256(hash_hermano + hash_actual)
            else:
                hash_actual = calcular_sha256(hash_actual + hash_hermano)
        return hash_actual == raiz_esperada

# PRUEBAS
if __name__ == "__main__":

    print("\n")
    print("  ÁRBOL DE MERKLE Y VERIFICACIÓN  ")
    print("_____________________________________\n")
    # Armamos 5 transacciones de prueba
    
    datos_originales = [
        "Bloque_1: Transaccion_A",
        "Bloque_2: Transaccion_B",
        "Bloque_3: Transaccion_C",
        "Bloque_4: Transaccion_D",
        "Bloque_5: Transaccion_E",
    ]
 
    print("1. Ingreso 5 transacciones simuladas (la raíz se calcula y se muestra):\n")
    raiz_merkle_original = MotorArbolMerkle.obtener_raiz(datos_originales)
    print(f"Merkle Root: {raiz_merkle_original}\n")
 
    # 2. Modificamos una transacción para demostrar que la raíz cambia
    print("2. MODIFICACIÓN DE UNA TRANSACCIÓN (la raíz debe cambiar)\n")
    datos_alterados = datos_originales.copy()
    datos_alterados[2] = "Bloque_3: Transaccion_C_MODIFICADA"
 
    nueva_raiz_merkle = MotorArbolMerkle.obtener_raiz(datos_alterados)
    print(f"Dato original:   '{datos_originales[2]}'")
    print(f"Dato modificado: '{datos_alterados[2]}'")
    print(f"Merkle Root original: {raiz_merkle_original}")
    print(f"Merkle Root nueva:    {nueva_raiz_merkle}")
    print(
        f"¿Las raíces coinciden?: {raiz_merkle_original == nueva_raiz_merkle} "
        f"(esperado: False, un solo dato distinto ya cambia toda la raíz)\n"
    )
 
    # 3. Probamos que la transacción 3 (índice 2) sí pertenece al árbol original
    print("3. PRUEBA DE INCLUSIÓN VÁLIDA (Dato 3 / Índice 2)\n")
    dato_objetivo = datos_originales[2]
    prueba_inclusion = MotorArbolMerkle.obtener_prueba_inclusion(datos_originales, 2)
 
    print(f"Dato a verificar: '{dato_objetivo}'")
    print("Pasos de la prueba (hash hermano necesario en cada nivel):")
    for nivel, (hash_hermano, direccion) in enumerate(prueba_inclusion, start=1):
        print(f"  Nivel {nivel}: hermano a la {direccion} -> {hash_hermano[:10]}...")
 
    es_valida = MotorArbolMerkle.verificar_prueba_inclusion(
        dato_objetivo, prueba_inclusion, raiz_merkle_original
    )
    print(f"Raíz recalculada coincide con la raíz original: {es_valida} (esperado: True)\n")
 
    # 4. Intentamos colar un dato falso usando la misma prueba: debe fallar
    print("4. PRUEBA CON DATO INCORRECTO (debe fallar)\n")
    dato_falso = "Bloque_3: Transaccion_FALSA"
 
    print(f"Dato a verificar: '{dato_falso}'")
    print("Se reutiliza la misma prueba del paso 3 (la que corresponde al Dato 3 real).")
 
    es_valida_falsa = MotorArbolMerkle.verificar_prueba_inclusion(
        dato_falso, prueba_inclusion, raiz_merkle_original
    )
    print(f"Raíz recalculada coincide con la raíz original: {es_valida_falsa} (esperado: False)\n")
    print("============ Fin de las pruebas ==================")
    print("\n")