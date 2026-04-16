# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Parity checks between interactive CLI (main.py) and Streamlit config.

These tests ensure the user-facing custom attack surface stays aligned between:
- `main.py` (terminal interactive runner)
- `streamlit/config.py` (web UI runner)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module spec: {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


REPO_ROOT = Path(__file__).resolve().parents[3]
MAIN_MODULE = _load_module_from_path("pyrit_main_module", REPO_ROOT / "main.py")
STREAMLIT_CONFIG_MODULE = _load_module_from_path(
    "pyrit_streamlit_config_module",
    REPO_ROOT / "streamlit" / "config.py",
)


def test_attack_keys_and_turn_types_are_aligned():
    main_attacks = [(k, turn_type) for (k, _, _, turn_type) in MAIN_MODULE.ATTACKS]
    web_attacks = [(k, turn_type) for (k, _, _, turn_type) in STREAMLIT_CONFIG_MODULE.ATTACKS]
    assert main_attacks == web_attacks


def test_scorer_keys_are_aligned():
    main_scorers = [k for (k, _, _) in MAIN_MODULE.SCORERS]
    web_scorers = [k for (k, _, _) in STREAMLIT_CONFIG_MODULE.SCORERS]
    assert main_scorers == web_scorers


def test_recommended_scorers_and_azure_scorers_are_aligned():
    assert MAIN_MODULE._RECOMMENDED_SCORERS == STREAMLIT_CONFIG_MODULE.RECOMMENDED_SCORERS
    assert MAIN_MODULE._AZURE_SCORERS == STREAMLIT_CONFIG_MODULE.AZURE_SCORERS


def test_converter_keys_and_categories_are_aligned():
    main_converters = [(name, category) for (name, _, _, category) in MAIN_MODULE.CONVERTERS]
    web_converters = [(name, category) for (name, _, _, category) in STREAMLIT_CONFIG_MODULE.CONVERTERS]
    assert main_converters == web_converters


def test_converter_param_schemas_are_aligned():
    main_extra = {k: [p[0] for p in v] for k, v in MAIN_MODULE._CONVERTER_EXTRA_PARAMS.items()}
    web_extra = {k: [p[0] for p in v] for k, v in STREAMLIT_CONFIG_MODULE.CONVERTER_EXTRA_PARAMS.items()}
    assert main_extra == web_extra

    main_toggle = {k: [p[0] for p in v] for k, v in MAIN_MODULE._CONVERTER_TOGGLE_PARAMS.items()}
    web_toggle = {k: [p[0] for p in v] for k, v in STREAMLIT_CONFIG_MODULE.CONVERTER_TOGGLE_PARAMS.items()}
    assert main_toggle == web_toggle

    main_choices = {
        key: (schema[0], [opt[0] for opt in schema[3]])
        for key, schema in MAIN_MODULE._CONVERTER_CHOICES.items()
    }
    web_choices = {
        key: (schema[0], [opt[0] for opt in schema[3]])
        for key, schema in STREAMLIT_CONFIG_MODULE.CONVERTER_CHOICES.items()
    }
    assert main_choices == web_choices


def test_converter_role_sets_and_category_keys_are_aligned():
    assert MAIN_MODULE._LOCALE_CONVERTERS == STREAMLIT_CONFIG_MODULE.LOCALE_CONVERTERS
    assert MAIN_MODULE._LLM_CONVERTERS == STREAMLIT_CONFIG_MODULE.LLM_CONVERTERS
    assert set(MAIN_MODULE._CONVERTER_CAT_LABELS.keys()) == set(STREAMLIT_CONFIG_MODULE.CONVERTER_CAT_LABELS.keys())


def test_role_play_and_builtin_attack_sets_are_aligned():
    assert MAIN_MODULE._ROLE_PLAYS == STREAMLIT_CONFIG_MODULE.ROLE_PLAYS

    main_builtin = {"flip", "context_compliance", "many_shot", "role_play", "skeleton_key"}
    assert main_builtin == STREAMLIT_CONFIG_MODULE.HAS_BUILTIN_CONVERTER
