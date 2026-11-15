# Proyecto No. 3 — Máquinas de Turing

Simulador de máquinas de Turing de una cinta escrito en Python. Lee la descripción formal de la máquina y sus cadenas de prueba desde un archivo YAML con el formato del enunciado, valida la definición, ejecuta las transiciones declaradas y muestra, para cada cadena, todas las descripciones instantáneas (IDs), la cinta final y si la cadena se acepta o se rechaza.

**Curso:** CC2019 — Teoría de la Computación
**Universidad:** Universidad del Valle de Guatemala
**Profesor:** Ing. Bidkar Pojoy

**Integrantes:**
- Vernel Josué Hernández Cáceres — 24584
- Derek Friedhelm Coronado Chilin — 24732

## Video explicativo

**Estado:** pendiente de grabación y publicación. El enlace no listado de YouTube se agregará en esta sección cuando el video exista. El guion, los comandos y la evidencia de la demostración están en [§22](#22-demostración-y-video).

---

## Índice

1. [Objetivo del proyecto](#1-objetivo-del-proyecto)
2. [Requisitos del enunciado y rúbrica](#2-requisitos-del-enunciado-y-rúbrica)
3. [Metodología adoptada](#3-metodología-adoptada)
4. [Fundamento formal](#4-fundamento-formal)
5. [Arquitectura](#5-arquitectura)
6. [Modelo de datos](#6-modelo-de-datos)
7. [Contrato YAML](#7-contrato-yaml)
8. [Motor de simulación y condiciones de parada](#8-motor-de-simulación-y-condiciones-de-parada)
9. [Descripciones instantáneas](#9-descripciones-instantáneas)
10. [Máquina reconocedora](#10-máquina-reconocedora)
11. [Máquina alteradora](#11-máquina-alteradora)
12. [Dificultad de las máquinas](#12-dificultad-de-las-máquinas)
13. [Decisiones de implementación en Python](#13-decisiones-de-implementación-en-python)
14. [Estrategia de validación](#14-estrategia-de-validación)
15. [Pruebas automatizadas](#15-pruebas-automatizadas)
16. [Instalación y ejecución](#16-instalación-y-ejecución)
17. [Resultados de la demostración](#17-resultados-de-la-demostración)
18. [Ejemplo completo](#18-ejemplo-completo)
19. [Discusión](#19-discusión)
20. [Limitaciones y alcance](#20-limitaciones-y-alcance)
21. [Organización del proyecto](#21-organización-del-proyecto)
22. [Demostración y video](#22-demostración-y-video)
23. [Desarrollo y autoría](#23-desarrollo-y-autoría)
24. [Referencias bibliográficas](#24-referencias-bibliográficas)

---

## 1. Objetivo del proyecto

**Objetivo general.** Implementar un simulador determinista, configurable y verificable de máquinas de Turing (MT) de una cinta que reproduzca fielmente las transiciones y las descripciones instantáneas de cada ejecución.

**Objetivos específicos.** Los cinco primeros son los objetivos específicos del enunciado; los dos últimos son del equipo.

1. Interpretar la configuración de la MT escrita en YAML (estados, alfabetos, δ).
2. Interpretar las cadenas de entrada que se colocan en la cinta (`simulation_strings`).
3. Diseñar las estructuras de datos que alojan la máquina, la cinta y cada configuración, y que permiten simular usando solo las funciones de transición descritas.
4. Mostrar la descripción instantánea de cada paso de la simulación.
5. Decidir la aceptación o el rechazo de cada entrada.
6. Distinguir la aceptación, el rechazo, la detención por el límite de pasos y los errores de configuración.
7. Diseñar, verificar y documentar una MT reconocedora y una MT alteradora para la demostración.

El programa:

1. lee un archivo YAML con la máquina y su lista de cadenas;
2. valida la estructura, los tipos y la coherencia formal, y reporta cada error con el campo exacto (`delta[4].output.final_state`);
3. imprime la descripción formal de la máquina con su tabla δ completa;
4. simula cada cadena desde la configuración inicial `[q0,B]w`, aplicando una regla de δ por paso;
5. imprime, por cadena, el resultado y su motivo, la cinta final, la ID final y la tabla completa «Paso | ID | Transición aplicada»;
6. termina con un resumen de todas las cadenas.

Ninguna parte del código de Python conoce las máquinas de la demostración: las dos se definen solo en YAML y las ejecuta el mismo motor.

## 2. Requisitos del enunciado y rúbrica

| Requisito del enunciado | Cómo se cumple | Sección |
|---|---|---|
| Leer un archivo YAML con la estructura indicada | `load_yaml` (PyYAML seguro) y `parse_machine` con las claves exactas del enunciado | [§7](#7-contrato-yaml) |
| Solo MT de una cinta | Una única cinta dispersa; la caché es un valor de la unidad de control, no una segunda cinta | [§4](#4-fundamento-formal) |
| El YAML incluye las cadenas a simular | `simulation_strings`, simuladas en el orden del archivo | [§7.1](#71-estructura-del-archivo) |
| El alfabeto de la cinta contiene al de entrada | El validador exige Σ ⊆ Γ y B ∈ Γ, B ∉ Σ | [§7.5](#75-validaciones) |
| Simular con las transiciones del YAML | `step` aplica δ([q, c], X) leída del archivo; no hay reglas implícitas | [§8](#8-motor-de-simulación-y-condiciones-de-parada) |
| Listado completo de IDs por cadena | Tabla de ID_0 a ID_n, sin recortar, con la regla aplicada en cada paso | [§9](#9-descripciones-instantáneas) |
| Indicar «aceptada» si la ID final contiene un estado final | `ACCEPTED`, con el motivo «alcanzó el estado final» | [§8](#8-motor-de-simulación-y-condiciones-de-parada) |
| Indicar «rechazada» si se detiene sin transición aplicable | `REJECTED`, con el estado, la caché y el símbolo sin regla | [§8](#8-motor-de-simulación-y-condiciones-de-parada) |
| MT reconocedora: 2 aceptadas y 2 rechazadas de longitud ≥ 5 | L = {aⁿbⁿ \| n ≥ 1}: `aaabbb`, `aaaabbbb` aceptadas; `aaabb`, `aabbbb` rechazadas | [§10](#10-máquina-reconocedora) |
| MT alteradora: 4 cadenas de longitud ≥ 5, sin dejar todo en blanco | Incremento binario: `10101`, `11011`, `11111`, `10000` | [§11](#11-máquina-alteradora) |
| Proporcionar las funciones de transición | Tablas δ en este README y en la cabecera de la salida del programa | [§10.4](#104-tabla-de-transiciones), [§11.5](#115-tabla-de-transiciones) |
| Video no listado con las ejecuciones y la arquitectura | Pendiente; guion preparado | [§22](#22-demostración-y-video) |
| Repositorio privado y README en la raíz | Repositorio privado en GitHub; este archivo | — |

**Decisiones propias (no exigidas por el enunciado).** El resultado `LIMIT_EXCEEDED` y la opción `--max-steps`, los estados finales terminales, la exigencia de símbolos de un solo carácter, el rechazo de claves YAML repetidas y la notación exacta de la cinta y del blanco. Se explican en [§7.4](#74-decisiones-adoptadas), [§8](#8-motor-de-simulación-y-condiciones-de-parada) y [§13](#13-decisiones-de-implementación-en-python).

**Rúbrica oficial (15 puntos).** La tabla indica qué evidencia aporta el repositorio para cada rubro. No es una nota prevista: la dificultad no tiene una escala definida en el enunciado y el video todavía no existe.

| Rubro | Puntos | Evidencia en el repositorio |
|---|---:|---|
| Reconocedora: 2 cadenas aceptadas | 2 | `aaabbb` (25 pasos) y `aaaabbbb` (41 pasos), [§17](#17-resultados-de-la-demostración) |
| Reconocedora: 2 cadenas no aceptadas | 2 | `aaabb` (17 pasos) y `aabbbb` (12 pasos), con su motivo |
| Dificultad de la reconocedora | 3 | Definición, tabla δ, corrección y número de pasos, [§10](#10-máquina-reconocedora) y [§12](#12-dificultad-de-las-máquinas) |
| Alteradora: 4 cadenas | 4 | Cuatro transformaciones de longitud 5, incluido el desbordamiento `11111 → 100000` |
| Dificultad de la alteradora | 3 | Acarreo, desbordamiento a la posición −1 y caché, [§11](#11-máquina-alteradora) y [§12](#12-dificultad-de-las-máquinas) |
| Discusión de la arquitectura | 1 | [§5](#5-arquitectura); debe explicarse además en el video |
| **Total** | **15** | |

## 3. Metodología adoptada

El simulador mecaniza el procedimiento con el que se resolvieron a mano los laboratorios 9 y 10 del curso. Cada paso del procedimiento tiene un equivalente en el código y una evidencia en la salida:

| Paso | Procedimiento de los laboratorios | Código | En la salida |
|---|---|---|---|
| 1 | Identificar Q, Σ, Γ, q0, B, F y δ | `load_yaml` → `parse_machine` → `validate_machine` | Bloque inicial `Q`, `Σ`, `Γ`, `q0`, `F`, `B` |
| 2 | Construir la tabla de transiciones | Índice de `TuringMachine` por (estado, caché, lectura) | Tabla δ numerada en el orden del YAML |
| 3 | Establecer la configuración inicial `[q0,B]w` | `simulate`: ID_0 con caché en blanco y cabezal en 0 | Fila 0 de la tabla de IDs |
| 4 | Leer el símbolo bajo el cabezal | `Configuration.scanned` | — |
| 5 | Buscar δ([q, c], X) | `TuringMachine.find_transition` | Columna «Transición aplicada» |
| 6 | Escribir, cambiar estado y caché, mover | `step` | Fila siguiente de la tabla |
| 7 | Registrar la nueva ID sin borrar las anteriores | `SimulationResult.configurations` (IDs inmutables) | Una fila por ID, de ID_0 a ID_n |
| 8 | Comprobar la condición de parada | `simulate` | `Resultado` y `Motivo` |
| 9 | Presentar IDs, cinta final y veredicto | `build_trace` → `src/output/` → `main.py` | `Cinta final`, `ID final`, vista de la cinta y resumen |

**¿Por qué mostrar todas las IDs?** El enunciado pide el listado completo, y es la forma de comprobar a mano cada paso: la fila k muestra la regla que transformó ID_k−1 en ID_k, de modo que cualquier fila se reconstruye a partir de la anterior. Por eso las IDs nunca se recortan, aunque la traza sea larga.

## 4. Fundamento formal

Una MT determinista de una cinta es M = (Q, Σ, Γ, δ, q0, B, F) (Hopcroft et al., 2001; Pojoy Corzo, 2026):

| Componente | Significado |
|---|---|
| Q | Conjunto finito de estados |
| Σ | Alfabeto de entrada, Σ ⊆ Γ |
| Γ | Alfabeto de la cinta |
| δ | Función parcial de transición |
| q0 ∈ Q | Estado inicial |
| B ∈ Γ \ Σ | Símbolo blanco |
| F ⊆ Q | Estados de aceptación |

**Caché.** El YAML del curso agrega a cada regla un valor `mem_cache_value` en la lectura y en la salida. El enunciado escribe sus reglas como `δ([q0, B], a) = ([q1, a], B, R)`: la caché es el segundo componente de la tupla de control. Se modela como «almacenamiento en el estado» (Hopcroft et al., 2001, §8.3.1), sin cabezal ni posiciones:

```text
δ : (Q × C) × Γ ⇀ (Q × C) × Γ × {L, R, S}
```

donde C es el dominio de valores de caché, que incluye el blanco. La caché inicial es el blanco.

**Movimientos.** Si δ([q, c], Xi) = ([p, c'], Y, D), con la tupla de control escrita inmediatamente antes del símbolo bajo el cabezal:

| D | ID_k | ID_k+1 |
|---|---|---|
| L | X1…Xi-1 [q, c] Xi…Xn | X1…Xi-2 [p, c'] Xi-1 Y Xi+1…Xn |
| R | X1…Xi-1 [q, c] Xi…Xn | X1…Xi-1 Y [p, c'] Xi+1…Xn |
| S | X1…Xi-1 [q, c] Xi…Xn | X1…Xi-1 [p, c'] Y Xi+1…Xn |

**Lenguaje aceptado.** L(M) = {w ∈ Σ* | [q0, B] w ⊢* α [p, c] β, p ∈ F}. Si no hay regla para la configuración actual y el estado no es final, la máquina se detiene y la cadena se rechaza.

## 5. Arquitectura

```text
machines/*.yaml
      │
      v
src/input        load_yaml → parse_machine → validate_machine
      │
      v
src/model        TuringMachine (δ indexada por estado, caché y símbolo)
                 Transition · Move · Tape · Configuration · SimulationResult · Outcome
      │
      v
src/simulator    step (una transición) → simulate (bucle y parada) → build_trace (Trace)
      │
      v
src/output       id_formatter · tape_formatter · result_formatter     (src/utils/notation.py)
      │
      v
main.py          CLI: --machine ARCHIVO [--max-steps N]
```

| Capa | Archivos | Responsabilidad | No hace |
|---|---|---|---|
| Entrada | `src/input/` | Leer, interpretar y validar el YAML | Ejecutar la máquina |
| Modelo | `src/model/` | Representar M, δ, la cinta, las IDs y los resultados con sus invariantes | Leer archivos ni imprimir |
| Simulador | `src/simulator/` | Aplicar δ, decidir la parada y verificar la traza | Formatear ni leer archivos |
| Salida | `src/output/`, `src/utils/notation.py` | Convertir la traza en texto (IDs, cinta, resultado) | Modificar el historial ni aplicar δ |
| CLI | `main.py` | Orquestar lectura → simulación → presentación | Duplicar el motor |
| Pruebas | `tests/` | Ejercitar cada capa por separado y el sistema completo | — |

Las dependencias van en un solo sentido: la salida depende del simulador y del modelo, el simulador del modelo, y el modelo de nada más. Los formateadores son funciones puras: reciben una `Trace` y devuelven líneas de texto. La CLI solo encadena `load_yaml → parse_machine → validate_machine → simulate → build_trace → format_*`.

Flujo mínimo de uso desde Python:

```python
machine, strings = parse_machine(load_yaml("machines/recognizer_anbn.yaml"))
validate_machine(machine, strings)
for word in strings:
    trace = build_trace(simulate(machine, word))   # ID_0 … ID_n verificadas
    print("\n".join(format_result(trace)))
```

## 6. Modelo de datos

| Clase | Contenido | Invariantes |
|---|---|---|
| `Transition` (`src/model/transition.py`) | `state, cache, read → next_state, next_cache, write, move` | Inmutable; `key = (state, cache, read)` |
| `Move` | `L = -1`, `R = +1`, `S = 0` | El valor es el desplazamiento del cabezal |
| `TuringMachine` (`turing_machine.py`) | `states, input_alphabet, tape_alphabet, initial_state, final_states, transitions` | Inmutable; conjuntos como `frozenset`; δ como tupla en el orden del YAML; detecta claves duplicadas |
| `Tape` (`tape.py`) | Celdas no blancas, `dict[int, str]` | Blanco implícito; índices negativos permitidos; escribir el blanco borra la celda |
| `Configuration` (`configuration.py`) | `step_index, state, cache, head, tape, applied` | Inmutable; `tape` es una copia de solo lectura; `applied` es la regla que produjo la ID (`None` en ID_0) |
| `SimulationResult` (`simulation_result.py`) | `word, outcome, configurations, reason` | Al menos ID_0; `steps` = número de IDs − 1 |
| `Outcome` | `ACCEPTED`, `REJECTED`, `LIMIT_EXCEEDED` | Un límite de pasos nunca es un rechazo |
| `Trace`, `TraceEntry` (`src/simulator/trace.py`) | Copia de las IDs lista para presentarse: paso, estado, caché, cabezal, cinta, símbolo leído y regla | Se construye solo si cada ID_k+1 es la aplicación de su regla a ID_k |

**Blanco.** `BLANK = None`. Una celda ausente de la cinta contiene el blanco, de modo que `tape.get(i)` aplica directamente la semántica de la MT.

**Cinta dispersa.** Solo se guardan las celdas no blancas (Klein, 2025, usa la misma idea). El cabezal puede salir del input por cualquiera de los dos lados sin desplazar el contenido. Una cinta matemáticamente infinita no implica memoria infinita: la cinta ocupa tantas celdas como símbolos no blancos tenga.

**Interfaz pública.**

```python
load_yaml(path) -> dict                                   # YamlLoadError
parse_machine(document) -> tuple[TuringMachine, list[str]]  # MachineParseError
validate_machine(machine, strings) -> None                # MachineValidationError (.errors)
TuringMachine.find_transition(state, cache, symbol) -> Transition | None
step(machine, configuration) -> Configuration | None
simulate(machine, word, max_steps=10_000) -> SimulationResult
build_trace(result) -> Trace                              # TraceError
format_id(entry, input_length, blank) -> str
format_id_lines(trace, blank) -> list[str]
format_result(trace, number, total, blank) -> list[str]
format_summary(traces, blank) -> list[str]
blank_glyph(machine) -> str; format_rule(rule, blank) -> str
```

Todas las excepciones de entrada heredan de `InputError` (a su vez `ValueError`).

## 7. Contrato YAML

### 7.1 Estructura del archivo

```yaml
q_states:
  q_list: [q0, q1, q2]        # Q
  initial: q0                  # q0
  final: q2                    # F (un estado o una lista)
alphabet: ['0', '1']           # Σ
tape_alphabet: ['0', '1', ~]   # Γ; el blanco es null (entrada vacía, null o ~)
delta:
- params:
    initial_state: q0          # estado actual
    mem_cache_value:           # caché leída (vacía = blanco)
    tape_input: '0'            # símbolo leído
  output:
    final_state: q0            # estado siguiente
    mem_cache_value:           # caché escrita
    tape_output: '0'           # símbolo escrito
    tape_displacement: R       # L, R o S
simulation_strings: ['10101', '11011']
```

Las siete claves de cada regla son obligatorias: una clave presente con valor vacío significa blanco y una clave ausente es un error. Las cadenas de `simulation_strings` se escriben sin separadores; `''` es la entrada vacía.

### 7.2 Equivalencia YAML → modelo

| YAML (`delta[i]`) | `Transition` | Admite blanco |
|---|---|---|
| `params.initial_state` | `state` | No |
| `params.mem_cache_value` | `cache` | Sí |
| `params.tape_input` | `read` | Sí |
| `output.final_state` | `next_state` | No |
| `output.mem_cache_value` | `next_cache` | Sí |
| `output.tape_output` | `write` | Sí |
| `output.tape_displacement` | `move` | No |

Los campos de `Transition` no repiten los nombres `initial_state`/`final_state` del YAML para no confundirlos con el estado inicial y los estados finales de la máquina.

### 7.3 Evidencia para el blanco y la caché

| # | Fuente | Evidencia |
|---|---|---|
| E1 | Enunciado, p. 2 | El blanco se escribe como `null`/`None`, «que en yaml se expresa con una entrada vacía» |
| E2 | Enunciado, p. 2 | `δ([q0, B], a) = ([q1, a], B, R)`: la caché es el segundo componente de la tupla de control |
| E3 | Enunciado, p. 3 | Esa regla se escribe con `params.mem_cache_value` vacío, `output.mem_cache_value: a` y `tape_output` vacío |
| E4 | Enunciado, p. 2 | `mem_cache_value` «puede ser blank o contener algo»; `tape_displacement` es L, R o S |
| E5 | Enunciado, pp. 2–3 | `final` singular; estados y `"#"` entre comillas |
| E6 | Enunciado, p. 2 | `tape_alphabet` incluye los símbolos de `alphabet` |
| E7 | Laboratorio 10, ejercicio 1 | Máquina completa para {α#α}: ID inicial `[q0, B]aab#aab`, caché inicial B |
| E8 | Deck del curso, «Language of a TM» | L(M) = {w ∈ Σ* \| q0w ⊢* αpβ, p ∈ F} |
| E9 | Laboratorio 9, ejercicio 3 | Las reglas que salen del estado de aceptación no influyen en la aceptación |

### 7.4 Decisiones adoptadas

| # | Decisión | Fundamento |
|---|---|---|
| D1 | El blanco es exactamente el `null` de YAML. `'B'`, `'None'`, `'null'` y `''` no son el blanco: `'B'` es un símbolo ordinario y `''` es inválido | E1, E3 |
| D2 | La clave de δ es (estado, caché, símbolo leído); la caché inicial es el blanco | E2, E3, E7 |
| D3 | La caché es un único valor de la unidad de control, no una segunda cinta. Su dominio es el blanco o cualquier cadena no vacía | E2, E4 |
| D4 | δ es una función: dos reglas con la misma clave, idénticas o en conflicto, son un error | Determinismo |
| D5 | Si no hay regla para la clave actual, la MT se detiene; nunca se infiere una regla implícita | δ parcial |
| D6 | Un estado de F es terminal: alcanzarlo acepta. Las reglas que salen de F se admiten, pero nunca se ejecutan | E8, E9 |
| D7 | Estados, símbolos y cadenas deben ser cadenas YAML; los números o booleanos se rechazan con la indicación de entrecomillarlos | E5; YAML 1.1 lee `0101` como 65 y `yes` como `True` |
| D8 | Cada símbolo de Σ y de Γ es un único carácter, porque `simulation_strings` se escribe sin separadores y la ID debe ser inequívoca | E3, E5 |

### 7.5 Validaciones

**Carga** (`src/input/yaml_loader.py`). El archivo se lee como UTF-8 (admite BOM) con el `SafeLoader` de PyYAML, que no construye objetos de Python (PyYAML, s. f.). Una subclase de `SafeLoader` agrega el rechazo de **claves repetidas**, porque PyYAML conservaría en silencio el último valor. Se reportan: archivo inexistente o ilegible, codificación inválida, sintaxis inválida, escalares imposibles (`2026-13-01`), claves repetidas, archivo vacío, varios documentos y raíz que no es un mapeo.

**Interpretación** (`src/input/machine_parser.py`). Comprueba estructura y tipos, con la ruta del campo en cada error: claves obligatorias; listas donde corresponde; estados y símbolos como cadenas no vacías (D7); el blanco solo en `tape_alphabet`, `mem_cache_value`, `tape_input` y `tape_output`; `final` como estado o lista; desplazamiento `L`, `R` o `S`; listas sin repetidos; ninguna clave de δ duplicada (D4).

**Validación** (`src/input/machine_validator.py`). Reúne todos los problemas de coherencia en un solo error:

| Regla | Campo reportado |
|---|---|
| Q no vacío; q0 ∈ Q; F no vacío y F ⊆ Q | `q_states.*` |
| Σ no vacío; B ∉ Σ; B ∈ Γ; Σ ⊆ Γ | `alphabet`, `tape_alphabet` |
| Símbolos de un carácter (D8) | `alphabet`, `tape_alphabet` |
| Estados de cada regla ∈ Q; lectura y escritura ∈ Γ | `delta[i].params.*`, `delta[i].output.*` |
| Cada cadena ∈ Σ* | `simulation_strings[k]` |

Ejemplos reales de mensajes:

```text
error: delta[4].output.tape_displacement: debe ser L, R o S, no 'X'
error: la máquina no es válida:
- simulation_strings[3]: '10201' usa símbolos fuera de alphabet: ['2']
```

Un error de entrada termina el programa con código 1 antes de simular cualquier cadena: nunca se confunde con el rechazo de una cadena.

### 7.6 Observaciones sobre el ejemplo del enunciado

El enunciado declara su ejemplo como incompleto y, tal como está impreso, no satisface la definición formal: `tape_alphabet` omite `a` y `b` (E6) y las cadenas usan `#`, que no aparece en `alphabet`. Además, su segunda regla escribe `a` en la caché al leer `b`, mientras que el texto indica `([q1, b], B, R)`. El simulador no corrige esos datos en silencio: el parser acepta la estructura y la validación reporta cada inconsistencia (`tests/fixtures/statement_example_mt_1.yaml`). La versión completa y ejecutable es la máquina del Laboratorio 10, en `machines/examples/basic_machine.yaml` (20 reglas).

## 8. Motor de simulación y condiciones de parada

`step(machine, current)` (`src/simulator/step.py`) ejecuta una sola transición:

1. leer el símbolo bajo el cabezal (blanco si la celda no existe);
2. buscar δ([estado, caché], símbolo);
3. si no hay regla, devolver `None` sin modificar nada;
4. escribir el símbolo de salida en una copia de la cinta (el blanco borra la celda);
5. tomar el nuevo estado y la nueva caché;
6. mover el cabezal (L = −1, R = +1, S = 0), incluso a posiciones negativas;
7. devolver una `Configuration` nueva con el paso siguiente y la regla aplicada.

`simulate(machine, word, max_steps)` (`src/simulator/engine.py`) repite `step` y decide la parada:

```text
simulate(M, w, max_steps):
    si max_steps < 1 o w ∉ Σ*: error
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
| El estado actual ∈ F | `ACCEPTED` | Definición de L(M); D6 |
| No hay regla para (estado, caché, lectura) | `REJECTED` | Enunciado: «terminar la ejecución sin poder aplicar una función de transición» |
| Hay regla, pero ya se aplicaron `max_steps` transiciones | `LIMIT_EXCEEDED` | Salvaguarda operativa |

**¿Por qué `LIMIT_EXCEEDED` no es un rechazo?** El problema de la parada no es decidible (kenjinote, 2026): una máquina que sigue ejecutándose tras 10 000 pasos podría detenerse más adelante. Informarla como rechazada sería afirmar algo que el simulador no sabe. Por eso la cota solo se aplica si la máquina aún puede continuar: una MT que se detiene, en F o sin regla, justo tras `max_steps` transiciones se acepta o se rechaza normalmente.

Cada llamada a `simulate` crea su propia ID_0, de modo que las cadenas de un archivo no comparten cinta, caché ni historial.

`build_trace(result)` (`src/simulator/trace.py`) copia las IDs y verifica, sin volver a ejecutar la máquina, que la secuencia sea una computación válida: ID_0 sin regla aplicada, pasos consecutivos, clave de cada regla igual a (estado, caché, símbolo leído) de la ID anterior, y estado, caché, cabezal y cinta de cada ID iguales a los que indica la regla. Si algo no coincide, lanza `TraceError`. La traza nunca se trunca: tiene `steps + 1` IDs.

## 9. Descripciones instantáneas

Se usa la notación del Laboratorio 10, X1…Xi-1 [q,c] Xi…Xn: la tupla de control `[estado,caché]` se escribe inmediatamente antes del símbolo bajo el cabezal.

| Elemento | Convención | Ejemplo |
|---|---|---|
| Tupla de control en una ID | `[q,c]`, sin espacio | `Bab[q3,B]#Xab` |
| Regla de δ | Notación del enunciado | `δ([q0, B], a) = ([q1, a], B, R)` |
| Blanco | `B`; si `B` es un símbolo de Γ o un valor de caché, el primer carácter libre desde `□` (`□`, `▢`, …) | `[q0,B]B` |
| Rango visible | De `min(0, cabezal, celdas no blancas)` a `max(\|w\| − 1, cabezal, celdas no blancas)` | `BBB#XXXB[q5,B]B` |

El rango incluye siempre la zona donde se escribió la entrada, para conservar los blancos que la máquina deja sobre ella, e incluye siempre el cabezal, aunque esté en una posición negativa (`[q2,B]100000` empieza en la posición −1) o sobre un blanco después del contenido (`11111[q0,B]B`). La caché se lee en el segundo componente de `[q,c]`.

Primeras IDs reales de `aab#aab` con la máquina del Laboratorio 10 (en ese YAML los estados se llaman `0`…`5`):

```text
Paso  ID              Transición aplicada
   0  [0,B]aab#aab    —
   1  B[1,a]ab#aab    δ([0, B], a) = ([1, a], B, R)
   2  Ba[1,a]b#aab    δ([1, a], a) = ([1, a], a, R)
   3  Bab[1,a]#aab    δ([1, a], b) = ([1, a], b, R)
   4  Bab#[2,a]aab    δ([1, a], #) = ([2, a], #, R)
   5  Bab[3,B]#Xab    δ([2, a], a) = ([3, B], X, L)
  …
  32  BBB#XXXB[5,B]B  δ([4, B], B) = ([5, B], B, R)
```

Coinciden con las IDs resueltas a mano en el Laboratorio 10, inciso b, incluida la ID final `BBB#XXXB[q5,B]B`.

## 10. Máquina reconocedora

**Archivo:** `machines/recognizer_anbn.yaml` · **Lenguaje:** L = {aⁿbⁿ | n ≥ 1}. Diseño de Derek (Gate 02), basado en Hopcroft et al. (2001), ejemplo 8.2, para {0ⁿ1ⁿ | n ≥ 1}, con a/b en lugar de 0/1.

### 10.1 Definición formal

| Componente | Valor |
|---|---|
| Q | {q0, q1, q2, q3, q4} |
| Σ | {a, b} |
| Γ | {a, b, X, Y, B} |
| q0 | q0 |
| F | {q4} |
| Caché | No se usa: vale B en todas las reglas |

`X` reemplaza a una `a` ya emparejada y `Y` a una `b` ya emparejada. La caché no aporta nada a este algoritmo, porque el estado ya distingue la fase del barrido.

### 10.2 Papel de cada estado

| Estado | Papel |
|---|---|
| q0 | Inicio de una ronda: marca con `X` la `a` más a la izquierda sin emparejar; si encuentra `Y`, ya no quedan `a` y pasa a la verificación |
| q1 | Busca hacia la derecha la primera `b` sin emparejar, cruzando `a` y `Y`, y la marca con `Y` |
| q2 | Regresa hacia la izquierda, cruzando `a` y `Y`, hasta la última `X` |
| q3 | Verificación final: solo deben quedar `Y` hasta el primer blanco |
| q4 | Aceptación (estado final, terminal) |

### 10.3 Algoritmo

1. **Marcar** (q0): si el símbolo es `a`, escribir `X` y moverse a la derecha.
2. **Buscar** (q1): cruzar `a` y `Y` hacia la derecha; en la primera `b`, escribir `Y` y moverse a la izquierda.
3. **Regresar** (q2): cruzar `a` y `Y` hacia la izquierda; al encontrar `X`, moverse a la derecha y volver a q0.
4. **Comprobar** (q0 → q3): si q0 lee `Y`, todas las `a` están marcadas; q3 cruza las `Y` y acepta en el primer blanco.

Cualquier otra combinación (estado, lectura) no tiene regla: la máquina se detiene fuera de F y la cadena se rechaza.

### 10.4 Tabla de transiciones

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

La numeración coincide con el orden del YAML y con la que imprime el programa. Claves sin regla y lo que detectan:

| Clave sin regla | Situación |
|---|---|
| (q0, B, b) | La cadena empieza con `b` o tiene una `b` antes de alguna `a` sin marcar |
| (q0, B, B) | Entrada vacía (n = 0 no pertenece a L) |
| (q1, B, B) | Sobran `a`: no queda `b` para emparejar |
| (q3, B, b) | Sobran `b` |
| (q3, B, a) | Hay una `a` después de las `b` |

### 10.5 Corrección y número de pasos

**Toda cadena aceptada es aⁿbⁿ con n ≥ 1.** La única regla que escribe el blanco (10) lo hace sobre una celda que ya estaba en blanco, así que las celdas 0 … |w|−1 siguen ocupadas y el primer blanco a la derecha está en |w|. Cada ronda completa (reglas 1, 5 y 8) convierte exactamente una `a` en `X` y una `b` en `Y`, y las `X` ocupan las posiciones 0, 1, …, k−1, porque q0 siempre marca la celda contigua a la última `X`. Para aceptar, q0 debe leer `Y` en la posición k tras k rondas y q3 debe cruzar solo `Y` hasta la posición |w|. Entonces la cinta es XᵏYˡ con k + l = |w|, y como hubo k rondas, l = k. Las `X` provienen de `a` y las `Y` de `b`, por lo que w = aᵏbᵏ, con k ≥ 1 porque en la primera visita a q0 la posición 0 nunca contiene `Y`.

**Toda cadena aⁿbⁿ con n ≥ 1 es aceptada.** En la ronda j (1 ≤ j ≤ n), q0 marca la `a` de la posición j−1, q1 cruza n−j letras `a` y j−1 letras `Y` y marca la `b` de la posición n+j−1, y q2 regresa hasta la `X` de la posición j−1. Tras n rondas, q0 lee la `Y` de la posición n, q3 cruza las n `Y` y en la posición 2n lee el blanco y acepta.

**Pasos.** Cada ronda aplica 1 + (n−1) + 1 + (n−1) + 1 = 2n + 1 reglas y la comprobación final 1 + (n−1) + 1 = n + 1. En total T(n) = n(2n + 1) + n + 1 = **2n² + 2n + 1**: 13 pasos para `aabb`, 25 para `aaabbb` y 41 para `aaaabbbb`. La complejidad es O(n²), porque cada ronda recorre la cadena de ida y vuelta.

### 10.6 Recorridos a mano

**`aabb`** (aceptada, 13 pasos):

| Paso | ID | Regla | Paso | ID | Regla |
|---|---|---|---|---|---|
| 0 | `[q0,B]aabb` | — | 7 | `XXY[q1,B]b` | 4 |
| 1 | `X[q1,B]abb` | 1 | 8 | `XX[q2,B]YY` | 5 |
| 2 | `Xa[q1,B]bb` | 3 | 9 | `X[q2,B]XYY` | 7 |
| 3 | `X[q2,B]aYb` | 5 | 10 | `XX[q0,B]YY` | 8 |
| 4 | `[q2,B]XaYb` | 6 | 11 | `XXY[q3,B]Y` | 2 |
| 5 | `X[q0,B]aYb` | 8 | 12 | `XXYY[q3,B]B` | 9 |
| 6 | `XX[q1,B]Yb` | 1 | 13 | `XXYYB[q4,B]B` | 10 |

**`abb`** (rechazada, 4 pasos): `[q0,B]abb ⊢ X[q1,B]bb ⊢ [q2,B]XYb ⊢ X[q0,B]Yb ⊢ XY[q3,B]b`. En ID_4 no hay regla para (q3, B, b) y q3 ∉ F: sobra una `b`.

### 10.7 Cadenas de la demostración

| Cadena | Longitud | Resultado | Pasos | Motivo |
|---|---|---|---|---|
| `aaabbb` | 6 | ACCEPTED | 25 | n = 3, T(3) = 25 |
| `aaaabbbb` | 8 | ACCEPTED | 41 | n = 4, T(4) = 41 |
| `aaabb` | 5 | REJECTED | 17 | Tras dos rondas de 7 reglas, q1 cruza `YY` y llega al blanco: falta una `b` (7 + 7 + 3) |
| `aabbbb` | 6 | REJECTED | 12 | Tras dos rondas de 5 reglas, q3 cruza `YY` y lee `b`: sobran dos `b` (5 + 5 + 2) |

## 11. Máquina alteradora

**Archivo:** `machines/transformer_binary_increment.yaml` · **Función:** sucesor binario. Diseño de Derek (Gate 02).

### 11.1 Función calculada

Para una cadena binaria no vacía w (bit más significativo a la izquierda), f(w) = representación binaria de value₂(w) + 1. La salida conserva los ceros a la izquierda (`0011 → 0100`) y, cuando todos los bits son 1, agrega un `1` a la izquierda (`11111 → 100000`), de modo que nunca se pierde el acarreo. Esa es la diferencia con la máquina del Laboratorio 9, ejercicio 2, que conserva la longitud y convierte `11` en `00`.

### 11.2 Definición formal

| Componente | Valor |
|---|---|
| Q | {q0, q1, q2} |
| Σ | {0, 1} |
| Γ | {0, 1, B} |
| q0 | q0 |
| F | {q2} |
| Caché | Registro de acarreo c ∈ {B, 1}: `1` = acarreo pendiente, B = sin acarreo |

En el YAML, `'0'`, `'1'` y el valor de caché `'1'` van entre comillas (D7).

### 11.3 Estados y caché

| Estado | Caché | Papel |
|---|---|---|
| q0 | B | Barrido a la derecha hasta el primer blanco después del número |
| q1 | 1 | Propagación del acarreo de derecha a izquierda: suma c al bit leído |
| q2 | B | Fin: el acarreo se absorbió (estado final, terminal) |

La tupla [q, c] guarda el acarreo de la suma. Al llegar al final del número, la regla 3 carga c = 1 (el «+1»). Cada regla de q1 calcula x + c sobre el bit leído x: si el resultado es 10, escribe 0 y conserva c = 1; si es 1, escribe 1, vacía la caché y se detiene. Por eso la ID final siempre muestra `[q2,B]`.

### 11.4 Algoritmo

1. **Barrido** (q0): cruzar los bits hacia la derecha sin modificarlos.
2. **Carga del acarreo** (q0 → q1): en el primer blanco, cargar c = 1 en la caché y moverse al bit menos significativo.
3. **Propagación** (q1, c = 1): cada `1` se reemplaza por `0` y el acarreo continúa a la izquierda.
4. **Fin** (q1 → q2): el primer `0` se reemplaza por `1`, la caché se vacía y la máquina se detiene sin moverse.
5. **Desbordamiento** (q1 → q2): si se agotan los bits, q1 lee el blanco a la izquierda del número, escribe ahí `1` y se detiene; el resultado tiene un bit más.

### 11.5 Tabla de transiciones

| # | Regla | Paso del algoritmo |
|---|---|---|
| 1 | δ([q0, B], 0) = ([q0, B], 0, R) | Barrido |
| 2 | δ([q0, B], 1) = ([q0, B], 1, R) | Barrido |
| 3 | δ([q0, B], B) = ([q1, 1], B, L) | Carga el acarreo inicial c = 1 |
| 4 | δ([q1, 1], 1) = ([q1, 1], 0, L) | 1 + 1 = 10: escribe 0, el acarreo sigue |
| 5 | δ([q1, 1], 0) = ([q2, B], 1, S) | 0 + 1 = 1: escribe 1, vacía la caché y se detiene |
| 6 | δ([q1, 1], B) = ([q2, B], 1, S) | Desbordamiento: nuevo bit más significativo |

Las seis claves son distintas. Ninguna regla sale de q2 y q1 solo se alcanza con c = 1, por lo que no hacen falta reglas para (q1, B, ·). Con una entrada binaria, la máquina siempre se detiene en q2: el resultado es `ACCEPTED` y la salida es el contenido final de la cinta.

### 11.6 Índice negativo, cinta final y número de pasos

- La entrada ocupa las posiciones 0 … |w|−1. En el desbordamiento, q1 llega a la posición −1 y escribe ahí el `1` nuevo; la cinta dispersa admite posiciones negativas, así que no hace falta desplazar la entrada.
- La regla 3 escribe el blanco sobre una celda que ya estaba en blanco y ninguna otra regla escribe el blanco: el resultado no tiene blancos intermedios ni laterales, y la cinta nunca queda vacía (el caso que el enunciado excluye).
- **Salida:** el contenido de la cinta desde la primera hasta la última celda no blanca (`tape_contents`); un blanco intermedio se mostraría como `B`.
- **Pasos:** si w termina en t unos, T(w) = |w| + 1 + t + 1 = **|w| + t + 2** (barrido, carga del acarreo, t propagaciones y la regla que se detiene). En el desbordamiento, t = |w| y T = 2|w| + 2.
- **Entrada vacía:** no forma parte del dominio de f, pero las reglas la procesan como el número 0 y la salida es `1`.

### 11.7 Recorrido a mano: `11111 → 100000`

| Paso | ID | Regla | Paso | ID | Regla |
|---|---|---|---|---|---|
| 0 | `[q0,B]11111` | — | 7 | `111[q1,1]10` | 4 |
| 1 | `1[q0,B]1111` | 2 | 8 | `11[q1,1]100` | 4 |
| 2 | `11[q0,B]111` | 2 | 9 | `1[q1,1]1000` | 4 |
| 3 | `111[q0,B]11` | 2 | 10 | `[q1,1]10000` | 4 |
| 4 | `1111[q0,B]1` | 2 | 11 | `[q1,1]B00000` | 4 |
| 5 | `11111[q0,B]B` | 2 | 12 | `[q2,B]100000` | 6 |
| 6 | `1111[q1,1]1` | 3 | | | |

En ID_11 el cabezal está en la posición −1. La regla 6 escribe el `1` nuevo y la cinta final, de −1 a 4, es `100000`.

### 11.8 Recorrido a mano: `10101 → 10110`

`[q0,B]10101 ⊢ 1[q0,B]0101 ⊢ 10[q0,B]101 ⊢ 101[q0,B]01 ⊢ 1010[q0,B]1 ⊢ 10101[q0,B]B ⊢ 1010[q1,1]1 ⊢ 101[q1,1]00 ⊢ 101[q2,B]10`, con las reglas 2, 1, 2, 1, 2, 3, 4 y 5: 8 pasos.

### 11.9 Cadenas de la demostración

| Cadena | Longitud | Salida | Pasos (\|w\| + t + 2) |
|---|---|---|---|
| `10101` | 5 | `10110` | 5 + 1 + 2 = 8 |
| `11011` | 5 | `11100` | 5 + 2 + 2 = 9 |
| `11111` | 5 | `100000` | 5 + 5 + 2 = 12 |
| `10000` | 5 | `10001` | 5 + 0 + 2 = 7 |

## 12. Dificultad de las máquinas

La rúbrica asigna 3 puntos a la dificultad de cada máquina, pero no define una escala. En el Gate 03 se decidió **conservar las dos máquinas**: ambas son correctas frente a oráculos independientes, {aⁿbⁿ | n ≥ 1} es el ejemplo que el propio enunciado propone para la reconocedora, y sustituir máquinas verificadas antes de la entrega aumentaría el riesgo sin un criterio de evaluación conocido. No se afirma ninguna puntuación.

| Máquina | Elementos de dificultad | Lo que no se afirma |
|---|---|---|
| Reconocedora | 5 estados y 10 reglas; dos marcadores (`X`, `Y`); barridos de ida y vuelta en cada ronda; cinco claves sin regla, cada una con un motivo de rechazo distinto; demostración de corrección; T(n) = 2n² + 2n + 1 | Que sea un diseño original: es el ejemplo 8.2 de Hopcroft et al. (2001), citado. No usa la caché |
| Alteradora | Escritura real sobre la cinta; propagación del acarreo; desbordamiento hacia la posición −1 sin desplazar la entrada; sin blancos residuales; conserva los ceros a la izquierda; T(w) = \|w\| + t + 2 | Que la caché sea indispensable: vale `1` exactamente cuando el estado es q1, así que el estado ya codifica el acarreo. Se usa para mostrar el mecanismo `mem_cache_value` en la clave de lectura y en el valor escrito |

Si el equipo decide reforzar este rubro, la alternativa es agregar una máquina cuyo algoritmo dependa de la caché (por ejemplo, invertir una cadena, como sugiere el enunciado, o reconocer w#w llevando el símbolo pendiente en la caché), definida solo en YAML, con su propia tabla δ, un oráculo independiente y commits separados.

## 13. Decisiones de implementación en Python

- **Cinta dispersa `dict[int, str]`.** Permite índices negativos y crecimiento hacia ambos lados sin desplazar el contenido; leer una celda ausente devuelve el blanco.
- **Modelos inmutables.** `@dataclass(frozen=True)`, `frozenset` y `MappingProxyType` para las cintas de cada ID. Una ID histórica no puede cambiar después de registrarse, así que la traza nunca muestra referencias a la cinta final.
- **δ indexada una sola vez.** `TuringMachine` construye al crearse un diccionario por (estado, caché, símbolo): búsqueda en O(1) esperado y detección de reglas duplicadas con su posición.
- **PyYAML seguro y estricto.** `SafeLoader` con rechazo de claves repetidas; sin conversión de tipos implícita (D7).
- **Errores acumulados.** El validador informa todos los problemas de una máquina a la vez, con la ruta del campo, en lugar de detenerse en el primero.
- **Traza verificada.** `build_trace` comprueba cada paso contra su regla; los formateadores solo convierten texto.
- **Blanco sin ambigüedad.** `blank_glyph` usa `B`, como los laboratorios, salvo que la máquina use `B` como símbolo o valor de caché; entonces busca el primer carácter libre desde `□`.
- **Salida en UTF-8.** `main.py` reconfigura `stdout` y `stderr` a UTF-8 para imprimir δ, ⊢ y ε también en consolas de Windows o con la salida redirigida.
- **Solo biblioteca estándar más PyYAML.** `argparse` para la CLI; `pytest` solo para las pruebas.

## 14. Estrategia de validación

1. **Oráculos independientes del simulador.** La pertenencia a {aⁿbⁿ} se calcula con su definición y el sucesor binario con `int(w, 2) + 1`; ninguno usa el motor.
2. **Pruebas exhaustivas.** Todas las cadenas sobre {a, b} de longitud ≤ 10 (2047) en la reconocedora y todas las binarias de longitud 1 a 10 (2046) en la alteradora, a nivel de biblioteca. A nivel de CLI, en un proceso aparte, todas las de longitud 0 a 8 sobre {a, b} (511) y 1 a 9 binarias (1022).
3. **Reproducción de δ desde el YAML.** Para las ocho cadenas de la demostración, cada ID_k+1 se recalcula a partir de ID_k con la δ leída directamente del archivo con `yaml.safe_load`, sin el parser ni el motor del proyecto.
4. **Fórmulas cerradas.** Los pasos reales se comparan con T(n) = 2n² + 2n + 1 y T(w) = |w| + t + 2.
5. **Equivalencia con los laboratorios.** Los resultados resueltos a mano se usan como oráculos:

| Laboratorio | Entrada | Resultado a mano | Simulador |
|---|---|---|---|
| 10 b) | `aab#aab` | `[q0,B]aab#aab ⊢^32 BBB#XXXB[q5,B]B`, aceptada | `ACCEPTED`, 32 transiciones, mismas IDs |
| 10 c) | `abb#aab` | `⊢^13 BBb#X[q2,b]ab`, δ([q2,b], a) no definida | `REJECTED`, 13 transiciones, estado 2, caché b |
| 9, ej. 2 a) | `100` | 5 pasos, `101 q_halt B` | 5 transiciones, cinta `101` |
| 9, ej. 2 b) | `10011` | 9 pasos, `101 q_halt 00` | 9 transiciones, cinta `10100` |
| 9, ej. 2 c) | `11` | 6 pasos, `q_halt BB00` | 6 transiciones, cinta `00`, cabezal −2 |

6. **Casos límite.** Cinta vacía, cabezal en posiciones negativas, estado final con reglas salientes, máquina sin reglas, detención exacta en `max_steps`, cadenas fuera de Σ, YAML inválido, claves repetidas y símbolos Unicode.
7. **Independencia.** Las mismas cadenas en otro orden, repetidas o intercaladas con otras producen reportes idénticos.

## 15. Pruebas automatizadas

```bash
python -m pytest -q
```

Resultado de la ejecución final en Fedora 43 con Python 3.14.6: **349 pruebas aprobadas, 0 fallidas, 0 omitidas**. La misma cifra se obtuvo en un entorno virtual nuevo instalado solo con `requirements.txt` a partir de `git archive`.

| Archivo | Pruebas | Contenido |
|---|---:|---|
| `test_yaml_loader.py` | 23 | Carga segura, UTF-8/BOM, claves repetidas, escalares inválidos, archivos vacíos o ilegibles |
| `test_parser.py` | 46 | Esquema del enunciado, tipos, blanco, `final` singular o lista, rutas de error |
| `test_validator.py` | 25 | Q, Σ, Γ, F, reglas y cadenas; todos los errores a la vez |
| `test_models.py` | 13 | Contratos e inmutabilidad de los modelos |
| `test_tape.py` | 8 | Cinta dispersa, blanco implícito, posiciones negativas |
| `test_transitions.py` | 9 | Índice de δ y duplicados |
| `test_step.py` | 12 | Paso atómico: escritura, movimiento, estado y caché |
| `test_engine.py` | 26 | Parada, límite de pasos, laboratorios 9 y 10 |
| `test_instantaneous_descriptions.py` | 16 | Traza completa, sin aliasing, verificación de cada paso |
| `test_id_formatter.py` | 19 | Notación de IDs, IDs de los laboratorios, blanco sin ambigüedad |
| `test_tape_formatter.py` | 14 | Contenido y vista de la cinta |
| `test_result_formatter.py` | 11 | Reporte y resumen; `LIMIT_EXCEEDED` nunca como rechazo |
| `test_cli.py` | 30 | Argumentos, errores, tabla δ en la cabecera, salida de ambas máquinas |
| `test_recognizer.py` | 37 | Demostración, recorridos a mano, fórmula de pasos, exhaustiva ≤ 10 |
| `test_transformer.py` | 25 | Demostración, desbordamiento en −1, caché, exhaustiva 1–10 |
| `test_integration.py` | 35 | Extremo a extremo por proceso aparte, oráculos, reproducción de δ, frontera de `max_steps`, independencia, errores de entrada, evidencia de `docs/evidence/` |

## 16. Instalación y ejecución

Requisitos: Python 3.10 o superior (el código usa la sintaxis `X | None`) y PyYAML. El proyecto se probó con Python 3.14.6 en Fedora 43 y, en el Gate 02, con Python 3.14.3 en Windows 11; no se probó en las versiones 3.10 a 3.13.

**Fedora / Linux** (comandos verificados):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python main.py --machine machines/recognizer_anbn.yaml
python main.py --machine machines/transformer_binary_increment.yaml
```

**Windows (PowerShell):** los mismos comandos, creando el entorno con `py -m venv .venv` y activándolo con `.venv\Scripts\Activate.ps1`. La instalación con `requirements.txt` y la suite se ejecutaron en Windows en el Gate 02; los comandos de activación del entorno no se volvieron a verificar en Windows.

| Argumento | Obligatorio | Descripción |
|---|---|---|
| `--machine ARCHIVO` | Sí | Archivo YAML con la máquina y su lista `simulation_strings` |
| `--max-steps N` | No | Máximo de transiciones por cadena (entero positivo; por defecto 10000) |

Otros ejemplos:

```bash
python main.py --machine machines/examples/basic_machine.yaml              # Laboratorio 10
python main.py --machine machines/recognizer_anbn.yaml --max-steps 30      # muestra LIMIT_EXCEEDED
python main.py --help
```

La salida estándar contiene, en este orden:

1. la descripción formal de la máquina (Q, Σ, Γ, q0, F, blanco) y la tabla δ completa, numerada en el orden del YAML;
2. por cada cadena: encabezado con la cadena y su longitud; `Resultado` (`ACCEPTED`, `REJECTED` o `LIMIT_EXCEEDED`) y `Motivo`; pasos, estado, caché y cabezal finales; `Cinta final`; `ID final`; vista de la cinta por posiciones con el cabezal; y la tabla completa «Paso | ID | Transición aplicada», de ID_0 a ID_n;
3. el bloque `=== Resumen ===`, con una fila por cadena.

| Código de salida | Significado |
|---|---|
| 0 | Todas las cadenas se simularon (aceptadas, rechazadas o detenidas por el límite) |
| 1 | El archivo no se pudo leer o la máquina no es válida; el detalle va a la salida de errores |
| 2 | Argumentos incorrectos |

## 17. Resultados de la demostración

Salida real de `python main.py --machine machines/recognizer_anbn.yaml` y `python main.py --machine machines/transformer_binary_increment.yaml` en la ejecución final. Coincide con los valores esperados de [§10.7](#107-cadenas-de-la-demostración) y [§11.9](#119-cadenas-de-la-demostración), y con los oráculos independientes.

| Máquina | Cadena | Longitud | Resultado | Pasos | Cinta final | ID final |
|---|---|---|---|---|---|---|
| Reconocedora | `aaabbb` | 6 | ACCEPTED | 25 | `XXXYYY` | `XXXYYYB[q4,B]B` |
| Reconocedora | `aaaabbbb` | 8 | ACCEPTED | 41 | `XXXXYYYY` | `XXXXYYYYB[q4,B]B` |
| Reconocedora | `aaabb` | 5 | REJECTED | 17 | `XXXYY` | `XXXYY[q1,B]B` |
| Reconocedora | `aabbbb` | 6 | REJECTED | 12 | `XXYYbb` | `XXYY[q3,B]bb` |
| Alteradora | `10101` | 5 | ACCEPTED | 8 | `10110` | `101[q2,B]10` |
| Alteradora | `11011` | 5 | ACCEPTED | 9 | `11100` | `11[q2,B]100` |
| Alteradora | `11111` | 5 | ACCEPTED | 12 | `100000` | `[q2,B]100000` |
| Alteradora | `10000` | 5 | ACCEPTED | 7 | `10001` | `1000[q2,B]1` |

Motivos de los rechazos:

- `aaabb`: «no hay regla para el estado 'q1' con caché el blanco leyendo el blanco, y 'q1' no es final» (falta una `b`).
- `aabbbb`: «no hay regla para el estado 'q3' con caché el blanco leyendo 'b', y 'q3' no es final» (sobran `b`).

En la alteradora, `ACCEPTED` significa que la máquina se detuvo normalmente en su estado final q2; el resultado de la transformación es la columna «Cinta final».

## 18. Ejemplo completo

Salida real de la alteradora: la cabecera y el reporte de la tercera cadena, `11111` (las otras tres cadenas y el resumen se omiten aquí).

```text
Máquina: machines/transformer_binary_increment.yaml
  Q  = {q0, q1, q2}
  Σ  = {0, 1}
  Γ  = {0, 1, B}
  q0 = q0
  F  = {q2}
  B  = B (blanco)
  δ  = 6 reglas, en el orden del YAML:
    1. δ([q0, B], 0) = ([q0, B], 0, R)
    2. δ([q0, B], 1) = ([q0, B], 1, R)
    3. δ([q0, B], B) = ([q1, 1], B, L)
    4. δ([q1, 1], 1) = ([q1, 1], 0, L)
    5. δ([q1, 1], 0) = ([q2, B], 1, S)
    6. δ([q1, 1], B) = ([q2, B], 1, S)
Cadenas: 4 · límite de pasos por cadena: 10000

=== Cadena 3 de 4: '11111' (longitud 5) ===
Resultado:     ACCEPTED (aceptada)
Motivo:        alcanzó el estado final 'q2'
Pasos:         12
Estado final:  q2
Caché final:   B
Cabezal final: -1
Cinta final:   100000
ID final:      [q2,B]100000

posición -1  0  1  2  3  4
cinta     1  0  0  0  0  0
cabezal   ^

Descripciones instantáneas (ID_0 a ID_12):
  Paso  ID            Transición aplicada
     0  [q0,B]11111   —
     1  1[q0,B]1111   δ([q0, B], 1) = ([q0, B], 1, R)
     2  11[q0,B]111   δ([q0, B], 1) = ([q0, B], 1, R)
     3  111[q0,B]11   δ([q0, B], 1) = ([q0, B], 1, R)
     4  1111[q0,B]1   δ([q0, B], 1) = ([q0, B], 1, R)
     5  11111[q0,B]B  δ([q0, B], 1) = ([q0, B], 1, R)
     6  1111[q1,1]1   δ([q0, B], B) = ([q1, 1], B, L)
     7  111[q1,1]10   δ([q1, 1], 1) = ([q1, 1], 0, L)
     8  11[q1,1]100   δ([q1, 1], 1) = ([q1, 1], 0, L)
     9  1[q1,1]1000   δ([q1, 1], 1) = ([q1, 1], 0, L)
    10  [q1,1]10000   δ([q1, 1], 1) = ([q1, 1], 0, L)
    11  [q1,1]B00000  δ([q1, 1], 1) = ([q1, 1], 0, L)
    12  [q2,B]100000  δ([q1, 1], B) = ([q2, B], 1, S)
```

La caché vale `1` mientras se propaga el acarreo (`[q1,1]`) y B al terminar (`[q2,B]`). La vista por posiciones muestra el índice −1 del bit nuevo.

## 19. Discusión

### Obstáculos encontrados

- **Semántica de `mem_cache_value`.** El enunciado no define cómo participa la caché en la búsqueda de reglas. Se fijó a partir de la notación δ([q, c], X) y del ejemplo del YAML (E2, E3) antes de escribir el parser, en lugar de ignorar el campo o convertirlo en una segunda cinta.
- **Ejemplo del enunciado incompleto.** No cumple Σ ⊆ Γ y usa símbolos fuera de Σ ([§7.6](#76-observaciones-sobre-el-ejemplo-del-enunciado)). Se decidió reportar esas inconsistencias en lugar de corregirlas en silencio.
- **YAML permisivo.** PyYAML conserva en silencio la última de dos claves repetidas y YAML 1.1 convierte `0101` en un número. Ambos casos cambiarían la máquina sin aviso; se rechazan explícitamente (`1065521`).
- **Detención exactamente en el límite.** Una primera versión del motor comprobaba el límite antes de buscar la regla, de modo que una máquina que se detenía sin regla justo tras `max_steps` transiciones se reportaba como `LIMIT_EXCEEDED`. Se corrigió en el Gate 01 (`093dffd`) y hay pruebas de esa frontera a nivel de motor y de CLI.
- **Portabilidad de las pruebas.** En Windows, `chmod(0)` no quita el permiso de lectura; la prueba de archivo ilegible se omite solo donde eso ocurre (`d43e572`).
- **Visibilidad de δ y blanco ambiguo.** La CLI mostraba solo el número de reglas y el glifo alternativo del blanco no se comparaba con Γ. Ambos se corrigieron en el Gate 03 (C24).

### Recomendaciones

- Definir siempre el blanco con una entrada vacía y entrecomillar los símbolos numéricos (`'0'`, `'1'`).
- Usar `--max-steps` bajo para explorar máquinas nuevas: un `LIMIT_EXCEEDED` indica que la máquina aún tenía reglas aplicables, no que rechace.
- Revisar la tabla δ impresa en la cabecera antes de leer las trazas: es exactamente la que ejecuta el motor.

## 20. Limitaciones y alcance

- Solo MT deterministas de una cinta. No hay multicinta ni no determinismo.
- Los estados finales son terminales: las reglas que salen de F se aceptan en el archivo, pero nunca se ejecutan.
- Cada símbolo de Σ y Γ es un único carácter. La caché admite cualquier cadena no vacía, pero no se valida contra Γ porque ninguna fuente lo exige.
- La tupla de control se escribe `[q,c]` sin escapar sus componentes: un estado o un valor de caché con `[`, `,` o `]` haría ambigua la ID. El validador no lo prohíbe; ninguna de las máquinas del proyecto usa esos caracteres.
- La cota por defecto es de 10 000 transiciones por cadena. Las trazas largas se imprimen completas (la reconocedora crece como 2n² + 2n + 1).
- La alteradora está diseñada para cadenas binarias no vacías (con ε produce `1`) y se detiene sobre el último bit modificado, sin regresar el cabezal al inicio.
- La rúbrica no define cómo se mide la dificultad de una máquina ([§12](#12-dificultad-de-las-máquinas)).
- Probado con Python 3.14; las versiones 3.10 a 3.13 no se probaron.

## 21. Organización del proyecto

```text
proyecto3-toc/
├── README.md
├── main.py                        CLI
├── requirements.txt               PyYAML, pytest
├── machines/
│   ├── recognizer_anbn.yaml       MT reconocedora (§10)
│   ├── transformer_binary_increment.yaml   MT alteradora (§11)
│   └── examples/basic_machine.yaml         máquina del Laboratorio 10
├── src/
│   ├── input/                     errors, yaml_loader, machine_parser, machine_validator
│   ├── model/                     transition, turing_machine, tape, configuration, simulation_result
│   ├── simulator/                 step, engine, trace
│   ├── output/                    id_formatter, tape_formatter, result_formatter
│   └── utils/notation.py          blanco, tupla de control y reglas de δ
├── tests/                         16 archivos de pruebas y fixtures/statement_example_mt_1.yaml
└── docs/
    ├── evidence/                  salida real de las dos demostraciones (§22.1)
    ├── handoff_gate_01_derek.md   entrega del Gate 01 al Gate 02
    └── handoff_gate_02_vernel.md  entrega del Gate 02 al Gate 03
```

Cada módulo incluye docstrings con su propósito y la propiedad formal que implementa. Los traspasos de `docs/` son registros de las entregas entre integrantes; el contenido técnico que antes estaba en `docs/architecture.md`, `docs/methodology.md` y `docs/test_cases.md` está integrado en este README.

## 22. Demostración y video

### 22.1 Evidencia en el repositorio

`docs/evidence/recognizer_anbn.txt` y `docs/evidence/transformer_binary_increment.txt` contienen la salida completa y real de los dos comandos de la demostración: la cabecera con la tabla δ, las cuatro cadenas con todas sus IDs y el resumen. `tests/test_integration.py` vuelve a ejecutar la CLI y comprueba que coincidan carácter por carácter, así que no pueden quedar desactualizados. Para regenerarlos, desde la raíz:

```bash
python main.py --machine machines/recognizer_anbn.yaml > docs/evidence/recognizer_anbn.txt
python main.py --machine machines/transformer_binary_increment.yaml > docs/evidence/transformer_binary_increment.txt
```

### 22.2 Guion del video

| Parte | Qué mostrar | Material | Rubro |
|---|---|---|---|
| 1. Presentación | Proyecto, integrantes y objetivo: simulador de MT de una cinta configurado con YAML | [§1](#1-objetivo-del-proyecto) | — |
| 2. Arquitectura | `main.py` → entrada → modelo → simulador → traza → salida; cinta dispersa, IDs inmutables, traza verificada | [§5](#5-arquitectura), [§6](#6-modelo-de-datos), [§8](#8-motor-de-simulación-y-condiciones-de-parada) | Arquitectura (1) |
| 3. Contrato YAML | Claves del enunciado, `mem_cache_value` dentro de [q, c], blanco = entrada vacía | [§7](#7-contrato-yaml) | — |
| 4. Reconocedora | Tabla δ completa (cabecera de la salida) y estrategia de marcar, buscar y regresar | [§10](#10-máquina-reconocedora) | Dificultad (3) |
| 5. Ejecución | `aaabbb` y `aaaabbbb` aceptadas; `aaabb` y `aabbbb` rechazadas, con su longitud, sus IDs y el motivo | [§17](#17-resultados-de-la-demostración) | Aceptadas (2), rechazadas (2) |
| 6. Alteradora | Tabla δ, acarreo en la caché y desbordamiento a la posición −1 | [§11](#11-máquina-alteradora) | Dificultad (3) |
| 7. Ejecución | `10101 → 10110`, `11011 → 11100`, `11111 → 100000`, `10000 → 10001`; la cinta final nunca queda en blanco | [§17](#17-resultados-de-la-demostración), [§18](#18-ejemplo-completo) | Cuatro cadenas (4) |
| 8. Motor único | Las dos máquinas son solo YAML; el código de Python no conoce ninguna | [§5](#5-arquitectura) | Arquitectura (1) |
| 9. Verificación y límites | `python -m pytest -q`, oráculos y limitaciones reales | [§14](#14-estrategia-de-validación), [§20](#20-limitaciones-y-alcance) | — |

Comandos de la grabación, verificados en Fedora:

```bash
python -m pytest -q
python main.py --machine machines/recognizer_anbn.yaml
python main.py --machine machines/transformer_binary_increment.yaml
```

Ninguna cadena necesita editarse en vivo: los dos archivos YAML ya contienen en `simulation_strings` exactamente las cuatro cadenas de cada demostración, todas de longitud ≥ 5.

## 23. Desarrollo y autoría

El proyecto se desarrolló en la rama `main`, sin ramas paralelas ni pull requests, en tres etapas consecutivas (Gates). Cada integrante publicó solo durante su etapa y entregó a la siguiente el SHA final, los resultados de las pruebas y las interfaces públicas.

| Gate | Responsable | Commits | Contenido |
|---|---|---|---|
| 01 | Vernel | C01–C09, 3 correcciones y el traspaso | Estructura, modelo, cinta, δ, carga y validación del YAML, paso atómico y motor |
| 02 | Derek | C10–C22, 1 corrección y el traspaso | Traza, formateadores de IDs, cinta y resultados, CLI, las dos máquinas, sus pruebas y su documentación |
| 03 | Vernel | C23–C26 | Pruebas de integración, observaciones del Gate 02, este README y la evidencia de entrega |

## 24. Referencias bibliográficas

### Enunciado del curso (fuente normativa)

- Universidad del Valle de Guatemala. (2026). *Proyecto No. 3* [Enunciado de proyecto]. CC2019 Teoría de la Computación.

### Material del curso

- Pojoy Corzo, B. A. (2026). *Theory of computation* [Diapositivas de clase]. CC2019 Teoría de la Computación, Universidad del Valle de Guatemala.

### Fundamentos teóricos de máquinas de Turing

- Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2001). *Introduction to automata theory, languages, and computation* (2nd ed.). Addison-Wesley. https://www.cs.columbia.edu/~toni/Courses/CSTheory2023/Handouts/Hopcroft-Motwani-Ullman-2001.pdf

### Implementación de máquinas de Turing en Python

- Klein, B. (2025, 21 de febrero). *9. Turing machine in Python*. Python Course. https://python-course.eu/applications-python/turing-machine.php

### Computabilidad y fundamentos introductorios

- kenjinote. (2026, 21 de septiembre). *Máquina de Turing y teoría de la computabilidad: El experimento mental de Alan Turing y el problema de la parada*. kenji.blog. https://kenji.blog/es/p/turing-machine-computability/

### Documentación técnica

- PyYAML. (s. f.). *PyYAML documentation*. https://pyyaml.org/wiki/PyYAMLDocumentation

---

El enunciado es la fuente de los requisitos y no se cuenta entre las cinco referencias de investigación. Hopcroft, Motwani y Ullman y el material del curso son el fundamento teórico: definición formal, IDs, almacenamiento en el estado (§8.3.1) y el ejemplo 8.2 en que se basa la reconocedora. Klein es la referencia técnica de la cinta dispersa en Python; kenjinote es material introductorio sobre la computabilidad y el problema de la parada, que justifica `LIMIT_EXCEEDED`; y la documentación de PyYAML respalda la carga segura de los archivos.
