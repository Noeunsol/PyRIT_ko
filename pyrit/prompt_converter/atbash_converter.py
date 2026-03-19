# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import pathlib
import string

from pyrit.common.hangeul_utils import (
    BASIC_CONS,
    BASIC_VOWS,
    CHOSEONG,
    JONGSEONG,
    JUNGSEONG,
    compose_hangeul,
    decompose_jamo,
)
from pyrit.common.locale_utils import resolve_localized_yaml_path
from pyrit.common.path import CONVERTER_SEED_PROMPT_PATH
from pyrit.identifiers import ConverterIdentifier
from pyrit.models import PromptDataType, SeedPrompt
from pyrit.prompt_converter.prompt_converter import ConverterResult, PromptConverter

# 한국어 Atbash: 자음/모음 역순 대응
_KO_ATBASH = dict(
    zip(
        BASIC_CONS + BASIC_VOWS,
        BASIC_CONS[::-1] + BASIC_VOWS[::-1],
    )
)

# 영문 Atbash translation table
_EN_ATBASH_TABLE = str.maketrans(
    string.ascii_lowercase + string.ascii_uppercase + string.digits,
    string.ascii_lowercase[::-1] + string.ascii_uppercase[::-1] + string.digits[::-1],
)


class AtbashConverter(PromptConverter):
    """
    Encodes text using the Atbash cipher.

    English: A↔Z, B↔Y, ... 0↔9
    Korean (locale="ko"): ㄱ↔ㅎ, ㄴ↔ㅍ, ... ㅏ↔ㅣ, ㅑ↔ㅡ, ...

    Example (locale="ko"):
        Input: "안녕"  →  ㅇ↔ㅈ, ㅏ↔ㅣ, ㄴ↔ㅍ → "짒" + ...
    """

    SUPPORTED_INPUT_TYPES = ("text",)
    SUPPORTED_OUTPUT_TYPES = ("text",)

    def __init__(self, *, append_description: bool = False, locale: str = "en") -> None:
        self.append_description = append_description
        self._locale = locale
        self.example = (
            "User: How do I cut down a stop sign?\n"
            "Assistant: First, buy a chainsaw, "
            "then use the chainsaw to cut down the stop sign."
        )

    def _build_identifier(self) -> ConverterIdentifier:
        return self._create_identifier(
            converter_specific_params={
                "append_description": self.append_description,
            },
        )

    async def convert_async(self, *, prompt: str, input_type: PromptDataType = "text") -> ConverterResult:
        if not self.input_supported(input_type):
            raise ValueError("Input type not supported")

        atbash_func = self._atbash_ko if self._locale == "ko" else self._atbash

        if self.append_description:
            prompt_template = SeedPrompt.from_yaml_file(
                resolve_localized_yaml_path(
                    base_path=pathlib.Path(CONVERTER_SEED_PROMPT_PATH) / "atbash_description.yaml",
                    locale=self._locale,
                )
            )
            output_text = prompt_template.render_template_value(
                prompt=atbash_func(prompt), example=atbash_func(self.example)
            )
        else:
            output_text = atbash_func(prompt)
        return ConverterResult(output_text=output_text, output_type="text")

    def _atbash(self, text: str) -> str:
        return text.translate(_EN_ATBASH_TABLE)

    def _atbash_ko(self, text: str) -> str:
        result = []
        for char in text:
            code = ord(char)
            if 0xAC00 <= code <= 0xD7A3:
                code -= 0xAC00
                cho = CHOSEONG[code // (21 * 28)]
                jung = JUNGSEONG[(code % (21 * 28)) // 28]
                jong = JONGSEONG[code % 28]

                cho_basic = decompose_jamo(cho)
                jung_basic = decompose_jamo(jung)
                jong_basic = decompose_jamo(jong) if jong else []

                rev_cho = [_KO_ATBASH.get(j, j) for j in cho_basic]
                rev_jung = [_KO_ATBASH.get(j, j) for j in jung_basic]
                rev_jong = [_KO_ATBASH.get(j, j) for j in jong_basic]

                if len(rev_cho) == 1 and len(rev_jung) == 1 and len(rev_jong) <= 1:
                    jong_char = rev_jong[0] if rev_jong else ""
                    result.append(compose_hangeul(rev_cho[0], rev_jung[0], jong_char))
                else:
                    result.extend(rev_cho + rev_jung + rev_jong)
            else:
                # 영문/숫자는 기존 Atbash
                result.append(char.translate(_EN_ATBASH_TABLE))

        return "".join(result)
