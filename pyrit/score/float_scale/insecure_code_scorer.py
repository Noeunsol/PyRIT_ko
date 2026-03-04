# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pathlib import Path
from typing import Optional, Union

from pyrit.common import verify_and_resolve_path
from pyrit.common.path import SCORER_SEED_PROMPT_PATH
from pyrit.exceptions.exception_classes import InvalidJsonException
from pyrit.identifiers import ScorerIdentifier
from pyrit.models import MessagePiece, Score, SeedPrompt
from pyrit.prompt_target import PromptChatTarget
from pyrit.score.float_scale.float_scale_scorer import FloatScaleScorer
from pyrit.score.score_utils import get_localized_file_paths, resolve_scorer_locale
from pyrit.score.scorer_prompt_validator import ScorerPromptValidator


class InsecureCodeScorer(FloatScaleScorer):
    """
    A scorer that uses an LLM to evaluate code snippets for potential security vulnerabilities.
    Configuration is loaded from a YAML file for dynamic prompts and instructions.
    """

    _default_validator: ScorerPromptValidator = ScorerPromptValidator(supported_data_types=["text"])
    _SUPPORTED_LOCALES = ("en", "ko")

    def __init__(
        self,
        *,
        chat_target: PromptChatTarget,
        system_prompt_path: Optional[Union[str, Path]] = None,
        validator: Optional[ScorerPromptValidator] = None,
    ):
        """
        Initialize the Insecure Code Scorer.

        Args:
            chat_target (PromptChatTarget): The target to use for scoring code security.
            system_prompt_path (Optional[Union[str, Path]]): Path to the YAML file containing the system prompt.
                Defaults to the default insecure code scoring prompt if not provided.
            validator (Optional[ScorerPromptValidator]): Custom validator for the scorer. Defaults to None.
        """
        super().__init__(validator=validator or self._default_validator)

        self._prompt_target = chat_target

        if not system_prompt_path:
            system_prompt_path = SCORER_SEED_PROMPT_PATH / "insecure_code" / "system_prompt.yaml"

        self._system_prompt_path: Path = verify_and_resolve_path(system_prompt_path)
        localized_prompt_paths = get_localized_file_paths(
            resolved_path=self._system_prompt_path, supported_locales=self._SUPPORTED_LOCALES
        )

        # Define the harm category
        self._harm_category = "security"

        self._system_prompts_by_locale: dict[str, str] = {}
        for locale, prompt_path in localized_prompt_paths.items():
            scoring_instructions_template = SeedPrompt.from_yaml_file(prompt_path)
            self._system_prompts_by_locale[locale] = scoring_instructions_template.render_template_value(
                harm_categories=self._harm_category
            )

        # Render the system prompt with the harm category
        self._system_prompt = self._system_prompts_by_locale["en"]

    def _build_identifier(self) -> ScorerIdentifier:
        """
        Build the scorer evaluation identifier for this scorer.

        Returns:
            ScorerIdentifier: The identifier for this scorer.
        """
        return self._create_identifier(
            system_prompt_template=self._system_prompt,
            prompt_target=self._prompt_target,
        )

    async def _score_piece_async(self, message_piece: MessagePiece, *, objective: Optional[str] = None) -> list[Score]:
        """
        Scores the given message piece using LLM to detect security vulnerabilities.

        Args:
            message_piece (MessagePiece): The code snippet to be scored.
            objective (Optional[str]): Optional objective description for scoring. Defaults to None.

        Returns:
            list[Score]: A list containing a single Score object.

        Raises:
            InvalidJsonException: If the expected 'score_value' key is missing in the response.
        """
        locale = self._resolve_locale(message_piece=message_piece)
        system_prompt = self._system_prompts_by_locale.get(locale, self._system_prompt)

        # Use _score_value_with_llm to interact with the LLM and retrieve an UnvalidatedScore
        unvalidated_score = await self._score_value_with_llm(
            prompt_target=self._prompt_target,
            system_prompt=system_prompt,
            message_value=message_piece.original_value,
            message_data_type=message_piece.converted_value_data_type,
            scored_prompt_id=message_piece.id,
            category=self._harm_category,
            objective=objective,
            attack_identifier=message_piece.attack_identifier,
        )

        # Modify the UnvalidatedScore parsing to check for 'score_value'
        try:
            # Attempt to use score_value if available
            raw_score_value = float(unvalidated_score.raw_score_value)
        except KeyError:
            raise InvalidJsonException(message="Expected 'score_value' key missing in the JSON response")

        # Convert UnvalidatedScore to Score, applying scaling and metadata
        score = unvalidated_score.to_score(
            score_value=str(self.scale_value_float(raw_score_value, 0, 1)),
            score_type="float_scale",
        )

        return [score]

    def _resolve_locale(self, *, message_piece: MessagePiece) -> str:
        return resolve_scorer_locale(labels=message_piece.labels, supported_locales=self._system_prompts_by_locale)
