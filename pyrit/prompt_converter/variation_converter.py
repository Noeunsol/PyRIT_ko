# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
import logging
import pathlib
import uuid
from textwrap import dedent
from typing import Optional

from pyrit.common.apply_defaults import REQUIRED_VALUE, apply_defaults
from pyrit.common.locale_utils import resolve_localized_yaml_path
from pyrit.common.path import CONVERTER_SEED_PROMPT_PATH
from pyrit.exceptions import (
    InvalidJsonException,
    pyrit_json_retry,
    remove_markdown_json,
)
from pyrit.identifiers import ConverterIdentifier
from pyrit.models import (
    Message,
    MessagePiece,
    PromptDataType,
    SeedPrompt,
)
from pyrit.prompt_converter.prompt_converter import ConverterResult, PromptConverter
from pyrit.prompt_target import PromptChatTarget

logger = logging.getLogger(__name__)


class VariationConverter(PromptConverter):
    """
    Generates variations of the input prompts using the converter target.
    """

    SUPPORTED_INPUT_TYPES = ("text",)
    SUPPORTED_OUTPUT_TYPES = ("text",)

    _USER_PROMPT_TEMPLATES_BY_LOCALE = {
        "en": (
            "Create {number_variations} variation of the seed prompt given by the user between the "
            "begin and end tags"
            "=== begin ==={prompt}=== end ==="
        ),
        "ko": (
            "시작과 끝 태그 사이에 사용자가 제공한 시드 프롬프트를 바탕으로 {number_variations}개의 변형된 "
            "버전을 만드세요"
            "=== 시작 ==={prompt}=== 끝 ==="
        ),
    }

    @apply_defaults
    def __init__(
        self,
        *,
        converter_target: PromptChatTarget = REQUIRED_VALUE,  # type: ignore[assignment]
        prompt_template: Optional[SeedPrompt] = None,
        locale: str = "en",
    ):
        """
        Initialize the converter with the specified target and prompt template.

        Args:
            converter_target (PromptChatTarget): The target to which the prompt will be sent for conversion.
                Can be omitted if a default has been configured via PyRIT initialization.
            prompt_template (SeedPrompt, optional): The template used for generating the system prompt.
                If not provided, a default template will be used.
            locale (str): Locale for the prompt template. Defaults to "en".

        Raises:
            ValueError: If converter_target is not provided and no default has been configured.
        """
        self.converter_target = converter_target
        self._locale = locale

        # set to default strategy if not provided
        prompt_template = (
            prompt_template
            if prompt_template
            else SeedPrompt.from_yaml_file(resolve_localized_yaml_path(base_path=pathlib.Path(CONVERTER_SEED_PROMPT_PATH) / "variation_converter.yaml", locale=locale))
        )

        self.number_variations = 1

        self.system_prompt = str(prompt_template.render_template_value(number_iterations=str(self.number_variations)))

    def _build_identifier(self) -> ConverterIdentifier:
        """
        Build the converter identifier with variation parameters.

        Returns:
            ConverterIdentifier: The identifier for this converter.
        """
        return self._create_identifier(
            converter_target=self.converter_target,
        )

    async def convert_async(self, *, prompt: str, input_type: PromptDataType = "text") -> ConverterResult:
        """
        Convert the given prompt by generating variations of it using the converter target.

        Args:
            prompt (str): The prompt to be converted.
            input_type (PromptDataType): The type of input data.

        Returns:
            ConverterResult: The result containing the generated variations.

        Raises:
            ValueError: If the input type is not supported.
        """
        if not self.input_supported(input_type):
            raise ValueError("Input type not supported")

        conversation_id = str(uuid.uuid4())

        self.converter_target.set_system_prompt(
            system_prompt=self.system_prompt,
            conversation_id=conversation_id,
            attack_identifier=None,
        )

        user_template = self._USER_PROMPT_TEMPLATES_BY_LOCALE.get(
            self._locale, self._USER_PROMPT_TEMPLATES_BY_LOCALE["en"]
        )
        prompt = user_template.format(number_variations=self.number_variations, prompt=prompt)

        request = Message(
            [
                MessagePiece(
                    role="user",
                    original_value=prompt,
                    converted_value=prompt,
                    conversation_id=conversation_id,
                    sequence=1,
                    prompt_target_identifier=self.converter_target.get_identifier(),
                    original_value_data_type=input_type,
                    converted_value_data_type=input_type,
                    converter_identifiers=[self.get_identifier()],
                )
            ]
        )
        response_msg = await self.send_variation_prompt_async(request)

        return ConverterResult(output_text=response_msg, output_type="text")

    @pyrit_json_retry
    async def send_variation_prompt_async(self, request: Message) -> str:
        """
        Send the message to the converter target and retrieve the response.

        Args:
            request (Message): The message to be sent to the converter target.

        Returns:
            str: The response message from the converter target.

        Raises:
            InvalidJsonException: If the response is not valid JSON or does not contain the expected keys.
        """
        response = await self.converter_target.send_prompt_async(message=request)

        response_msg = response[0].get_value()
        response_msg = remove_markdown_json(response_msg)
        try:
            response = json.loads(response_msg)

        except json.JSONDecodeError:
            raise InvalidJsonException(message=f"Invalid JSON response: {response_msg}")

        try:
            return str(response[0])
        except KeyError:
            raise InvalidJsonException(message=f"Invalid JSON response: {response_msg}")
