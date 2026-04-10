# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from __future__ import annotations

from typing import Optional, Union

from pyrit.identifiers import ScorerIdentifier
from pyrit.models import MessagePiece, Score, UnvalidatedScore
from pyrit.prompt_target import PromptChatTarget
from pyrit.score.float_scale.float_scale_scorer import FloatScaleScorer
from pyrit.score.score_utils import resolve_scorer_locale
from pyrit.score.scorer_prompt_validator import ScorerPromptValidator


class SelfAskGeneralFloatScaleScorer(FloatScaleScorer):
    """
    A general-purpose self-ask float-scale scorer that uses a chat target and a configurable
    system prompt and prompt format. The final score is normalized to [0, 1].
    """

    _default_validator: ScorerPromptValidator = ScorerPromptValidator(
        supported_data_types=["text"],
        is_objective_required=True,
    )
    _SUPPORTED_LOCALES = ("en", "ko")

    def __init__(
        self,
        *,
        chat_target: PromptChatTarget,
        system_prompt_format_string: Union[str, dict[str, str]],
        prompt_format_string: Optional[Union[str, dict[str, str]]] = None,
        category: Optional[str] = None,
        min_value: int = 0,
        max_value: int = 100,
        validator: Optional[ScorerPromptValidator] = None,
        score_value_output_key: str = "score_value",
        rationale_output_key: str = "rationale",
        description_output_key: str = "description",
        metadata_output_key: str = "metadata",
        category_output_key: str = "category",
    ) -> None:
        """
        Initialize the SelfAskGeneralFloatScaleScorer.

        The target LLM must return JSON with at least the following keys:
        - score_value: a numeric value in the model's native scale (e.g., 0-100)
        - rationale: a short explanation

        Optionally it can include description, metadata, and category. If category is not provided
        in the response, the provided `category` argument will be applied.

        Args:
            chat_target (PromptChatTarget): The chat target used to score.
            system_prompt_format_string (Union[str, dict[str, str]]): System prompt template with placeholders for
                objective, task (alias of objective), prompt/response (same value), and message_piece.
                You can pass a locale map
                (e.g., {"en": "...", "ko": "..."}) or a single string used for all locales.
            prompt_format_string (Optional[Union[str, dict[str, str]]]): User prompt template with the same
                placeholders. You can pass a locale map or a single string.
            category (Optional[str]): Category for the score.
            min_value (int): Minimum of the model's native scale. Defaults to 0.
            max_value (int): Maximum of the model's native scale. Defaults to 100.
            validator (Optional[ScorerPromptValidator]): Custom validator. If omitted, a default
                validator will be used requiring text input and an objective.
            score_value_output_key (str): JSON key for the score value. Defaults to "score_value".
            rationale_output_key (str): JSON key for the rationale. Defaults to "rationale".
            description_output_key (str): JSON key for the description. Defaults to "description".
            metadata_output_key (str): JSON key for the metadata. Defaults to "metadata".
            category_output_key (str): JSON key for the category. Defaults to "category".

        Raises:
            ValueError: If system_prompt_format_string is not provided or empty.
            ValueError: If min_value is greater than max_value.
        """
        super().__init__(validator=validator or self._default_validator)
        self._prompt_target = chat_target
        if not system_prompt_format_string:
            raise ValueError("system_prompt_format_string must be provided and non-empty.")
        self._system_prompt_formats_by_locale = self._resolve_localized_prompt_templates(
            prompt_templates=system_prompt_format_string,
            argument_name="system_prompt_format_string",
        )
        self._prompt_formats_by_locale = (
            self._resolve_localized_prompt_templates(
                prompt_templates=prompt_format_string,
                argument_name="prompt_format_string",
            )
            if prompt_format_string
            else None
        )

        self._system_prompt_format_string = self._system_prompt_formats_by_locale["en"]
        self._prompt_format_string = self._prompt_formats_by_locale["en"] if self._prompt_formats_by_locale else None

        if min_value > max_value:
            raise ValueError("min_value must be less than or equal to max_value")

        self._score_category = category
        self._min_value = min_value
        self._max_value = max_value
        self._score_value_output_key = score_value_output_key
        self._rationale_output_key = rationale_output_key
        self._description_output_key = description_output_key
        self._metadata_output_key = metadata_output_key
        self._category_output_key = category_output_key

    def _build_identifier(self) -> ScorerIdentifier:
        """
        Build the scorer evaluation identifier for this scorer.

        Returns:
            ScorerIdentifier: The identifier for this scorer.
        """
        return self._create_identifier(
            system_prompt_template=self._system_prompt_format_string,
            user_prompt_template=self._prompt_format_string,
            prompt_target=self._prompt_target,
            scorer_specific_params={
                "min_value": self._min_value,
                "max_value": self._max_value,
            },
        )

    async def _score_piece_async(self, message_piece: MessagePiece, *, objective: Optional[str] = None) -> list[Score]:
        """
        Score a single message piece using the configured prompts and scale to [0, 1].

        Args:
            message_piece (MessagePiece): The piece to score.
            objective (str, optional): Context objective for the scoring.

        Returns:
            list[Score]: A list with a single float-scale score in [0, 1].
        """
        original_prompt = message_piece.converted_value
        locale = resolve_scorer_locale(
            labels=message_piece.labels,
            supported_locales=self._system_prompt_formats_by_locale,
        )
        selected_system_prompt_template = self._system_prompt_formats_by_locale[locale]
        selected_prompt_template = self._prompt_formats_by_locale[locale] if self._prompt_formats_by_locale else None

        # Render system prompt and user prompt.
        # Keep aliases for backward compatibility with existing templates.
        format_args = {
            "objective": objective,
            "task": objective,
            "prompt": original_prompt,
            "response": original_prompt,
            "message_piece": message_piece,
        }
        system_prompt = selected_system_prompt_template.format(**format_args)

        user_prompt = original_prompt
        if selected_prompt_template:
            user_prompt = selected_prompt_template.format(**format_args)

        unvalidated: UnvalidatedScore = await self._score_value_with_llm(
            prompt_target=self._prompt_target,
            system_prompt=system_prompt,
            message_value=user_prompt,
            message_data_type=message_piece.converted_value_data_type,
            scored_prompt_id=message_piece.id,
            category=self._score_category,
            objective=objective,
            attack_identifier=message_piece.attack_identifier,
            score_value_output_key=self._score_value_output_key,
            rationale_output_key=self._rationale_output_key,
            description_output_key=self._description_output_key,
            metadata_output_key=self._metadata_output_key,
            category_output_key=self._category_output_key,
        )

        score = unvalidated.to_score(
            score_value=str(
                self.scale_value_float(float(unvalidated.raw_score_value), self._min_value, self._max_value)
            ),
            score_type="float_scale",
        )
        return [score]

    @classmethod
    def _resolve_localized_prompt_templates(
        cls, *, prompt_templates: Union[str, dict[str, str]], argument_name: str
    ) -> dict[str, str]:
        if isinstance(prompt_templates, str):
            if not prompt_templates:
                raise ValueError(f"{argument_name} must be provided and non-empty.")
            return {locale: prompt_templates for locale in cls._SUPPORTED_LOCALES}

        fallback_prompt = prompt_templates.get("en") or prompt_templates.get("ko")
        if not fallback_prompt:
            raise ValueError(
                f"{argument_name} must include at least one non-empty locale prompt for 'en' or 'ko'."
            )

        localized_prompts: dict[str, str] = {}
        for locale in cls._SUPPORTED_LOCALES:
            localized_prompts[locale] = prompt_templates.get(locale) or fallback_prompt

        return localized_prompts
