"""Catálogo de las cuatro máquinas del menú interactivo: ruta del YAML y textos de presentación.

El catálogo solo selecciona configuraciones. Q, Σ, Γ, q0, F y δ se leen siempre
del YAML (fuente de verdad); aquí solo hay explicaciones para personas: el
objetivo, las fases del procedimiento mecanizado, el papel de cada estado y de
cada marcador, el uso de la caché y el dominio de entrada que el menú acepta.
``tests/test_interactive.py`` comprueba que los estados y los marcadores
descritos sean exactamente los de cada YAML.
"""

import re
from dataclasses import dataclass
from pathlib import Path

MACHINES_DIR = Path(__file__).resolve().parents[2] / "machines"
"""Directorio de los YAML, independiente del directorio de trabajo."""


@dataclass(frozen=True)
class CatalogEntry:
    """Una máquina del menú.

    ``domain`` es una expresión regular que la cadena completa debe cumplir para
    ejecutarse desde el menú, además de pertenecer a Σ*; ``domain_text`` la
    explica al usuario. ``symbols`` describe los símbolos de Γ que no son bits
    ni letras de la entrada (marcadores y separadores).
    """

    file: str
    menu_label: str
    title: str
    recognizer: bool
    objective: str
    function: str
    phases: tuple[str, ...]
    states: dict[str, str]
    symbols: dict[str, str]
    cache: str
    halting: str
    outcome: str
    domain: str
    domain_text: str

    @property
    def path(self) -> Path:
        return MACHINES_DIR / self.file

    def admits(self, word: str) -> bool:
        """``True`` si ``word`` tiene la forma que la máquina espera."""
        return re.fullmatch(self.domain, word) is not None


CATALOG: tuple[CatalogEntry, ...] = (
    CatalogEntry(
        file="recognizer_anbn.yaml",
        menu_label="Reconocedora — a^n b^n",
        title="Reconocedora aⁿbⁿ",
        recognizer=True,
        objective="Decidir si una cadena sobre {a, b} tiene n letras a seguidas de exactamente n letras b, con n ≥ 1.",
        function="L = {aⁿbⁿ | n ≥ 1} (Hopcroft et al., 2001, ejemplo 8.2, con a/b en lugar de 0/1).",
        phases=(
            "Marcar (q0): reemplaza la a sin emparejar más a la izquierda por X y avanza a la derecha.",
            "Buscar (q1): cruza a e Y hacia la derecha; reemplaza la primera b por Y y retrocede.",
            "Regresar (q2): cruza a e Y hacia la izquierda hasta la última X y vuelve a q0 para otra ronda.",
            "Comprobar (q0 → q3): si q0 lee Y ya no quedan a; q3 cruza las Y y, en el primer blanco, pasa a q4.",
        ),
        states={
            "q0": "inicio de ronda: marca la siguiente a o detecta que ya no quedan",
            "q1": "busca hacia la derecha la primera b sin emparejar",
            "q2": "regresa hacia la izquierda hasta la última X",
            "q3": "verificación final: después de las X solo deben quedar Y",
            "q4": "aceptación (estado final, terminal)",
        },
        symbols={"X": "a ya emparejada", "Y": "b ya emparejada"},
        cache="No se usa: vale B en todas las reglas, porque el estado ya distingue la fase de cada barrido.",
        halting=(
            "Se detiene al entrar a q4 o en una configuración sin regla: q0 con b o blanco, "
            "q1 con blanco (sobran a) y q3 con a o b (sobran b o hay una a después de las b)."
        ),
        outcome=(
            "ACCEPTED si la ID llega a q4; REJECTED si la máquina se detiene fuera de F sin regla "
            "aplicable. La cinta final solo muestra las marcas; no es una salida."
        ),
        domain=r"[ab]*",
        domain_text="cualquier cadena sobre {a, b}, incluida la vacía; la máquina decide si pertenece a L",
    ),
    CatalogEntry(
        file="transformer_binary_increment.yaml",
        menu_label="Alteradora — Incremento binario",
        title="Incremento binario",
        recognizer=False,
        objective="Calcular el sucesor de un número binario escrito con el bit más significativo a la izquierda.",
        function=(
            "f(w) = value₂(w) + 1 en binario, con los ceros iniciales conservados; "
            "si todos los bits son 1, el resultado tiene un bit más (11111 → 100000)."
        ),
        phases=(
            "Barrido (q0): cruza los bits hacia la derecha sin modificarlos.",
            "Carga del acarreo (q0 → q1): en el primer blanco carga 1 en la caché y vuelve al último bit.",
            "Propagación (q1 con caché 1): cada 1 se reemplaza por 0 y el acarreo sigue a la izquierda.",
            "Fin (q1 → q2): el primer 0 se reemplaza por 1, la caché se vacía y la máquina se detiene.",
            "Desbordamiento (q1 → q2): si se agotan los bits, escribe 1 en el blanco de la izquierda (posición −1).",
        ),
        states={
            "q0": "barrido hacia la derecha hasta el final del número",
            "q1": "propagación del acarreo de derecha a izquierda",
            "q2": "fin: el acarreo se absorbió (estado final, terminal)",
        },
        symbols={},
        cache=(
            "Registro de acarreo: 1 = acarreo pendiente, B = sin acarreo. Vale 1 exactamente mientras "
            "el estado es q1, así que el estado ya codifica el acarreo."
        ),
        halting="Con una entrada binaria siempre llega a q2, al escribir el 1 que absorbe el acarreo.",
        outcome="ACCEPTED al llegar a q2; la salida es la cinta final, de la primera a la última celda no blanca.",
        domain=r"[01]+",
        domain_text="cadena binaria no vacía; los ceros iniciales se conservan",
    ),
    CatalogEntry(
        file="transformer_binary_reverse.yaml",
        menu_label="Alteradora — Inversión de cadenas",
        title="Inversión de cadenas",
        recognizer=False,
        objective="Invertir una cadena binaria en las mismas posiciones de la cinta.",
        function="f(w₁w₂…wₙ) = wₙ…w₂w₁ para w ∈ {0, 1}*; |f(w)| = |w| y f(ε) = ε.",
        phases=(
            "Elegir (q0): guarda en la caché el bit sin procesar más a la izquierda y deja el hueco *.",
            "Llevar (q1): cruza los bits sin procesar hacia la derecha hasta un bit colocado o el blanco, y retrocede.",
            "Intercambiar (q2): escribe la marca del bit de la caché (o o i) y carga en la caché el bit que había.",
            "Regresar (q3): cruza los bits sin procesar hasta el hueco, escribe ahí la marca del bit de la caché "
            "y vuelve a q0.",
            "Centro (q2 sobre *): en longitud impar, el bit central se coloca en su propia celda.",
            "Rebobinar (q4): cuando q0 lee un bit colocado, o tras el centro, vuelve al inicio de la cadena.",
            "Restaurar (q5): convierte o en 0 e i en 1 de izquierda a derecha; en el blanco final pasa a q6.",
        ),
        states={
            "q0": "elige el siguiente bit de la izquierda o detecta que ya no quedan",
            "q1": "lleva el bit de la caché hacia el extremo derecho sin procesar",
            "q2": "intercambia el bit de la caché con el del extremo derecho",
            "q3": "lleva el bit recogido de vuelta al hueco",
            "q4": "rebobina hasta el inicio de la cadena",
            "q5": "restaura las marcas a bits",
            "q6": "fin (estado final, terminal)",
        },
        symbols={
            "*": "hueco: la celda cuyo bit viaja en la caché",
            "o": "0 ya colocado en su posición final",
            "i": "1 ya colocado en su posición final",
        },
        cache=(
            "Bit en tránsito: 0 o 1 mientras se traslada (q1, q2, q3) y B cuando no viaja ninguno. "
            "Es indispensable: q1, q2 y q3 son los mismos para ambos bits y solo la caché indica cuál se mueve."
        ),
        halting=(
            "Cada ronda coloca dos bits, así que hay ⌈n/2⌉ rondas; luego q4 rebobina, q5 restaura y "
            "la máquina llega a q6. Con la entrada vacía, q0 lee el blanco y pasa directamente a q6."
        ),
        outcome="ACCEPTED al llegar a q6; la salida es la cinta final, en las posiciones 0 … n−1, sin marcas.",
        domain=r"[01]*",
        domain_text="cadena binaria, incluida la vacía",
    ),
    CatalogEntry(
        file="transformer_binary_addition.yaml",
        menu_label="Alteradora — Suma binaria",
        title="Suma binaria",
        recognizer=False,
        objective="Sumar dos números binarios escritos en la cinta como A#B y dejar solo el resultado.",
        function=(
            "f(A#B) = value₂(A) + value₂(B) en binario, con max(|A|, |B|) bits y uno más si hay "
            "desbordamiento; los ceros iniciales se conservan."
        ),
        phases=(
            "Validar (q0 a q3): una pasada comprueba que A y B sean binarios no vacíos y que haya un solo #; "
            "si no, la máquina se detiene sin regla.",
            "Tomar (q4): borra el último bit b de B y guarda en la caché b + acarreo (B = 0, 1 o 2).",
            "Llevar (q5): cruza lo que queda de B hacia la izquierda hasta #.",
            "Sumar (q6): cruza los bits ya calculados; en la siguiente columna de A, o en el blanco a su "
            "izquierda, que vale 0, escribe la marca de (a + caché) mod 2 y deja el acarreo en la caché.",
            "Volver (q7): regresa con el acarreo hasta el blanco que sigue a B y repite desde q4.",
            "Acarreo final (q4 sobre # con caché 1): B se agotó; el acarreo se suma a la siguiente columna.",
            "Restaurar (q8): B se agotó sin acarreo; borra #, convierte o en 0 e i en 1 y pasa a q9.",
        ),
        states={
            "q0": "validación: A debe empezar con un bit",
            "q1": "validación: cruza A hasta #",
            "q2": "validación: B debe empezar con un bit",
            "q3": "validación: cruza B hasta el blanco final",
            "q4": "toma el último bit de B o detecta que B se agotó",
            "q5": "lleva la suma hacia A cruzando lo que queda de B",
            "q6": "cruza el resultado parcial y suma en la columna siguiente",
            "q7": "regresa con el acarreo hasta el final de B",
            "q8": "borra # y restaura las marcas a bits",
            "q9": "fin (estado final, terminal)",
        },
        symbols={
            "#": "separador entre A y B (símbolo de entrada); se borra al terminar",
            "o": "bit 0 del resultado ya calculado",
            "i": "bit 1 del resultado ya calculado",
        },
        cache=(
            "Hacia la izquierda (q5, q6) lleva la suma b + acarreo, de 0 a 2; hacia la derecha (q7, q4) "
            "lleva el acarreo, 0 o 1. El blanco representa 0."
        ),
        halting=(
            "Cada ronda borra un bit de B o absorbe el acarreo en una columna nueva, así que la máquina "
            "siempre llega a q9 cuando la entrada tiene la forma A#B."
        ),
        outcome=(
            "ACCEPTED al llegar a q9; la salida es la cinta final, contigua y sin # ni marcas. "
            "Una cadena de Σ* sin la forma A#B se rechaza durante la validación."
        ),
        domain=r"[01]+#[01]+",
        domain_text="A#B: dos números binarios no vacíos separados por un único # (p. ej. 1011#0110)",
    ),
)
