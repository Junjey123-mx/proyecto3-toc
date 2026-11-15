# Metodología mecanizada

El simulador reproduce el procedimiento con el que se resolvieron los
laboratorios 9 y 10: cada ID se obtiene de la anterior aplicando una sola regla
de δ, y la tabla «Paso | ID | Transición» se puede reconstruir a partir del
historial de configuraciones.

## 1. Paso atómico (`src/simulator/step.py`)

Notación del deck («Moves of a TM») con la caché dentro de la tupla de control,
como en el Laboratorio 10. Si δ([q, c], Xi) = ([p, c'], Y, D):

| D | ID_k | ID_k+1 |
|---|---|---|
| L | X1…Xi-1 [q, c] Xi…Xn | X1…Xi-2 [p, c'] Xi-1 Y Xi+1…Xn |
| R | X1…Xi-1 [q, c] Xi…Xn | X1…Xi-1 Y [p, c'] Xi+1…Xn |
| S | X1…Xi-1 [q, c] Xi…Xn | X1…Xi-1 [p, c'] Y Xi+1…Xn |

`step(machine, current) -> Configuration | None` ejecuta, en este orden:

1. Leer el símbolo bajo el cabezal (`current.scanned`; blanco si la celda no existe).
2. Buscar δ([estado, caché], símbolo) con `find_transition`.
3. Si no hay regla, devolver `None` sin modificar nada.
4. Escribir el símbolo de salida en una copia de la cinta (el blanco borra la celda).
5. Tomar el nuevo estado y la nueva caché de la regla.
6. Mover el cabezal según `Move` (L = −1, R = +1, S = 0); puede quedar en posiciones negativas.
7. Devolver una `Configuration` nueva con `step_index + 1` y `applied` = la regla.

La ID anterior nunca cambia: la cinta de la nueva ID es otra copia de solo
lectura. `step` no decide la parada; eso corresponde a `simulate`.

## 2. Procedimiento del docente y su equivalente en código

| Paso | Procedimiento (laboratorios 9 y 10) | Código |
|---|---|---|
| 1 | Identificar Q, Σ, Γ, q0, B, F y δ | `load_yaml` → `parse_machine` → `validate_machine` |
| 2 | Construir la tabla de transiciones | Índice de `TuringMachine` (clave estado, caché, lectura) |
| 3 | Establecer la configuración inicial `[q0, B] w` | `simulate`: ID_0 con caché en blanco y cabezal en 0 |
| 4 | Leer el símbolo bajo el cabezal | `Configuration.scanned` |
| 5 | Buscar δ([q, c], X) | `TuringMachine.find_transition` |
| 6 | Escribir, cambiar estado y caché, mover | `step` |
| 7 | Registrar la nueva ID sin borrar las anteriores | `SimulationResult.configurations` (IDs inmutables) |
| 8 | Comprobar la condición de parada | `simulate` |
| 9 | Presentar IDs, cinta final y veredicto | Gate 02 (`src/output/`, CLI) a partir de `SimulationResult` |

## 3. Motor (`src/simulator/engine.py`)

```text
simulate(M, w, max_steps):
    si max_steps < 1 o w ∉ Σ*: ValueError
    ID ← (paso 0, q0, caché B, cabezal 0, cinta w)
    historial ← [ID]
    mientras estado(ID) ∉ F:
        siguiente ← step(M, ID)
        si siguiente = nada: devolver REJECTED
        si paso(ID) ≥ max_steps: devolver LIMIT_EXCEEDED
        historial.agregar(siguiente); ID ← siguiente
    devolver ACCEPTED
```

| Condición, en orden | Resultado | Fundamento |
|---|---|---|
| El estado actual ∈ F | `ACCEPTED` | L(M) = {w ∈ Σ* \| q0w ⊢* αpβ, p ∈ F} (deck); D6 |
| No hay regla para (estado, caché, lectura) | `REJECTED` | Enunciado: «terminar la ejecución sin poder aplicar una función de transición» |
| Hay regla, pero ya se aplicaron `max_steps` transiciones | `LIMIT_EXCEEDED` | Salvaguarda operativa; la parada no es decidible (kenjinote, 2026) |

- La cota solo se aplica si la máquina aún puede continuar: una MT que se
  detiene (en F o sin regla) justo tras `max_steps` transiciones se acepta o se
  rechaza normalmente.
- `max_steps` vale `DEFAULT_MAX_STEPS = 10_000` salvo que se indique otro entero positivo.
- `LIMIT_EXCEEDED` no es un rechazo: significa que la simulación no terminó dentro de la cota.
- Un archivo o una máquina inválidos son `InputError` y nunca llegan al motor;
  una cadena fuera de Σ* pasada directamente a `simulate` es `ValueError`.
- Cada llamada crea su propia ID_0, por lo que varias cadenas simuladas con la
  misma máquina no comparten cinta, caché ni historial.

## 4. Ejemplo ejecutado

Salida real de `simulate` con `machines/examples/basic_machine.yaml` (máquina
del Laboratorio 10) y la cadena `abb#aab`. La tabla la produce un script
auxiliar a partir de `result.configurations`; el formato definitivo de las IDs
corresponde al Gate 02.

| k | estado | caché | cabezal | cinta (celdas no blancas) | regla aplicada |
|---|---|---|---|---|---|
| 0 | 0 | B | 0 | `0:a 1:b 2:b 3:# 4:a 5:a 6:b` | — |
| 1 | 1 | a | 1 | `1:b 2:b 3:# 4:a 5:a 6:b` | δ([0, B], a) = ([1, a], B, R) |
| 2 | 1 | a | 2 | `1:b 2:b 3:# 4:a 5:a 6:b` | δ([1, a], b) = ([1, a], b, R) |
| 3 | 1 | a | 3 | `1:b 2:b 3:# 4:a 5:a 6:b` | δ([1, a], b) = ([1, a], b, R) |
| 4 | 2 | a | 4 | `1:b 2:b 3:# 4:a 5:a 6:b` | δ([1, a], #) = ([2, a], #, R) |
| 5 | 3 | B | 3 | `1:b 2:b 3:# 4:X 5:a 6:b` | δ([2, a], a) = ([3, B], X, L) |
| 6 | 3 | B | 2 | `1:b 2:b 3:# 4:X 5:a 6:b` | δ([3, B], #) = ([3, B], #, L) |
| 7 | 3 | B | 1 | `1:b 2:b 3:# 4:X 5:a 6:b` | δ([3, B], b) = ([3, B], b, L) |
| 8 | 3 | B | 0 | `1:b 2:b 3:# 4:X 5:a 6:b` | δ([3, B], b) = ([3, B], b, L) |
| 9 | 0 | B | 1 | `1:b 2:b 3:# 4:X 5:a 6:b` | δ([3, B], B) = ([0, B], B, R) |
| 10 | 1 | b | 2 | `2:b 3:# 4:X 5:a 6:b` | δ([0, B], b) = ([1, b], B, R) |
| 11 | 1 | b | 3 | `2:b 3:# 4:X 5:a 6:b` | δ([1, b], b) = ([1, b], b, R) |
| 12 | 2 | b | 4 | `2:b 3:# 4:X 5:a 6:b` | δ([1, b], #) = ([2, b], #, R) |
| 13 | 2 | b | 5 | `2:b 3:# 4:X 5:a 6:b` | δ([2, b], X) = ([2, b], X, R) |

Resultado: `REJECTED` tras 13 transiciones, con el motivo «no hay regla para el
estado '2' con caché 'b' leyendo 'a', y '2' no es final».

## 5. Equivalencia con los laboratorios

Los resultados resueltos a mano en los laboratorios se usan como oráculos en
`tests/test_engine.py` y `tests/test_step.py`; todos coinciden con el simulador.

| Laboratorio | Entrada | Resultado a mano | Simulador |
|---|---|---|---|
| 10 b) | `aab#aab` | `[q0,B]aab#aab ⊢^32 BBB#XXXB[q5,B]B`, aceptada | `ACCEPTED`, 32 transiciones, estado 5, cabezal 8 |
| 10 b), primeras IDs | `aab#aab` | ID_1…ID_5 hasta `Bab[q3,B]#Xab` | Iguales paso a paso |
| 10 c) | `abb#aab` | `⊢^13 BBb#X[q2,b]ab`, δ([q2,b], a) no definida | `REJECTED`, 13 transiciones, estado 2, caché b |
| 9, ej. 2 a) | `100` | 5 pasos, `101 q_halt B` | 5 transiciones, cinta `101`, cabezal 3 |
| 9, ej. 2 b) | `10011` | 9 pasos, `101 q_halt 00` | 9 transiciones, cinta `10100`, cabezal 3 |
| 9, ej. 2 c) | `11` | 6 pasos, `q_halt BB00` (se pierde el acarreo) | 6 transiciones, cinta `00`, cabezal −2 |

## 6. Traza y notación de las IDs

### 6.1 Traza (`src/simulator/trace.py`)

`build_trace(result) -> Trace` copia cada `Configuration` de
`result.configurations` en una `TraceEntry` (paso, estado, caché, cabezal,
cinta de solo lectura, símbolo leído y regla aplicada) y verifica, sin volver a
ejecutar la máquina, que la secuencia sea una computación válida:

| Comprobación | Error si falla |
|---|---|
| ID_0 tiene paso 0 y ninguna regla aplicada | `TraceError` |
| Los pasos son 0, 1, …, n, sin saltos | `TraceError` |
| La clave de la regla de ID_k+1 es (estado, caché, símbolo leído) de ID_k | `TraceError` |
| Estado, caché, cabezal y cinta de ID_k+1 son los que indica esa regla | `TraceError` |

La traza nunca se trunca: `len(trace.entries) == result.steps + 1`.

### 6.2 Notación (`src/output/id_formatter.py`, `src/utils/notation.py`)

Se usa la notación del Laboratorio 10, X1…Xi-1 [q,c] Xi…Xn: la tupla de control
`[estado,caché]` se escribe inmediatamente antes del símbolo bajo el cabezal.

| Elemento | Convención | Ejemplo |
|---|---|---|
| Tupla de control en una ID | `[q,c]`, sin espacio | `Bab[q3,B]#Xab` |
| Regla de δ | Notación del enunciado | `δ([q0, B], a) = ([q1, a], B, R)` |
| Blanco | `B`; si `B` es símbolo de Γ o valor de caché, el primer carácter libre desde `□` (`□`, `▢`, …; `blank_glyph`) | `[q0,B]B` |
| Rango visible | De `min(0, cabezal, celdas no blancas)` a `max(longitud(w) − 1, cabezal, celdas no blancas)` | `BBB#XXXB[q5,B]B` |

El rango incluye siempre la zona donde se escribió la entrada, para conservar
los blancos que la máquina deja sobre ella (como en `BBB#XXXB[q5,B]B`), y
siempre incluye el cabezal, aunque esté en una posición negativa
(`[qhalt,B]BB00`, Laboratorio 9) o sobre un blanco después del contenido
(`ab[q1,B]B`). Las IDs completas nunca se recortan.

`format_id_lines(trace)` produce la tabla «Paso | ID | Transición aplicada».
La fila k muestra la regla que transformó ID_k−1 en ID_k, por lo que cada fila
se reconstruye a mano a partir de la anterior. Las primeras filas de
`aab#aab` con la máquina del Laboratorio 10 (los estados se llaman `0`…`5`
en ese YAML):

```text
Paso  ID              Transición aplicada
   0  [0,B]aab#aab    —
   1  B[1,a]ab#aab    δ([0, B], a) = ([1, a], B, R)
   2  Ba[1,a]b#aab    δ([1, a], a) = ([1, a], a, R)
   3  Bab[1,a]#aab    δ([1, a], b) = ([1, a], b, R)
   4  Bab#[2,a]aab    δ([1, a], #) = ([2, a], #, R)
   5  Bab[3,B]#Xab    δ([2, a], a) = ([3, B], X, L)
```

Coinciden con las IDs resueltas a mano en el Laboratorio 10, inciso b, y la ID
final es `BBB#XXXB[5,B]B` (`tests/test_id_formatter.py`).

## 7. Procedimiento de los laboratorios en la salida de la CLI

`python main.py --machine <archivo>` presenta los nueve pasos de la tabla del
§2 en la salida estándar, en el mismo orden en que se resolvían a mano los
laboratorios 9 y 10:

| Paso | En la salida |
|---|---|
| 1–2. Componentes formales y δ | Bloque inicial `Q`, `Σ`, `Γ`, `q0`, `F`, `B` y la tabla δ completa, numerada en el orden del YAML |
| 3. Configuración inicial | Fila 0 de la tabla de IDs: `[q0,B]w` |
| 4–6. Leer, buscar δ, escribir y mover | Columna «Transición aplicada» de cada fila |
| 7. Registrar la nueva ID | Una fila por ID, de ID_0 a ID_n, sin recortar |
| 8. Condición de parada | `Resultado` y `Motivo` (regla faltante, estado final o límite de pasos) |
| 9. Resultado | `Cinta final`, `ID final`, vista de la cinta y resumen |

Las dos máquinas de demostración y sus recorridos a mano están en
`docs/test_cases.md`.
