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

## 4. Contrato YAML del curso y búsqueda en δ

### 4.1 Evidencia de las fuentes

| # | Fuente | Evidencia |
|---|---|---|
| E1 | Enunciado, p. 2 (`estructura-mt.yaml`) | «para definir el símbolo de blank, usaremos null o None, que en yaml se expresa con una entrada vacía» |
| E2 | Enunciado, p. 2 | `δ([q0, B], a) = ([q1, a], B, R)`: la caché es el segundo componente de la tupla de control |
| E3 | Enunciado, p. 3 (`example_mt_1.yaml`) | Esa regla se escribe con `params.mem_cache_value` vacío (B), `output.mem_cache_value: a` y `tape_output` vacío (B) |
| E4 | Enunciado, p. 2 | `mem_cache_value`: «Puede ser blank o contener algo»; `tape_displacement`: «L, R o S» |
| E5 | Enunciado, pp. 2–3 | `final` singular (`'5'`); estados entre comillas (`'0'`…`'5'`); `"#"` entre comillas |
| E6 | Enunciado, p. 2 | `tape_alphabet` «incluye los símbolos de alphabet también» |
| E7 | Laboratorio 10, ejercicio 1 | La máquina completa del ejemplo: L = {α#α}, Σ = {a, b, #}, Γ = {a, b, #, B, X}, F = {q5}; ID inicial `[q0, B]aab#aab` (caché inicial B) |
| E8 | Deck, «Language of a TM» | L(M) = {w ∈ Σ* \| q0w ⊢* αpβ, p ∈ F} |
| E9 | Laboratorio 9, ejercicio 3 | Se definen reglas salientes de q_acc y se pide omitirlas: no influyen en la aceptación |

### 4.2 Decisiones adoptadas

| # | Decisión | Fundamento |
|---|---|---|
| D1 | El blanco es exactamente el `null` de YAML (entrada vacía, `null` o `~`), que PyYAML entrega como `None`. `'B'`, `'None'`, `'null'` y `''` **no** son el blanco: `'B'` es un símbolo ordinario y `''` es inválido | E1, E3 |
| D2 | La clave de δ es (estado, caché, símbolo leído); la caché inicial es el blanco | E2, E3, E7 |
| D3 | La caché es un único valor de la unidad de control (no tiene cabezal ni posiciones; no es una segunda cinta). Su dominio es el blanco o cualquier cadena no vacía; no se restringe a Γ porque ninguna fuente lo exige | E2, E4 |
| D4 | δ es una función: dos reglas con la misma clave, idénticas o en conflicto, son un error de configuración | Determinismo (deck, «The Turing Machine») |
| D5 | Si no hay regla para la clave actual, la MT se detiene; nunca se infiere una regla implícita | Hopcroft et al. (2001), δ parcial |
| D6 | Un estado de F es terminal: alcanzarlo acepta y detiene la simulación. Las reglas que salen de F se admiten, pero nunca se ejecutan | E8, E9 |
| D7 | Estados, símbolos y cadenas deben ser cadenas YAML; los valores numéricos o booleanos se rechazan con la indicación de entrecomillarlos (`'0'`), en lugar de convertirlos | E5; YAML 1.1 lee `0101` como 65 y `yes` como `True` |
| D8 | Cada símbolo de Σ y de Γ es un único carácter. En Σ es necesario porque `simulation_strings` se escribe sin separadores (`aab#aab`); en Γ mantiene inequívoca la ID `X1…Xi-1 q Xi…Xn` | E3, E5; deck, «Instantaneous Descriptions» |

### 4.3 Equivalencia YAML → modelo

| YAML (`delta[i]`) | `Transition` | Blanco permitido |
|---|---|---|
| `params.initial_state` | `state` | No |
| `params.mem_cache_value` | `cache` | Sí |
| `params.tape_input` | `read` | Sí |
| `output.final_state` | `next_state` | No |
| `output.mem_cache_value` | `next_cache` | Sí |
| `output.tape_output` | `write` | Sí |
| `output.tape_displacement` | `move` (`Move[...]`) | No |

Las siete claves son obligatorias en cada regla; una clave presente con valor
vacío significa blanco, una clave ausente es un error.

### 4.4 Búsqueda

`TuringMachine.find_transition(state, cache, symbol) -> Transition | None`
consulta un diccionario construido una sola vez al crear la máquina, en tiempo
O(1) esperado. Los duplicados se detectan en esa construcción (D4) con las
posiciones de ambas reglas. `None` significa «no hay regla» (D5).

### 4.5 Observaciones sobre el ejemplo del enunciado

El enunciado declara su ejemplo como **incompleto** y, tal como está impreso,
no satisface la definición formal: `tape_alphabet` omite `a` y `b` (E6), y las
cadenas usan `#`, que no aparece en `alphabet` (E7 confirma Σ = {a, b, #}).
Además, su segunda regla escribe `a` en la caché al leer `b`, mientras que el
texto indica `([q1, b], B, R)`. El simulador no corrige silenciosamente esos
datos: el parser acepta la estructura y la validación reporta cada
inconsistencia. La versión completa y ejecutable es la máquina del Laboratorio
10 (E7).

## 5. Entrada

Toda falla de entrada es una subclase de `InputError` (`src/input/errors.py`,
a su vez `ValueError`). Un error de entrada se reporta antes de simular y nunca
se confunde con el rechazo de una cadena.

### 5.1 Carga (`src/input/yaml_loader.py`)

`load_yaml(path) -> dict` lee el archivo como UTF-8 (admite BOM) y lo interpreta
con `yaml.safe_load` (PyYAML, s. f.), que no construye objetos de Python. Lanza
`YamlLoadError` si el archivo no existe o no se puede leer, no es UTF-8, tiene
sintaxis inválida, está vacío, contiene varios documentos o su raíz no es un
mapeo.

### 5.2 Interpretación (`src/input/machine_parser.py`)

`parse_machine(document) -> tuple[TuringMachine, list[str]]` aplica la
equivalencia de §4.3 y devuelve la máquina con `simulation_strings` en el orden
del archivo. Comprueba **estructura y tipos** y lanza `MachineParseError` con la
ruta del campo (`delta[3].output.tape_displacement`):

- claves obligatorias presentes (las claves adicionales se ignoran);
- `q_list`, `alphabet`, `tape_alphabet`, `delta` y `simulation_strings` son listas;
- estados y símbolos son cadenas no vacías, sin conversión de tipos (D7);
- el blanco solo se admite en `tape_alphabet`, `mem_cache_value`, `tape_input`
  y `tape_output` (D1);
- `final` es un estado o una lista de estados;
- `tape_displacement` es exactamente `L`, `R` o `S`;
- no hay elementos repetidos en las listas de estados y alfabetos;
- no hay dos reglas con la misma clave (D4, detectado por `TuringMachine`);
- cada cadena de `simulation_strings` es una cadena YAML; `''` es la entrada vacía.

**Archivos de ejemplo.** `machines/examples/basic_machine.yaml` es la máquina
del Laboratorio 10 en el formato del enunciado (20 reglas con w ∈ {a, b}
expandido) y sirve como referencia ejecutable para las pruebas.
`tests/fixtures/statement_example_mt_1.yaml` transcribe literalmente el ejemplo
incompleto del enunciado para comprobar la compatibilidad del parser.

### 5.3 Validación (`src/input/machine_validator.py`)

`validate_machine(machine, strings) -> None` comprueba la definición formal y
reúne **todos** los problemas en un único `MachineValidationError`, cuya lista
`errors` indica el campo YAML de cada uno. No modifica la máquina.

| Regla | Campo reportado |
|---|---|
| Q no vacío; q0 ∈ Q; F no vacío y F ⊆ Q | `q_states.*` |
| Σ no vacío; B ∉ Σ; B ∈ Γ; Σ ⊆ Γ | `alphabet`, `tape_alphabet` |
| Símbolos de un carácter (D8) | `alphabet`, `tape_alphabet` |
| Estados de cada regla ∈ Q; lectura y escritura ∈ Γ | `delta[i].params.*`, `delta[i].output.*` |
| Cada cadena ∈ Σ* | `simulation_strings[k]` |

No se valida: el dominio de la caché (D3) ni las reglas que salen de F (D6).
La separación de responsabilidades es: estructura y tipos en el parser,
determinismo en `TuringMachine`, coherencia entre componentes en el validador.

## 6. Interfaz pública del Gate 01

Firmas vigentes según el código probado. El Gate 02 consume estas interfaces
sin modificar el núcleo; cualquier extensión debe hacerse con interfaz
explícita y pruebas.

```python
# src/input
load_yaml(path: str | Path) -> dict[str, Any]                            # YamlLoadError
parse_machine(document: Mapping[str, Any]) -> tuple[TuringMachine, list[str]]  # MachineParseError
validate_machine(machine: TuringMachine, strings: list[str]) -> None     # MachineValidationError (.errors)
# Todas las excepciones anteriores heredan de InputError (ValueError).

# src/model
BLANK = None                                         # símbolo blanco; Symbol = str | None
Move.L / Move.R / Move.S                             # .value = -1 / +1 / 0; .name = "L" / "R" / "S"
Transition(state, cache, read, next_state, next_cache, write, move)       # .key
TuringMachine(states, input_alphabet, tape_alphabet, initial_state, final_states, transitions)
TuringMachine.find_transition(state, cache, symbol) -> Transition | None
Tape(cells=None); Tape.from_input(word); .read(i); .write(i, s); .snapshot()
Configuration(step_index, state, cache, head, tape, applied=None)        # .scanned
SimulationResult(word, outcome, configurations, reason)                  # .final, .steps
Outcome.ACCEPTED / Outcome.REJECTED / Outcome.LIMIT_EXCEEDED

# src/simulator
step(machine: TuringMachine, current: Configuration) -> Configuration | None
simulate(machine: TuringMachine, word: str, max_steps: int = DEFAULT_MAX_STEPS) -> SimulationResult
DEFAULT_MAX_STEPS = 10_000
```

Flujo mínimo de uso:

```python
document = load_yaml(path)
machine, strings = parse_machine(document)
validate_machine(machine, strings)
for word in strings:
    result = simulate(machine, word)
    for config in result.configurations:   # ID_0 … ID_n
        ...                                 # config.state, .cache, .head, .tape, .applied
    result.outcome, result.reason, result.final.tape
```

Para dibujar una ID: las celdas no blancas son `config.tape` (posición →
símbolo); toda otra posición es blanco. La porción visible va desde
`min([config.head, *config.tape])` hasta `max([config.head, *config.tape])`.
