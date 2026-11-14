# Máquinas de demostración y casos de prueba

Este documento contiene el diseño formal de las dos máquinas de demostración
del Gate 02 y sus casos de prueba. Ambas se escriben en el formato YAML del
enunciado (`docs/architecture.md`, §4) y las ejecuta el mismo motor genérico:
ninguna parte del código de Python conoce el lenguaje ni la función que calculan.

Convenciones: B es el blanco (entrada vacía en el YAML), las reglas se escriben
como en el enunciado, δ([q, c], X) = ([p, c'], Y, D), y las IDs con la notación
del Laboratorio 10 (`docs/methodology.md`, §6).

## 1. Máquina reconocedora: L = {aⁿbⁿ | n ≥ 1}

### 1.1 Definición formal

M₁ = (Q, Σ, Γ, δ, q0, B, F) con:

| Componente | Valor |
|---|---|
| Q | {q0, q1, q2, q3, q4} |
| Σ | {a, b} |
| Γ | {a, b, X, Y, B} |
| q0 | q0 |
| B | blanco (entrada vacía en el YAML) |
| F | {q4} |
| Caché | No se utiliza: vale B en todas las reglas, en `params` y en `output` |

Marcadores: `X` reemplaza a una `a` ya emparejada y `Y` a una `b` ya emparejada.
La caché no aporta nada a este algoritmo, porque el estado ya distingue la fase
del barrido; por eso se deja en blanco en las siete claves de cada regla,
como indica el contrato del YAML.

### 1.2 Papel de cada estado

| Estado | Papel |
|---|---|
| q0 | Inicio de una ronda: marca con `X` la `a` más a la izquierda sin emparejar; si encuentra `Y`, ya no quedan `a` y pasa a la verificación |
| q1 | Busca hacia la derecha la primera `b` sin emparejar, cruzando `a` y `Y`, y la marca con `Y` |
| q2 | Regresa hacia la izquierda, cruzando `a` y `Y`, hasta la última `X` |
| q3 | Verificación final: solo deben quedar `Y` hasta el primer blanco |
| q4 | Aceptación (estado final, terminal) |

### 1.3 Algoritmo

1. **Marcar** (q0): si el símbolo es `a`, escribir `X` y moverse a la derecha.
2. **Buscar** (q1): cruzar `a` y `Y` hacia la derecha; en la primera `b`, escribir `Y` y moverse a la izquierda.
3. **Regresar** (q2): cruzar `a` y `Y` hacia la izquierda; al encontrar `X`, moverse a la derecha y volver a q0.
4. **Comprobar** (q0 → q3): si q0 lee `Y`, todas las `a` están marcadas; q3 cruza las `Y` y acepta en el primer blanco.

Cualquier otra combinación (estado, lectura) no tiene regla, de modo que la
máquina se detiene fuera de F y la cadena se rechaza.

### 1.4 Tabla de transiciones

| # | Regla | Paso del algoritmo |
|---|---|---|
| 1 | δ([q0, B], a) = ([q1, B], X, R) | Marcar |
| 2 | δ([q0, B], Y) = ([q3, B], Y, R) | Comprobar |
| 3 | δ([q1, B], a) = ([q1, B], a, R) | Buscar |
| 4 | δ([q1, B], Y) = ([q1, B], Y, R) | Buscar |
| 5 | δ([q1, B], b) = ([q2, B], Y, L) | Buscar: marca la `b` |
| 6 | δ([q2, B], a) = ([q2, B], a, L) | Regresar |
| 7 | δ([q2, B], Y) = ([q2, B], Y, L) | Regresar |
| 8 | δ([q2, B], X) = ([q0, B], X, R) | Regresar: siguiente ronda |
| 9 | δ([q3, B], Y) = ([q3, B], Y, R) | Comprobar |
| 10 | δ([q3, B], B) = ([q4, B], B, R) | Aceptar |

Las claves (estado, caché, lectura) son todas distintas, así que δ es una
función. Combinaciones sin regla y su significado:

| Clave sin regla | Situación que detecta |
|---|---|
| (q0, B, b) | La cadena empieza con `b` o tiene una `b` antes de alguna `a` sin marcar |
| (q0, B, B) | Entrada vacía (n = 0 no pertenece a L) |
| (q1, B, B) | Sobran `a`: no queda `b` para emparejar |
| (q3, B, b) | Sobran `b` |
| (q3, B, a) | Hay una `a` después de las `b` (la cadena no está en a\*b\*) |

El diseño es el de Hopcroft et al. (2001), ejemplo 8.2, para {0ⁿ1ⁿ | n ≥ 1},
con a/b en lugar de 0/1 y la caché fija en blanco.

### 1.5 Corrección

**Toda cadena aceptada es aⁿbⁿ con n ≥ 1.** La única regla que escribe el
blanco (10) lo hace sobre una celda que ya estaba en blanco, así que las celdas
0 … |w|−1 siguen ocupadas y el primer blanco a la derecha está en |w|. Cada ronda completa (reglas 1, 5 y 8) convierte
exactamente una `a` en `X` y una `b` en `Y`, y las `X` ocupan las posiciones
0, 1, …, k−1, porque q0 siempre marca la celda contigua a la última `X`. Para
aceptar, q0 debe leer `Y` en la posición k tras k rondas y q3 debe cruzar solo
`Y` hasta la posición |w|. Entonces la cinta es XᵏYˡ con k + l = |w|, y como
hubo k rondas, l = k. Las `X` provienen de `a` y las `Y` de `b`, por lo que
w = aᵏbᵏ. Además k ≥ 1, porque en la primera visita a q0 la posición 0 contiene
un símbolo de la entrada (o el blanco), nunca `Y`.

**Toda cadena aⁿbⁿ con n ≥ 1 es aceptada.** En la ronda j (1 ≤ j ≤ n), q0 marca
la `a` de la posición j−1. q1 cruza n−j letras `a` y j−1 letras `Y` y marca la
`b` de la posición n+j−1. q2 regresa hasta la `X` de la posición j−1 y q0
continúa en la posición j. Tras n rondas, q0 lee la `Y` de la posición n, q3
cruza las n `Y` y en la posición 2n lee el blanco y acepta.

**Número de pasos de una cadena aceptada.** Cada ronda aplica 1 + (n−1) + 1 +
(n−1) + 1 = 2n + 1 reglas, y la comprobación final aplica 1 + (n−1) + 1 = n + 1.
En total, T(n) = n(2n+1) + n + 1 = 2n² + 2n + 1: 13 pasos para `aabb`, 25 para
`aaabbb` y 41 para `aaaabbbb`.

### 1.6 Recorridos a mano

**`aabb` (aceptada, 13 pasos):**

| Paso | ID | Regla |
|---|---|---|
| 0 | `[q0,B]aabb` | — |
| 1 | `X[q1,B]abb` | 1 |
| 2 | `Xa[q1,B]bb` | 3 |
| 3 | `X[q2,B]aYb` | 5 |
| 4 | `[q2,B]XaYb` | 6 |
| 5 | `X[q0,B]aYb` | 8 |
| 6 | `XX[q1,B]Yb` | 1 |
| 7 | `XXY[q1,B]b` | 4 |
| 8 | `XX[q2,B]YY` | 5 |
| 9 | `X[q2,B]XYY` | 7 |
| 10 | `XX[q0,B]YY` | 8 |
| 11 | `XXY[q3,B]Y` | 2 |
| 12 | `XXYY[q3,B]B` | 9 |
| 13 | `XXYYB[q4,B]B` | 10 |

**`abb` (rechazada, 4 pasos):**

| Paso | ID | Regla |
|---|---|---|
| 0 | `[q0,B]abb` | — |
| 1 | `X[q1,B]bb` | 1 |
| 2 | `[q2,B]XYb` | 5 |
| 3 | `X[q0,B]Yb` | 8 |
| 4 | `XY[q3,B]b` | 2 |

En ID_4 no hay regla para (q3, B, b) y q3 ∉ F: sobra una `b`.

### 1.7 Cadenas de la demostración

Resultados esperados según el análisis anterior. Los resultados observados en
el simulador se registran con las pruebas.

| Cadena | Longitud | Esperado | Pasos esperados | Motivo |
|---|---|---|---|---|
| `aaabbb` | 6 | ACCEPTED | 25 | n = 3, T(3) = 25 |
| `aaaabbbb` | 8 | ACCEPTED | 41 | n = 4, T(4) = 41 |
| `aaabb` | 5 | REJECTED | 17 | Tras dos rondas, q1 cruza `YY` y llega al blanco: falta una `b`; ID final `XXXYY[q1,B]B` |
| `aabbbb` | 6 | REJECTED | 12 | Tras dos rondas, q3 cruza `YY` y lee `b`: sobran dos `b`; ID final `XXYY[q3,B]bb` |

Pasos de los rechazos: en `aaabb`, cada una de las dos primeras rondas aplica 7
reglas y la tercera se detiene tras 3 (marca y dos cruces), 7 + 7 + 3 = 17. En
`aabbbb`, cada ronda aplica 5 reglas y la comprobación se detiene tras 2,
5 + 5 + 2 = 12.

### 1.8 Pruebas automatizadas (`tests/test_recognizer.py`)

Las pruebas cargan `machines/recognizer_anbn.yaml` con el mismo flujo que la
CLI (`load_yaml` → `parse_machine` → `validate_machine` → `simulate`) y comparan
resultado, pasos, estado final, ID final y motivo, no solo el veredicto.

| Prueba | Qué verifica |
|---|---|
| Demostración | Las cuatro cadenas de §1.7: resultado, pasos, estado e ID final |
| Rechazos justificados | La última ID de `aaabb` y `aabbbb` no tiene regla y su estado no es final |
| Recorridos a mano | Las 14 IDs de `aabb` (con el número de regla de §1.4) y las 5 de `abb` |
| Complementarias | `ab`, `aabb` aceptadas; `abb`, `aab`, `ba`, `abab`, `aaaa`, `bbbb`, ε, `aabba`, `abba` rechazadas, con el estado y el símbolo donde se detienen |
| Fórmula de pasos | T(n) = 2n² + 2n + 1 para n = 1, 2, 3, 4, 5, 10, 25 |
| Cadenas largas desbalanceadas | a¹⁰b⁹, a⁹b¹⁰, a²⁵b²⁴, `a`, `b` rechazadas |
| Exhaustiva | Las 2047 cadenas sobre {a, b} de longitud ≤ 10 coinciden con la definición de L |
| Límite de pasos | `aaaabbbb` con `max_steps=40` da `LIMIT_EXCEEDED` (no `REJECTED`); con 41 se acepta |
| Independencia | Simular otra cadena entre dos ejecuciones de `aaabbb` no cambia su traza |

Resultados observados con `python main.py --machine machines/recognizer_anbn.yaml`
(coinciden con los esperados de §1.7):

| Cadena | Resultado | Pasos | ID final |
|---|---|---|---|
| `aaabbb` | ACCEPTED | 25 | `XXXYYYB[q4,B]B` |
| `aaaabbbb` | ACCEPTED | 41 | `XXXXYYYYB[q4,B]B` |
| `aaabb` | REJECTED | 17 | `XXXYY[q1,B]B` |
| `aabbbb` | REJECTED | 12 | `XXYY[q3,B]bb` |

## 2. Máquina alteradora: incremento binario con acarreo

### 2.1 Función calculada

Para una cadena binaria w = bₖ₋₁…b₁b₀ no vacía (bit más significativo a la
izquierda):

  f(w) = representación binaria de value₂(w) + 1

La salida conserva los ceros a la izquierda de la entrada (`0011 → 0100`) y,
cuando todos los bits son 1, agrega un bit `1` a la izquierda
(`11111 → 100000`), de modo que nunca se pierde el acarreo. Esta es la
diferencia con la máquina del Laboratorio 9, ejercicio 2, que conserva la
longitud y convierte `11` en `00` (`tests/test_engine.py`).

### 2.2 Definición formal

M₂ = (Q, Σ, Γ, δ, q0, B, F) con:

| Componente | Valor |
|---|---|
| Q | {q0, q1, q2} |
| Σ | {0, 1} |
| Γ | {0, 1, B} |
| q0 | q0 |
| B | blanco (entrada vacía en el YAML) |
| F | {q2} |
| Caché | Registro de acarreo c ∈ {B, 1}: `1` = hay un acarreo pendiente, B = no hay acarreo |

En el YAML, los estados se escriben sin comillas (`q0`) y los símbolos `'0'` y
`'1'` entre comillas, como exige el contrato (D7). Lo mismo vale para el valor
de caché `'1'`.

### 2.3 Papel de los estados y de la caché

| Estado | Caché | Papel |
|---|---|---|
| q0 | B | Barrido a la derecha hasta el primer blanco después del número |
| q1 | 1 | Propagación del acarreo de derecha a izquierda: suma c al bit leído |
| q2 | B | Fin: el acarreo se absorbió (estado final, terminal) |

La caché funciona como el «almacenamiento en el estado» de Hopcroft et al.
(2001, §8.3.1): la tupla de control [q, c] guarda el acarreo de la suma.
Al llegar al final del número, la regla 3 carga c = 1 (el «+1»). Cada regla de
q1 calcula x + c sobre el bit leído x: si el resultado es 10, escribe 0 y
conserva c = 1; si es 1, escribe 1, vacía la caché y se detiene. Por eso la ID
final siempre muestra `[q2,B]`: ya no queda acarreo pendiente.

### 2.4 Algoritmo

1. **Barrido** (q0): cruzar los bits hacia la derecha sin modificarlos.
2. **Retorno con acarreo inicial** (q0 → q1): en el primer blanco, cargar c = 1 en la caché y moverse a la izquierda, al bit menos significativo.
3. **Propagación** (q1, c = 1): cada `1` se reemplaza por `0` y el acarreo continúa a la izquierda.
4. **Detención al reemplazar 0** (q1 → q2): el primer `0` se reemplaza por `1`, la caché se vacía y la máquina se detiene sin moverse.
5. **Desbordamiento** (q1 → q2): si se agotan los bits (q1 lee el blanco a la izquierda del número), se escribe `1` en esa celda y la máquina se detiene; el resultado tiene un bit más.

### 2.5 Tabla de transiciones

| # | Regla | Paso del algoritmo |
|---|---|---|
| 1 | δ([q0, B], 0) = ([q0, B], 0, R) | Barrido |
| 2 | δ([q0, B], 1) = ([q0, B], 1, R) | Barrido |
| 3 | δ([q0, B], B) = ([q1, 1], B, L) | Carga el acarreo inicial c = 1 |
| 4 | δ([q1, 1], 1) = ([q1, 1], 0, L) | 1 + 1 = 10: escribe 0, el acarreo sigue |
| 5 | δ([q1, 1], 0) = ([q2, B], 1, S) | 0 + 1 = 1: escribe 1, vacía la caché y se detiene |
| 6 | δ([q1, 1], B) = ([q2, B], 1, S) | Desbordamiento: nuevo bit más significativo |

Las seis claves son distintas. Ninguna regla sale de q2, y q1 solo se alcanza
con c = 1, por lo que no hacen falta reglas para (q1, B, ·). Con una entrada
binaria, la máquina siempre se detiene en q2: el resultado es `ACCEPTED` y la
salida es el contenido final de la cinta.

### 2.6 Índice negativo, cinta final y número de pasos

- La entrada ocupa las posiciones 0 … |w|−1. En el desbordamiento, q1 llega a la
  posición −1 (el blanco a la izquierda del bit más significativo) y escribe ahí
  el `1` nuevo. La cinta dispersa admite posiciones negativas, así que no hace
  falta desplazar la entrada.
- La regla 3 escribe el blanco sobre una celda que ya estaba en blanco
  (posición |w|), y ninguna otra regla escribe el blanco. Por eso el resultado
  no tiene blancos intermedios ni laterales.
- **Salida:** el contenido de la cinta desde la primera hasta la última celda
  no blanca (`tape_contents`, `src/output/tape_formatter.py`). Si apareciera un
  blanco intermedio, se mostraría como `B` en lugar de ocultarse.
- **Pasos:** si w termina en t unos, T(w) = |w| + 1 + t + 1 = |w| + t + 2
  (barrido, carga del acarreo, t propagaciones y la regla que se detiene).
  En el desbordamiento, t = |w| y T = 2|w| + 2.
- **Entrada vacía:** no forma parte del dominio de f, pero las reglas la
  procesan como el número 0: la regla 3 se aplica en la posición 0, la regla 6
  escribe `1` en −1 y la salida es `1`.

### 2.7 Recorrido a mano: `11111 → 100000` (12 pasos)

| Paso | ID | Regla |
|---|---|---|
| 0 | `[q0,B]11111` | — |
| 1 | `1[q0,B]1111` | 2 |
| 2 | `11[q0,B]111` | 2 |
| 3 | `111[q0,B]11` | 2 |
| 4 | `1111[q0,B]1` | 2 |
| 5 | `11111[q0,B]B` | 2 |
| 6 | `1111[q1,1]1` | 3 |
| 7 | `111[q1,1]10` | 4 |
| 8 | `11[q1,1]100` | 4 |
| 9 | `1[q1,1]1000` | 4 |
| 10 | `[q1,1]10000` | 4 |
| 11 | `[q1,1]B00000` | 4 |
| 12 | `[q2,B]100000` | 6 |

En ID_11 el cabezal está en la posición −1. La regla 6 escribe el `1` nuevo y
la cinta final, de −1 a 4, es `100000`.

### 2.8 Recorrido a mano: `10101 → 10110` (8 pasos)

| Paso | ID | Regla |
|---|---|---|
| 0 | `[q0,B]10101` | — |
| 1 | `1[q0,B]0101` | 2 |
| 2 | `10[q0,B]101` | 1 |
| 3 | `101[q0,B]01` | 2 |
| 4 | `1010[q0,B]1` | 1 |
| 5 | `10101[q0,B]B` | 2 |
| 6 | `1010[q1,1]1` | 3 |
| 7 | `101[q1,1]00` | 4 |
| 8 | `101[q2,B]10` | 5 |

### 2.9 Cadenas de la demostración

| Cadena | Longitud | Salida esperada | Pasos esperados (longitud + t + 2) |
|---|---|---|---|
| `10101` | 5 | `10110` | 5 + 1 + 2 = 8 |
| `11011` | 5 | `11100` | 5 + 2 + 2 = 9 |
| `11111` | 5 | `100000` | 5 + 5 + 2 = 12 |
| `10000` | 5 | `10001` | 5 + 0 + 2 = 7 |

### 2.10 Pruebas automatizadas (`tests/test_transformer.py`)

La salida se compara con la definición de f (value₂(w) + 1 en binario,
conservando los ceros a la izquierda). Las pruebas también comparan el estado
final, la caché, la ID final y los pasos reales con T(w) = |w| + t + 2.

| Prueba | Qué verifica |
|---|---|
| Demostración | Las cuatro cadenas de §2.9: salida, pasos, estado `q2`, caché B e ID final |
| Complementarias | `0→1`, `1→10`, `111→1000`, `1010→1011`, `0011→0100`, `0111→1000`, `01→10` |
| Índice negativo | En `11111` el bit nuevo queda en la posición −1, con el cabezal sobre él |
| Recorridos a mano | Las 13 IDs de `11111` (con el número de regla de §2.5) y las 9 de `10101` |
| Caché | Vale `1` exactamente en las IDs con estado q1 y B en el resto |
| Entradas largas | 1⁶⁰, 10⁵⁹, (10)³⁰, 0⁴⁰1²⁰ |
| Exhaustiva | Las 2046 cadenas binarias de longitud 1 a 10: salida y número de pasos |
| No borra la cinta | La salida tiene longitud \|w\| o \|w\| + 1 y solo contiene 0 y 1 |
| Entrada vacía | Se procesa como 0: salida `1` en 2 pasos |
| Límite de pasos | `11111` con `max_steps=11` da `LIMIT_EXCEEDED`; con 12 produce `100000` |
| Independencia | Simular otra cadena entre dos ejecuciones de `11111` no cambia su traza |

Resultados observados con
`python main.py --machine machines/transformer_binary_increment.yaml`
(coinciden con los esperados de §2.9):

| Cadena | Resultado | Pasos | Cinta final | ID final |
|---|---|---|---|---|
| `10101` | ACCEPTED | 8 | `10110` | `101[q2,B]10` |
| `11011` | ACCEPTED | 9 | `11100` | `11[q2,B]100` |
| `11111` | ACCEPTED | 12 | `100000` | `[q2,B]100000` |
| `10000` | ACCEPTED | 7 | `10001` | `1000[q2,B]1` |
