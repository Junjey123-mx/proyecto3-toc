"""Validación semántica de una máquina interpretada y de sus cadenas de prueba."""

from src.input.errors import MachineValidationError
from src.model.transition import BLANK, Symbol
from src.model.turing_machine import TuringMachine


def validate_machine(machine: TuringMachine, strings: list[str]) -> None:
    """Comprueba que M = (Q, Σ, Γ, δ, q0, B, F) sea coherente y que cada cadena esté en Σ*.

    Reúne todos los problemas y lanza un único ``MachineValidationError`` cuya
    lista ``errors`` indica el campo YAML de cada uno. No modifica la máquina.
    La caché no se restringe a Γ (D3) y las reglas que salen de un estado final
    se admiten aunque nunca se ejecuten (D6).
    """
    states, sigma, gamma = machine.states, machine.input_alphabet, machine.tape_alphabet
    # Los problemas se acumulan para informar todos en un solo error, cada uno con su campo YAML.
    errors: list[str] = []

    if not states:
        errors.append("q_states.q_list: debe declarar al menos un estado")
    if machine.initial_state not in states:
        errors.append(f"q_states.initial: {machine.initial_state!r} no pertenece a q_list")
    if not machine.final_states:
        errors.append("q_states.final: debe declarar al menos un estado final")
    errors += [f"q_states.final: {state!r} no pertenece a q_list" for state in sorted(machine.final_states - states)]

    if not sigma:
        errors.append("alphabet: debe declarar al menos un símbolo de entrada")
    if BLANK in sigma:
        errors.append("alphabet: el blanco no puede ser un símbolo de entrada")
    if BLANK not in gamma:
        errors.append("tape_alphabet: debe incluir el blanco como entrada vacía ('-')")
    # Σ ⊆ Γ; el blanco se excluye porque su presencia en Σ ya tiene su propio mensaje.
    missing = sorted(symbol for symbol in sigma - gamma if symbol is not BLANK)
    if missing:
        errors.append(f"tape_alphabet: debe incluir los símbolos de alphabet; faltan {missing}")
    # La cinta se escribe sin separadores, así que cada símbolo debe ocupar un solo carácter.
    errors += [
        f"alphabet: {symbol!r} debe ser un único carácter porque las cadenas se leen carácter por carácter"
        for symbol in sorted(s for s in sigma if s is not BLANK and len(s) != 1)
    ]
    errors += [
        f"tape_alphabet: {symbol!r} debe ser un único carácter para que las IDs no sean ambiguas"
        for symbol in sorted(s for s in gamma - sigma if s is not BLANK and len(s) != 1)
    ]

    # Cada regla usa estados de Q y símbolos de Γ; los valores de caché quedan libres (D3).
    for index, rule in enumerate(machine.transitions):
        where = f"delta[{index}]"
        if rule.state not in states:
            errors.append(f"{where}.params.initial_state: {rule.state!r} no pertenece a q_list")
        if rule.read not in gamma:
            errors.append(f"{where}.params.tape_input: {_show(rule.read)} no pertenece a tape_alphabet")
        if rule.next_state not in states:
            errors.append(f"{where}.output.final_state: {rule.next_state!r} no pertenece a q_list")
        if rule.write not in gamma:
            errors.append(f"{where}.output.tape_output: {_show(rule.write)} no pertenece a tape_alphabet")

    for index, word in enumerate(strings):
        outside = sorted(set(word) - sigma)
        if outside:
            errors.append(f"simulation_strings[{index}]: {word!r} usa símbolos fuera de alphabet: {outside}")

    if errors:
        raise MachineValidationError(errors)


def _show(symbol: Symbol) -> str:
    """Símbolo para los mensajes de error: «el blanco» o el símbolo entre comillas."""
    return "el blanco" if symbol is BLANK else repr(symbol)
