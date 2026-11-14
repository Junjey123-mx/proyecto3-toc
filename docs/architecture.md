# Arquitectura del simulador

Simulador de máquinas de Turing (MT) deterministas de **una cinta**, cuya unidad
de control almacena además un valor de **caché**, tal como lo define el
enunciado del Proyecto No. 3 (`mem_cache_value`).

## 1. Capas

```text
YAML ─> src/input      load_yaml → parse_machine → validate_machine
            │
            v
        src/model      TuringMachine · Transition · Tape · Configuration · SimulationResult
            │
            v
        src/simulator  step (una transición) → simulate (bucle y parada)
            │
            v
        Gate 02        trace · output (formateadores) · CLI
```

| Capa | Responsabilidad | No hace |
|---|---|---|
| `input` | Leer, interpretar y validar el YAML | Ejecutar la máquina |
| `model` | Representar M, δ, cinta, IDs y resultados con sus invariantes | Leer archivos ni imprimir |
| `simulator` | Aplicar δ y decidir la parada | Formatear ni leer archivos |
| `output`/CLI (Gate 02) | Presentar IDs y resultados | Modificar el historial ni aplicar δ |

## 2. Modelo formal

M = (Q, Σ, Γ, δ, q0, B, F), con la caché como parte de la unidad de control
(Hopcroft et al., 2001, §8.3.1, «almacenamiento en el estado»):

```text
δ : (Q × C) × Γ ⇀ (Q × C) × Γ × {L, R, S}
```

donde C es el dominio de valores de caché (incluye el blanco). La notación del
enunciado es `δ([q0, B], a) = ([q1, a], B, R)`.

| Clase (`src/model/`) | Contenido | Invariantes |
|---|---|---|
| `Transition` | `state, cache, read → next_state, next_cache, write, move` | Inmutable; `move` es `Move`; `key = (state, cache, read)` |
| `Move` | `L = -1`, `R = +1`, `S = 0` | El valor es el desplazamiento del cabezal |
| `TuringMachine` | `states, input_alphabet, tape_alphabet, initial_state, final_states, transitions` | Inmutable; conjuntos como `frozenset`; δ como `tuple` en orden del YAML; `final_states` acepta un estado singular |
| `Configuration` | `step_index, state, cache, head, tape, applied` | Inmutable; `tape` es copia de solo lectura de las celdas no blancas; `applied` es la regla que produjo la ID (`None` en ID_0) |
| `SimulationResult` | `word, outcome, configurations, reason` | Al menos ID_0; `final` = última ID; `steps` = IDs − 1 |
| `Outcome` | `ACCEPTED`, `REJECTED`, `LIMIT_EXCEEDED` | Un límite de pasos nunca es un rechazo |

**Blanco.** `BLANK = None` (`src/model/transition.py`). Una celda ausente de
`Configuration.tape` contiene el blanco, por lo que `tape.get(i)` aplica
directamente la semántica de la MT.

**Nombres.** Los campos de `Transition` no repiten `initial_state`/`final_state`
del YAML para no confundirlos con el estado inicial y los estados finales de la
máquina; la equivalencia exacta está en el docstring de `Transition`.

## 3. Cinta

`Tape` (`src/model/tape.py`) es la cinta de trabajo: un `dict[int, str]` con
solo las celdas no blancas (Klein, 2025, usa la misma idea de cinta dispersa).

| Operación | Semántica |
|---|---|
| `Tape.from_input(word)` | `word[i]` en la posición `i`; blanco en el resto |
| `read(i)` | Símbolo almacenado o `None` (blanco) |
| `write(i, s)` | Escribe `s`; escribir `None` borra la celda |
| `snapshot()` | Copia de solo lectura (`MappingProxyType`) independiente de la cinta |

Las posiciones son enteros sin cota, incluidos los negativos, de modo que el
cabezal puede salir por la izquierda del input. La porción visible de una ID
(del primer al último no blanco, extendida hasta el cabezal) se obtiene de las
claves del snapshot y de `Configuration.head`; no se almacenan rangos visitados.
