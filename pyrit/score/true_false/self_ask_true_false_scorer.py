# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import enum
from pathlib import Path
from typing import Any, Iterator, Optional, Union

import yaml

from pyrit.common import verify_and_resolve_path
from pyrit.common.path import SCORER_SEED_PROMPT_PATH
from pyrit.identifiers import ScorerIdentifier
from pyrit.models import MessagePiece, Score, SeedPrompt
from pyrit.prompt_target import PromptChatTarget
from pyrit.score.score_utils import get_localized_file_paths, resolve_scorer_locale
from pyrit.score.scorer_prompt_validator import ScorerPromptValidator
from pyrit.score.true_false.true_false_score_aggregator import (
    TrueFalseAggregatorFunc,
    TrueFalseScoreAggregator,
)
from pyrit.score.true_false.true_false_scorer import TrueFalseScorer

TRUE_FALSE_QUESTIONS_PATH = Path(SCORER_SEED_PROMPT_PATH, "true_false_question").resolve()


class TrueFalseQuestionPaths(enum.Enum):
    """Paths to true/false question YAML files."""

    CURRENT_EVENTS = Path(TRUE_FALSE_QUESTIONS_PATH, "current_events.yaml").resolve()
    GROUNDED = Path(TRUE_FALSE_QUESTIONS_PATH, "grounded.yaml").resolve()
    PROMPT_INJECTION = Path(TRUE_FALSE_QUESTIONS_PATH, "prompt_injection.yaml").resolve()
    QUESTION_ANSWERING = Path(TRUE_FALSE_QUESTIONS_PATH, "question_answering.yaml").resolve()
    GANDALF = Path(TRUE_FALSE_QUESTIONS_PATH, "gandalf.yaml").resolve()
    YES_NO = Path(TRUE_FALSE_QUESTIONS_PATH, "yes_no_answer.yaml").resolve()
    TASK_ACHIEVED = Path(TRUE_FALSE_QUESTIONS_PATH, "task_achieved.yaml").resolve()


class TrueFalseQuestion:
    """
    A class that represents a true/false question.

    This is sent to an LLM and can be used as an alternative to a yaml file from TrueFalseQuestionPaths.
    """

    _DEFAULT_FALSE_DESCRIPTION_BY_LOCALE = {
        "en": "Anything that does not fulfill or is not related to the true description.",
        "ko": "참(true) 설명에 충족하지 않거나 관련이 없는 모든 것.",
    }

    def __init__(
        self,
        *,
        true_description: str,
        false_description: str = "",
        category: str = "",
        metadata: str = "",
        locale: str = "en",
    ):
        """
        Initialize a TrueFalseQuestion instance.

        Args:
            true_description (str): Description of what constitutes a "true" response.
            false_description (str): Description of what constitutes a "false" response.
                Defaults to a generic description if not provided.
            category (str): The category of the question. Defaults to an empty string.
            metadata (str): Additional metadata for context. Defaults to an empty string.
            locale (str): Locale for default false_description. Defaults to "en".
        """
        self.true_description = true_description

        self.false_description = (
            false_description
            or self._DEFAULT_FALSE_DESCRIPTION_BY_LOCALE.get(locale, self._DEFAULT_FALSE_DESCRIPTION_BY_LOCALE["en"])
        )

        self.category = category
        self.metadata = metadata

        self._keys = ["category", "true_description", "false_description"]

    def __getitem__(self, key: str) -> Any:
        """Return the value of the specified key."""
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set the value of the specified key."""
        setattr(self, key, value)

    def __iter__(self) -> Iterator[str]:
        """Return an iterator over the keys."""
        # Define which keys should be included when iterating
        return iter(self._keys)


class SelfAskTrueFalseScorer(TrueFalseScorer):
    """
    A class that represents a self-ask true/false for scoring.

    Given written descriptions of "true" and "false" (passed as a file or a TrueFalseQuestion), it returns the value
    that matches either description most closely.

    If no descriptions are provided, it defaults to the TASK_ACHIEVED scorer.
    """

    _default_validator: ScorerPromptValidator = ScorerPromptValidator(
        supported_data_types=["text", "image_path"],
    )
    _SUPPORTED_LOCALES = ("en", "ko")
    _SYSTEM_PROMPT_FILES = {
        "en": "true_false_system_prompt.yaml",
        "ko": "true_false_system_prompt_ko.yaml",
    }
    _QUESTION_REQUIRED_KEYS = ("category", "true_description", "false_description")
    _SCORING_LABELS_BY_LOCALE = {
        "en": {"objective": "objective", "response": "response"},
        "ko": {"objective": "목표", "response": "응답"},
    }

    def __init__(
        self,
        *,
        chat_target: PromptChatTarget,
        true_false_question_path: Optional[Union[str, Path]] = None,
        true_false_question: Optional[TrueFalseQuestion] = None,
        true_false_system_prompt_path: Optional[Union[str, Path]] = None,
        validator: Optional[ScorerPromptValidator] = None,
        score_aggregator: TrueFalseAggregatorFunc = TrueFalseScoreAggregator.OR,
    ) -> None:
        """
        Initialize the SelfAskTrueFalseScorer.

        Args:
            chat_target (PromptChatTarget): The chat target to interact with.
            true_false_question_path (Optional[Union[str, Path]]): The path to the true/false question file.
            true_false_question (Optional[TrueFalseQuestion]): The true/false question object.
            true_false_system_prompt_path (Optional[Union[str, Path]]): The path to the system prompt file.
            validator (Optional[ScorerPromptValidator]): Custom validator. Defaults to None.
            score_aggregator (TrueFalseAggregatorFunc): The aggregator function to use.
                Defaults to TrueFalseScoreAggregator.OR.

        Raises:
            ValueError: If both true_false_question_path and true_false_question are provided.
            ValueError: If required keys are missing in true_false_question.
        """
        super().__init__(validator=validator or self._default_validator, score_aggregator=score_aggregator)

        self._prompt_target = chat_target

        if true_false_question_path and true_false_question:
            raise ValueError("Only one of true_false_question_path or true_false_question should be provided.")
        if not true_false_question_path and not true_false_question:
            true_false_question_path = TrueFalseQuestionPaths.TASK_ACHIEVED.value

        templates_by_locale: dict[str, SeedPrompt] = {}
        if true_false_system_prompt_path:
            resolved = verify_and_resolve_path(true_false_system_prompt_path)
            localized_paths = get_localized_file_paths(
                resolved_path=resolved, supported_locales=self._SUPPORTED_LOCALES
            )
            for locale, prompt_path in localized_paths.items():
                templates_by_locale[locale] = SeedPrompt.from_yaml_file(prompt_path)
        else:
            for locale, file_name in self._SYSTEM_PROMPT_FILES.items():
                prompt_path = verify_and_resolve_path(TRUE_FALSE_QUESTIONS_PATH / file_name)
                templates_by_locale[locale] = SeedPrompt.from_yaml_file(prompt_path)

        questions_by_locale = self._resolve_questions_by_locale(
            true_false_question_path=true_false_question_path,
            true_false_question=true_false_question,
        )

        self._score_categories_by_locale = {
            locale: question["category"] for locale, question in questions_by_locale.items()
        }
        self._score_category = self._score_categories_by_locale["en"]

        self._system_prompts_by_locale = {}
        for locale, prompt_template in templates_by_locale.items():
            question = questions_by_locale[locale]
            metadata = question.get("metadata", "")
            self._system_prompts_by_locale[locale] = prompt_template.render_template_value(
                true_description=question["true_description"],
                false_description=question["false_description"],
                metadata=metadata,
            )
        self._system_prompt = self._system_prompts_by_locale["en"]

    def _resolve_locale(self, *, message_piece: MessagePiece) -> str:
        return resolve_scorer_locale(labels=message_piece.labels, supported_locales=self._system_prompts_by_locale)

    def _build_identifier(self) -> ScorerIdentifier:
        """
        Build the scorer evaluation identifier for this scorer.

        Returns:
            ScorerIdentifier: The identifier for this scorer.
        """
        return self._create_identifier(
            system_prompt_template=self._system_prompt,
            user_prompt_template="objective: {objective}\nresponse: {response}",
            prompt_target=self._prompt_target,
            score_aggregator=self._score_aggregator.__name__,
        )

    async def _score_piece_async(self, message_piece: MessagePiece, *, objective: Optional[str] = None) -> list[Score]:
        """
        Scores the given message piece using "self-ask" for the chat target.

        Args:
            message_piece (MessagePiece): The message piece containing the text or image to be scored.
            objective (Optional[str]): The objective to evaluate against (the original attacker model's objective).
                Defaults to None.

        Returns:
            list[Score]: A list containing a single Score object.
                The category is configured from the TrueFalseQuestionPath.
                The score_value is True or False based on which description fits best.
                Metadata can be configured to provide additional information.
        """
        # Build scoring prompt - for non-text content, extra context about objective is sent as a prepended text piece
        locale = self._resolve_locale(message_piece=message_piece)
        labels = self._SCORING_LABELS_BY_LOCALE.get(locale, self._SCORING_LABELS_BY_LOCALE["en"])
        obj_label = labels["objective"]
        resp_label = labels["response"]

        is_non_text = message_piece.converted_value_data_type != "text"
        if is_non_text:
            prepended_text = f"{obj_label}: {objective}\n{resp_label}:"
            scoring_value = message_piece.converted_value
            scoring_data_type = message_piece.converted_value_data_type
        else:
            prepended_text = None
            scoring_value = f"{obj_label}: {objective}\n{resp_label}: {message_piece.converted_value}"
            scoring_data_type = "text"
        system_prompt = self._system_prompts_by_locale[locale]
        category = self._score_categories_by_locale.get(locale, self._score_category)

        unvalidated_score = await self._score_value_with_llm(
            prompt_target=self._prompt_target,
            system_prompt=system_prompt,
            message_value=scoring_value,
            message_data_type=scoring_data_type,
            scored_prompt_id=message_piece.id,
            prepended_text_message_piece=prepended_text,
            category=category,
            objective=objective,
            attack_identifier=message_piece.attack_identifier,
        )

        score = unvalidated_score.to_score(score_value=unvalidated_score.raw_score_value, score_type="true_false")
        return [score]

    @classmethod
    def _validate_true_false_question(cls, *, question: dict[str, Any]) -> None:
        for key in cls._QUESTION_REQUIRED_KEYS:
            if key not in question:
                raise ValueError(f"{key} must be provided in true_false_question.")

    def _resolve_questions_by_locale(
        self,
        *,
        true_false_question_path: Optional[Union[str, Path]],
        true_false_question: Optional[TrueFalseQuestion],
    ) -> dict[str, dict[str, Any]]:
        if true_false_question:
            question_dict = {key: true_false_question[key] for key in true_false_question}
            self._validate_true_false_question(question=question_dict)
            return {locale: question_dict for locale in self._SUPPORTED_LOCALES}

        if not true_false_question_path:
            raise ValueError("Either true_false_question_path or true_false_question must be provided.")

        resolved_question_path = verify_and_resolve_path(true_false_question_path)
        localized_question_paths = get_localized_file_paths(
            resolved_path=resolved_question_path, supported_locales=self._SUPPORTED_LOCALES
        )

        questions_by_locale: dict[str, dict[str, Any]] = {}
        for locale, path in localized_question_paths.items():
            question = yaml.safe_load(path.read_text(encoding="utf-8"))
            self._validate_true_false_question(question=question)
            questions_by_locale[locale] = question

        return questions_by_locale
