# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import dataclasses
from pathlib import Path
from typing import Any, Collection, Mapping, Optional

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
    paths = get_localized_file_paths(resolved_path=base_path.resolve())
    return paths.get(locale, base_path.resolve())


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


# ---------------------------------------------------------------------------
# Locale-aware system prompt helpers
# ---------------------------------------------------------------------------

_LOCALE_SYSTEM_PROMPTS: dict[str, str] = {
    "ko": "항상 한국어로 응답하세요.",
}


def get_locale_system_prompt(locale: str) -> Optional[str]:
    """Return a system-prompt string that instructs the LLM to respond in the
    given locale's language.

    Returns ``None`` for English or unsupported locales (no extra instruction needed).
    """
    normalized = normalize_locale_value(locale)
    return _LOCALE_SYSTEM_PROMPTS.get(normalized)


# ---------------------------------------------------------------------------
# Notebook locale helper
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class NotebookLocale:
    """Lightweight locale context for notebooks.

    Set locale once at the top of a notebook, then reference throughout::

        L = NotebookLocale("ko")
        objective = L.pick(en="Tell me ...", ko="알려줘 ...")
        memory_labels = L.labels(harm_category="illegal")
        ConsoleAttackResultPrinter(locale=L.locale)
    """

    locale: str

    def __post_init__(self) -> None:
        self.locale = normalize_locale_value(self.locale) or DEFAULT_LOCALE

    # -- content selection ---------------------------------------------------

    def pick(self, *, en: str, ko: str) -> str:
        """Select a content string based on the active locale."""
        return {"en": en, "ko": ko}.get(self.locale, en)

    # -- memory labels -------------------------------------------------------

    def labels(self, **extra: str) -> dict[str, str]:
        """Build memory_labels dict with locale included."""
        return {"locale": self.locale, **extra}

    # -- prepended conversation ----------------------------------------------

    @property
    def prepend(self) -> list:
        """Pre-built locale system prompt as a prepended conversation list."""
        prompt = get_locale_system_prompt(self.locale)
        if prompt:
            from pyrit.models import Message

            return [Message.from_system_prompt(prompt)]
        return []

    # -- file name / path resolution -----------------------------------------

    def yaml(self, base_name: str) -> str:
        """Resolve a YAML filename to its localized variant.

        ``L.yaml("dan_1.yaml")`` returns ``"dan_1_ko.yaml"`` when locale is
        ``"ko"`` and ``"dan_1.yaml"`` when locale is ``"en"``.
        """
        if self.locale == DEFAULT_LOCALE:
            return base_name
        dot = base_name.rfind(".")
        if dot < 0:
            return f"{base_name}_{self.locale}"
        return f"{base_name[:dot]}_{self.locale}{base_name[dot:]}"

    def yaml_path(self, base_path: Path) -> Path:
        """Resolve a full Path to its localized variant."""
        return resolve_localized_yaml_path(base_path=base_path, locale=self.locale)
