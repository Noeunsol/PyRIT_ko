# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations

from typing import Iterable, Optional, Sequence

from pyrit.common.locale_utils import resolve_locale_from_labels

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = {"en", "ko"}


def resolve_locale(*, labels: Optional[dict[str, str]]) -> str:
    """Resolve locale from labels using shared alias/fallback behavior."""
    return resolve_locale_from_labels(
        labels=labels,
        supported_locales=SUPPORTED_LOCALES,
        default_locale=DEFAULT_LOCALE,
    )


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
