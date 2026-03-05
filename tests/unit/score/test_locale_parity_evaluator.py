# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations

from typing import Optional

import pytest

from pyrit.identifiers import ScorerIdentifier
from pyrit.models import Message, MessagePiece, Score
from pyrit.score.float_scale.float_scale_scorer import FloatScaleScorer
from pyrit.score.score_utils import resolve_scorer_locale
from pyrit.score.scorer_evaluation.locale_parity_evaluator import (
    evaluate_scorer_locale_parity_async,
)
from pyrit.score.scorer_prompt_validator import ScorerPromptValidator
from pyrit.score.true_false.true_false_scorer import TrueFalseScorer


class DeterministicLocaleTrueFalseScorer(TrueFalseScorer):
    _default_validator: ScorerPromptValidator = ScorerPromptValidator(supported_data_types=["text"])

    def __init__(self) -> None:
        super().__init__(validator=self._default_validator)

    def _build_identifier(self) -> ScorerIdentifier:
        return self._create_identifier()

    async def _score_piece_async(self, message_piece: MessagePiece, *, objective: Optional[str] = None) -> list[Score]:
        locale = resolve_scorer_locale(labels=message_piece.labels, supported_locales=("en", "ko"))
        value = "pass" in message_piece.converted_value.lower()
        if locale == "ko" and "flip" in message_piece.converted_value.lower():
            value = not value

        return [
            Score(
                score_value=str(value),
                score_value_description="",
                score_metadata=None,
                score_type="true_false",
                score_category=["parity"],
                score_rationale="deterministic test scorer",
                scorer_class_identifier=self.get_identifier(),
                message_piece_id=message_piece.id,
                objective=objective,
            )
        ]


class DeterministicLocaleFloatScaleScorer(FloatScaleScorer):
    _default_validator: ScorerPromptValidator = ScorerPromptValidator(supported_data_types=["text"])

    def __init__(self) -> None:
        super().__init__(validator=self._default_validator)

    def _build_identifier(self) -> ScorerIdentifier:
        return self._create_identifier()

    async def _score_piece_async(self, message_piece: MessagePiece, *, objective: Optional[str] = None) -> list[Score]:
        locale = resolve_scorer_locale(labels=message_piece.labels, supported_locales=("en", "ko"))
        text = message_piece.converted_value.lower()

        if "close" in text:
            value = 0.8 if locale == "en" else 0.77
            return [self._make_score(message_piece=message_piece, category=["calibration"], value=value, objective=objective)]

        if "far" in text:
            value = 0.8 if locale == "en" else 0.2
            return [self._make_score(message_piece=message_piece, category=["calibration"], value=value, objective=objective)]

        if "extra" in text:
            if locale == "en":
                return [
                    self._make_score(message_piece=message_piece, category=["a"], value=0.7, objective=objective),
                    self._make_score(message_piece=message_piece, category=["b"], value=0.4, objective=objective),
                ]
            return [self._make_score(message_piece=message_piece, category=["a"], value=0.7, objective=objective)]

        return [self._make_score(message_piece=message_piece, category=["calibration"], value=0.5, objective=objective)]

    def _make_score(self, *, message_piece: MessagePiece, category: list[str], value: float, objective: Optional[str]) -> Score:
        return Score(
            score_value=str(value),
            score_value_description="",
            score_metadata=None,
            score_type="float_scale",
            score_category=category,
            score_rationale="deterministic test scorer",
            scorer_class_identifier=self.get_identifier(),
            message_piece_id=message_piece.id,
            objective=objective,
        )


def _make_text_message(text: str) -> Message:
    return Message(message_pieces=[MessagePiece(role="assistant", original_value=text, converted_value=text)])


@pytest.mark.asyncio
async def test_locale_parity_true_false_full_match(patch_central_database):
    scorer = DeterministicLocaleTrueFalseScorer()
    messages = [_make_text_message("pass case"), _make_text_message("neutral case")]

    summary = await evaluate_scorer_locale_parity_async(scorer=scorer, messages=messages)

    assert summary.total_messages == 2
    assert summary.fully_matched_messages == 2
    assert summary.message_match_rate == 1.0
    assert summary.score_match_rate == 1.0


@pytest.mark.asyncio
async def test_locale_parity_true_false_detects_value_mismatch(patch_central_database):
    scorer = DeterministicLocaleTrueFalseScorer()
    messages = [_make_text_message("pass flip case")]

    summary = await evaluate_scorer_locale_parity_async(scorer=scorer, messages=messages)

    assert summary.total_messages == 1
    assert summary.fully_matched_messages == 0
    assert summary.score_match_rate == 0.0
    assert summary.results[0].comparisons[0].mismatch_reason == "value_mismatch"


@pytest.mark.asyncio
async def test_locale_parity_float_uses_tolerance_threshold(patch_central_database):
    scorer = DeterministicLocaleFloatScaleScorer()
    messages = [_make_text_message("close"), _make_text_message("far")]

    summary = await evaluate_scorer_locale_parity_async(
        scorer=scorer,
        messages=messages,
        float_tolerance=0.05,
    )

    assert summary.total_score_comparisons == 2
    assert summary.matched_score_comparisons == 1
    assert summary.score_match_rate == 0.5
    assert summary.max_absolute_difference > 0.5


@pytest.mark.asyncio
async def test_locale_parity_detects_missing_score_pairs(patch_central_database):
    scorer = DeterministicLocaleFloatScaleScorer()
    messages = [_make_text_message("extra")]

    summary = await evaluate_scorer_locale_parity_async(scorer=scorer, messages=messages)

    assert summary.missing_score_pairs == 1
    assert summary.results[0].has_missing_scores is True
    reasons = [comparison.mismatch_reason for comparison in summary.results[0].comparisons]
    assert "missing_score_pair" in reasons
