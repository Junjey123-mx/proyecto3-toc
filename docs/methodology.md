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
