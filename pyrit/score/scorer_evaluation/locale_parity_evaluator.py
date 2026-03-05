# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import mean
from typing import Dict, Optional, Sequence, Tuple

from pyrit.models import Message, Score
from pyrit.score.score_utils import normalize_score_to_float
from pyrit.score.scorer import Scorer


@dataclass
class LocaleScoreComparison:
    """
    Comparison result for one aligned score pair between locales.
    """

    score_type: str
    score_category: list[str]
    en_score_value: Optional[str]
    ko_score_value: Optional[str]
    en_normalized_value: Optional[float]
    ko_normalized_value: Optional[float]
    absolute_difference: Optional[float]
    is_match: bool
    mismatch_reason: Optional[str] = None


@dataclass
class LocaleMessageParityResult:
    """
    Parity result for one message across English and Korean locale runs.
    """

    message_index: int
    objective: Optional[str]
    comparison_count: int
    matched_count: int
    has_missing_scores: bool
    is_full_match: bool
    comparisons: list[LocaleScoreComparison]


@dataclass
class LocaleParitySummary:
    """
    Aggregate parity summary for a scorer across multiple messages.
    """

    total_messages: int
    fully_matched_messages: int
    message_match_rate: float
    total_score_comparisons: int
    matched_score_comparisons: int
    score_match_rate: float
    average_absolute_difference: float
    max_absolute_difference: float
    missing_score_pairs: int
    results: list[LocaleMessageParityResult]


async def evaluate_scorer_locale_parity_async(
    *,
    scorer: Scorer,
    messages: Sequence[Message],
    objectives: Optional[Sequence[Optional[str]]] = None,
    english_locale: str = "en",
    korean_locale: str = "ko",
    float_tolerance: float = 0.05,
    persist_scores: bool = False,
) -> LocaleParitySummary:
    """
    Evaluate score parity between English and Korean locale branches for the same input messages.

    Args:
        scorer: The scorer instance to evaluate.
        messages: Messages to score in both locales.
        objectives: Optional objective list aligned by index with messages.
        english_locale: Locale value for English branch.
        korean_locale: Locale value for Korean branch.
        float_tolerance: Allowed absolute difference for float_scale parity.
        persist_scores: If True, use scorer.score_async() and persist scores to memory.
            If False (default), use internal scoring path without persisting scores.

    Returns:
        LocaleParitySummary: Aggregate parity metrics and per-message details.

    Raises:
        ValueError: If objectives are provided with a different length than messages.
    """
    if objectives is not None and len(objectives) != len(messages):
        raise ValueError("objectives must have the same length as messages.")

    results: list[LocaleMessageParityResult] = []
    absolute_differences: list[float] = []
    total_score_comparisons = 0
    matched_score_comparisons = 0
    missing_score_pairs = 0

    for index, message in enumerate(messages):
        objective = objectives[index] if objectives else None

        english_scores = await _score_message_for_locale_async(
            scorer=scorer,
            message=message,
            locale=english_locale,
            objective=objective,
            persist_scores=persist_scores,
        )
        korean_scores = await _score_message_for_locale_async(
            scorer=scorer,
            message=message,
            locale=korean_locale,
            objective=objective,
            persist_scores=persist_scores,
        )

        comparisons = _compare_score_lists(
            english_scores=english_scores,
            korean_scores=korean_scores,
            float_tolerance=float_tolerance,
        )

        comparison_count = len(comparisons)
        matched_count = sum(1 for c in comparisons if c.is_match)
        has_missing_scores = any(c.mismatch_reason == "missing_score_pair" for c in comparisons)
        is_full_match = comparison_count > 0 and matched_count == comparison_count and not has_missing_scores

        for comparison in comparisons:
            total_score_comparisons += 1
            if comparison.is_match:
                matched_score_comparisons += 1
            if comparison.mismatch_reason == "missing_score_pair":
                missing_score_pairs += 1
            if comparison.absolute_difference is not None:
                absolute_differences.append(comparison.absolute_difference)

        results.append(
            LocaleMessageParityResult(
                message_index=index,
                objective=objective,
                comparison_count=comparison_count,
                matched_count=matched_count,
                has_missing_scores=has_missing_scores,
                is_full_match=is_full_match,
                comparisons=comparisons,
            )
        )

    total_messages = len(results)
    fully_matched_messages = sum(1 for r in results if r.is_full_match)

    message_match_rate = (fully_matched_messages / total_messages) if total_messages else 0.0
    score_match_rate = (matched_score_comparisons / total_score_comparisons) if total_score_comparisons else 0.0
    average_absolute_difference = mean(absolute_differences) if absolute_differences else 0.0
    max_absolute_difference = max(absolute_differences) if absolute_differences else 0.0

    return LocaleParitySummary(
        total_messages=total_messages,
        fully_matched_messages=fully_matched_messages,
        message_match_rate=message_match_rate,
        total_score_comparisons=total_score_comparisons,
        matched_score_comparisons=matched_score_comparisons,
        score_match_rate=score_match_rate,
        average_absolute_difference=average_absolute_difference,
        max_absolute_difference=max_absolute_difference,
        missing_score_pairs=missing_score_pairs,
        results=results,
    )


async def _score_message_for_locale_async(
    *,
    scorer: Scorer,
    message: Message,
    locale: str,
    objective: Optional[str],
    persist_scores: bool,
) -> list[Score]:
    localized_message = message.duplicate_message()
    for piece in localized_message.message_pieces:
        labels = dict(piece.labels or {})
        labels["locale"] = locale
        labels["target_lang"] = locale
        piece.labels = labels

    if persist_scores:
        return await scorer.score_async(localized_message, objective=objective)

    # Internal scoring path for parity diagnostics without writing to memory.
    scorer._validator.validate(localized_message, objective=objective)  # noqa: SLF001
    scores = await scorer._score_async(localized_message, objective=objective)  # noqa: SLF001
    scorer.validate_return_scores(scores=scores)
    return scores


def _compare_score_lists(
    *,
    english_scores: list[Score],
    korean_scores: list[Score],
    float_tolerance: float,
) -> list[LocaleScoreComparison]:
    grouped_en = _group_scores_for_alignment(scores=english_scores)
    grouped_ko = _group_scores_for_alignment(scores=korean_scores)
    all_keys = sorted(set(grouped_en) | set(grouped_ko))

    comparisons: list[LocaleScoreComparison] = []
    for key in all_keys:
        en_group = grouped_en.get(key, [])
        ko_group = grouped_ko.get(key, [])
        max_group_len = max(len(en_group), len(ko_group))

        for index in range(max_group_len):
            en_score = en_group[index] if index < len(en_group) else None
            ko_score = ko_group[index] if index < len(ko_group) else None
            comparisons.append(
                _compare_score_pair(
                    english_score=en_score,
                    korean_score=ko_score,
                    float_tolerance=float_tolerance,
                )
            )

    return comparisons


def _group_scores_for_alignment(scores: list[Score]) -> Dict[Tuple[str, Tuple[str, ...]], list[Score]]:
    grouped: Dict[Tuple[str, Tuple[str, ...]], list[Score]] = defaultdict(list)
    for score in scores:
        key = (score.score_type, tuple(sorted(score.score_category or [])))
        grouped[key].append(score)

    for key in grouped:
        grouped[key].sort(
            key=lambda s: (
                s.score_value,
                s.score_value_description or "",
                s.score_rationale or "",
            )
        )

    return grouped


def _compare_score_pair(
    *,
    english_score: Optional[Score],
    korean_score: Optional[Score],
    float_tolerance: float,
) -> LocaleScoreComparison:
    if english_score is None or korean_score is None:
        score = english_score or korean_score
        return LocaleScoreComparison(
            score_type=score.score_type if score else "unknown",
            score_category=score.score_category or [] if score else [],
            en_score_value=english_score.score_value if english_score else None,
            ko_score_value=korean_score.score_value if korean_score else None,
            en_normalized_value=normalize_score_to_float(english_score) if english_score else None,
            ko_normalized_value=normalize_score_to_float(korean_score) if korean_score else None,
            absolute_difference=None,
            is_match=False,
            mismatch_reason="missing_score_pair",
        )

    en_normalized = normalize_score_to_float(english_score)
    ko_normalized = normalize_score_to_float(korean_score)
    absolute_difference = abs(en_normalized - ko_normalized)

    if english_score.score_type == "true_false" and korean_score.score_type == "true_false":
        is_match = english_score.get_value() == korean_score.get_value()
    else:
        is_match = absolute_difference <= float_tolerance

    return LocaleScoreComparison(
        score_type=english_score.score_type,
        score_category=english_score.score_category or [],
        en_score_value=english_score.score_value,
        ko_score_value=korean_score.score_value,
        en_normalized_value=en_normalized,
        ko_normalized_value=ko_normalized,
        absolute_difference=absolute_difference,
        is_match=is_match,
        mismatch_reason=None if is_match else "value_mismatch",
    )
