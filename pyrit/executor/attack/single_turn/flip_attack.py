# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import pathlib
import uuid
from typing import Any, Optional

from pyrit.common.apply_defaults import REQUIRED_VALUE, apply_defaults
from pyrit.common.path import EXECUTOR_SEED_PROMPT_PATH
from pyrit.executor.attack.core import AttackConverterConfig, AttackScoringConfig
from pyrit.executor.attack.core.attack_parameters import AttackParameters
from pyrit.executor.attack.single_turn.prompt_sending import PromptSendingAttack
from pyrit.executor.attack.single_turn.single_turn_attack_strategy import (
    SingleTurnAttackContext,
)
from pyrit.models import (
    AttackResult,
    Message,
    SeedPrompt,
)
from pyrit.prompt_converter import FlipConverter
from pyrit.prompt_normalizer import PromptConverterConfiguration, PromptNormalizer
from pyrit.prompt_target import PromptChatTarget

logger = logging.getLogger(__name__)

# FlipAttack generates prepended_conversation internally from its system prompt.
FlipAttackParameters = AttackParameters.excluding("prepended_conversation", "next_message")


class FlipAttack(PromptSendingAttack):
    """
    Implement the FlipAttack method found here:
    https://arxiv.org/html/2410.02832v1.

    Essentially, it adds a system prompt to the beginning of the conversation to flip each word in the prompt.
    """

    _SYSTEM_PROMPT_FILES = {
        "en": "flip_attack.yaml",
        "ko": "flip_attack_ko.yaml",
    }

    @apply_defaults
    def __init__(
        self,
        objective_target: PromptChatTarget = REQUIRED_VALUE,  # type: ignore[assignment]
        attack_converter_config: Optional[AttackConverterConfig] = None,
        attack_scoring_config: Optional[AttackScoringConfig] = None,
        prompt_normalizer: Optional[PromptNormalizer] = None,
        max_attempts_on_failure: int = 0,
    ) -> None:
        """
        Args:
            objective_target (PromptChatTarget): The target system to attack.
            attack_converter_config (AttackConverterConfig, Optional): Configuration for the prompt converters.
            attack_scoring_config (AttackScoringConfig, Optional): Configuration for scoring components.
            prompt_normalizer (PromptNormalizer, Optional): Normalizer for handling prompts.
            max_attempts_on_failure (int, Optional): Maximum number of attempts to retry on failure.
        """
        super().__init__(
            objective_target=objective_target,
            attack_converter_config=attack_converter_config,
            attack_scoring_config=attack_scoring_config,
            prompt_normalizer=prompt_normalizer,
            max_attempts_on_failure=max_attempts_on_failure,
            params_type=FlipAttackParameters,
        )

        flip_converter = PromptConverterConfiguration.from_converters(converters=[FlipConverter()])
        self._request_converters = flip_converter + self._request_converters

        # Backward-compatible default English system prompt attribute.
        self._system_prompt = self._load_system_prompt_for_locale(locale="en")
        self._localized_system_prompts = {"en": self._system_prompt}

    def _resolve_locale(self, *, context: SingleTurnAttackContext[Any]) -> str:
        merged_labels = {**self._memory_labels, **context.memory_labels}
        locale = str(merged_labels.get("locale", "en")).lower()
        if locale not in self._SYSTEM_PROMPT_FILES:
            logger.warning(f"Unsupported locale '{locale}' for FlipAttack. Falling back to 'en'.")
            return "en"
        return locale

    def _load_system_prompt_for_locale(self, *, locale: str) -> Message:
        prompt_file_name = self._SYSTEM_PROMPT_FILES[locale]
        system_prompt_path = pathlib.Path(EXECUTOR_SEED_PROMPT_PATH) / prompt_file_name
        system_prompt = SeedPrompt.from_yaml_file(system_prompt_path).value
        return Message.from_system_prompt(system_prompt=system_prompt)

    def _get_system_prompt_for_locale(self, *, locale: str) -> Message:
        if locale not in self._localized_system_prompts:
            self._localized_system_prompts[locale] = self._load_system_prompt_for_locale(locale=locale)
        return self._localized_system_prompts[locale]

    async def _setup_async(self, *, context: SingleTurnAttackContext[Any]) -> None:
        """
        Set up the FlipAttack by preparing conversation context.

        Args:
            context (SingleTurnAttackContext): The attack context containing attack parameters.
        """
        # Ensure the context has a conversation ID
        context.conversation_id = str(uuid.uuid4())
        locale = self._resolve_locale(context=context)
        context.prepended_conversation = [self._get_system_prompt_for_locale(locale=locale)]

        # Initialize context with prepended conversation (system prompt) and merged labels
        await self._conversation_manager.initialize_context_async(
            context=context,
            target=self._objective_target,
            conversation_id=context.conversation_id,
            memory_labels=self._memory_labels,
        )

    async def _perform_async(self, *, context: SingleTurnAttackContext[Any]) -> AttackResult:
        """
        Perform the FlipAttack.

        Args:
            context (SingleTurnAttackContext): The attack context containing attack parameters.

        Returns:
            AttackResult: The result of the attack.
        """
        initial_prompt = "TASK is '⟪" + context.objective.replace("'", "") + "⟫'"
        context.next_message = Message.from_prompt(prompt=initial_prompt, role="user")

        return await super()._perform_async(context=context)
