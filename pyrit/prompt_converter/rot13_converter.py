# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import codecs
from typing import Optional

from pyrit.common.hangeul_utils import (
    BASIC_CONS,
    BASIC_VOWS,
    CHOSEONG,
    JONGSEONG,
    JUNGSEONG,
    compose_hangeul,
    decompose_jamo,
)
from pyrit.prompt_converter.text_selection_strategy import WordSelectionStrategy
from pyrit.prompt_converter.word_level_converter import WordLevelConverter

# 한국어 ROT: 자음 7칸, 모음 5칸 회전 (각 절반)
_KO_ROT = dict(
    zip(
        BASIC_CONS + BASIC_VOWS,
        BASIC_CONS[7:] + BASIC_CONS[:7] + BASIC_VOWS[5:] + BASIC_VOWS[:5],
    )
)


class ROT13Converter(WordLevelConverter):
    """
    Encodes prompts using the ROT13 cipher.

    When locale="ko", decomposes Hangeul syllables into basic jamo,
    rotates consonants by 7 and vowels by 5 (half of 14 and 10),
    then recomposes into Hangeul syllables.

    Example (locale="ko"):
        Input: "안녕"
        ㅇㅏㄴ → ㅊㅛㅌ → "촛"
        ㄴㅕㅇ → ㅌㅠㅊ → "튜ㅊ" (종성 ㅊ)
    """

    def __init__(
        self,
        *,
        locale: str = "en",
        word_selection_strategy: Optional[WordSelectionStrategy] = None,
    ) -> None:
        super().__init__(word_selection_strategy=word_selection_strategy)
        self._locale = locale

    async def convert_word_async(self, word: str) -> str:
        if self._locale == "ko":
            return self._rot_ko(word)
        return codecs.encode(word, "rot13")

    def _rot_ko(self, text: str) -> str:
        result = []
        i = 0
        while i < len(text):
            code = ord(text[i])
            if 0xAC00 <= code <= 0xD7A3:
                # 한글 음절 분해
                code -= 0xAC00
                cho_idx = code // (21 * 28)
                jung_idx = (code % (21 * 28)) // 28
                jong_idx = code % 28

                cho = CHOSEONG[cho_idx]
                jung = JUNGSEONG[jung_idx]
                jong = JONGSEONG[jong_idx]

                # 기본 자모로 분해 → 회전 → 재조합
                cho_basic = decompose_jamo(cho)
                jung_basic = decompose_jamo(jung)
                jong_basic = decompose_jamo(jong) if jong else []

                rotated_cho = [_KO_ROT.get(j, j) for j in cho_basic]
                rotated_jung = [_KO_ROT.get(j, j) for j in jung_basic]
                rotated_jong = [_KO_ROT.get(j, j) for j in jong_basic]

                # 재조합: 기본 자모 1개씩이면 음절로, 아니면 그대로
                if len(rotated_cho) == 1 and len(rotated_jung) == 1 and len(rotated_jong) <= 1:
                    jong_char = rotated_jong[0] if rotated_jong else ""
                    result.append(compose_hangeul(rotated_cho[0], rotated_jung[0], jong_char))
                else:
                    result.extend(rotated_cho + rotated_jung + rotated_jong)
            else:
                # 영문/숫자/기호는 기존 ROT13
                result.append(codecs.encode(text[i], "rot13"))
            i += 1
        return "".join(result)
