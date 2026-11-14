# Entrega del Gate 02 al Gate 03

**De:** Derek (C10–C22) · **Para:** Vernel (C23–C26) · **Rama:** `main`

## 1. Estado entregado

Base recibida: `d818cfb` (`docs(handoff): document gate 01 interfaces for gate 02`).

| Commit | SHA | Autor | Mensaje |
|---|---|---|---|
| C09+4 | `d43e572` | dcoronado91 | `fix(tests): skip unreadable-file check where chmod cannot revoke read access` |
| C10 | `992da7e` | dcoronado91 | `feat(trace): capture immutable configurations` |
| C11 | `095e49b` | dcoronado91 | `feat(output): format instantaneous descriptions` |
| C12 | `d2b025a` | dcoronado91 | `feat(output): render tape and head` |
| C13 | `85febb4` | dcoronado91 | `feat(output): format simulation results` |
| C14 | `6ac71da` | dcoronado91 | `feat(cli): run yaml simulations` |
| C15 | `33873e7` | dcoronado91 | `docs(machine): formalize anbn recognizer` |
| C16 | `a64e304` | dcoronado91 | `feat(machine): add anbn recognizer yaml` |
| C17 | `862a810` | dcoronado91 | `test(machine): verify recognizer cases` |
| C18 | `c7ef952` | dcoronado91 | `docs(machine): formalize binary incrementer` |
| C19 | `a584f5f` | dcoronado91 | `feat(machine): add binary incrementer yaml` |
| C20 | `1e14611` | dcoronado91 | `test(machine): verify binary transformations` |
| C21 | `3b017a5` | dcoronado91 | `test(trace): verify cli and output contracts` |
| **C22** | **`5af9c73`** | dcoronado91 | `docs(machines): document demonstrations` |

**Commit adicional, fuera del roadmap (`d43e572`):** al recibir el Gate 01, la
suite fallaba en Windows en `tests/test_yaml_loader.py::test_unreadable_file`.
`chmod(0)` en Windows solo activa el atributo de solo lectura y el archivo sigue
siendo legible; el código de `load_yaml` era correcto. Ahora la prueba se omite
únicamente si el archivo sigue siendo legible después de `chmod(0)`. En Linux o
macOS sin root se sigue ejecutando igual que antes. No se modificó `src/input/`.

Este documento se agrega en un commit propio posterior a C22. Antes de editar:

```bash
git status                       # árbol limpio
git pull --ff-only origin main   # si falla, detenerse y avisar; no forzar
python -m pip install -r requirements.txt
python -m pytest -q
```

## 2. Comandos de ejecución

```bash
python main.py --machine machines/recognizer_anbn.yaml
python main.py --machine machines/transformer_binary_increment.yaml
python main.py --machine machines/examples/basic_machine.yaml --max-steps 500
python main.py --help
```

Códigos de salida: 0 si se simularon todas las cadenas, 1 si hay un error de
archivo o la máquina no es válida (mensaje en stderr) y 2 si los argumentos son
incorrectos. `LIMIT_EXCEEDED` no cambia el código de salida.

## 3. Resultados reales

`python -m pytest -q` (Windows 11, Python 3.14.3): **310 aprobadas, 1 omitida**
(`test_unreadable_file`, ver §1).

| Máquina | Cadena | Resultado | Pasos | Cinta final | ID final |
|---|---|---|---|---|---|
| Reconocedora | `aaabbb` | ACCEPTED | 25 | `XXXYYY` | `XXXYYYB[q4,B]B` |
| Reconocedora | `aaaabbbb` | ACCEPTED | 41 | `XXXXYYYY` | `XXXXYYYYB[q4,B]B` |
| Reconocedora | `aaabb` | REJECTED | 17 | `XXXYY` | `XXXYY[q1,B]B` |
| Reconocedora | `aabbbb` | REJECTED | 12 | `XXYYbb` | `XXYY[q3,B]bb` |
| Alteradora | `10101` | ACCEPTED | 8 | `10110` | `101[q2,B]10` |
| Alteradora | `11011` | ACCEPTED | 9 | `11100` | `11[q2,B]100` |
| Alteradora | `11111` | ACCEPTED | 12 | `100000` | `[q2,B]100000` |
| Alteradora | `10000` | ACCEPTED | 7 | `10001` | `1000[q2,B]1` |

Los pasos coinciden con los derivados a mano: T(n) = 2n² + 2n + 1 para aⁿbⁿ
y T(w) = |w| + t + 2 para el incremento, con t = unos finales
(`docs/test_cases.md`, §1.5 y §2.6).

| Archivo de pruebas | Pruebas | Contenido |
|---|---|---|
| `tests/test_instantaneous_descriptions.py` | 16 | Traza: `len = steps + 1`, no aliasing, 0 pasos, 500 pasos, caché, posiciones negativas, verificación de cada paso |
| `tests/test_id_formatter.py` | 18 | Notación de IDs: reproduce IDs del Lab 10 y del Lab 9, blancos, extremos, `□` |
| `tests/test_tape_formatter.py` | 14 | Contenido de cinta, vista por posiciones, cabezal, modo condensado |
| `tests/test_result_formatter.py` | 11 | Reporte por cadena y resumen; `LIMIT_EXCEEDED` nunca como rechazo |
| `tests/test_cli.py` | 28 | Argumentos, errores de archivo, integración YAML → stdout de ambas máquinas, Unicode, ejecuciones sucesivas |
| `tests/test_recognizer.py` | 37 | Demostración, recorridos a mano, bordes, fórmula de pasos, exhaustiva hasta longitud 10 |
| `tests/test_transformer.py` | 25 | Demostración, desbordamiento en −1, caché, recorridos a mano, exhaustiva hasta longitud 10 |

## 4. Tablas de transiciones

Detalle, corrección y recorridos a mano: `docs/test_cases.md`.

**Reconocedora** (`machines/recognizer_anbn.yaml`): Q = {q0…q4}, Σ = {a, b},
Γ = {a, b, X, Y, B}, F = {q4}; la caché vale B en todas las reglas.

| # | Regla |
|---|---|
| 1 | δ([q0, B], a) = ([q1, B], X, R) |
| 2 | δ([q0, B], Y) = ([q3, B], Y, R) |
| 3 | δ([q1, B], a) = ([q1, B], a, R) |
| 4 | δ([q1, B], Y) = ([q1, B], Y, R) |
| 5 | δ([q1, B], b) = ([q2, B], Y, L) |
| 6 | δ([q2, B], a) = ([q2, B], a, L) |
| 7 | δ([q2, B], Y) = ([q2, B], Y, L) |
| 8 | δ([q2, B], X) = ([q0, B], X, R) |
| 9 | δ([q3, B], Y) = ([q3, B], Y, R) |
| 10 | δ([q3, B], B) = ([q4, B], B, R) |

**Alteradora** (`machines/transformer_binary_increment.yaml`): Q = {q0, q1, q2},
Σ = {0, 1}, Γ = {0, 1, B}, F = {q2}; la caché es el acarreo (`1` o B).

| # | Regla |
|---|---|
| 1 | δ([q0, B], 0) = ([q0, B], 0, R) |
| 2 | δ([q0, B], 1) = ([q0, B], 1, R) |
| 3 | δ([q0, B], B) = ([q1, 1], B, L) |
| 4 | δ([q1, 1], 1) = ([q1, 1], 0, L) |
| 5 | δ([q1, 1], 0) = ([q2, B], 1, S) |
| 6 | δ([q1, 1], B) = ([q2, B], 1, S) |

## 5. IDs: dónde están y cómo se muestran

```text
SimulationResult ─ build_trace ─> Trace(word, outcome, reason, entries = ID_0 … ID_n)
                                    └─ TraceEntry(step, state, cache, head, tape, applied) · scanned · span()
Trace ─> format_id / format_id_lines   (src/output/id_formatter.py)
      ─> render_entry_tape / tape_contents (src/output/tape_formatter.py)
      ─> format_result / format_summary    (src/output/result_formatter.py)
```

- `build_trace(result)` (`src/simulator/trace.py`) verifica, sin volver a
  simular, que cada ID_k+1 sea la aplicación de su regla a ID_k; si no, lanza
  `TraceError`.
- Notación del Laboratorio 10: `X1…Xi-1[q,c]Xi…Xn`, con el blanco como `B`
  (`□` si `B` es un símbolo de la máquina). El rango visible va de
  `min(0, cabezal, celdas)` a `max(|w|−1, cabezal, celdas)`; las IDs nunca se
  recortan (`docs/methodology.md`, §6).
- En la CLI, cada cadena imprime su tabla «Paso | ID | Transición aplicada»
  después de la vista de la cinta final (`docs/test_cases.md`, §3.3).
- Todos los formateadores son funciones puras sobre `Trace` y la CLI solo
  orquesta `load_yaml → parse_machine → validate_machine → simulate →
  build_trace → format_*`.

Firmas públicas del Gate 02:

```python
# src/simulator/trace.py
build_trace(result: SimulationResult) -> Trace                      # TraceError
TraceEntry.from_configuration(config); entry.scanned; entry.span(input_length) -> (izq, der)
Trace.steps; Trace.final
# src/utils/notation.py
blank_glyph(machine) -> str; show_symbol(symbol, blank); format_control(state, cache, blank, compact=True)
format_rule(rule, blank) -> str
# src/output
format_id(entry, input_length, blank) -> str; format_id_lines(trace, blank) -> list[str]
tape_contents(tape, blank) -> str; render_tape(tape, head, left, right, blank, max_cells=None) -> list[str]
render_entry_tape(entry, input_length, blank, max_cells=None) -> list[str]
format_outcome(outcome); format_result(trace, number, total, blank, max_tape_cells=None); format_summary(traces, blank)
# main.py
main(argv=None) -> int; run(path, max_steps, out, err) -> int; EXIT_OK = 0; EXIT_INPUT_ERROR = 1
```

## 6. Acuerdos de compatibilidad y pendientes

- No se modificó `src/model/`, `src/input/`, `src/simulator/step.py` ni
  `src/simulator/engine.py`. El único cambio sobre el Gate 01 es la prueba de §1.
- La alteradora se detiene al reemplazar el primer `0`, como pide la
  especificación del Gate 02, así que el cabezal queda sobre el último bit
  modificado. La salida es `tape_contents` (de la primera a la última celda no
  blanca).
- La reconocedora no usa la caché; la alteradora sí, como registro de acarreo.
- README: solo se llenaron §4 (máquinas), §14 (ejecución) y §15 (demostraciones).
  «Estado del proyecto» y las demás secciones quedan para C25.
- Sin defectos conocidos pendientes. La «dificultad» de las máquinas no tiene
  un criterio cuantitativo en la rúbrica; no se afirma ninguna puntuación.
- A partir de este commit, Derek deja de publicar en `main`.
