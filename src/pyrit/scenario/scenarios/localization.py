# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
"""Shared locale helpers for all scenarios (airt, foundry, garak).

Centralizes the locale/dataset/YAML path resolution logic so every scenario
resolves ``memory_labels["locale"]`` the same way and picks ``_ko`` variants
consistently.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Sequence

from pyrit.common.locale_utils import get_localized_file_paths, resolve_locale_from_labels

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = {"en", "ko"}


def resolve_locale(*, labels: Optional[dict[str, str]]) -> str:
    """Resolve locale from labels using shared alias/fallback behavior."""
    return resolve_locale_from_labels(
        labels=labels,
        supported_locales=SUPPORTED_LOCALES,
        default_locale=DEFAULT_LOCALE,
    )


def get_localized_yaml_path(
    *,
    base_path: Path,
    labels: Optional[dict[str, str]],
) -> Path:
    """Resolve a YAML asset path to its locale-aware variant with automatic fallback.

    Given an English base path (e.g. ``.../malware.yaml``), this returns the
    Korean sibling (``.../malware_ko.yaml``) when the resolved locale is ``"ko"``
    and the sibling exists. Otherwise falls back to the English base_path.

    Used for scorer question YAMLs, executor system prompts, and any other
    localizable YAML resource inside a Scenario.
    """
    locale = resolve_locale(labels=labels)
    localized = get_localized_file_paths(
        resolved_path=base_path.resolve(),
        supported_locales=SUPPORTED_LOCALES,
    )
    return localized.get(locale, localized[DEFAULT_LOCALE])


def get_localized_dataset_names(
    *,
    dataset_names: Sequence[str],
    labels: Optional[dict[str, str]],
    available_dataset_names: Optional[Iterable[str]] = None,
) -> list[str]:
    """
    Return locale-aware dataset names with fallback.

    For Korean locale, attempts to use `<name>_ko` variants.
    If `available_dataset_names` is provided, only switch to localized names
    that are available there; otherwise keep the original name.
    """
    locale = resolve_locale(labels=labels)
    if locale != "ko":
        return list(dataset_names)

    available = set(available_dataset_names) if available_dataset_names is not None else None
    localized: list[str] = []
    for name in dataset_names:
        if name.endswith("_ko"):
            localized.append(name)
            continue
        ko_name = f"{name}_ko"
        if available is None or ko_name in available:
            localized.append(ko_name)
        else:
            localized.append(name)
    return localized
