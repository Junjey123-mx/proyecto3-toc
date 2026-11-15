# Entrega del Gate 01 al Gate 02

> **Nota posterior (Gate 03, C25):** el contenido de `docs/architecture.md`,
> `docs/methodology.md` y `docs/test_cases.md` se integró en el `README.md`.
> Las rutas citadas en este registro corresponden a la fecha de la entrega y
> se pueden consultar en el historial, p. ej. `git show 78d73b5:docs/test_cases.md`.

**De:** Vernel (C01–C09) · **Para:** Derek (C10–C22) · **Rama:** `main`

## 1. Estado recibido

| Commit | SHA | Mensaje |
|---|---|---|
| C01 | `2a56d90` | `chore: initialize Turing machine project structure` |
| C02 | `8227c3d` | `feat(model): define machine and transition contracts` |
| C03 | `0cfbb86` | `feat(model): implement sparse tape` |
| C04 | `0dbecc2` | `feat(model): implement transition lookup` |
| C05 | `12427b2` | `feat(input): load yaml safely` |
| C06 | `7f7cecf` | `feat(input): parse instructor yaml schema` |
| C07 | `41811b1` | `feat(input): validate machine definitions` |
| C08 | `cd73751` | `feat(simulator): execute atomic transition` |
| **C09** | **`5bf9feb`** | `feat(simulator): implement execution engine` |

Correcciones posteriores a C09, surgidas de la auditoría del Gate 01 (no estaban
en el roadmap):

| Commit | SHA | Motivo |
|---|---|---|
| C09+1 | `aadce5f` | `fix(gitignore): anchor local output patterns to repository root`: la regla `output/` de C01 ignoraba `src/output/`; ahora ese paquete está versionado |
| C09+2 | `1065521` | `fix(input): reject repeated keys and invalid scalars in yaml`: PyYAML aceptaba claves repetidas en silencio |
| C09+3 | `093dffd` | `fix(simulator): reject machines that halt exactly at the step limit` |

Este documento se agrega en un commit propio posterior. Antes de editar:

```bash
git status                       # árbol limpio
git pull --ff-only origin main   # si falla, detenerse y avisar; no forzar
python -m pip install -r requirements.txt
python -m pytest -q              # toda la suite debe pasar antes de C10
```

Requisitos: Python ≥ 3.10, PyYAML y pytest (`requirements.txt`).

## 2. Qué hay implementado

```text
YAML → load_yaml → parse_machine → validate_machine → simulate → SimulationResult
                                                        └─ step (una regla por llamada)
```

- `docs/architecture.md`: contrato YAML (§4), entrada (§5) e **interfaz pública** (§6).
- `docs/methodology.md`: paso atómico, motor, condiciones de parada, ejemplo ejecutado
  y equivalencia con los laboratorios 9 y 10.
- `machines/examples/basic_machine.yaml`: máquina del Laboratorio 10 (L = {α#α}) en
  el formato del enunciado; es la referencia ejecutable de las pruebas.

## 3. Uso desde la CLI y los formateadores

```python
from src.input.errors import InputError
from src.input.yaml_loader import load_yaml
from src.input.machine_parser import parse_machine
from src.input.machine_validator import validate_machine
from src.simulator.engine import simulate

try:
    machine, strings = parse_machine(load_yaml(path))
    validate_machine(machine, strings)
except InputError as error:      # archivo ilegible, YAML inválido o máquina incoherente
    ...                           # str(error) ya trae el campo (p. ej. delta[3].output.tape_output)

for word in strings:
    result = simulate(machine, word)          # simulate(machine, word, max_steps=N) para otra cota
```

`SimulationResult`:

| Campo | Contenido |
|---|---|
| `word` | Cadena simulada |
| `outcome` | `Outcome.ACCEPTED`, `Outcome.REJECTED` o `Outcome.LIMIT_EXCEEDED` |
| `configurations` | Tupla ID_0 … ID_n, en orden; `len = steps + 1` |
| `reason` | Motivo legible de la parada |
| `final` | Última ID |
| `steps` | Transiciones aplicadas |

Cada `Configuration` (inmutable) tiene `step_index`, `state`, `cache`, `head`,
`tape` (solo lectura, posición → símbolo, solo celdas no blancas), `applied`
(la `Transition` que la produjo; `None` en ID_0) y `scanned`. El blanco es
`None`: `config.tape.get(i)` devuelve `None` en cualquier celda en blanco. Una
`Transition` tiene `state, cache, read, next_state, next_cache, write, move`;
`move.name` es `"L"`, `"R"` o `"S"`.

## 4. Contrato YAML para escribir las dos máquinas

- **Blanco:** entrada vacía (`-` en listas, `clave:` sin valor). `B`, `'None'` o `''` no son el blanco.
- `tape_alphabet` debe incluir **todos** los símbolos de `alphabet` y el blanco.
- **Entrecomillar** todo lo que YAML leería como número o booleano: estados `'0'`,
  símbolos `'0'`/`'1'` y cadenas binarias `'10101'`. Sin comillas, el parser lo rechaza.
- `"#"` siempre entre comillas (en YAML `#` inicia un comentario).
- Cada símbolo es **un solo carácter**; cada cadena de `simulation_strings` solo usa símbolos de `alphabet`.
- Las siete claves de cada regla son obligatorias (`params`: `initial_state`,
  `mem_cache_value`, `tape_input`; `output`: `final_state`, `mem_cache_value`,
  `tape_output`, `tape_displacement`). Si la caché no se usa, déjela vacía en ambos lados.
- `tape_displacement`: exactamente `L`, `R` o `S`.
- No repetir una clave dentro del mismo mapeo (p. ej. dos `tape_input` en una regla
  copiada): el cargador lo rechaza con la línea del error.
- No puede haber dos reglas con el mismo (`initial_state`, `mem_cache_value`, `tape_input`).
- **Los estados finales son terminales:** al entrar a F la cadena se acepta y no se aplica
  ninguna otra regla. El rechazo es detenerse fuera de F sin regla aplicable.

Plantilla de una regla, δ([q0, B], '1') = ([q0, B], '1', R):

```yaml
- params:
    initial_state: q0
    mem_cache_value:
    tape_input: '1'
  output:
    final_state: q0
    mem_cache_value:
    tape_output: '1'
    tape_displacement: R
```

## 5. Archivos del Gate 02

| Commit | Archivos previstos |
|---|---|
| C10 | `src/simulator/trace.py` (las IDs ya son snapshots inmutables; no es necesario copiarlas otra vez) |
| C11–C13 | `src/output/id_formatter.py`, `tape_formatter.py`, `result_formatter.py`, `src/utils/notation.py` |
| C14 | `main.py` |
| C15–C20 | `machines/recognizer_anbn.yaml`, `machines/transformer_binary_increment.yaml`, `docs/test_cases.md` |
| C17, C20, C21 | `tests/test_recognizer.py`, `test_transformer.py`, `test_instantaneous_descriptions.py`, `test_cli.py` |

**Conservar sin cambios** salvo defecto reproducible y documentado: `src/model/`,
`src/input/`, `src/simulator/step.py`, `src/simulator/engine.py` y sus pruebas.

## 6. Observaciones para el Gate 02

- **Notación de IDs:** el Laboratorio 10 usa `X1…Xi-1 [q, c] Xi…Xn` con `B` para
  el blanco y conserva los blancos a la izquierda (`BBB#XXXB[q5,B]B`). Si se
  muestra el blanco como `B`, conviene no usar `B` como símbolo de cinta en las
  máquinas de demostración, porque `B` es un símbolo válido distinto del blanco.
- **Incremento binario:** la máquina del Laboratorio 9 (en `tests/test_engine.py`)
  pierde el acarreo (`11 → 00`); la máquina alteradora debe producir `11111 → 100000`.
  El cabezal puede moverse a posiciones negativas.
- `Configuration` no es *hashable* (su cinta es un `mappingproxy`); para comparar
  IDs use `==`.
- `simulate` lanza `ValueError` si la cadena usa símbolos fuera de Σ o si
  `max_steps < 1`; las cadenas del YAML ya se validan antes con `validate_machine`.
- `reason` está redactado en español para el usuario final; para decidir, use `outcome`.
- `LIMIT_EXCEEDED` solo aparece si, tras `max_steps` transiciones, todavía había una
  regla aplicable; no debe mostrarse como «rechazada».
