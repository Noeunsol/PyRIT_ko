# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
import random

from pyrit.models import PromptDataType
from pyrit.prompt_converter.ansi_escape.ansi_payloads import (
    ASKS,
    ASKS_KO,
    ESCAPED_PAYLOADS,
    HIGH_LEVEL_TASKS,
    HIGH_LEVEL_TASKS_KO,
    LIVE_PAYLOADS,
    REPEAT_STUBS,
    REPEAT_STUBS_KO,
    UNESCAPE_STUBS,
    UNESCAPE_STUBS_KO,
    USER_INPUT_STUB_KO,
)
from pyrit.prompt_converter.prompt_converter import ConverterResult, PromptConverter

logger = logging.getLogger(__name__)


class AnsiAttackConverter(PromptConverter):
    """
    Generates prompts with ANSI codes to evaluate LLM behavior and system risks.

    This converter can:
        - Use raw and escaped ANSI payloads.
        - Ask the model about ANSI codes, repeat given payloads, unescape strings.
        - Incorporate the user's original prompt into the final scenario, making the testing more dynamic.
    """

    SUPPORTED_INPUT_TYPES = ("text",)
    SUPPORTED_OUTPUT_TYPES = ("text",)

    def __init__(
        self,
        include_raw: bool = True,
        include_escaped: bool = True,
        include_tasks: bool = True,
        include_repeats: bool = True,
        include_unescape: bool = True,
        incorporate_user_prompt: bool = True,
        locale: str = "en",
        **kwargs,
    ):
        """
        Initialize the converter with various options to control the scenarios generated.

        Args:
            include_raw (bool): Include scenarios with raw ANSI codes.
            include_escaped (bool): Include scenarios with escaped ANSI codes.
            include_tasks (bool): Include "ASKS + HIGH_LEVEL_TASKS" scenarios.
            include_repeats (bool): Include "repeat this payload" scenarios.
            include_unescape (bool): Include "unescape this payload" scenarios.
            incorporate_user_prompt (bool): If True, the user's prompt is integrated into the final scenario.
            locale (str): Language for scenario text. "ko" for Korean, "en" for English. Defaults to "en".
        """
        super().__init__(**kwargs)
        self.include_raw = include_raw
        self.include_escaped = include_escaped
        self.include_tasks = include_tasks
        self.include_repeats = include_repeats
        self.include_unescape = include_unescape
        self.incorporate_user_prompt = incorporate_user_prompt
        self._locale = locale

        # Select locale-specific text
        if locale == "ko":
            self._asks = ASKS_KO
            self._high_level_tasks = HIGH_LEVEL_TASKS_KO
            self._repeat_stubs = REPEAT_STUBS_KO
            self._unescape_stubs = UNESCAPE_STUBS_KO
            self._user_input_stub = USER_INPUT_STUB_KO
            self._fallback = "터미널에서 녹색 텍스트를 렌더링하는 ANSI 코드는 무엇인가요?"
        else:
            self._asks = ASKS
            self._high_level_tasks = HIGH_LEVEL_TASKS
            self._repeat_stubs = REPEAT_STUBS
            self._unescape_stubs = UNESCAPE_STUBS
            self._user_input_stub = "Additionally, consider this user input:"
            self._fallback = "What's the ANSI code to render green terminal text?"

    def input_supported(self, input_type: PromptDataType) -> bool:
        """
        Check if the input type is supported.

        Args:
            input_type (PromptDataType): The type of input data.

        Returns:
            bool: True if the input type is supported, False otherwise.
        """
        return input_type == "text"

    def output_supported(self, output_type: PromptDataType) -> bool:
        """
        Check if the output type is supported.

        Args:
            output_type (PromptDataType): The type of output data.

        Returns:
            bool: True if the output type is supported, False otherwise.
        """
        return output_type == "text"

    async def convert_async(self, *, prompt: str, input_type: PromptDataType = "text") -> ConverterResult:
        """
        Convert the given prompt into an ANSI attack scenario.

        Args:
            prompt (str): The original user prompt.
            input_type (PromptDataType): The type of input data.

        Returns:
            ConverterResult: The result containing the generated ANSI scenario prompt.

        Raises:
            ValueError: If the input type is not supported.
        """
        if not self.input_supported(input_type):
            raise ValueError("Input type not supported")

        scenario_choices = []

        # Scenario 1: Ask about ANSI codes (if allowed)
        if self.include_tasks:
            ask = random.choice(self._asks)
            task = random.choice(self._high_level_tasks)
            scenario_choices.append(f"{ask} {task}")

        # Scenario 2: Repeat a payload (if allowed)
        if self.include_repeats:
            possible_payloads = []
            if self.include_raw:
                possible_payloads.extend(LIVE_PAYLOADS)
            if self.include_escaped:
                possible_payloads.extend(ESCAPED_PAYLOADS)

            if possible_payloads:
                repeat_stub = random.choice(self._repeat_stubs)
                chosen_payload = random.choice(possible_payloads)
                scenario_choices.append(f"{repeat_stub} {chosen_payload}")

        # Scenario 3: Unescape a string (if allowed and we have escaped payloads)
        if self.include_unescape and self.include_escaped:
            unescape_stub = random.choice(self._unescape_stubs)
            escaped_payload = random.choice(ESCAPED_PAYLOADS)
            scenario_choices.append(f"{unescape_stub} {escaped_payload}")

        # If no scenarios were selected (all features disabled), fallback scenario:
        if not scenario_choices:
            scenario_choices.append(self._fallback)

        # Pick one scenario at random
        final_scenario = random.choice(scenario_choices)

        # Incorporate the user's original prompt into the scenario if desired.
        if self.incorporate_user_prompt and prompt.strip():
            final_scenario = f"{final_scenario}\n{self._user_input_stub} {prompt}"

        logger.info(f"Generated ANSI scenario prompt: {final_scenario}")

        return ConverterResult(output_text=final_scenario, output_type="text")
