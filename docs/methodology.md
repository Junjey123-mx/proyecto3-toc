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
        si paso(ID) ≥ max_steps: devolver LIMIT_EXCEEDED
        siguiente ← step(M, ID)
        si siguiente = nada: devolver REJECTED
        historial.agregar(siguiente); ID ← siguiente
    devolver ACCEPTED
```

| Condición, en orden | Resultado | Fundamento |
|---|---|---|
| El estado actual ∈ F | `ACCEPTED` | L(M) = {w ∈ Σ* \| q0w ⊢* αpβ, p ∈ F} (deck); D6 |
| Se aplicaron `max_steps` transiciones | `LIMIT_EXCEEDED` | Salvaguarda operativa; la parada no es decidible (kenjinote, 2026) |
| No hay regla para (estado, caché, lectura) | `REJECTED` | Enunciado: «terminar la ejecución sin poder aplicar una función de transición» |

- La aceptación se comprueba primero: si F se alcanza exactamente en la
  transición `max_steps`, la cadena se acepta.
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
