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


def test_load_errors_are_input_errors():
    assert issubclass(YamlLoadError, InputError)
    assert issubclass(InputError, ValueError)
