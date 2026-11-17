# Proyecto No. 3 — Máquinas de Turing

Simulador de máquinas de Turing de una cinta escrito en Python. Lee la descripción formal de la máquina y sus cadenas de prueba desde un archivo YAML con el formato del enunciado, valida la definición, ejecuta las transiciones declaradas y muestra, para cada cadena, todas las descripciones instantáneas (IDs), la cinta final y si la cadena se acepta o se rechaza.

El proyecto incluye cuatro máquinas definidas solo en YAML y ejecutadas por el mismo motor: una reconocedora de {aⁿbⁿ | n ≥ 1} y tres alteradoras (incremento binario, inversión de cadenas binarias y suma de dos números binarios). Se usan por comandos (`--machine ARCHIVO`) o desde un menú numérico (`--interactive`) que presenta cada máquina y ejecuta una cadena por vez.

**Curso:** CC2019 — Teoría de la Computación
**Universidad:** Universidad del Valle de Guatemala
**Profesor:** Ing. Bidkar Pojoy

**Integrantes:**
- Vernel Josué Hernández Cáceres — 24584
- Derek Friedhelm Coronado Chilin — 24732

## Video explicativo

**Estado:** pendiente de grabación y publicación. El enlace no listado de YouTube se agregará en esta sección cuando el video exista. El guion, los comandos y la evidencia de la demostración están en [§21](#21-demostración-y-guion-del-video).

---

## Índice

1. [Objetivo del proyecto](#1-objetivo-del-proyecto)
2. [Flujo general del simulador](#2-flujo-general-del-simulador)
3. [Fundamento formal y metodología mecanizada](#3-fundamento-formal-y-metodología-mecanizada)
4. [Máquinas de Turing incluidas](#4-máquinas-de-turing-incluidas)
5. [Arquitectura](#5-arquitectura)
6. [Modelo de datos](#6-modelo-de-datos)
7. [Contrato YAML](#7-contrato-yaml)
8. [Motor de simulación y condiciones de parada](#8-motor-de-simulación-y-condiciones-de-parada)
9. [Descripciones instantáneas](#9-descripciones-instantáneas)
10. [Máquina reconocedora](#10-máquina-reconocedora)
11. [Máquina alteradora: incremento binario](#11-máquina-alteradora-incremento-binario)
12. [Máquina alteradora: inversión de cadenas](#12-máquina-alteradora-inversión-de-cadenas)
13. [Máquina alteradora: suma binaria](#13-máquina-alteradora-suma-binaria)
14. [Comparación y dificultad de las máquinas](#14-comparación-y-dificultad-de-las-máquinas)
15. [Menú interactivo](#15-menú-interactivo)
16. [Decisiones de implementación en Python](#16-decisiones-de-implementación-en-python)
17. [Validación y pruebas automatizadas](#17-validación-y-pruebas-automatizadas)
18. [Instalación y ejecución](#18-instalación-y-ejecución)
19. [Ejemplo completo de simulación](#19-ejemplo-completo-de-simulación)
20. [Resultados de las máquinas](#20-resultados-de-las-máquinas)
21. [Demostración y guion del video](#21-demostración-y-guion-del-video)
22. [Discusión, obstáculos y recomendaciones](#22-discusión-obstáculos-y-recomendaciones)
23. [Limitaciones y alcance](#23-limitaciones-y-alcance)
24. [Organización del repositorio y autoría](#24-organización-del-repositorio-y-autoría)
25. [Referencias bibliográficas](#25-referencias-bibliográficas)

---

## 1. Objetivo del proyecto

**Objetivo general.** Implementar un simulador determinista, configurable y verificable de máquinas de Turing (MT) de una cinta que reproduzca fielmente las transiciones y las descripciones instantáneas de cada ejecución.

**Objetivos específicos.** Los cinco primeros son los objetivos específicos del enunciado (Universidad del Valle de Guatemala, 2026); los tres últimos son del equipo.

1. Interpretar la configuración de la MT escrita en YAML (estados, alfabetos, δ).
2. Interpretar las cadenas de entrada que se colocan en la cinta (`simulation_strings`).
3. Diseñar las estructuras de datos que alojan la máquina, la cinta y cada configuración, y que permiten simular usando solo las funciones de transición descritas.
4. Mostrar la descripción instantánea de cada paso de la simulación.
5. Decidir la aceptación o el rechazo de cada entrada.
6. Distinguir la aceptación, el rechazo, la detención por el límite de pasos y los errores de configuración.
7. Diseñar, verificar y documentar una MT reconocedora y tres MT alteradoras, con la suma binaria como alteradora principal de la demostración.
8. Ofrecer un menú interactivo que presente cada máquina y ejecute, una por vez, cadenas predefinidas o ingresadas en la terminal.

Con `python main.py --machine ARCHIVO`, el programa:

1. lee un archivo YAML con la máquina y su lista de cadenas;
2. valida la estructura, los tipos y la coherencia formal, y reporta cada error con el campo exacto (`delta[4].output.final_state`);
3. imprime la descripción formal de la máquina con su tabla δ completa;
4. simula cada cadena desde la configuración inicial `[q0,B]w`, aplicando una regla de δ por paso;
5. imprime, por cadena, el resultado y su motivo, la cinta final, la ID final y la tabla completa «Paso | ID | Transición aplicada»;
6. termina con un resumen de todas las cadenas.

Con `python main.py --interactive` se elige una de las cuatro máquinas en un menú, se lee su ficha técnica (componentes, tabla δ y procedimiento) y se ejecuta una cadena por vez, con todas sus IDs y un veredicto final destacado ([§15](#15-menú-interactivo)).

Ninguna parte del código de Python conoce las máquinas: las cuatro se definen solo en YAML y las ejecuta el mismo motor. La inversión y la suma se calculan con reglas δ; `w[::-1]` e `int(A, 2) + int(B, 2)` solo aparecen en las pruebas, como oráculos.

### 1.1 Requisitos del enunciado

| Requisito del enunciado | Cómo se cumple | Sección |
|---|---|---|
| Leer un archivo YAML con la estructura indicada | `load_yaml` (PyYAML seguro) y `parse_machine` con las claves exactas del enunciado | [§7](#7-contrato-yaml) |
| Solo MT de una cinta | Una única cinta dispersa; la caché es un valor de la unidad de control, no una segunda cinta | [§3.1](#31-definición-formal) |
| El YAML incluye las cadenas a simular | `simulation_strings`, simuladas en el orden del archivo | [§7.1](#71-estructura-del-archivo) |
| El alfabeto de la cinta contiene al de entrada | El validador exige Σ ⊆ Γ y B ∈ Γ, B ∉ Σ | [§7.5](#75-validaciones) |
| Simular con las transiciones del YAML | `step` aplica δ([q, c], X) leída del archivo; no hay reglas implícitas | [§8](#8-motor-de-simulación-y-condiciones-de-parada) |
| Listado completo de IDs por cadena | Tabla de ID_0 a ID_n, sin recortar, con la regla aplicada en cada paso | [§9](#9-descripciones-instantáneas) |
| Indicar «aceptada» si la ID final contiene un estado final | `ACCEPTED`, con el motivo «alcanzó el estado final» | [§8](#8-motor-de-simulación-y-condiciones-de-parada) |
| Indicar «rechazada» si se detiene sin transición aplicable | `REJECTED`, con el estado, la caché y el símbolo sin regla | [§8](#8-motor-de-simulación-y-condiciones-de-parada) |
| MT reconocedora: 2 aceptadas y 2 rechazadas de longitud ≥ 5 | L = {aⁿbⁿ \| n ≥ 1}: `aaabbb`, `aaaabbbb` aceptadas; `aaabb`, `aabbbb` rechazadas | [§10](#10-máquina-reconocedora) |
| MT alteradora: 4 cadenas de longitud ≥ 5, sin dejar todo en blanco | Principal, suma binaria: `1011#0110`, `1111#0001`, `10101#10111`, `10000#00001`. Complementarias: incremento binario e inversión, con cuatro cadenas cada una | [§13](#13-máquina-alteradora-suma-binaria), [§11](#11-máquina-alteradora-incremento-binario), [§12](#12-máquina-alteradora-inversión-de-cadenas) |
| Proporcionar las funciones de transición | Tablas δ en este README, en la cabecera de la salida del programa y en la ficha del menú | [§10.4](#104-tabla-de-transiciones), [§11.5](#115-tabla-de-transiciones), [§12.5](#125-tabla-de-transiciones), [§13.5](#135-tabla-de-transiciones) |
| Video no listado con las ejecuciones y la arquitectura | Pendiente; guion preparado | [§21](#21-demostración-y-guion-del-video) |
| Repositorio privado y README en la raíz | Repositorio privado en GitHub; este archivo | — |

**Decisiones propias (no exigidas por el enunciado).** El resultado `LIMIT_EXCEEDED` y la opción `--max-steps`, los estados finales terminales, la exigencia de símbolos de un solo carácter, el rechazo de claves YAML repetidas, la notación exacta de la cinta y del blanco, las dos alteradoras adicionales y el menú `--interactive` ([§15](#15-menú-interactivo)). Se explican en [§7.4](#74-decisiones-adoptadas), [§8](#8-motor-de-simulación-y-condiciones-de-parada) y [§16](#16-decisiones-de-implementación-en-python).

### 1.2 Rúbrica oficial

La rúbrica oficial asigna 15 puntos. La tabla indica qué evidencia aporta el repositorio para cada rubro. No es una nota prevista: la dificultad no tiene una escala definida en el enunciado y el video todavía no existe.

| Rubro | Puntos | Evidencia en el repositorio |
|---|---:|---|
| Reconocedora: 2 cadenas aceptadas | 2 | `aaabbb` (25 pasos) y `aaaabbbb` (41 pasos), [§20](#20-resultados-de-las-máquinas) |
| Reconocedora: 2 cadenas no aceptadas | 2 | `aaabb` (17 pasos) y `aabbbb` (12 pasos), con su motivo |
| Dificultad de la reconocedora | 3 | Definición, tabla δ, corrección y número de pasos, [§10](#10-máquina-reconocedora) y [§14](#14-comparación-y-dificultad-de-las-máquinas) |
| Alteradora: 4 cadenas | 4 | Suma binaria: `1011#0110 → 10001`, `1111#0001 → 10000`, `10101#10111 → 101100`, `10000#00001 → 10001`, [§20](#20-resultados-de-las-máquinas) |
| Dificultad de la alteradora | 3 | Suma: 10 estados, 57 reglas, validación del formato, acarreo de tres valores en la caché y desbordamiento a posiciones negativas, [§13](#13-máquina-alteradora-suma-binaria) y [§14](#14-comparación-y-dificultad-de-las-máquinas) |
| Discusión de la arquitectura | 1 | [§2](#2-flujo-general-del-simulador) y [§5](#5-arquitectura); debe explicarse además en el video |
| **Total** | **15** | |

## 2. Flujo general del simulador

```text
   python main.py --machine ARCHIVO           python main.py --interactive
   cualquier YAML válido, todas sus           catálogo: una de las cuatro máquinas
   simulation_strings                         y una cadena por vez
                  │                                         │
                  └────────────────────┬────────────────────┘
                                       v
                             Carga y validación
                load_yaml → parse_machine → validate_machine
                                       │
                                       v
                                Modelo formal
            TuringMachine M = (Q, Σ, Γ, δ, q0, B, F), δ indexada
                                       │
                                       v
                            Motor de simulación
              simulate: ID_0 = [q0, B] w y step hasta la parada
                                       │
                                       v
                              Traza de las IDs
             build_trace: ID_0 … ID_n, cada paso verificado con δ
                                       │
                                       v
                          Presentación y veredicto
        --machine: src/output (cabecera, reporte por cadena, resumen)
        menú: src/cli/simulation_view (bloques y veredicto al final)
```

Las dos entradas convergen antes de la carga. El menú interactivo no es un segundo motor de simulación: su catálogo (`src/cli/machine_catalog.py`) solo contiene la ruta de cada YAML y los textos de presentación, y al elegir una máquina y una cadena llama a las mismas funciones que `--machine`. Por eso una cadena produce las mismas IDs, la misma configuración final y el mismo resultado en los dos modos ([§15.1](#151-arquitectura-del-menú)); solo cambia el orden en que se presentan.

Cada etapa tiene una única responsabilidad:

1. **Carga y validación.** Convierte el archivo en una máquina. Un archivo ilegible, un YAML mal formado o una máquina incoherente se informan aquí, con el campo exacto, y nunca llegan al motor ([§7](#7-contrato-yaml)).
2. **Modelo formal.** Representa M, su función δ indexada por (estado, caché, símbolo leído), la cinta y cada configuración ([§6](#6-modelo-de-datos)).
3. **Motor de simulación.** Aplica una regla por paso y decide la parada: aceptación, rechazo o límite de pasos ([§8](#8-motor-de-simulación-y-condiciones-de-parada)).
4. **Traza de las IDs.** Copia el historial y comprueba que cada ID resulte de aplicar su regla a la anterior ([§9](#9-descripciones-instantáneas)).
5. **Presentación y veredicto.** Convierte la traza en texto sin modificarla ni volver a aplicar δ ([§5](#5-arquitectura)).

## 3. Fundamento formal y metodología mecanizada

El simulador mecaniza el procedimiento con el que se resolvieron a mano los laboratorios 9 y 10 del curso: primero se fija la definición formal de la máquina y después se aplica δ una vez por paso, registrando cada descripción instantánea.

### 3.1 Definición formal

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

### 3.2 Procedimiento mecanizado

Antes de la primera transición se preparan la máquina y la configuración inicial:

| Preparación | Definición matemática | Módulo | Operación | En la terminal |
|---|---|---|---|---|
| Identificar la máquina | M = (Q, Σ, Γ, δ, q0, B, F), con Σ ⊆ Γ y B ∈ Γ \ Σ | `src/input/` | `load_yaml` → `parse_machine` → `validate_machine`: lee el YAML y comprueba tipos y coherencia | Bloque `Q`, `Σ`, `Γ`, `q0`, `F`, `B` |
| Tabular δ | δ : (Q × C) × Γ ⇀ (Q × C) × Γ × {L, R, S} | `src/model/turing_machine.py` | Indexa δ por (estado, caché, lectura) y rechaza dos reglas con la misma clave | Tabla δ numerada en el orden del YAML |
| Configuración inicial | ID_0 = [q0, B] w | `simulate` (`src/simulator/engine.py`) | Estado inicial, caché en blanco, cabezal en la posición 0 y w escrita desde esa posición | Fila 0 de la tabla de IDs |

Cada transición ID_k ⊢ ID_k+1 sigue diez pasos. Los pasos 1 a 8 ocurren en `step` (`src/simulator/step.py`) y los pasos 9 y 10 en `simulate`; los comentarios del código usan la misma numeración.

| Paso | Definición matemática | Módulo | Operación | En la terminal |
|---|---|---|---|---|
| 1. Leer la configuración actual | ID_k = X1…Xi-1 [q, c] Xi…Xn | `step` | Recibe la última ID registrada; nunca la modifica | Fila k de la tabla de IDs |
| 2. Identificar estado, caché y símbolo | q, c y Xi | `Configuration` | `state`, `cache` y `scanned`; una celda ausente contiene el blanco | `[q,c]`, escrito justo antes del símbolo leído |
| 3. Buscar la transición | δ([q, c], Xi) | `TuringMachine.find_transition` | Consulta el índice de δ; sin regla devuelve `None` y la máquina se detiene | Columna «Transición aplicada» de la fila k + 1 |
| 4. Escribir | Xi ← Y | `Tape.write` | Escribe en una copia de la cinta; escribir el blanco borra la celda | Símbolo Y en ID_k+1 |
| 5. Actualizar el estado | q ← p | `step` | Toma el estado siguiente de la regla | Primer componente de `[p,c']` |
| 6. Actualizar la caché | c ← c' | `step` | Toma la caché siguiente de la regla; la caché no ocupa ninguna celda de la cinta | Segundo componente de `[p,c']` |
| 7. Mover el cabezal | i ← i + D, con L = −1, S = 0 y R = +1 | `Move`, `step` | Desplaza el cabezal; las posiciones negativas son válidas | Posición de `[p,c']` en ID_k+1 |
| 8. Construir la nueva configuración | ID_k ⊢ ID_k+1 | `Configuration` | Paso k + 1, estado, caché, cabezal, copia de solo lectura de la cinta y regla aplicada | — |
| 9. Registrar la ID | (ID_0, …, ID_k+1) | `simulate`, `build_trace` | Agrega la ID al historial sin borrar las anteriores; `build_trace` verifica después cada paso con su regla | Una fila por ID, de ID_0 a ID_n |
| 10. Comprobar la terminación | q ∈ F: acepta; δ([q, c], Xi) indefinida: rechaza; hay regla, pero k = `max_steps`: límite | `simulate` | Comprueba, en ese orden, el estado final, la falta de regla y el límite de pasos | `Resultado` y `Motivo`, o el bloque VEREDICTO FINAL del menú |

Las tres comprobaciones del paso 10 no ocurren en el mismo punto de `simulate`. El estado final se comprueba sobre cada ID ya registrada, antes de buscar su regla, y la falta de regla en cuanto `step` devuelve `None`. El límite se revisa después del paso 8: si k = `max_steps`, la ID_k+1 calculada se descarta sin pasar por el paso 9, y la traza termina con exactamente `max_steps` transiciones.

Al detenerse, `src/output/` (con `--machine`) o `src/cli/simulation_view.py` (en el menú) presentan la cinta final, la ID final, la vista de la cinta por posiciones y el veredicto, sin volver a aplicar δ. En [§19.2](#192-una-transición-paso-a-paso) se recorren los diez pasos sobre una transición real.

### 3.3 ¿Por qué mostrar todas las IDs?

El enunciado pide el listado completo, y es la forma de comprobar a mano cada paso: la fila k muestra la regla que transformó ID_k−1 en ID_k, de modo que cualquier fila se reconstruye a partir de la anterior. Por eso las IDs nunca se recortan, aunque la traza sea larga.

## 4. Máquinas de Turing incluidas

Las cuatro máquinas del proyecto se definen solo en YAML, en `machines/`, y las ejecuta el mismo motor: ninguna parte del código de Python contiene sus reglas.

| Máquina | Archivo | Tipo | Lenguaje o transformación | Estados | Reglas δ | Caché | Sección |
|---|---|---|---|---:|---:|---|---|
| Reconocedora aⁿbⁿ | `machines/recognizer_anbn.yaml` | Reconocedora | L = {aⁿbⁿ \| n ≥ 1} | 5 | 10 | No se usa | [§10](#10-máquina-reconocedora) |
| Incremento binario | `machines/transformer_binary_increment.yaml` | Alteradora | w ↦ value₂(w) + 1, en binario | 3 | 6 | Acarreo: B, 1 | [§11](#11-máquina-alteradora-incremento-binario) |
| Inversión de cadenas | `machines/transformer_binary_reverse.yaml` | Alteradora | w ↦ wᴿ | 7 | 33 | Bit en tránsito: B, 0, 1 | [§12](#12-máquina-alteradora-inversión-de-cadenas) |
| Suma binaria (principal) | `machines/transformer_binary_addition.yaml` | Alteradora | A#B ↦ value₂(A) + value₂(B), en binario | 10 | 57 | Suma y acarreo: B, 1, 2 | [§13](#13-máquina-alteradora-suma-binaria) |

Cadenas de la demostración (`simulation_strings` de cada archivo) y su resultado real:

| Máquina | Cadenas | Resultado |
|---|---|---|
| Reconocedora | `aaabbb`, `aaaabbbb`, `aaabb`, `aabbbb` | Las dos primeras se aceptan y las dos últimas se rechazan |
| Incremento | `10101`, `11011`, `11111`, `10000` | `10110`, `11100`, `100000`, `10001` |
| Inversión | `10110`, `11001`, `10000`, `11100` | `01101`, `10011`, `00001`, `00111` |
| Suma | `1011#0110`, `1111#0001`, `10101#10111`, `10000#00001` | `10001`, `10000`, `101100`, `10001` |

El repositorio incluye además dos máquinas de referencia que no forman parte de la demostración:

| Archivo | Contenido | Sección |
|---|---|---|
| `machines/examples/basic_machine.yaml` | Máquina completa del Laboratorio 10, ejercicio 1: 6 estados, 20 reglas y caché con los valores B, a y b | [§9](#9-descripciones-instantáneas), [§17.1](#171-estrategia-de-validación) |
| `tests/fixtures/statement_example_mt_1.yaml` | Ejemplo del enunciado tal como está impreso; la validación reporta sus inconsistencias | [§7.6](#76-observaciones-sobre-el-ejemplo-del-enunciado) |

Todas siguen el formato de [§7](#7-contrato-yaml). La comparación de las cuatro máquinas del proyecto está en [§14](#14-comparación-y-dificultad-de-las-máquinas) y sus resultados completos en [§20](#20-resultados-de-las-máquinas).

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
src/output       id_formatter · tape_formatter · result_formatter · machine_formatter
                 (src/utils/notation.py)
      │
      ├──────────────────────────────┐
      v                              v
main.py --machine ARCHIVO        src/cli (main.py --interactive)
todas las cadenas del YAML       machine_catalog: rutas y textos de presentación
                                 interactive_menu: ficha y una cadena por vez
                                 simulation_view: bloques de cada ejecución
```

| Capa | Archivos | Responsabilidad | No hace |
|---|---|---|---|
| Entrada | `src/input/` | Leer, interpretar y validar el YAML | Ejecutar la máquina |
| Modelo | `src/model/` | Representar M, δ, la cinta, las IDs y los resultados con sus invariantes | Leer archivos ni imprimir |
| Simulador | `src/simulator/` | Aplicar δ, decidir la parada y verificar la traza | Formatear ni leer archivos |
| Salida | `src/output/`, `src/utils/notation.py` | Convertir la traza y la máquina en texto (IDs, cinta, resultado, componentes y tabla δ) | Modificar el historial ni aplicar δ |
| CLI | `main.py` | Elegir el modo y orquestar lectura → simulación → presentación | Duplicar el motor |
| Menú | `src/cli/` | Navegar, presentar la ficha de cada máquina, validar cadenas nuevas y guardarlas durante la sesión | Simular por su cuenta, conocer reglas δ ni escribir en los YAML |
| Pruebas | `tests/` | Ejercitar cada capa por separado y el sistema completo | — |

Las dependencias van en un solo sentido: el menú depende de la entrada, del simulador y de la salida; la salida, del simulador y del modelo; el simulador, del modelo; y el modelo, de nada más. Los formateadores son funciones puras: reciben una `Trace` o una `TuringMachine` y devuelven líneas de texto. Los dos modos encadenan lo mismo, `load_yaml → parse_machine → validate_machine → simulate → build_trace → format_*`: `--machine` lo hace para todas las cadenas del archivo y el menú para la cadena elegida.

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
describe_machine(machine, blank) -> list[str]             # cabecera de --machine
formal_components(machine, blank); cache_values(machine); format_delta_table(machine, blank)
format_procedure(trace, blank); format_final_configuration(trace, blank)  # bloques de format_result
run_menu(read=input, out=None, max_steps=10_000) -> int   # 0 al salir, 130 con Ctrl+C
format_simulation(trace, machine, recognizer, blank)      # src/cli/simulation_view.py
CATALOG: tuple[CatalogEntry, ...]                         # src/cli/machine_catalog.py
```

Todas las excepciones de entrada heredan de `InputError` (a su vez `ValueError`). Para decidir, use `outcome`: `reason` es un texto en español para el usuario. Una `Configuration` no es *hashable* (su cinta es un `mappingproxy`); dos IDs se comparan con `==`.

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

### 7.7 Cómo escribir una máquina nueva

Lista de comprobación, usada para las cuatro máquinas del proyecto:

- El blanco es una entrada vacía (`-` en una lista, `clave:` sin valor); `B`, `'None'` y `''` no lo son.
- `tape_alphabet` incluye todos los símbolos de `alphabet` y el blanco.
- Se entrecomilla todo lo que YAML leería como número o booleano (estados `'0'`, símbolos `'0'`/`'1'`, cadenas binarias `'10101'`) y los símbolos con significado en YAML: `'#'` inicia un comentario y `'*'` un alias.
- Cada símbolo es un solo carácter y cada cadena de `simulation_strings` usa solo símbolos de `alphabet`.
- Las siete claves de cada regla son obligatorias; si la caché no se usa, se deja vacía en ambos lados.
- No hay dos reglas con el mismo (`initial_state`, `mem_cache_value`, `tape_input`) ni claves repetidas dentro de una regla copiada.
- Los estados finales son terminales: al entrar a F la cadena se acepta. El rechazo es detenerse fuera de F sin regla.

Plantilla de una regla, δ([q0, B], 1) = ([q0, B], 1, R):

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

## 8. Motor de simulación y condiciones de parada

`step(machine, current)` (`src/simulator/step.py`) ejecuta una sola transición, que corresponde a los pasos 1 a 8 de [§3.2](#32-procedimiento-mecanizado):

- **Pasos 1 y 2:** toma la ID actual, con su estado, su caché y el símbolo bajo el cabezal (blanco si la celda no existe).
- **Paso 3:** busca δ([estado, caché], símbolo); si no hay regla, devuelve `None` sin modificar nada.
- **Paso 4:** escribe el símbolo de salida en una copia de la cinta (el blanco borra la celda).
- **Pasos 5 y 6:** toma el nuevo estado y la nueva caché de la regla.
- **Paso 7:** mueve el cabezal (L = −1, R = +1, S = 0), incluso a posiciones negativas.
- **Paso 8:** devuelve una `Configuration` nueva con el paso siguiente y la regla aplicada.

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
| Rango visible | De `min(0, cabezal, celdas no blancas)` a `max(\|w\| − 1, cabezal, celdas no blancas)`; con w = ε, solo el cabezal y las celdas no blancas | `BBB#XXXB[q5,B]B` |

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

**Archivo:** `machines/recognizer_anbn.yaml` · **Lenguaje:** L = {aⁿbⁿ | n ≥ 1}. Adaptación de Derek Coronado del ejemplo 8.2 de Hopcroft et al. (2001), que reconoce {0ⁿ1ⁿ | n ≥ 1}, con a/b en lugar de 0/1.

**Objetivo formal.** Decidir si una cadena w ∈ {a, b}* consiste en n letras `a` seguidas de exactamente n letras `b`, con n ≥ 1: la máquina se detiene en F si w ∈ L, y fuera de F, sin regla aplicable, si w ∉ L.

### 10.1 Definición formal

| Componente | Valor |
|---|---|
| Q | {q0, q1, q2, q3, q4} |
| Σ | {a, b} |
| Γ | {a, b, X, Y, B} |
| q0 | q0 |
| F | {q4} |
| Blanco | B (entrada vacía en el YAML) |
| Marcadores | `X` y `Y` |
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

**Invariante.** En cada visita a q0, con el cabezal en la posición k (k = 0 en ID_0), las posiciones 0 … k−1 contienen `X` y en w eran `a`; la cinta tiene exactamente k celdas `Y`, cada una en el lugar de una `b` de w; y todas las demás celdas coinciden con w. Se mantiene porque solo las reglas 1 (`a` → `X`) y 5 (`b` → `Y`) cambian un símbolo, cada ronda completa aplica cada una exactamente una vez y la regla 8 deja el cabezal en la celda contigua a la última `X`. Para w = aⁿbⁿ, la cinta al empezar la ronda k + 1 es Xᵏaⁿ⁻ᵏYᵏbⁿ⁻ᵏ.

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

La salida completa de las cuatro cadenas, con todas sus IDs, está en `docs/evidence/recognizer_anbn.txt` ([§20.1](#201-evidencia-en-el-repositorio)).

## 11. Máquina alteradora: incremento binario

**Archivo:** `machines/transformer_binary_increment.yaml` · **Función:** sucesor binario. Diseño de Derek Coronado.

**Objetivo formal.** Calcular en la propia cinta el sucesor binario de la entrada: al detenerse en q2, la cinta contiene value₂(w) + 1 en binario y nada más.

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
| Blanco | B (entrada vacía en el YAML) |
| Marcadores | Ninguno: Γ = Σ ∪ {B} |
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

**Invariante del acarreo.** Sea v(cinta) = Σ xᵢ · 2^(|w|−1−i) el valor de los bits de la cinta según su posición i (la posición −1 vale 2^|w|). En toda ID con estado q1 y el cabezal en la posición p, la caché vale 1, las celdas p+1 … |w|−1 contienen `0` y v(cinta) + 2^(|w|−1−p) = value₂(w) + 1. La regla 3 lo establece (p = |w| − 1 y la cinta es w). La regla 4 lo conserva: con k = |w| − 1 − p, cambia un `1` de valor 2ᵏ por un `0` y el acarreo pasa a valer 2ᵏ⁺¹. Las reglas 5 y 6 escriben en p el `1` que representaba el acarreo y vacían la caché, así que al llegar a q2 v(cinta) = value₂(w) + 1.

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

La salida completa está en `docs/evidence/transformer_binary_increment.txt`, y [§19](#19-ejemplo-completo-de-simulación) explica la tercera cadena paso a paso.

## 12. Máquina alteradora: inversión de cadenas

**Archivo:** `machines/transformer_binary_reverse.yaml` · **Función:** inversa de una cadena binaria. Máquina complementaria, diseñada por Vernel Hernández.

**Objetivo formal.** Reescribir la entrada w ∈ {0, 1}* como wᴿ en las mismas posiciones de la cinta, trasladando un bit por vez en la caché.

### 12.1 Función calculada

Para w = w₁w₂…wₙ ∈ {0, 1}*, f(w) = wᴿ = wₙ…w₂w₁: los mismos bits en orden inverso, en las mismas posiciones 0 … n−1 de la cinta. La longitud se conserva (`10000 → 00001` mantiene sus ceros) y f(ε) = ε.

### 12.2 Definición formal

| Componente | Valor |
|---|---|
| Q | {q0, q1, q2, q3, q4, q5, q6} |
| Σ | {0, 1} |
| Γ | {0, 1, \*, o, i, B} |
| q0 | q0 |
| F | {q6} |
| Blanco | B (entrada vacía en el YAML) |
| Marcadores | `*`, `o` e `i` |
| Caché | Bit en tránsito c ∈ {B, 0, 1} |
| δ | 33 reglas |

### 12.3 Estados, marcadores y caché

| Estado | Caché | Papel |
|---|---|---|
| q0 | B | Elige el bit sin procesar más a la izquierda o detecta que ya no quedan |
| q1 | 0 o 1 | Lleva el bit de la caché hacia el extremo derecho sin procesar |
| q2 | 0 o 1 | Intercambia el bit de la caché con el del extremo derecho |
| q3 | 0 o 1 | Lleva el bit recogido de vuelta al hueco |
| q4 | B | Rebobina hasta el inicio de la cadena |
| q5 | B | Restaura las marcas a bits |
| q6 | B | Fin (estado final, terminal) |

| Símbolo | Significado |
|---|---|
| `*` | Hueco: la celda cuyo bit viaja en la caché |
| `o` | 0 ya colocado en su posición final |
| `i` | 1 ya colocado en su posición final |

La caché es indispensable: q1, q2 y q3 son los mismos estados para los dos bits, y solo el segundo componente de `[q,c]` indica cuál se está trasladando. Sin caché harían falta dos copias de cada uno de esos estados. Las marcas `o`/`i` permiten leer el resultado parcial en la propia ID: en `o[q4,B]iioi` ya se ve `01101`.

### 12.4 Algoritmo

1. **Elegir** (q0): leer el bit sin procesar más a la izquierda, guardarlo en la caché, escribir el hueco `*` y moverse a la derecha.
2. **Llevar** (q1): cruzar los bits sin procesar hasta un bit ya colocado o el blanco y retroceder una celda, al último bit sin procesar.
3. **Intercambiar** (q2): escribir la marca del bit de la caché y cargar en la caché el bit que había ahí.
4. **Regresar** (q3): cruzar los bits sin procesar hacia la izquierda hasta el hueco, escribir ahí la marca del bit de la caché, vaciarla y volver a q0.
5. **Centro** (q2 sobre `*`): en longitud impar, el último bit sin procesar es el central; se marca en su propia celda.
6. **Rebobinar** (q4): cuando q0 lee un bit colocado (longitud par) o tras el centro, ir al blanco anterior a la cadena.
7. **Restaurar** (q5): convertir `o` en 0 e `i` en 1 de izquierda a derecha; en el blanco final, pasar a q6.

### 12.5 Tabla de transiciones

| # | Regla | Paso del algoritmo |
|---|---|---|
| 1 | δ([q0, B], 0) = ([q1, 0], \*, R) | Elegir |
| 2 | δ([q0, B], 1) = ([q1, 1], \*, R) | Elegir |
| 3 | δ([q0, B], o) = ([q4, B], o, L) | Fin de las rondas (longitud par) |
| 4 | δ([q0, B], i) = ([q4, B], i, L) | Fin de las rondas (longitud par) |
| 5 | δ([q0, B], B) = ([q6, B], B, S) | Entrada vacía |
| 6 | δ([q1, 0], 0) = ([q1, 0], 0, R) | Llevar |
| 7 | δ([q1, 0], 1) = ([q1, 0], 1, R) | Llevar |
| 8 | δ([q1, 0], o) = ([q2, 0], o, L) | Llevar: fin del tramo sin procesar |
| 9 | δ([q1, 0], i) = ([q2, 0], i, L) | Llevar: fin del tramo sin procesar |
| 10 | δ([q1, 0], B) = ([q2, 0], B, L) | Llevar: fin del tramo sin procesar |
| 11 | δ([q1, 1], 0) = ([q1, 1], 0, R) | Llevar |
| 12 | δ([q1, 1], 1) = ([q1, 1], 1, R) | Llevar |
| 13 | δ([q1, 1], o) = ([q2, 1], o, L) | Llevar: fin del tramo sin procesar |
| 14 | δ([q1, 1], i) = ([q2, 1], i, L) | Llevar: fin del tramo sin procesar |
| 15 | δ([q1, 1], B) = ([q2, 1], B, L) | Llevar: fin del tramo sin procesar |
| 16 | δ([q2, 0], 0) = ([q3, 0], o, L) | Intercambiar |
| 17 | δ([q2, 0], 1) = ([q3, 1], o, L) | Intercambiar |
| 18 | δ([q2, 0], \*) = ([q4, B], o, L) | Centro (longitud impar) |
| 19 | δ([q2, 1], 0) = ([q3, 0], i, L) | Intercambiar |
| 20 | δ([q2, 1], 1) = ([q3, 1], i, L) | Intercambiar |
| 21 | δ([q2, 1], \*) = ([q4, B], i, L) | Centro (longitud impar) |
| 22 | δ([q3, 0], 0) = ([q3, 0], 0, L) | Regresar |
| 23 | δ([q3, 0], 1) = ([q3, 0], 1, L) | Regresar |
| 24 | δ([q3, 0], \*) = ([q0, B], o, R) | Llenar el hueco |
| 25 | δ([q3, 1], 0) = ([q3, 1], 0, L) | Regresar |
| 26 | δ([q3, 1], 1) = ([q3, 1], 1, L) | Regresar |
| 27 | δ([q3, 1], \*) = ([q0, B], i, R) | Llenar el hueco |
| 28 | δ([q4, B], o) = ([q4, B], o, L) | Rebobinar |
| 29 | δ([q4, B], i) = ([q4, B], i, L) | Rebobinar |
| 30 | δ([q4, B], B) = ([q5, B], B, R) | Rebobinar: inicio de la cadena |
| 31 | δ([q5, B], o) = ([q5, B], 0, R) | Restaurar |
| 32 | δ([q5, B], i) = ([q5, B], 1, R) | Restaurar |
| 33 | δ([q5, B], B) = ([q6, B], B, S) | Fin |

No hay claves sin regla alcanzables desde una entrada de Σ*: la máquina nunca rechaza y siempre termina en q6.

### 12.6 Corrección, cinta final y número de pasos

**Invariante.** Al llegar a q0 por j-ésima vez (j = 0, 1, …), las celdas k y n−1−k con k < j ya contienen las marcas de wₙ₋ₖ y wₖ₊₁ (los extremos intercambiados) y las celdas j … n−1−j conservan w sin cambios. La ronda j+1 lleva wⱼ₊₁ a la celda n−1−j y trae wₙ₋ⱼ a la celda j, así que el invariante se mantiene. Hay ⌈n/2⌉ rondas; en longitud impar la última es el centro. `tests/test_reverse.py` comprueba este invariante en cada visita a q0 para todas las cadenas de longitud 1 a 7.

**Cinta final.** La máquina solo escribe en las posiciones 0 … n−1. Cada hueco se llena en la misma ronda y q5 restaura todas las marcas, de modo que la salida es contigua, sin `*`, `o` ni `i`, y con los ceros en su lugar.

**Pasos.** Cada ronda completa j, con 1 ≤ j ≤ ⌊n/2⌋, cuesta 2n − 4j + 5 transiciones. El resto cuesta 3n/2 + 3 si n es par (detectar el fin, rebobinar y restaurar) y (3n + 9)/2 si es impar (el centro, rebobinar y restaurar). En total:

T(0) = 1 y T(n) = ⌊(n² + 6n + 6) / 2⌋ para n ≥ 1

Por ejemplo, 30 pasos para n = 5 y 48 para n = 7. El tiempo es O(n²) y el espacio, n celdas.

### 12.7 Recorrido a mano: `10110 → 01101`

| Paso | ID | Regla | Paso | ID | Regla |
|---|---|---|---|---|---|
| 0 | `[q0,B]10110` | — | 16 | `o*[q3,1]1oi` | 17 |
| 1 | `*[q1,1]0110` | 2 | 17 | `o[q3,1]*1oi` | 26 |
| 2 | `*0[q1,1]110` | 11 | 18 | `oi[q0,B]1oi` | 27 |
| 3 | `*01[q1,1]10` | 12 | 19 | `oi*[q1,1]oi` | 2 |
| 4 | `*011[q1,1]0` | 12 | 20 | `oi[q2,1]*oi` | 13 |
| 5 | `*0110[q1,1]B` | 11 | 21 | `o[q4,B]iioi` | 21 |
| 6 | `*011[q2,1]0` | 15 | 22 | `[q4,B]oiioi` | 29 |
| 7 | `*01[q3,0]1i` | 19 | 23 | `[q4,B]Boiioi` | 28 |
| 8 | `*0[q3,0]11i` | 23 | 24 | `[q5,B]oiioi` | 30 |
| 9 | `*[q3,0]011i` | 23 | 25 | `0[q5,B]iioi` | 31 |
| 10 | `[q3,0]*011i` | 22 | 26 | `01[q5,B]ioi` | 32 |
| 11 | `o[q0,B]011i` | 24 | 27 | `011[q5,B]oi` | 32 |
| 12 | `o*[q1,0]11i` | 1 | 28 | `0110[q5,B]i` | 31 |
| 13 | `o*1[q1,0]1i` | 7 | 29 | `01101[q5,B]B` | 32 |
| 14 | `o*11[q1,0]i` | 7 | 30 | `01101[q6,B]B` | 33 |
| 15 | `o*1[q2,0]1i` | 9 | | | |

Ronda 1 (pasos 1–11): el `1` de la posición 0 viaja en la caché (`[q1,1]`), se intercambia con el `0` de la posición 4 (paso 7, `[q3,0]`) y el `0` llena el hueco (paso 11). Ronda 2 (pasos 12–18): lo mismo con las posiciones 1 y 3. Paso 21: el bit central se marca sin moverse. Pasos 22–30: rebobinar y restaurar.

### 12.8 Cadenas de la demostración

| Cadena | Longitud | Salida | Pasos (T(5)) |
|---|---|---|---|
| `10110` | 5 | `01101` | 30 |
| `11001` | 5 | `10011` | 30 |
| `10000` | 5 | `00001` | 30 |
| `11100` | 5 | `00111` | 30 |

El número de pasos depende solo de la longitud: la máquina recorre las mismas celdas sea cual sea el valor de cada bit. La salida completa está en `docs/evidence/transformer_binary_reverse.txt`.

## 13. Máquina alteradora: suma binaria

**Archivo:** `machines/transformer_binary_addition.yaml` · **Función:** suma de dos números binarios. Es la alteradora principal de la demostración ([§14](#14-comparación-y-dificultad-de-las-máquinas)). Diseño de Vernel Hernández.

**Objetivo formal.** Dada una entrada A#B con dos números binarios, dejar en la cinta únicamente value₂(A) + value₂(B) en binario, y rechazar, sin modificar la cinta, las cadenas de Σ* que no tienen esa forma.

### 13.1 Función calculada y política de salida

La entrada es A#B, con A y B binarios no vacíos (bit más significativo a la izquierda) y un único separador `#`. La salida es value₂(A) + value₂(B) en binario:

- **Ancho:** max(|A|, |B|) bits, y uno más si la suma se desborda (`1111#0001 → 10000`).
- **Ceros iniciales:** se conservan hasta ese ancho (`0001#0010 → 0011`, `0#0 → 0`), igual que en el incremento binario. El resultado nunca es una cadena vacía.
- **Operandos de distinta longitud:** el operando corto se completa con ceros a la izquierda (`1#1011 → 1100`).
- **Región de salida:** termina en la posición |A| − 1, donde terminaba A, y crece hacia la izquierda, a posiciones negativas si B es más largo o hay desbordamiento. El separador y B se borran, así que la cinta final contiene solo el resultado.

Para `10101#10111`, 21 + 23 = 44 = `101100`.

### 13.2 Definición formal

| Componente | Valor |
|---|---|
| Q | {q0, q1, …, q9} |
| Σ | {0, 1, #} |
| Γ | {0, 1, #, o, i, B} |
| q0 | q0 |
| F | {q9} |
| Blanco | B (entrada vacía en el YAML) |
| Marcadores | `o` e `i`; `#` es el separador de Σ |
| Caché | Suma en tránsito o acarreo, c ∈ {B, 1, 2}; B representa 0 |
| δ | 57 reglas |

### 13.3 Estados, marcadores y caché

| Estado | Caché | Papel |
|---|---|---|
| q0 | B | Validación: A debe empezar con un bit |
| q1 | B | Validación: cruza A hasta `#` |
| q2 | B | Validación: B debe empezar con un bit |
| q3 | B | Validación: cruza B hasta el blanco final |
| q4 | acarreo B o 1 | Toma el último bit de B o detecta que B se agotó |
| q5 | suma B, 1 o 2 | Lleva la suma hacia A cruzando lo que queda de B |
| q6 | suma B, 1 o 2 | Cruza el resultado parcial y suma en la columna siguiente |
| q7 | acarreo B o 1 | Regresa con el acarreo hasta el final de B |
| q8 | B | Borra `#` y restaura las marcas a bits |
| q9 | B | Fin (estado final, terminal) |

| Símbolo | Significado |
|---|---|
| `#` | Separador entre A y B (símbolo de entrada); se borra al terminar |
| `o` | Bit 0 del resultado ya calculado |
| `i` | Bit 1 del resultado ya calculado |

La caché transporta información aritmética en los dos sentidos. Hacia la izquierda lleva b + acarreo, que vale 0, 1 o 2; hacia la derecha lleva el nuevo acarreo, 0 o 1. Sin ella, q4, q5, q6 y q7 tendrían que duplicarse o triplicarse para recordar esos valores.

### 13.4 Algoritmo

1. **Validar** (q0 → q3): recorrer la entrada una vez y comprobar la forma [01]⁺#[01]⁺. Cada símbolo se reescribe igual, así que una cadena mal formada se rechaza sin modificar la cinta.
2. **Tomar** (q4): leer el último bit b de B, borrarlo y guardar en la caché b + acarreo.
3. **Llevar** (q5): cruzar lo que queda de B hacia la izquierda hasta `#`.
4. **Sumar** (q6): cruzar las marcas del resultado parcial; en la siguiente columna de A, o en el blanco a su izquierda, que vale 0, calcular a + caché. Escribir la marca de su bit menos significativo y dejar el acarreo en la caché.
5. **Volver** (q7): cruzar marcas, `#` y B hacia la derecha hasta el blanco, y repetir desde el paso 2.
6. **Acarreo final** (q4 lee `#` con caché 1): B se agotó, pero queda acarreo; volver al paso 4 con suma 1.
7. **Restaurar** (q4 lee `#` con caché B → q8): borrar `#`, convertir `o` en 0 e `i` en 1 hacia la izquierda y detenerse en q9 en el primer bit de A no tocado o en el blanco.

### 13.5 Tabla de transiciones

| # | Regla | Paso del algoritmo |
|---|---|---|
| 1 | δ([q0, B], 0) = ([q1, B], 0, R) | Validación |
| 2 | δ([q0, B], 1) = ([q1, B], 1, R) | Validación |
| 3 | δ([q1, B], 0) = ([q1, B], 0, R) | Validación |
| 4 | δ([q1, B], 1) = ([q1, B], 1, R) | Validación |
| 5 | δ([q1, B], #) = ([q2, B], #, R) | Validación |
| 6 | δ([q2, B], 0) = ([q3, B], 0, R) | Validación |
| 7 | δ([q2, B], 1) = ([q3, B], 1, R) | Validación |
| 8 | δ([q3, B], 0) = ([q3, B], 0, R) | Validación |
| 9 | δ([q3, B], 1) = ([q3, B], 1, R) | Validación |
| 10 | δ([q3, B], B) = ([q4, B], B, L) | Validación: fin de B |
| 11 | δ([q4, B], 0) = ([q5, B], B, L) | Tomar el bit de B |
| 12 | δ([q4, B], 1) = ([q5, 1], B, L) | Tomar el bit de B |
| 13 | δ([q4, B], #) = ([q8, B], B, L) | B agotado: restaurar |
| 14 | δ([q4, 1], 0) = ([q5, 1], B, L) | Tomar el bit de B |
| 15 | δ([q4, 1], 1) = ([q5, 2], B, L) | Tomar el bit de B |
| 16 | δ([q4, 1], #) = ([q6, 1], #, L) | B agotado: acarreo final |
| 17 | δ([q5, B], 0) = ([q5, B], 0, L) | Llevar |
| 18 | δ([q5, B], 1) = ([q5, B], 1, L) | Llevar |
| 19 | δ([q5, B], #) = ([q6, B], #, L) | Llevar: cruzar # |
| 20 | δ([q5, 1], 0) = ([q5, 1], 0, L) | Llevar |
| 21 | δ([q5, 1], 1) = ([q5, 1], 1, L) | Llevar |
| 22 | δ([q5, 1], #) = ([q6, 1], #, L) | Llevar: cruzar # |
| 23 | δ([q5, 2], 0) = ([q5, 2], 0, L) | Llevar |
| 24 | δ([q5, 2], 1) = ([q5, 2], 1, L) | Llevar |
| 25 | δ([q5, 2], #) = ([q6, 2], #, L) | Llevar: cruzar # |
| 26 | δ([q6, B], o) = ([q6, B], o, L) | Cruzar el resultado |
| 27 | δ([q6, B], i) = ([q6, B], i, L) | Cruzar el resultado |
| 28 | δ([q6, B], 0) = ([q7, B], o, R) | Sumar |
| 29 | δ([q6, B], 1) = ([q7, B], i, R) | Sumar |
| 30 | δ([q6, B], B) = ([q7, B], o, R) | Sumar en el blanco (vale 0) |
| 31 | δ([q6, 1], o) = ([q6, 1], o, L) | Cruzar el resultado |
| 32 | δ([q6, 1], i) = ([q6, 1], i, L) | Cruzar el resultado |
| 33 | δ([q6, 1], 0) = ([q7, B], i, R) | Sumar |
| 34 | δ([q6, 1], 1) = ([q7, 1], o, R) | Sumar |
| 35 | δ([q6, 1], B) = ([q7, B], i, R) | Sumar en el blanco (vale 0) |
| 36 | δ([q6, 2], o) = ([q6, 2], o, L) | Cruzar el resultado |
| 37 | δ([q6, 2], i) = ([q6, 2], i, L) | Cruzar el resultado |
| 38 | δ([q6, 2], 0) = ([q7, 1], o, R) | Sumar |
| 39 | δ([q6, 2], 1) = ([q7, 1], i, R) | Sumar |
| 40 | δ([q6, 2], B) = ([q7, 1], o, R) | Sumar en el blanco (vale 0) |
| 41 | δ([q7, B], o) = ([q7, B], o, R) | Volver |
| 42 | δ([q7, B], i) = ([q7, B], i, R) | Volver |
| 43 | δ([q7, B], #) = ([q7, B], #, R) | Volver |
| 44 | δ([q7, B], 0) = ([q7, B], 0, R) | Volver |
| 45 | δ([q7, B], 1) = ([q7, B], 1, R) | Volver |
| 46 | δ([q7, B], B) = ([q4, B], B, L) | Volver: fin de B |
| 47 | δ([q7, 1], o) = ([q7, 1], o, R) | Volver |
| 48 | δ([q7, 1], i) = ([q7, 1], i, R) | Volver |
| 49 | δ([q7, 1], #) = ([q7, 1], #, R) | Volver |
| 50 | δ([q7, 1], 0) = ([q7, 1], 0, R) | Volver |
| 51 | δ([q7, 1], 1) = ([q7, 1], 1, R) | Volver |
| 52 | δ([q7, 1], B) = ([q4, 1], B, L) | Volver: fin de B |
| 53 | δ([q8, B], o) = ([q8, B], 0, L) | Restaurar |
| 54 | δ([q8, B], i) = ([q8, B], 1, L) | Restaurar |
| 55 | δ([q8, B], 0) = ([q9, B], 0, S) | Fin |
| 56 | δ([q8, B], 1) = ([q9, B], 1, S) | Fin |
| 57 | δ([q8, B], B) = ([q9, B], B, R) | Fin |

### 13.6 Formato de entrada: errores y rechazos

Hay que distinguir dos casos:

- **Símbolos fuera de Σ = {0, 1, #}**, como `1a#0`, son un **error de entrada**. El validador del YAML, `simulate` y el menú lo informan antes de simular, y nunca se presenta como rechazo.
- **Cadenas de Σ\* sin la forma A#B** sí se simulan. Las rechaza la pasada de validación, al detenerse sin regla y con la cinta intacta:

| Entrada | Caso | Se detiene en | Clave sin regla |
|---|---|---|---|
| ε | Cadena vacía | q0 | (q0, B, B) |
| `#01` | A vacío | q0 | (q0, B, #) |
| `01#` | B vacío | q2 | (q2, B, B) |
| `1011` | Falta el separador | q1 | (q1, B, B) |
| `1##0` | Separadores contiguos | q2 | (q2, B, #) |
| `1#0#1` | Separadores duplicados | q3 | (q3, B, #) |

El menú interactivo comprueba además el formato A#B antes de ejecutar una cadena nueva ([§15.6](#156-validaciones-de-entrada)).

### 13.7 Corrección, número de pasos y espacio

**Invariante.** Al llegar a q4 por k-ésima vez durante las rondas:

- ya se borraron los k últimos bits de B;
- las k columnas menos significativas del resultado están escritas como marcas en las posiciones |A|−1 … |A|−k;
- la caché contiene el acarreo c_k que entra en la columna k;
- las celdas a la izquierda conservan los bits de A aún no sumados.

La ronda calcula a_k + b_k + c_k: q4 carga b_k + c_k, q6 suma a_k (0 si la columna está fuera de A) y escribe el bit (a_k + b_k + c_k) mod 2 con el acarreo ⌊(a_k + b_k + c_k) / 2⌋. Es la suma escolar columna por columna. Cuando B se agota sin acarreo, los bits de A que quedan son los más significativos del resultado y no cambian. Con acarreo, se procesa una columna más.

**Terminación.** Cada ronda borra un bit de B o, una vez agotado B, absorbe el acarreo en una columna más a la izquierda, donde a lo sumo hay unos de A y después blancos (0). Por eso la máquina siempre llega a q9 cuando la entrada tiene la forma A#B.

**Pasos.** Sea m el número de columnas procesadas: |B| más las rondas de acarreo final. Entonces:

T(A#B) = |A#B| + m² + |B|² + 4m + 3

La fórmula se compone de cuatro partes:
- la validación cuesta |A#B| + 1;
- cada una de las |B| rondas con un bit de B cuesta exactamente 2|B| + 3, sea cual sea la columna;
- la j-ésima ronda de acarreo final cuesta 2(|B| + j − 1) + 4;
- la restauración cuesta m + 2.

La suite la comprueba en todos los pares con operandos de hasta 4 bits y en 150 pares aleatorios de hasta 16 bits. Además se verificó, fuera de la suite, en los 15 876 pares con |A|, |B| ≤ 6. Como m ≤ max(|A|, |B|) + 1, el tiempo es O(n²) en la longitud n de la entrada, y el espacio es de n + max(0, m − |A|) celdas.

### 13.8 Recorrido a mano: `1#1 → 10`

| Paso | ID | Regla | Paso | ID | Regla |
|---|---|---|---|---|---|
| 0 | `[q0,B]1#1` | — | 10 | `[q6,1]o#B` | 16 |
| 1 | `1[q1,B]#1` | 2 | 11 | `[q6,1]Bo#B` | 31 |
| 2 | `1#[q2,B]1` | 5 | 12 | `i[q7,B]o#B` | 35 |
| 3 | `1#1[q3,B]B` | 7 | 13 | `io[q7,B]#B` | 41 |
| 4 | `1#[q4,B]1` | 10 | 14 | `io#[q7,B]B` | 43 |
| 5 | `1[q5,1]#B` | 12 | 15 | `io[q4,B]#B` | 46 |
| 6 | `[q6,1]1#B` | 22 | 16 | `i[q8,B]oBB` | 13 |
| 7 | `o[q7,1]#B` | 34 | 17 | `[q8,B]i0BB` | 53 |
| 8 | `o#[q7,1]B` | 49 | 18 | `[q8,B]B10BB` | 54 |
| 9 | `o[q4,1]#B` | 52 | 19 | `[q9,B]10BB` | 57 |

El recorrido sigue estos pasos:
- Pasos 0–4: validación.
- Paso 5: se borra el bit de B y la caché lleva 1 + 0 (`[q5,1]`).
- Paso 7: en la columna 0, 1 + 1 = 10, así que escribe `o` y regresa con acarreo (`[q7,1]`).
- Paso 10: B se agotó con acarreo (regla 16).
- Paso 12: el acarreo se escribe en el blanco de la posición −1 (`i`).
- Pasos 15–19: q4 lee `#` sin acarreo, lo borra y restaura `io` a `10`.

T = 3 + 2² + 1² + 4·2 + 3 = 19.

### 13.9 Cadenas de la demostración

| Cadena | Operación | Salida | Columnas m | Pasos (fórmula) |
|---|---|---|---|---|
| `1011#0110` | 11 + 6 = 17 | `10001` | 5 | 9 + 25 + 16 + 20 + 3 = 73 |
| `1111#0001` | 15 + 1 = 16 | `10000` | 5 | 9 + 25 + 16 + 20 + 3 = 73 |
| `10101#10111` | 21 + 23 = 44 | `101100` | 6 | 11 + 36 + 25 + 24 + 3 = 99 |
| `10000#00001` | 16 + 1 = 17 | `10001` | 5 | 11 + 25 + 25 + 20 + 3 = 84 |

Las cuatro entradas tienen más de cinco caracteres y cubren el acarreo encadenado, el desbordamiento, la suma sin acarreo y los ceros iniciales de B. La salida completa está en `docs/evidence/transformer_binary_addition.txt`.

## 14. Comparación y dificultad de las máquinas

La rúbrica asigna 3 puntos a la dificultad de la reconocedora y 3 a la de la alteradora, pero no define una escala. Esta sección no afirma ninguna puntuación: compara las máquinas con criterios medibles.

| Criterio | Reconocedora aⁿbⁿ | Incremento | Inversión | Suma |
|---|---|---|---|---|
| Estados | 5 | 3 | 7 | 10 |
| Reglas δ | 10 | 6 | 33 | 57 |
| Marcadores en Γ \ Σ | `X`, `Y` | — | `*`, `o`, `i` | `o`, `i` (y el separador `#` de Σ) |
| Valores de caché | B (no se usa) | B, 1 (redundante con q1) | B, 0, 1 (bit en tránsito) | B, 1, 2 (suma y acarreo) |
| Recorridos | n rondas de ida y vuelta y una verificación | Una ida y una vuelta parcial | ⌈n/2⌉ rondas de ida y vuelta, rebobinado y restauración | Validación, m rondas de ida y vuelta y restauración |
| Manipulación de posiciones | Marca en el lugar | Escribe en −1 al desbordarse | Intercambia extremos con un hueco | Borra B, escribe hacia la izquierda y llega a posiciones negativas |
| Tiempo | 2n² + 2n + 1 | \|w\| + t + 2 | ⌊(n² + 6n + 6)/2⌋ | \|w\| + m² + \|B\|² + 4m + 3 |
| Espacio | n celdas | \|w\| + 1 | n | n + max(0, m − \|A\|) |
| Justificación | Corrección e invariante (§10.5) | Análisis del acarreo (§11.6) | Invariante de rondas (§12.6) | Invariante por columnas (§13.7) |
| Rechaza entradas | Sí, con cinco motivos distintos | No | No | Sí, cuando no tienen la forma A#B |

**Máquinas de la demostración.**

- **Reconocedora: aⁿbⁿ.** Es el ejemplo que propone el propio enunciado, es correcta frente a un oráculo independiente y tiene cinco motivos de rechazo distintos. Se cita como el ejemplo 8.2 de Hopcroft et al. (2001), así que no se presenta como diseño original.
- **Alteradora principal: la suma binaria.** Es la que más estados y reglas tiene y la única que combina validación del formato, aritmética con acarreo de tres valores en la caché, borrado de un operando y crecimiento hacia posiciones negativas. Su paso a la demostración dependía de superar todas las pruebas; las supera: todos los pares con operandos de hasta 4 bits, 150 pares aleatorios de hasta 16 bits y la fórmula de pasos ([§13.7](#137-corrección-número-de-pasos-y-espacio)).
- **Complementarias.** El incremento binario y la inversión, cuyo algoritmo depende de la caché y que retoma el ejemplo «darle la vuelta a una cadena» del enunciado, se conservan para mostrar el mismo motor con otras transformaciones.

En el incremento, la caché repite información que ya contiene el estado q1; en la inversión y en la suma, en cambio, es indispensable.

## 15. Menú interactivo

`python main.py --interactive` abre un menú numérico con las cuatro máquinas. El menú no carga archivos arbitrarios: las máquinas salen de un catálogo interno de rutas conocidas, y cualquier otro YAML se ejecuta con `--machine`.

### 15.1 Arquitectura del menú

| Módulo | Responsabilidad | No hace |
|---|---|---|
| `src/cli/machine_catalog.py` | `CATALOG`: para cada máquina, la ruta de su YAML (relativa al código, no al directorio de trabajo) y los textos de presentación: objetivo, fases, papel de cada estado y marcador, uso de la caché, terminación y formato de entrada | Contener reglas δ, Q, Σ o Γ: esos datos se leen del YAML |
| `src/cli/interactive_menu.py` | `Menu`: navegación numérica, ficha técnica, lista de cadenas de la sesión, validación de cadenas nuevas, ejecución de una cadena y pausa | Simular por su cuenta ni escribir en los YAML |
| `src/cli/simulation_view.py` | `format_simulation`: los cinco bloques de una ejecución y el titular del veredicto (§15.7) | Simular ni calcular resultados: solo ordena una traza ya calculada |
| `src/output/machine_formatter.py` | Componentes formales, valores de caché y tabla δ por columnas; también la cabecera de `--machine` | Modificar la máquina |

El menú reutiliza la misma cadena de funciones que `--machine`: `load_yaml → parse_machine → validate_machine` al abrir una máquina, y `simulate → build_trace` al ejecutar una cadena. Para presentar el resultado, `simulation_view` usa `format_procedure` y `format_final_configuration`, las mismas funciones con que `format_result` arma el reporte de `--machine`. Las IDs, las reglas aplicadas y la configuración final son idénticas en los dos modos; el menú solo cambia el orden y deja el veredicto al final. `tests/test_interactive.py` comprueba esa igualdad, sección por sección, con las 16 cadenas predefinidas, y también que los estados y marcadores descritos en el catálogo sean exactamente los de cada YAML.

### 15.2 Flujo de navegación

```text
Menú principal ── 1–4 ──> ficha técnica de la máquina (una vez; no simula nada)
  │                          │
  5: Salir                   v
                      Submenú de la máquina
                        1. Cadenas disponibles ── n ──> ejecuta solo esa cadena ── ENTER ──> vuelve a la lista
                        │                         └─ «Regresar» ──> submenú
                        2. Ingresar una cadena nueva ── válida ──> se agrega y se ejecuta ── ENTER ──> submenú
                        │                              └─ inválida ──> diagnóstico: 1. Intentar de nuevo · 2. Regresar
                        3. Regresar al menú principal
```

La ficha técnica se imprime una vez por cada selección de la máquina en el menú principal, justo antes del submenú. No se repite al volver de una ejecución ni al regresar de la lista. Por eso el submenú no tiene una opción «Ver información»: repetía la ficha que ya está en pantalla. Para verla de nuevo basta con regresar (`3`) y volver a elegir la máquina.

La ficha técnica tiene siete partes:
- A: nombre y archivo de la máquina;
- B: objetivo formal;
- C: lenguaje o transformación;
- D: Q, Σ, Γ, q0, F, el blanco, los valores de caché y el número de reglas, leídos del YAML;
- E: la tabla δ completa por columnas (estado, caché, lectura, estado siguiente, caché siguiente, escritura y movimiento);
- F: el procedimiento mecanizado (fases, estados, marcadores, caché y terminación);
- G: la condición de aceptación o la transformación completa.

### 15.3 Modo `--machine` y modo `--interactive`

| | `--machine ARCHIVO` | `--interactive` |
|---|---|---|
| Máquinas | Cualquier YAML válido | Las cuatro del catálogo |
| Cadenas | Todas las de `simulation_strings`, en orden | Una por vez: predefinida o escrita en la terminal |
| Cabecera | Componentes y δ en notación del enunciado | Ficha técnica con la tabla δ por columnas y la explicación del procedimiento |
| Reporte por cadena | `format_result` completo: veredicto, configuración final y todas las IDs | Las mismas IDs y la misma configuración final, en bloques delimitados y con el veredicto al final ([§15.7](#157-presentación-de-una-ejecución)) |
| Pausa | Ninguna | «Presione ENTER para regresar al submenú...» después de cada ejecución |
| Errores | Código 1 y mensaje en la salida de errores | Diagnóstico y reintento; el menú continúa |
| Fin | Al terminar las cadenas | «Salir», fin de la entrada (código 0) o Ctrl+C (código 130) |

`--machine` e `--interactive` son excluyentes; `--max-steps N` se aplica a los dos.

### 15.4 Ejecutar una cadena predefinida

1. `python main.py --interactive` y elegir la máquina (por ejemplo `4`, suma binaria). Se muestra la ficha.
2. En el submenú, `1` (Cadenas disponibles). Cada cadena aparece numerada con su origen, `[predefinida]` o `[agregada en sesión]`.
3. Escribir el número de la cadena. Se ejecuta solo esa, con el procedimiento completo y el veredicto al final ([§15.7](#157-presentación-de-una-ejecución)).
4. Pulsar ENTER en la pausa. La lista vuelve a mostrarse; su última opción, «Regresar», vuelve al submenú.

### 15.5 Ingresar una cadena nueva

1. En el submenú, `2` (Ingresar una cadena nueva). El menú muestra la máquina, el alfabeto permitido y el formato esperado.
2. Escribir la cadena tal cual, por ejemplo `0011` o `101#11`. Los ceros iniciales se conservan: la cadena nunca se convierte a número. En las máquinas cuyo dominio incluye ε, una línea vacía es la cadena vacía.
3. Si es válida, se agrega a la lista de la sesión (sin duplicados) y se ejecuta de inmediato; después de ENTER se vuelve al submenú. La lista se conserva al regresar al menú principal y volver a la máquina, pero solo mientras el programa está abierto: el YAML nunca se modifica.

### 15.6 Validaciones de entrada

| Contexto | Entrada | Respuesta |
|---|---|---|
| Menú o submenú | Número de una opción (se toleran espacios alrededor) | Se ejecuta la opción |
| Menú o submenú | Vacía, texto, `0`, fuera de rango, `1.0` | «Opción no válida» o «No escribió ninguna opción»; se vuelve a preguntar |
| Cadena nueva | Símbolo fuera de Σ (`1021`, `10 01`) | Diagnóstico con los símbolos inválidos; reintentar o regresar |
| Cadena nueva | Fuera del formato de la máquina | Diagnóstico con el formato esperado |
| Pausa tras una ejecución | ENTER (se acepta cualquier línea) | Vuelve a la lista de cadenas o al submenú |
| Cualquiera | Fin de la entrada (Ctrl+D) | «Fin de la entrada: el simulador se cierra.», código 0 |
| Cualquiera | Ctrl+C | «Interrumpido con Ctrl+C: el simulador se cierra.», código 130, sin traza de error |

Formato de cada máquina:

| Máquina | Formato admitido |
|---|---|
| Reconocedora | Cualquier cadena sobre {a, b}, incluida ε; la máquina decide si pertenece a L |
| Incremento | Cadena binaria no vacía |
| Inversión | Cadena binaria, incluida ε |
| Suma | A#B: dos números binarios no vacíos y un único `#` |

Las opciones del menú y las cadenas se piden en momentos distintos, así que un `1` escrito como opción nunca se toma como la cadena binaria `1`. Una cadena que el menú no admite tampoco se presenta como rechazo: el rechazo solo lo decide la máquina al simular.

### 15.7 Presentación de una ejecución

Cada ejecución, desde la lista o como cadena nueva, se imprime en cinco bloques delimitados y en este orden. Los separadores son ASCII: `=` para el inicio, el veredicto y el fin, y `-` para las secciones intermedias. La notación formal conserva sus símbolos Unicode (δ, ε, ⊢).

| Bloque | Contenido | Origen |
|---|---|---|
| INICIO DE SIMULACIÓN | Máquina y su archivo, cadena de entrada y longitud | Catálogo y cadena elegida |
| PROCEDIMIENTO PASO A PASO | Todas las IDs, de ID_0 a ID_n, cada una con la regla δ que la produjo | `format_procedure`: las mismas líneas que `--machine` |
| CONFIGURACIÓN FINAL | Estado, caché, cabezal, cinta e ID final, y la cinta por posiciones con el cabezal | `format_final_configuration`: las mismas líneas que `--machine` |
| VEREDICTO FINAL | Titular, cadena evaluada (o cadena original y cinta resultante), pasos y motivo | `outcome`, `reason` y la configuración final de la traza |
| FIN DE SIMULACIÓN | Cierre; después viene la pausa | — |

Ningún resultado aparece antes del procedimiento: primero se ve cómo se ejecutó la máquina y al final su conclusión. El titular depende del resultado y del tipo de máquina:

| Resultado | Reconocedora | Alteradora |
|---|---|---|
| `ACCEPTED` | `ACCEPTED — CADENA ACEPTADA` | `ACCEPTED — TRANSFORMACIÓN COMPLETADA`, con la cadena original y la cinta resultante |
| `REJECTED` | `REJECTED — CADENA RECHAZADA` | `REJECTED — PROCESAMIENTO RECHAZADO` |
| `LIMIT_EXCEEDED` | `LIMIT_EXCEEDED — LÍMITE DE PASOS ALCANZADO` | `LIMIT_EXCEEDED — LÍMITE DE PASOS ALCANZADO` |

El motivo es el texto que el motor produce al detenerse, no un mensaje genérico. Por ejemplo: «No hay regla para el estado 'q1' con caché el blanco leyendo el blanco, y 'q1' no es final.» Con `LIMIT_EXCEEDED` se agrega que no se demostró aceptación ni rechazo, porque la máquina aún tenía una transición aplicable. La cinta resultante es el contenido de la configuración final, de la primera a la última celda no blanca: el menú no calcula la transformación por su cuenta.

El menú solo ejecuta cadenas con el formato de la máquina. Por eso, con las cuatro máquinas actuales, una alteradora no llega a `REJECTED` desde el menú. El titular existe para que un rechazo nunca se presente como transformación completada, y `tests/test_interactive.py` lo comprueba con la suma sobre `1011`.

Al terminar, el menú muestra «Presione ENTER para regresar al submenú...» y no imprime nada más hasta recibir la línea. Desde «Cadenas disponibles» se vuelve a la lista; desde «Ingresar una cadena nueva», al submenú de la máquina. Si la entrada termina durante la pausa (Ctrl+D, o una entrada redirigida que se agota), el simulador se cierra con código 0. Con Ctrl+C se cierra con código 130. `--machine` no hace pausas.

### 15.8 Ejemplo real

Sesión real en la reconocedora con la cadena `aab`, ingresada como cadena nueva: opción `1` en el menú principal, luego `2` en el submenú (se omite la ficha que se imprime al elegir la máquina). Después de cada prompt se muestra lo que se escribió; tras «Presione ENTER…» se pulsó ENTER sin texto.

```text
=========================================
           MÁQUINA SELECCIONADA
=========================================

Reconocedora — a^n b^n

1. Cadenas disponibles
2. Ingresar una cadena nueva
3. Regresar al menú principal

Seleccione una opción: 2

INGRESAR NUEVA CADENA

Máquina: Reconocedora aⁿbⁿ
Alfabeto permitido: {a, b}
Formato: cualquier cadena sobre {a, b}, incluida la vacía; la máquina decide si pertenece a L
Deje la línea vacía para ingresar la cadena vacía (ε).
Ingrese una cadena: aab
'aab' se agregó a la lista de esta sesión (n.º 5).

=================================================
               INICIO DE SIMULACIÓN
=================================================

Máquina: Reconocedora — a^n b^n (recognizer_anbn.yaml)
Cadena de entrada: 'aab'
Longitud: 3

-------------------------------------------------
            PROCEDIMIENTO PASO A PASO
-------------------------------------------------

Descripciones instantáneas (ID_0 a ID_7):
  Paso  ID          Transición aplicada
     0  [q0,B]aab   —
     1  X[q1,B]ab   δ([q0, B], a) = ([q1, B], X, R)
     2  Xa[q1,B]b   δ([q1, B], a) = ([q1, B], a, R)
     3  X[q2,B]aY   δ([q1, B], b) = ([q2, B], Y, L)
     4  [q2,B]XaY   δ([q2, B], a) = ([q2, B], a, L)
     5  X[q0,B]aY   δ([q2, B], X) = ([q0, B], X, R)
     6  XX[q1,B]Y   δ([q0, B], a) = ([q1, B], X, R)
     7  XXY[q1,B]B  δ([q1, B], Y) = ([q1, B], Y, R)

-------------------------------------------------
               CONFIGURACIÓN FINAL
-------------------------------------------------

Estado final:  q1
Caché final:   B
Cabezal final: 3
Cinta final:   XXY
ID final:      XXY[q1,B]B

posición 0 1 2 3
cinta    X X Y B
cabezal        ^

=================================================
                 VEREDICTO FINAL
=================================================

           REJECTED — CADENA RECHAZADA

Cadena evaluada:  'aab'
Pasos realizados: 7

Motivo:
No hay regla para el estado 'q1' con caché el blanco leyendo el blanco, y 'q1' no es final.

=================================================
                FIN DE SIMULACIÓN
=================================================

Presione ENTER para regresar al submenú...

=========================================
           MÁQUINA SELECCIONADA
=========================================

Reconocedora — a^n b^n

1. Cadenas disponibles
2. Ingresar una cadena nueva
3. Regresar al menú principal

Seleccione una opción: 3
```

`aab` no pertenece a L: la máquina marcó las dos `a`, pero q1 llega al blanco sin encontrar una segunda `b` que emparejar. Con `aabbbb` (cadena 4 de la lista) se detiene en `REJECTED` en 12 pasos, y con `aaabbb` en `ACCEPTED` en 25.

## 16. Decisiones de implementación en Python

| Decisión | Dónde | Por qué |
|---|---|---|
| Cinta dispersa `dict[int, str]` | `src/model/tape.py` | Admite índices negativos y crecimiento hacia ambos lados sin desplazar el contenido; leer una celda ausente devuelve el blanco |
| Modelos inmutables | `src/model/` (salvo la cinta de trabajo `Tape`), `src/simulator/trace.py` | `@dataclass(frozen=True)`, `frozenset` y `MappingProxyType` para la cinta de cada ID: una ID registrada no cambia después, así que la traza nunca muestra referencias a la cinta final |
| δ indexada una sola vez | `src/model/turing_machine.py` | Un diccionario por (estado, caché, símbolo) da búsqueda en O(1) esperado y detecta las reglas duplicadas con su posición |
| PyYAML seguro y estricto | `src/input/yaml_loader.py` | `SafeLoader` con rechazo de claves repetidas; sin conversión de tipos implícita (D7) |
| Errores acumulados | `src/input/machine_validator.py` | Informa todos los problemas de una máquina a la vez, con la ruta del campo, en lugar de detenerse en el primero |
| Traza verificada | `src/simulator/trace.py` | `build_trace` comprueba cada paso contra su regla; los formateadores solo convierten texto |
| Blanco sin ambigüedad | `src/utils/notation.py` | `blank_glyph` usa `B`, como los laboratorios, salvo que la máquina use `B` como símbolo o valor de caché; entonces busca el primer carácter libre desde `□` |
| Salida en UTF-8 | `main.py` | Reconfigura `stdout` y `stderr` para imprimir δ, ⊢ y ε también en consolas de Windows o con la salida redirigida |
| Catálogo separado del menú | `src/cli/machine_catalog.py` | Solo contiene rutas y textos; la definición formal y δ se leen siempre del YAML, así que una corrección en el YAML se refleja en la ficha sin tocar Python |
| Un solo formateador de máquinas | `src/output/machine_formatter.py` | La cabecera de `--machine` (`describe_machine`) y la ficha del menú (`formal_components`, `format_delta_table`) salen del mismo módulo |
| Entrada inyectable | `run_menu(read, out)` | Las pruebas usan un teclado simulado y comparan el texto sin depender de una terminal real |
| Documentación en el código | Todos los módulos de producción | Docstrings con la responsabilidad y la propiedad formal de cada módulo, clase y función, salvo los métodos especiales (`__init__`, `__post_init__`, `__repr__`) y los `__init__.py` vacíos; comentarios `#` con los pasos de [§3.2](#32-procedimiento-mecanizado) donde ocurren |
| Un solo motor para los dos modos | `src/cli/` | El menú llama a `simulate`, `build_trace` y `src/output/`, sin simulador ni formateador propios; `tests/test_interactive.py` comprueba con las 16 cadenas predefinidas que las IDs y la configuración final coincidan con `--machine` |
| Biblioteca estándar más PyYAML | `requirements.txt` | `argparse` para la CLI; `re`, `textwrap` y `dataclasses` para el menú; `pytest` solo para las pruebas |

## 17. Validación y pruebas automatizadas

La corrección se comprueba con oráculos independientes del simulador ([§17.1](#171-estrategia-de-validación)) y con una suite automatizada que ejecuta esas comprobaciones ([§17.2](#172-pruebas-automatizadas)).

### 17.1 Estrategia de validación

1. **Oráculos independientes del simulador.** Ninguno usa el motor y solo existen en las pruebas:
   - la pertenencia a {aⁿbⁿ} se calcula con su definición;
   - el sucesor binario, con `int(w, 2) + 1`;
   - la inversa, con `w[::-1]`;
   - la suma, con `int(A, 2) + int(B, 2)` y el ancho de la política de salida.
2. **Pruebas exhaustivas.** A nivel de biblioteca:
   - todas las cadenas sobre {a, b} de longitud ≤ 10 (2047) en la reconocedora;
   - todas las binarias de longitud 1 a 10 (2046) en el incremento;
   - todas las de longitud 0 a 10 (2047) en la inversión;
   - todos los pares A#B con operandos de 1 a 4 bits (900) en la suma, más 150 pares aleatorios de hasta 16 bits con semilla fija.

   A nivel de CLI, en un proceso aparte:
   - todas las de longitud 0 a 8 sobre {a, b} (511) en la reconocedora;
   - las binarias de longitud 1 a 9 (1022) en el incremento;
   - las binarias de longitud 0 a 8 (511) en la inversión;
   - los pares A#B con operandos de 1 a 3 bits (196) en la suma.
3. **Reproducción de δ desde el YAML.** Para las 16 cadenas de la demostración, cada ID_k+1 se recalcula a partir de ID_k con la δ leída directamente del archivo con `yaml.safe_load`, sin el parser ni el motor del proyecto.
4. **Fórmulas cerradas.** Los pasos reales se comparan con T(n) = 2n² + 2n + 1, T(w) = |w| + t + 2, en la inversión con T(n) = ⌊(n² + 6n + 6)/2⌋ y en la suma con T(A#B) = |A#B| + m² + |B|² + 4m + 3.
5. **Invariantes.** En la inversión, cada visita a q0 se compara con el invariante de rondas (§12.6). En la suma, la caché al entrar a q6 se compara con la suma b_k + acarreo_k de cada columna calculada aparte.
6. **Equivalencia con los laboratorios.** Los resultados resueltos a mano se usan como oráculos:

| Laboratorio | Entrada | Resultado a mano | Simulador |
|---|---|---|---|
| 10 b) | `aab#aab` | `[q0,B]aab#aab ⊢^32 BBB#XXXB[q5,B]B`, aceptada | `ACCEPTED`, 32 transiciones, mismas IDs |
| 10 c) | `abb#aab` | `⊢^13 BBb#X[q2,b]ab`, δ([q2,b], a) no definida | `REJECTED`, 13 transiciones, estado 2, caché b |
| 9, ej. 2 a) | `100` | 5 pasos, `101 q_halt B` | 5 transiciones, cinta `101` |
| 9, ej. 2 b) | `10011` | 9 pasos, `101 q_halt 00` | 9 transiciones, cinta `10100` |
| 9, ej. 2 c) | `11` | 6 pasos, `q_halt BB00` | 6 transiciones, cinta `00`, cabezal −2 |

7. **Casos límite.** Se cubren:
   - cinta vacía y cabezal en posiciones negativas;
   - estado final con reglas salientes y máquina sin reglas;
   - detención exacta en `max_steps`;
   - cadenas fuera de Σ, YAML inválido, claves repetidas y símbolos Unicode;
   - cadenas de Σ\* sin la forma A#B (rechazadas con la cinta intacta) y ε en la inversión.
8. **Independencia.** Las mismas cadenas en otro orden, repetidas o intercaladas con otras producen reportes idénticos. En el menú, las cadenas de una máquina no aparecen en otra.
9. **Equivalencia entre modos.** Cada cadena predefinida de las cuatro máquinas, ejecutada desde el menú, muestra exactamente las mismas IDs, reglas aplicadas y configuración final que `--machine`, y un veredicto con el mismo resultado, número de pasos y motivo.
10. **Mutaciones.** En copias temporales se alteraron:
    - reglas de los YAML nuevos: escrituras, destinos, la regla de ε y un segundo `#` admitido;
    - el menú: sin sesiones, sin validación del formato y con IDs recortadas;
    - la presentación: ficha repetida tras cada ejecución, sin pausa, veredicto antes del procedimiento y motivo genérico.

    En cada caso fallaron pruebas, así que las pruebas detectan esos defectos.
11. **Coherencia de la documentación.** `tests/test_integration.py` comprueba sobre este README que:
    - cada enlace interno apunte a un encabezado existente, y cada referencia «§» nombre una sección que existe, con el número de su encabezado;
    - el índice enumere todas las secciones, en orden;
    - cada ruta citada exista, salvo los documentos retirados que se integraron aquí, y ningún enlace use una ruta absoluta;
    - las secciones citadas desde las pruebas y los YAML existan, y cada YAML cite la sección que describe su máquina;
    - la secuencia de teclas del video (§21) produzca las ocho ejecuciones obligatorias;
    - la tabla de §17.2 coincida con las pruebas que recoge pytest.

### 17.2 Pruebas automatizadas

```bash
python -m pytest -q
```

Resultado en Fedora 43 con Python 3.14.6: **524 pruebas aprobadas, 0 fallidas, 0 omitidas**. El mismo resultado se obtuvo en un entorno virtual nuevo, sobre una copia limpia del repositorio (`git archive`), instalando solo `requirements.txt` (PyYAML 6.0.3, pytest 9.2.0).

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
| `test_transformer.py` | 25 | Incremento: demostración, desbordamiento en −1, caché, exhaustiva 1–10 |
| `test_reverse.py` | 29 | Inversión: demostración, palíndromos, ceros, paridad, ε, invariante de rondas, caché, exhaustiva 0–10, fórmula de pasos |
| `test_addition.py` | 42 | Suma: demostración, acarreo, desbordamiento, cero, ceros iniciales, formatos mal formados, símbolos fuera de Σ, exhaustiva ≤ 4 bits, aleatoria ≤ 16 bits, fórmula de pasos, caché por columna, recorrido de `1#1` |
| `test_interactive.py` | 78 | Menú: navegación, submenú de tres opciones, ficha una vez por selección, opciones inválidas, ejecución individual con las mismas IDs y configuración que `--machine`, orden de los bloques, veredictos, pausa con ENTER, cadenas nuevas, validación, sesión, EOF, Ctrl+C, otro directorio de trabajo, recorrido real en un proceso aparte, catálogo frente al YAML |
| `test_integration.py` | 61 | Extremo a extremo por proceso aparte con las cuatro máquinas: oráculos, reproducción de δ, frontera de `max_steps`, independencia, errores de entrada, evidencia de `docs/evidence/`, secuencia del video en `--interactive`; en el README, índice, enlaces, referencias «§», rutas, secciones citadas desde los YAML y las pruebas, y conteos |

## 18. Instalación y ejecución

Requisitos: Python 3.10 o superior (el código usa la sintaxis `X | None`) y PyYAML. El proyecto se probó con Python 3.14.6 en Fedora 43. En Windows 11, con Python 3.14.3, se ejecutó una versión anterior de la suite: 310 pruebas aprobadas y 1 omitida, la de archivo ilegible ([§22](#22-discusión-obstáculos-y-recomendaciones)). No se probó en las versiones 3.10 a 3.13.

**Fedora / Linux** (comandos verificados):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python main.py --interactive
python main.py --machine machines/recognizer_anbn.yaml
python main.py --machine machines/transformer_binary_addition.yaml
python main.py --machine machines/transformer_binary_increment.yaml
python main.py --machine machines/transformer_binary_reverse.yaml
```

**Windows (PowerShell):** los mismos comandos, creando el entorno con `py -m venv .venv` y activándolo con `.venv\Scripts\Activate.ps1`. La instalación con `requirements.txt` y esa versión de la suite se ejecutaron en Windows; los comandos de activación del entorno y la suite actual no se volvieron a verificar allí.

| Argumento | Obligatorio | Descripción |
|---|---|---|
| `--machine ARCHIVO` | Uno de los dos | Archivo YAML con la máquina; simula todas sus `simulation_strings` |
| `--interactive` | Uno de los dos | Menú numérico con las cuatro máquinas ([§15](#15-menú-interactivo)) |
| `--max-steps N` | No | Máximo de transiciones por cadena (entero positivo; por defecto 10000) |

Otros ejemplos:

```bash
python main.py --machine machines/examples/basic_machine.yaml              # Laboratorio 10
python main.py --machine machines/recognizer_anbn.yaml --max-steps 30      # muestra LIMIT_EXCEEDED
python main.py --help
```

Con `--machine`, la salida estándar contiene, en este orden:

1. la descripción formal de la máquina (Q, Σ, Γ, q0, F, blanco) y la tabla δ completa, numerada en el orden del YAML;
2. por cada cadena: encabezado con la cadena y su longitud; `Resultado` (`ACCEPTED`, `REJECTED` o `LIMIT_EXCEEDED`) y `Motivo`; pasos, estado, caché y cabezal finales; `Cinta final`; `ID final`; vista de la cinta por posiciones con el cabezal; y la tabla completa «Paso | ID | Transición aplicada», de ID_0 a ID_n;
3. el bloque `=== Resumen ===`, con una fila por cadena.

| Código de salida | Significado |
|---|---|
| 0 | Todas las cadenas se simularon (aceptadas, rechazadas o detenidas por el límite), o el menú se cerró con «Salir» o al terminar la entrada |
| 1 | El archivo no se pudo leer o la máquina no es válida; el detalle va a la salida de errores |
| 2 | Argumentos incorrectos (por ejemplo, ninguno de los dos modos, o los dos a la vez) |
| 130 | El menú se interrumpió con Ctrl+C |

## 19. Ejemplo completo de simulación

Este ejemplo sigue una ejecución completa del incremento binario ([§11](#11-máquina-alteradora-incremento-binario)) con la cadena `11111`. Se eligió porque es corta, usa la caché, modifica todas las celdas de la entrada y termina con el cabezal en una posición negativa. Todo el texto en bloques de esta sección es salida real del programa; las salidas completas de las cuatro máquinas están en `docs/evidence/`.

### 19.1 Salida del programa

Cabecera y reporte de la tercera cadena de `python main.py --machine machines/transformer_binary_increment.yaml` (las otras tres cadenas y el resumen se omiten):

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

### 19.2 Una transición, paso a paso

La fila 7 de la tabla aplica a ID_6 los diez pasos de [§3.2](#32-procedimiento-mecanizado):

| Paso | En el ejemplo |
|---|---|
| 1. Leer la configuración actual | ID_6 = `1111[q1,1]1` |
| 2. Identificar estado, caché y símbolo | q = q1, c = 1 (acarreo pendiente) y el símbolo leído es `1`, en la posición 4 |
| 3. Buscar la transición | δ([q1, 1], 1) = ([q1, 1], 0, L), la regla 4 del YAML |
| 4. Escribir | La posición 4 pasa de `1` a `0` |
| 5. Actualizar el estado | q1 |
| 6. Actualizar la caché | 1: el acarreo continúa |
| 7. Mover el cabezal | L: de la posición 4 a la 3 |
| 8. Construir la nueva configuración | ID_7 = `111[q1,1]10` |
| 9. Registrar la ID | Fila 7 de la tabla; ID_6 no cambia |
| 10. Comprobar la terminación | q1 ∉ F y hay regla para (q1, 1, 1): la simulación continúa |

### 19.3 Configuración inicial, parada y resultado

- **Configuración inicial.** ID_0 = `[q0,B]11111`: estado q0, caché en blanco y cabezal en la posición 0, sobre el primer `1`.
- **Barrido y carga del acarreo.** Las filas 1 a 5 cruzan los bits sin cambiarlos. En ID_5 = `11111[q0,B]B` el cabezal lee el blanco de la posición 5, y la fila 6 aplica la regla 3, que carga el acarreo en la caché: ID_6 muestra `[q1,1]`.
- **Propagación.** Las filas 7 a 11 aplican la regla 4 y cambian cada `1` por `0` hacia la izquierda. En ID_11 = `[q1,1]B00000` el cabezal está en la posición −1, sobre un blanco.
- **Parada.** La fila 12 aplica la regla 6: escribe el `1` nuevo en la posición −1, vacía la caché y no mueve el cabezal. En ID_12 = `[q2,B]100000` el estado q2 pertenece a F, así que la simulación se detiene con `ACCEPTED` y el motivo «alcanzó el estado final 'q2'».
- **Cinta final.** `100000`, de la posición −1 a la 4, como muestra la vista por posiciones: value₂(11111) + 1 = 31 + 1 = 32.
- **Pasos.** 12 = |w| + t + 2 = 5 + 5 + 2, la fórmula de [§11.6](#116-índice-negativo-cinta-final-y-número-de-pasos).

### 19.4 El mismo resultado en el menú

Con `python main.py --interactive`, opción `2` (incremento binario), `1` (Cadenas disponibles) y la cadena `3`, la ejecución muestra las mismas IDs y la misma configuración final, y termina con este veredicto real:

```text
=================================================
                 VEREDICTO FINAL
=================================================

       ACCEPTED — TRANSFORMACIÓN COMPLETADA

Cadena original:  '11111'
Cinta resultante: '100000'
Pasos realizados: 12

Motivo:
Alcanzó el estado final 'q2'.

=================================================
                FIN DE SIMULACIÓN
=================================================
```

En una alteradora, `ACCEPTED` significa que la máquina terminó en su estado final; la cinta resultante es la transformación de la entrada.

## 20. Resultados de las máquinas

Salida real de `python main.py --machine` con los cuatro archivos de `machines/`, guardada en `docs/evidence/`. Coincide con los valores esperados de [§10.7](#107-cadenas-de-la-demostración), [§11.9](#119-cadenas-de-la-demostración), [§12.8](#128-cadenas-de-la-demostración) y [§13.9](#139-cadenas-de-la-demostración), y con los oráculos independientes. Desde el menú, cada cadena muestra las mismas IDs y la misma configuración final, organizadas en bloques ([§15.7](#157-presentación-de-una-ejecución)).

| Máquina | Cadena | Longitud | Resultado | Pasos | Cinta final | ID final |
|---|---|---|---|---|---|---|
| Reconocedora | `aaabbb` | 6 | ACCEPTED | 25 | `XXXYYY` | `XXXYYYB[q4,B]B` |
| Reconocedora | `aaaabbbb` | 8 | ACCEPTED | 41 | `XXXXYYYY` | `XXXXYYYYB[q4,B]B` |
| Reconocedora | `aaabb` | 5 | REJECTED | 17 | `XXXYY` | `XXXYY[q1,B]B` |
| Reconocedora | `aabbbb` | 6 | REJECTED | 12 | `XXYYbb` | `XXYY[q3,B]bb` |
| Suma (principal) | `1011#0110` | 9 | ACCEPTED | 73 | `10001` | `[q9,B]10001BBBBB` |
| Suma (principal) | `1111#0001` | 9 | ACCEPTED | 73 | `10000` | `[q9,B]10000BBBBB` |
| Suma (principal) | `10101#10111` | 11 | ACCEPTED | 99 | `101100` | `[q9,B]101100BBBBBB` |
| Suma (principal) | `10000#00001` | 11 | ACCEPTED | 84 | `10001` | `[q9,B]10001BBBBBB` |
| Incremento | `10101` | 5 | ACCEPTED | 8 | `10110` | `101[q2,B]10` |
| Incremento | `11011` | 5 | ACCEPTED | 9 | `11100` | `11[q2,B]100` |
| Incremento | `11111` | 5 | ACCEPTED | 12 | `100000` | `[q2,B]100000` |
| Incremento | `10000` | 5 | ACCEPTED | 7 | `10001` | `1000[q2,B]1` |
| Inversión | `10110` | 5 | ACCEPTED | 30 | `01101` | `01101[q6,B]B` |
| Inversión | `11001` | 5 | ACCEPTED | 30 | `10011` | `10011[q6,B]B` |
| Inversión | `10000` | 5 | ACCEPTED | 30 | `00001` | `00001[q6,B]B` |
| Inversión | `11100` | 5 | ACCEPTED | 30 | `00111` | `00111[q6,B]B` |

Motivos de los rechazos:

- `aaabb`: «no hay regla para el estado 'q1' con caché el blanco leyendo el blanco, y 'q1' no es final» (falta una `b`).
- `aabbbb`: «no hay regla para el estado 'q3' con caché el blanco leyendo 'b', y 'q3' no es final» (sobran `b`).

En las alteradoras, `ACCEPTED` significa que la máquina se detuvo normalmente en su estado final; el resultado de la transformación es la columna «Cinta final». En la suma, la ID final muestra como `B` las celdas donde estaban `#` y B, porque el rango visible incluye toda la zona de la entrada; la cinta final contiene solo el resultado.

### 20.1 Evidencia en el repositorio

`docs/evidence/` contiene la salida completa y real de `--machine` para las cuatro máquinas: la cabecera con la tabla δ, las cuatro cadenas de cada una con todas sus IDs y el resumen. Los archivos son:
- `recognizer_anbn.txt`
- `transformer_binary_addition.txt`
- `transformer_binary_increment.txt`
- `transformer_binary_reverse.txt`

`tests/test_integration.py` vuelve a ejecutar la CLI y comprueba que la salida coincida carácter por carácter con los cuatro archivos. Para regenerarlos, desde la raíz y en Linux:

```bash
for m in recognizer_anbn transformer_binary_addition transformer_binary_increment transformer_binary_reverse; do
    python main.py --machine machines/$m.yaml > docs/evidence/$m.txt
done
```

## 21. Demostración y guion del video

La demostración principal se hace en una sola sesión de `python main.py --interactive`, con la reconocedora aⁿbⁿ y la suma binaria. Las otras dos alteradoras son evidencia complementaria si el tiempo lo permite; no deben desplazar las ocho ejecuciones obligatorias.

| Parte | Qué mostrar | Cómo | Material | Rubro |
|---|---|---|---|---|
| 1. Presentación | Proyecto, integrantes y objetivo | Este README | [§1](#1-objetivo-del-proyecto) | — |
| 2. Arquitectura | Un solo motor genérico: entrada → modelo → simulador → traza → salida; la CLI y el menú usan las mismas funciones | Diagrama de [§2](#2-flujo-general-del-simulador) | [§2](#2-flujo-general-del-simulador), [§5](#5-arquitectura), [§15.1](#151-arquitectura-del-menú) | Arquitectura (1) |
| 3. Formato YAML | Claves del enunciado, caché dentro de [q, c], blanco = entrada vacía | Abrir `machines/transformer_binary_addition.yaml` | [§7](#7-contrato-yaml) | — |
| 4. Menú | Las cuatro máquinas; al elegir una se muestra su ficha una vez y el submenú de tres opciones | `python main.py --interactive` | [§15](#15-menú-interactivo) | — |
| 5. Reconocedora | Ficha: Q, Γ, tabla δ y fases de marcar, buscar, regresar y comprobar | `1` | [§10](#10-máquina-reconocedora) | Dificultad (3) |
| 6. Dos aceptadas | `aaabbb` (25 pasos) y `aaaabbbb` (41 pasos): inicio, todas las IDs, configuración final y veredicto | `1` (Cadenas disponibles), `1`, ENTER, `2`, ENTER | [§20](#20-resultados-de-las-máquinas) | Aceptadas (2) |
| 7. Dos rechazadas | `aaabb` y `aabbbb`: el veredicto final da el motivo real, la clave sin regla | `3`, ENTER, `4`, ENTER; luego `5` (Regresar) y `3` (menú principal) | [§10.4](#104-tabla-de-transiciones) | No aceptadas (2) |
| 8. Alteradora principal | Ficha de la suma: validación, caché con la suma (B, 1, 2) y el acarreo, marcas `o`/`i` | `4` | [§13](#13-máquina-alteradora-suma-binaria) | Dificultad (3) |
| 9. Cuatro transformaciones | `1011#0110 → 10001`, `1111#0001 → 10000`, `10101#10111 → 101100`, `10000#00001 → 10001`: «TRANSFORMACIÓN COMPLETADA» con la cinta resultante | `1`, luego `1`, `2`, `3` y `4`, cada una seguida de ENTER | [§13.9](#139-cadenas-de-la-demostración) | Cuatro cadenas (4) |
| 10. Tabla δ e IDs | En una traza: la fila k muestra la regla que transformó ID_k−1; `[q5,2]` lleva una suma de 2; el resultado crece hacia la posición −1 | Sobre la traza anterior | [§9](#9-descripciones-instantáneas), [§13.8](#138-recorrido-a-mano-11--10) | Arquitectura (1), dificultad (3) |
| 11. Entradas nuevas | Diagnóstico de `1011` (sin `#`) y ejecución de `101#11 → 1000` | `5` (Regresar), `2`, `1011`, `1`, `101#11`, ENTER | [§15.5](#155-ingresar-una-cadena-nueva)–[§15.8](#158-ejemplo-real) | — |
| 12. Conclusión | `python -m pytest -q`, oráculos independientes y limitaciones reales; si hay tiempo, inversión e incremento | `3`, `5` (Salir) | [§17.1](#171-estrategia-de-validación), [§17.2](#172-pruebas-automatizadas), [§23](#23-limitaciones-y-alcance) | — |

Secuencia completa de teclas de las partes 4 a 12:

```text
1  1  1 ⏎ 2 ⏎ 3 ⏎ 4 ⏎  5  3  4  1  1 ⏎ 2 ⏎ 3 ⏎ 4 ⏎  5  2  1011  1  101#11 ⏎  3  5
```

`⏎` es ENTER sin texto: contesta la pausa que sigue a cada ejecución.

La secuencia se verificó en Fedora con la entrada redirigida desde un archivo. Produce exactamente las ocho ejecuciones obligatorias (`aaabbb`, `aaaabbbb` aceptadas; `aaabb`, `aabbbb` rechazadas; las cuatro sumas) y la de `101#11`, y termina con «Hasta luego.». Ninguna cadena obligatoria necesita escribirse en vivo: las ocho están en `simulation_strings`. Comandos alternativos, sin menú:

```bash
python -m pytest -q
python main.py --machine machines/recognizer_anbn.yaml
python main.py --machine machines/transformer_binary_addition.yaml
```

## 22. Discusión, obstáculos y recomendaciones

### Obstáculos encontrados

- **Semántica de `mem_cache_value`.** El enunciado no define cómo participa la caché en la búsqueda de reglas. Se fijó a partir de la notación δ([q, c], X) y del ejemplo del YAML (E2, E3) antes de escribir el parser, en lugar de ignorar el campo o convertirlo en una segunda cinta.
- **Ejemplo del enunciado incompleto.** No cumple Σ ⊆ Γ y usa símbolos fuera de Σ ([§7.6](#76-observaciones-sobre-el-ejemplo-del-enunciado)). Se decidió reportar esas inconsistencias en lugar de corregirlas en silencio.
- **YAML permisivo.** PyYAML conserva en silencio la última de dos claves repetidas y YAML 1.1 convierte `0101` en un número. Ambos casos cambiarían la máquina sin aviso; se rechazan explícitamente.
- **Detención exactamente en el límite.** Una primera versión del motor comprobaba el límite antes de buscar la regla, de modo que una máquina que se detenía sin regla justo tras `max_steps` transiciones se reportaba como `LIMIT_EXCEEDED`. Se corrigió calculando primero si hay regla aplicable, y hay pruebas de esa frontera a nivel de motor y de CLI.
- **Portabilidad de las pruebas.** En Windows, `chmod(0)` no quita el permiso de lectura; la prueba de archivo ilegible se omite solo donde eso ocurre.
- **Visibilidad de δ y blanco ambiguo.** La CLI mostraba solo el número de reglas y el glifo alternativo del blanco no se comparaba con Γ. Ahora la cabecera imprime la tabla δ completa y `blank_glyph` descarta cualquier glifo que la máquina use en Γ o en la caché.
- **Invertir con un solo valor de caché.** La caché guarda un solo símbolo, pero un intercambio necesita dos. Se resolvió con un hueco `*`: el bit de la izquierda viaja en la caché, en el extremo derecho se cambia por el bit que había y ese bit regresa en la caché a llenar el hueco.
- **Sumar operandos de distinta longitud.** Rellenar con ceros o desplazar el operando corto habría exigido muchas más reglas. Bastó con tratar el blanco a la izquierda de A como un 0: el resultado crece hacia posiciones negativas, que la cinta dispersa admite.
- **Formato frente a rechazo.** En la suma se separó la validación del formato (q0–q3, sin escribir nada) del cálculo, para que una cadena mal formada se rechace sin dejar una cinta a medio calcular. El menú, además, no admite esas cadenas, para no presentar como rechazo un error de captura.

### Recomendaciones

- Definir siempre el blanco con una entrada vacía y entrecomillar los símbolos numéricos (`'0'`, `'1'`).
- Usar `--max-steps` bajo para explorar máquinas nuevas: un `LIMIT_EXCEEDED` indica que la máquina aún tenía reglas aplicables, no que rechace.
- Revisar la tabla δ impresa en la cabecera, o en la ficha del menú, antes de leer las trazas: es exactamente la que ejecuta el motor.
- Para explorar una máquina, usar el menú e ingresar cadenas cortas; las trazas crecen de forma cuadrática.

## 23. Limitaciones y alcance

- Solo MT deterministas de una cinta. No hay multicinta ni no determinismo.
- Los estados finales son terminales: las reglas que salen de F se aceptan en el archivo, pero nunca se ejecutan.
- Cada símbolo de Σ y Γ es un único carácter. La caché admite cualquier cadena no vacía, pero no se valida contra Γ porque ninguna fuente lo exige.
- La tupla de control se escribe `[q,c]` sin escapar sus componentes: un estado o un valor de caché con `[`, `,` o `]` haría ambigua la ID. El validador no lo prohíbe; ninguna de las máquinas del proyecto usa esos caracteres.
- La cota por defecto es de 10 000 transiciones por cadena. Las trazas largas se imprimen completas (la reconocedora crece como 2n² + 2n + 1).
- El incremento binario está diseñado para cadenas binarias no vacías (con ε produce `1`) y se detiene sobre el último bit modificado, sin regresar el cabezal al inicio.
- La suma conserva los ceros iniciales hasta max(|A|, |B|) bits: `0001#0010` produce `0011`, no `11`. Su ID final muestra como blancos las celdas que ocupaban `#` y B.
- Las trazas de la inversión y de la suma crecen como O(n²): sumar dos números de 16 bits toma unos 600 pasos, y todas las IDs se imprimen.
- El menú solo ofrece las cuatro máquinas del catálogo; cualquier otro YAML se ejecuta con `--machine`. Las cadenas agregadas en el menú se pierden al cerrar el programa, porque no se escriben en el YAML.
- El formato que exige el menú ([§15.6](#156-validaciones-de-entrada)) se declara en el catálogo. Para ver a la suma rechazar una cadena mal formada, esa cadena debe estar en `simulation_strings` y ejecutarse con `--machine`.
- La prueba de Ctrl+C con una señal real se omite en Windows, y el menú no se probó en Windows.
- La rúbrica no define cómo se mide la dificultad de una máquina ([§14](#14-comparación-y-dificultad-de-las-máquinas)).
- Probado con Python 3.14; las versiones 3.10 a 3.13 no se probaron.

## 24. Organización del repositorio y autoría

```text
proyecto3-toc/
├── README.md
├── main.py                        CLI
├── requirements.txt               PyYAML, pytest
├── machines/
│   ├── recognizer_anbn.yaml                MT reconocedora (§10)
│   ├── transformer_binary_increment.yaml   MT alteradora: incremento (§11)
│   ├── transformer_binary_reverse.yaml     MT alteradora: inversión (§12)
│   ├── transformer_binary_addition.yaml    MT alteradora: suma, principal (§13)
│   └── examples/basic_machine.yaml         máquina del Laboratorio 10
├── src/
│   ├── input/                     errors, yaml_loader, machine_parser, machine_validator
│   ├── model/                     transition, turing_machine, tape, configuration, simulation_result
│   ├── simulator/                 step, engine, trace
│   ├── output/                    id_formatter, tape_formatter, result_formatter, machine_formatter
│   ├── cli/                       machine_catalog, interactive_menu, simulation_view (§15)
│   └── utils/notation.py          blanco, tupla de control y reglas de δ
├── tests/                         19 archivos de pruebas y fixtures/statement_example_mt_1.yaml
└── docs/
    └── evidence/                  salida real de las cuatro demostraciones (§20.1)
```

Cada módulo con código incluye docstrings con su responsabilidad y la propiedad formal que implementa, y comentarios `#` donde ocurre cada paso del procedimiento mecanizado ([§3.2](#32-procedimiento-mecanizado)). Este README es el único documento técnico del proyecto:
- El contenido que antes estaba en `docs/architecture.md`, `docs/methodology.md` y `docs/test_cases.md` se integró en este README.
- Los registros de traspaso entre integrantes (`docs/handoff_gate_01_derek.md` y `docs/handoff_gate_02_vernel.md`) también se integraron: la guía para escribir máquinas está en §7.7 y las notas de la interfaz pública en §6.

Los archivos retirados siguen en el historial de Git, por ejemplo `git show 6a27bab:docs/handoff_gate_01_derek.md`.

### 24.1 Autoría y desarrollo

El proyecto se desarrolló en la rama `main`, sin ramas paralelas ni pull requests, en etapas consecutivas. Cada integrante publicó solo durante su etapa y entregó a la siguiente el SHA final, los resultados de las pruebas y las interfaces públicas.

| Integrante | Aportes |
|---|---|
| Vernel Josué Hernández Cáceres | Estructura del proyecto, modelo, cinta dispersa, δ, carga y validación del YAML, paso atómico y motor; pruebas de integración y evidencia de entrega; máquinas de inversión y de suma binaria; menú interactivo y su presentación; estructura actual de este README y revisión final de la documentación del código |
| Derek Friedhelm Coronado Chilin | Traza verificada; formateadores de IDs, de la cinta y de los resultados; CLI con `--machine`; máquina reconocedora aⁿbⁿ e incremento binario, con sus pruebas y su documentación; corrección de portabilidad de la suite y su ejecución en Windows 11; primeras secciones del README sobre la CLI y las demostraciones |

El autor de cada commit se consulta con `git log --format='%h %an %s'`; el historial no se reescribió.

## 25. Referencias bibliográficas

### Enunciado del curso (fuente normativa)

- Universidad del Valle de Guatemala. (2026). *Proyecto No. 3* [Enunciado de proyecto]. CC2019 Teoría de la Computación.

### Material del curso

- Pojoy Corzo, B. A. (2026). *Theory of computation* [Diapositivas de clase]. CC2019 Teoría de la Computación, Universidad del Valle de Guatemala.

### Fundamentos teóricos de máquinas de Turing

- Hopcroft, J. E., Motwani, R., & Ullman, J. D. (2001). *Introduction to automata theory, languages, and computation* (2.ª ed.). Addison-Wesley. https://www.cs.columbia.edu/~toni/Courses/CSTheory2023/Handouts/Hopcroft-Motwani-Ullman-2001.pdf

### Implementación de máquinas de Turing en Python

- Klein, B. (2025, 21 de febrero). *9. Turing machine in Python*. Python Course. https://python-course.eu/applications-python/turing-machine.php

### Computabilidad y fundamentos introductorios

- kenjinote. (2026, 21 de septiembre). *Máquina de Turing y teoría de la computabilidad: El experimento mental de Alan Turing y el problema de la parada*. kenji.blog. https://kenji.blog/es/p/turing-machine-computability/

### Documentación técnica

- PyYAML. (s. f.). *PyYAML documentation*. https://pyyaml.org/wiki/PyYAMLDocumentation

---

El enunciado es la fuente de los requisitos y no se cuenta entre las cinco referencias de investigación. Hopcroft, Motwani y Ullman y el material del curso son el fundamento teórico: definición formal, IDs, almacenamiento en el estado (§8.3.1) y el ejemplo 8.2 en que se basa la reconocedora. Klein es la referencia técnica de la cinta dispersa en Python; kenjinote es material introductorio sobre la computabilidad y el problema de la parada, que justifica `LIMIT_EXCEEDED`; y la documentación de PyYAML respalda la carga segura de los archivos.
