# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
from pathlib import Path
from typing import Any, Collection, Mapping, Optional

logger = logging.getLogger(__name__)

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES: tuple[str, ...] = ("en", "ko")
LOCALE_ALIAS_MAP = {"kr": "ko"}


def normalize_locale_value(locale_value: str) -> str:
    """
    Normalize a locale-like string to a primary locale subtag.

    Examples:
    - "ko-KR" -> "ko"
    - "en_US" -> "en"
    - "kr" -> "ko" (alias)
    """
    normalized = locale_value.strip().lower().replace("_", "-")
    if not normalized:
        return ""

    primary_subtag = normalized.split("-", maxsplit=1)[0]
    return LOCALE_ALIAS_MAP.get(primary_subtag, primary_subtag)


def resolve_locale_from_labels(
    *,
    labels: Optional[Mapping[str, Any]],
    supported_locales: Collection[str] = SUPPORTED_LOCALES,
    default_locale: str = DEFAULT_LOCALE,
) -> str:
    """
    Resolve locale from labels with fallback behavior.

    Resolution order:
    1) labels["locale"]
    2) labels["target_lang"] (alias)
    3) default_locale
    """
    supported = tuple(dict.fromkeys(supported_locales))
    if not supported:
        return default_locale

    fallback_locale = default_locale if default_locale in supported else supported[0]
    label_values = labels or {}
    raw_locale = str(label_values.get("locale") or label_values.get("target_lang") or fallback_locale)
    locale = normalize_locale_value(raw_locale) or fallback_locale
    return locale if locale in supported else fallback_locale


def infer_localized_path_pair(*, path: Path) -> tuple[Path, Path]:
    """
    Infer paired English/Korean asset paths from a path.

    Convention:
    - English file: `name.yaml`
    - Korean file: `name_ko.yaml`
    """
    if path.stem.endswith("_ko"):
        return path.with_name(f"{path.stem[:-3]}{path.suffix}"), path
    return path, path.with_name(f"{path.stem}_ko{path.suffix}")


def resolve_localized_yaml_path(*, base_path: Path, locale: str = DEFAULT_LOCALE) -> Path:
    """
    Resolve a YAML path to its localized variant.

    If a localized variant (e.g., ``name_ko.yaml``) exists, returns that path;
    otherwise falls back to the original path.
    """
    resolved = base_path.resolve()
    paths = get_localized_file_paths(resolved_path=resolved)
    result = paths.get(locale, resolved)

    if locale != DEFAULT_LOCALE and result == resolved:
        logger.warning(
            "Localized YAML for locale '%s' not found: %s — falling back to default '%s'",
            locale,
            base_path.name,
            DEFAULT_LOCALE,
        )

    return result


def get_localized_file_paths(
    *,
    resolved_path: Path,
    supported_locales: Collection[str] = SUPPORTED_LOCALES,
) -> dict[str, Path]:
    """
    Build locale-to-path mapping using sibling `_ko` file inference.

    If localized sibling files do not exist, the resolved_path is used as fallback.
    """
    supported = tuple(dict.fromkeys(supported_locales))
    localized_paths = {locale: resolved_path for locale in supported}
    english_candidate, korean_candidate = infer_localized_path_pair(path=resolved_path)

    if "en" in localized_paths and english_candidate.exists():
        localized_paths["en"] = english_candidate.resolve()
    if "ko" in localized_paths and korean_candidate.exists():
        localized_paths["ko"] = korean_candidate.resolve()

    return localized_paths
