# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from pathlib import Path
from typing import Any, Optional, cast

import requests

from pyrit.common.apply_defaults import REQUIRED_VALUE, apply_defaults
from pyrit.common.path import DATASETS_PATH, JAILBREAK_TEMPLATES_PATH
from pyrit.executor.attack.core.attack_config import AttackConverterConfig, AttackScoringConfig
from pyrit.executor.attack.core.attack_parameters import AttackParameters
from pyrit.executor.attack.single_turn.prompt_sending import PromptSendingAttack
from pyrit.executor.attack.single_turn.single_turn_attack_strategy import SingleTurnAttackContext
from pyrit.models import AttackResult, Message, SeedPrompt
from pyrit.prompt_normalizer import PromptNormalizer
from pyrit.prompt_target import PromptTarget

# ManyShotJailbreakAttack does not support prepended conversations
# as it constructs its own prompt format with examples.
ManyShotJailbreakParameters = AttackParameters.excluding("prepended_conversation", "next_message")


def fetch_many_shot_jailbreaking_dataset() -> list[dict[str, str]]:
    """
    Fetch many-shot jailbreaking dataset from a specified source.

    Returns:
        list[dict[str, str]]: A list of many-shot jailbreaking examples.
    """
    source = "https://raw.githubusercontent.com/KutalVolkan/many-shot-jailbreaking-dataset/5eac855/examples.json"
    response = requests.get(source)
    response.raise_for_status()
    return cast(list[dict[str, str]], response.json())


def fetch_many_shot_jailbreaking_dataset_ko() -> list[dict[str, str]]:
    """
    Fetch Korean many-shot jailbreaking dataset from local template assets.

    Returns:
        list[dict[str, str]]: A list of Korean many-shot jailbreaking examples.
    """
    source = DATASETS_PATH / "jailbreak" / "many_shot" / "many_shot_examples_ko.json"
    with source.open("r", encoding="utf-8") as file:
        return cast(list[dict[str, str]], json.load(file))


class ManyShotJailbreakAttack(PromptSendingAttack):
    """
    Implement the Many Shot Jailbreak method as discussed in research found here:
    https://www.anthropic.com/research/many-shot-jailbreaking.

    Prepends the seed prompt with a faux dialogue between a human and an AI, using examples from a dataset
    to demonstrate successful jailbreaking attempts. This method leverages the model's ability to learn from
    examples to bypass safety measures.
    """

    DEFAULT_TEMPLATE_PATH: Path = JAILBREAK_TEMPLATES_PATH / "multi_parameter" / "many_shot_template.yaml"
    DEFAULT_TEMPLATE_KO_PATH: Path = JAILBREAK_TEMPLATES_PATH / "multi_parameter" / "many_shot_template_ko.yaml"
    DEFAULT_TEMPLATE_FILES: dict[str, Path] = {
        "en": DEFAULT_TEMPLATE_PATH,
        "ko": DEFAULT_TEMPLATE_KO_PATH,
    }

    @apply_defaults
    def __init__(
        self,
        objective_target: PromptTarget = REQUIRED_VALUE,  # type: ignore[assignment]
        attack_converter_config: Optional[AttackConverterConfig] = None,
        attack_scoring_config: Optional[AttackScoringConfig] = None,
        prompt_normalizer: Optional[PromptNormalizer] = None,
        max_attempts_on_failure: int = 0,
        example_count: int = 100,
        many_shot_examples: Optional[list[dict[str, str]]] = None,
    ) -> None:
        """
        Args:
            objective_target (PromptTarget): The target system to attack.
            attack_converter_config (AttackConverterConfig, Optional): Configuration for the prompt converters.
            attack_scoring_config (AttackScoringConfig, Optional): Configuration for scoring components.
            prompt_normalizer (PromptNormalizer, Optional): Normalizer for handling prompts.
            max_attempts_on_failure (int, Optional): Maximum number of attempts to retry on failure. Defaults to 0.
            example_count (int): The number of examples to include from many_shot_examples or the Many
                Shot Jailbreaking dataset. Defaults to the first 100.
            many_shot_examples (list[dict[str, str]], Optional): The many shot jailbreaking examples to use.
                If not provided, takes the first `example_count` examples from Many Shot Jailbreaking dataset.

        Raises:
            ValueError: If many_shot_examples is empty.
        """
        super().__init__(
            objective_target=objective_target,
            attack_converter_config=attack_converter_config,
            attack_scoring_config=attack_scoring_config,
            prompt_normalizer=prompt_normalizer,
            max_attempts_on_failure=max_attempts_on_failure,
            params_type=ManyShotJailbreakParameters,
        )

        # Default English template for backward compatibility
        self._template = SeedPrompt.from_yaml_file(self.DEFAULT_TEMPLATE_PATH)
        self._localized_templates: dict[str, SeedPrompt] = {"en": self._template}
        self._example_count = example_count
        self._localized_examples: dict[str, list[dict[str, str]]] = {}
        # Fetch the Many Shot Jailbreaking example dataset
        if many_shot_examples is not None:
            self._examples = many_shot_examples[:example_count]
            # Custom examples apply to all locales.
            self._localized_examples = {"en": self._examples, "ko": self._examples}
        else:
            self._examples = fetch_many_shot_jailbreaking_dataset()[:example_count]
            self._localized_examples["en"] = self._examples

        if not self._examples:
            raise ValueError("Many shot examples must be provided.")

    def _resolve_locale(self, *, context: SingleTurnAttackContext[Any]) -> str:
        return super()._resolve_locale(context=context, supported_locales=set(self.DEFAULT_TEMPLATE_FILES))

    def _get_template_for_locale(self, *, locale: str) -> SeedPrompt:
        if locale not in self._localized_templates:
            self._localized_templates[locale] = SeedPrompt.from_yaml_file(self.DEFAULT_TEMPLATE_FILES[locale])
        return self._localized_templates[locale]

    def _get_examples_for_locale(self, *, locale: str) -> list[dict[str, str]]:
        if locale not in self._localized_examples:
            if locale == "ko":
                self._localized_examples[locale] = fetch_many_shot_jailbreaking_dataset_ko()[: self._example_count]
            else:
                self._localized_examples[locale] = fetch_many_shot_jailbreaking_dataset()[: self._example_count]

        examples = self._localized_examples[locale]
        if not examples:
            raise ValueError("Many shot examples must be provided.")
        return examples

    async def _perform_async(self, *, context: SingleTurnAttackContext[Any]) -> AttackResult:
        """
        Perform the ManyShotJailbreakAttack.

        Args:
            context (SingleTurnAttackContext): The attack context containing attack parameters.

        Returns:
            AttackResult: The result of the attack.
        """
        locale = self._resolve_locale(context=context)
        template = self._get_template_for_locale(locale=locale)
        examples = self._get_examples_for_locale(locale=locale)
        many_shot_prompt = template.render_template_value(prompt=context.objective, examples=examples)
        context.next_message = Message.from_prompt(prompt=many_shot_prompt, role="user")

        return await super()._perform_async(context=context)
