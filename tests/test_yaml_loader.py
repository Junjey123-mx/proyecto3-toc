"""Lectura segura de YAML: documentos válidos y fallos de archivo, codificación y sintaxis."""

import os

import pytest

from src.input.errors import InputError, YamlLoadError
from src.input.yaml_loader import load_yaml


def write(tmp_path, text, name="machine.yaml"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_mapping_preserving_quoted_states_and_null_blank(tmp_path):
    path = write(tmp_path, "---\nq_states:\n  initial: '0'\ntape_alphabet:\n- X\n-\n")
    assert load_yaml(path) == {"q_states": {"initial": "0"}, "tape_alphabet": ["X", None]}
    assert load_yaml(str(path)) == load_yaml(path)


def test_utf8_byte_order_mark_is_ignored(tmp_path):
    path = tmp_path / "bom.yaml"
    path.write_bytes("﻿alphabet:\n- a\n".encode("utf-8"))
    assert load_yaml(path) == {"alphabet": ["a"]}


def test_missing_file(tmp_path):
    with pytest.raises(YamlLoadError, match="no se puede leer"):
        load_yaml(tmp_path / "missing.yaml")


def test_directory_is_not_a_yaml_file(tmp_path):
    with pytest.raises(YamlLoadError, match="no se puede leer"):
        load_yaml(tmp_path)


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root ignora permisos")
def test_unreadable_file(tmp_path):
    path = write(tmp_path, "alphabet: [a]\n")
    path.chmod(0)
    try:
        with pytest.raises(YamlLoadError, match="no se puede leer"):
            load_yaml(path)
    finally:
        path.chmod(0o600)


def test_non_utf8_file(tmp_path):
    path = tmp_path / "latin1.yaml"
    path.write_bytes("alphabet: [ñ]\n".encode("latin-1"))
    with pytest.raises(YamlLoadError, match="UTF-8"):
        load_yaml(path)


def test_badly_indented_yaml(tmp_path):
    path = write(tmp_path, "q_states:\n  q_list:\n  - '0'\n    initial: '0'\n")
    with pytest.raises(YamlLoadError, match="YAML inválido"):
        load_yaml(path)


@pytest.mark.parametrize("text", ["", "# solo comentarios\n", "---\n"])
def test_empty_document(tmp_path, text):
    with pytest.raises(YamlLoadError, match="no contiene un documento"):
        load_yaml(write(tmp_path, text))


def test_multiple_documents_are_rejected(tmp_path):
    with pytest.raises(YamlLoadError, match="YAML inválido"):
        load_yaml(write(tmp_path, "alphabet: [a]\n---\nalphabet: [b]\n"))


@pytest.mark.parametrize("text", ["- a\n- b\n", "texto\n", "5\n"])
def test_root_must_be_a_mapping(tmp_path, text):
    with pytest.raises(YamlLoadError, match="raíz"):
        load_yaml(write(tmp_path, text))


def test_python_tags_are_never_executed(tmp_path):
    marker = tmp_path / "executed"
    path = write(tmp_path, f'payload: !!python/object/apply:os.system ["touch {marker}"]\n')
    with pytest.raises(YamlLoadError, match="YAML inválido"):
        load_yaml(path)
    assert not marker.exists()


def test_repeated_key_inside_a_rule_is_rejected(tmp_path):
    text = "delta:\n- params:\n    tape_input: a\n    tape_input:\n"
    with pytest.raises(YamlLoadError, match="clave repetida 'tape_input'"):
        load_yaml(write(tmp_path, text))


def test_repeated_root_key_is_rejected(tmp_path):
    text = "simulation_strings:\n- ab\nsimulation_strings: []\n"
    with pytest.raises(YamlLoadError, match="clave repetida 'simulation_strings'"):
        load_yaml(write(tmp_path, text))


def test_same_key_in_different_mappings_is_allowed(tmp_path):
    text = "delta:\n- params: {tape_input: a}\n- params: {tape_input: b}\n"
    assert load_yaml(write(tmp_path, text)) == {"delta": [{"params": {"tape_input": "a"}}, {"params": {"tape_input": "b"}}]}


def test_merge_keys_are_not_mistaken_for_repeated_keys(tmp_path):
    text = "base: &b {x: 1, y: 1}\nother:\n  <<: *b\n  x: 2\n"
    assert load_yaml(write(tmp_path, text))["other"] == {"x": 2, "y": 1}


@pytest.mark.parametrize("scalar", ["2026-13-01", "0000-00-00", '!!int "abc"'])
def test_impossible_scalars_are_load_errors_not_bare_value_errors(tmp_path, scalar):
    with pytest.raises(YamlLoadError, match="YAML inválido"):
        load_yaml(write(tmp_path, f"simulation_strings:\n- {scalar}\n"))


def test_load_errors_are_input_errors():
    assert issubclass(YamlLoadError, InputError)
    assert issubclass(InputError, ValueError)
