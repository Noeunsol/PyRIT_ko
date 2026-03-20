# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
from typing import Optional

from pyrit.identifiers import ConverterIdentifier
from pyrit.models import PromptDataType
from pyrit.prompt_converter.prompt_converter import ConverterResult, PromptConverter

logger = logging.getLogger(__name__)

_MESSAGES = {
    "en": {
        "prompt_header": "The next {input_type} prompt to be sent:",
        "select_with_converter": (
            "Select an option:\n"
            "  (1) Proceed with sending the prompt as is.\n"
            "  (2) Manually modify the prompt.\n"
            "  (3) Run the prompt through a converter before sending it.\n"
            "Enter your choice (1/2/3): "
        ),
        "select_without_converter": (
            "Select an option:\n"
            "  (1) Proceed with sending the prompt as is.\n"
            "  (2) Manually modify the prompt.\n"
            "Enter your choice (1/2): "
        ),
        "enter_new_prompt": "Enter new prompt to send: ",
        "available_converters": "Available converters: {converters}",
        "select_converter_index": "Enter the converter index (0 to {max_index}): ",
        "invalid_input": "Invalid input. Please try again.",
        "invalid_index": "Invalid index. Please enter a number between 0 and {max_index}.",
        "no_converters": "No converters were passed into the HumanInTheLoopConverter.",
    },
    "ko": {
        "prompt_header": "다음 {input_type} 프롬프트가 전송됩니다:",
        "select_with_converter": (
            "옵션을 선택하세요:\n"
            "  (1) 프롬프트를 그대로 전송.\n"
            "  (2) 프롬프트를 직접 수정.\n"
            "  (3) 변환기를 적용한 후 전송.\n"
            "원하는 번호를 입력하세요 (1/2/3): "
        ),
        "select_without_converter": (
            "옵션을 선택하세요:\n"
            "  (1) 프롬프트를 그대로 전송.\n"
            "  (2) 프롬프트를 직접 수정.\n"
            "원하는 번호를 입력하세요 (1/2): "
        ),
        "enter_new_prompt": "전송할 새 프롬프트를 입력하세요: ",
        "available_converters": "사용 가능한 변환기: {converters}",
        "select_converter_index": "적용할 변환기의 인덱스를 입력하세요 (0 ~ {max_index}): ",
        "invalid_input": "잘못된 입력입니다. 다시 시도하세요.",
        "invalid_index": "잘못된 인덱스입니다. 0에서 {max_index} 사이의 숫자를 입력하세요.",
        "no_converters": "HumanInTheLoopConverter에 변환기가 전달되지 않았습니다.",
    },
}


class HumanInTheLoopConverter(PromptConverter):
    """
    Allows review of each prompt sent to a target before sending it.

    Users can choose to send the prompt as is, modify the prompt,
    or run the prompt through one of the passed-in converters before sending it.
    """

    SUPPORTED_INPUT_TYPES = ("text",)
    SUPPORTED_OUTPUT_TYPES = ("text",)

    def __init__(
        self,
        converters: Optional[list[PromptConverter]] = None,
        locale: str = "en",
        **kwargs,
    ):
        """
        Initialize the converter with a list of possible converters to run input through.

        Args:
            converters (List[PromptConverter], Optional): List of possible converters to run input through.
            locale (str): Language for UI messages. "ko" for Korean, "en" for English. Defaults to "ko".
        """
        super().__init__(**kwargs)
        self._converters = converters or []
        self._msg = _MESSAGES.get(locale, _MESSAGES["en"])

    def _build_identifier(self) -> ConverterIdentifier:
        """
        Build identifier with sub-converters.

        Returns:
            ConverterIdentifier: The identifier for this converter.
        """
        return self._create_identifier(sub_converters=self._converters)

    async def convert_async(self, *, prompt: str, input_type: PromptDataType = "text") -> ConverterResult:
        """
        Convert the given prompt by allowing user interaction before sending it to a target.

        User is given three options to choose from:
            (1) Proceed with sending the prompt as is.
            (2) Manually modify the prompt.
            (3) Run the prompt through a converter before sending it.

        Args:
            prompt (str): The prompt to be converted.
            input_type (PromptDataType): The type of input data.

        Returns:
            ConverterResult: The result containing the modified prompt.

        Raises:
            ValueError: If no converters are provided and the user chooses to run a converter.
        """
        header = self._msg["prompt_header"].format(input_type=input_type)
        if self._converters:
            valid_choices = ["1", "2", "3"]
            menu = self._msg["select_with_converter"]
        else:
            valid_choices = ["1", "2"]
            menu = self._msg["select_without_converter"]

        user_input = ""
        while user_input not in valid_choices:
            user_input = input(f"\n{header}\n[{prompt}]\n\n{menu}").strip()
            if user_input not in valid_choices:
                print(self._msg["invalid_input"])

        if user_input == "1":
            return ConverterResult(output_text=prompt, output_type=input_type)
        elif user_input == "2":
            new_input = input(self._msg["enter_new_prompt"])
            return await self.convert_async(prompt=new_input, input_type=input_type)
        elif user_input == "3":
            if not self._converters:
                raise ValueError(self._msg["no_converters"])

            converters_str = ", ".join(
                f"[{i}] {c.__class__.__name__}" for i, c in enumerate(self._converters)
            )
            max_index = len(self._converters) - 1
            converter_index = -1
            while not 0 <= converter_index <= max_index:
                try:
                    converter_index = int(
                        input(
                            f"\n{self._msg['available_converters'].format(converters=converters_str)}\n"
                            f"{self._msg['select_converter_index'].format(max_index=max_index)}"
                        ).strip()
                    )
                    if not 0 <= converter_index <= max_index:
                        converter_index = -1
                except ValueError:
                    pass

            converter = self._converters[converter_index]
            new_result = await converter.convert_async(prompt=prompt, input_type=input_type)
            return await self.convert_async(prompt=new_result.output_text, input_type=new_result.output_type)

        return ConverterResult(output_text=prompt, output_type=input_type)
