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
