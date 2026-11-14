# Proyecto No. 3 — Máquinas de Turing

Simulador de máquinas de Turing de una cinta desarrollado en Python, configurable mediante archivos YAML y orientado a reproducir el procedimiento formal de ejecución y sus descripciones instantáneas.

**Curso:** CC2019 — Teoría de la Computación  
**Universidad:** Universidad del Valle de Guatemala  
**Profesor:** Ing. Bidkar Pojoy

**Integrantes:**
- Vernel Josué Hernández Cáceres — 24584
- Derek Friedhelm Coronado Chilin — 24732

---

## Estado del proyecto

Proyecto en fase de inicialización.

El desarrollo se organizará en 26 commits, distribuidos secuencialmente entre los dos integrantes, utilizando únicamente la rama `main`.

## Índice

1. [Objetivo del proyecto](#1-objetivo-del-proyecto)
2. [Requisitos y alcance](#2-requisitos-y-alcance)
3. [Metodología adoptada](#3-metodología-adoptada)
4. [Máquinas de Turing implementadas](#4-máquinas-de-turing-implementadas)
5. [Arquitectura](#5-arquitectura)
6. [Modelo de datos](#6-modelo-de-datos)
7. [Lectura y validación YAML](#7-lectura-y-validación-yaml)
8. [Motor de simulación](#8-motor-de-simulación)
9. [Descripciones instantáneas](#9-descripciones-instantáneas)
10. [Criterios de aceptación y rechazo](#10-criterios-de-aceptación-y-rechazo)
11. [Decisiones de implementación](#11-decisiones-de-implementación)
12. [Estrategia de validación](#12-estrategia-de-validación)
13. [Pruebas automatizadas](#13-pruebas-automatizadas)
14. [Ejecución](#14-ejecución)
15. [Casos de demostración](#15-casos-de-demostración)
16. [Resultados](#16-resultados)
17. [Discusión](#17-discusión)
18. [Limitaciones y alcance](#18-limitaciones-y-alcance)
19. [Organización del proyecto](#19-organización-del-proyecto)
20. [Referencias bibliográficas](#20-referencias-bibliográficas)

---

## 1. Objetivo del proyecto

*Pendiente de implementación.*

## 2. Requisitos y alcance

*Pendiente de implementación.*

## 3. Metodología adoptada

*Pendiente de implementación.*

## 4. Máquinas de Turing implementadas

*Pendiente de implementación.*

## 5. Arquitectura

*Pendiente de implementación.*

## 6. Modelo de datos

*Pendiente de implementación.*

## 7. Lectura y validación YAML

*Pendiente de implementación.*

## 8. Motor de simulación

*Pendiente de implementación.*

## 9. Descripciones instantáneas

*Pendiente de implementación.*

## 10. Criterios de aceptación y rechazo

*Pendiente de implementación.*

## 11. Decisiones de implementación

*Pendiente de implementación.*

## 12. Estrategia de validación

*Pendiente de implementación.*

## 13. Pruebas automatizadas

*Pendiente de implementación.*

## 14. Ejecución

Requisitos: Python 3.10 o superior.

```bash
python -m pip install -r requirements.txt
python main.py --machine machines/examples/basic_machine.yaml
python main.py --machine machines/examples/basic_machine.yaml --max-steps 500
python main.py --help
```

| Argumento | Obligatorio | Descripción |
|---|---|---|
| `--machine ARCHIVO` | Sí | Archivo YAML con la máquina y su lista `simulation_strings` |
| `--max-steps N` | No | Máximo de transiciones por cadena (entero positivo; por defecto 10000) |

El programa simula en orden cada cadena de `simulation_strings` y escribe en la
salida estándar:

1. La descripción formal de la máquina (Q, Σ, Γ, q0, F, blanco y número de reglas).
2. Por cada cadena: resultado (`ACCEPTED`, `REJECTED` o `LIMIT_EXCEEDED`), motivo,
   pasos, estado, caché y cabezal finales, contenido final de la cinta, ID final,
   vista de la cinta con la posición del cabezal y la tabla completa de
   descripciones instantáneas (ID_0 a ID_n) con la regla aplicada en cada paso.
3. Un resumen con una fila por cadena.

`LIMIT_EXCEEDED` significa que la máquina todavía tenía una regla aplicable al
agotar `--max-steps`; no es un rechazo.

| Código de salida | Significado |
|---|---|
| 0 | Todas las cadenas se simularon |
| 1 | El archivo no se pudo leer o la máquina no es válida (detalle en la salida de errores) |
| 2 | Argumentos incorrectos |

`machines/examples/basic_machine.yaml` es la máquina del Laboratorio 10 que se
usa como referencia de las pruebas.

## 15. Casos de demostración

*Pendiente de implementación.*

## 16. Resultados

*Pendiente de implementación.*

## 17. Discusión

*Pendiente de implementación.*

## 18. Limitaciones y alcance

*Pendiente de implementación.*

## 19. Organización del proyecto

*Pendiente de implementación.*

---

## 20. Referencias bibliográficas

### Enunciado y material del curso

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

Las referencias de Hopcroft, Motwani y Ullman, junto con el material del curso, constituyen el fundamento teórico del proyecto. Klein proporciona una referencia técnica para la implementación del modelo en Python, mientras que kenjinote se utiliza como material introductorio de computabilidad. La documentación de PyYAML respalda el procesamiento de archivos de configuración.

Las decisiones de implementación se desarrollarán y justificarán en las secciones correspondientes a medida que se complete cada fase del proyecto.
