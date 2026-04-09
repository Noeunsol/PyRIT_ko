# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pathlib import Path
from typing import Any, Collection, Dict, List, Mapping, Optional, Union

from pyrit.common.locale_utils import (
    DEFAULT_LOCALE as DEFAULT_SCORER_LOCALE,
    LOCALE_ALIAS_MAP,
    SUPPORTED_LOCALES as SUPPORTED_SCORER_LOCALES,
    get_localized_file_paths as _get_localized_file_paths,
    infer_localized_path_pair as _infer_localized_path_pair,
    normalize_locale_value as _normalize_locale_value,
    resolve_locale_from_labels as _resolve_locale_from_labels,
)
from pyrit.common.utils import combine_dict
from pyrit.models import Score

# Key used by FloatScaleThresholdScorer to store the original float value
# in score_metadata when converting float_scale to true_false
ORIGINAL_FLOAT_VALUE_KEY = "original_float_value"


def normalize_locale_value(locale_value: str) -> str:
    """Backward-compatible wrapper for locale normalization."""
    return _normalize_locale_value(locale_value)


def resolve_scorer_locale(
    *,
    labels: Optional[Mapping[str, Any]],
    supported_locales: Collection[str] = SUPPORTED_SCORER_LOCALES,
    default_locale: str = DEFAULT_SCORER_LOCALE,
) -> str:
    """
    Resolve the scorer locale from labels with fallback behavior.

    Resolution order:
    1) labels["locale"]
    2) labels["target_lang"] (alias)
    3) default_locale

    Args:
        labels: Optional labels attached to a message piece.
        supported_locales: Allowed locales.
        default_locale: Fallback locale.

    Returns:
        A locale guaranteed to exist in supported_locales when possible.
    """
    return _resolve_locale_from_labels(
        labels=labels,
        supported_locales=supported_locales,
        default_locale=default_locale,
    )


def infer_localized_path_pair(*, path: Path) -> tuple[Path, Path]:
    """Backward-compatible wrapper for localized path pairing."""
    return _infer_localized_path_pair(path=path)


def get_localized_file_paths(
    *,
    resolved_path: Path,
    supported_locales: Collection[str] = SUPPORTED_SCORER_LOCALES,
) -> dict[str, Path]:
    """Backward-compatible wrapper for localized path discovery."""
    return _get_localized_file_paths(
        resolved_path=resolved_path,
        supported_locales=supported_locales,
    )


def combine_metadata_and_categories(scores: List[Score]) -> tuple[Dict[str, Union[str, int, float]], List[str]]:
    """
    Combine metadata and categories from multiple scores with deduplication.

    Args:
        scores: List of Score objects.

    Returns:
        Tuple of (metadata dict, sorted category list with empty strings filtered).
    """
    metadata: Dict[str, Union[str, int, float]] = {}
    category_set: set[str] = set()

    for s in scores:
        metadata = combine_dict(metadata, getattr(s, "score_metadata", None))
        score_categories = getattr(s, "score_category", None) or []
        category_set.update([c for c in score_categories if c])

    category = sorted(category_set)
    return metadata, category


def format_score_for_rationale(score: Score) -> str:
    """
    Format a single score for inclusion in an aggregated rationale.

    Args:
        score: The Score object to format.

    Returns:
        Formatted string with scorer class, value, and rationale.
    """
    if score.scorer_class_identifier:
        class_type = score.scorer_class_identifier.class_name or "Unknown"
    else:
        class_type = "Unknown"
    return f"   - {class_type} {score.score_value}: {score.score_rationale or ''}"


def normalize_score_to_float(score: Optional[Score]) -> float:
    """
    Normalize any score to a float value between 0.0 and 1.0.

    This function extracts a float value from a score object, handling different
    score types and metadata. It first checks for the original float value in
    score metadata (stored by FloatScaleThresholdScorer) to preserve granularity.
    Falls back to the score value if metadata is not present.

    This is useful for providing numerical feedback to adversarial chats in
    multi-turn attacks, regardless of whether the underlying scorer produces
    float_scale or true_false type scores.

    Args:
        score: The score to normalize, or None.

    Returns:
        Float value between 0.0 and 1.0. Returns 0.0 if score is None.
    """
    if not score:
        return 0.0

    # Check for original float value in metadata (from FloatScaleThresholdScorer)
    # This preserves granularity when using threshold scorers
    if score.score_metadata:
        original_float = score.score_metadata.get(ORIGINAL_FLOAT_VALUE_KEY)
        if original_float is not None:
            return float(original_float)

    # Fall back to the score value itself
    score_value = score.get_value()
    if isinstance(score_value, bool):
        return 1.0 if score_value else 0.0
    elif isinstance(score_value, (int, float)):
        return float(score_value)
    else:
        return 0.0
