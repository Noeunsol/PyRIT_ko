# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import random
from typing import Optional

from pyrit.common.hangeul_utils import CHOSEONG, JONGSEONG, JUNGSEONG
from pyrit.identifiers import ConverterIdentifier
from pyrit.prompt_converter.text_selection_strategy import WordSelectionStrategy
from pyrit.prompt_converter.word_level_converter import WordLevelConverter


class LeetspeakConverter(WordLevelConverter):
    """
    Converts a string to a leetspeak version.

    When locale is "ko", decomposes Korean syllables (Hangeul) into jamo
    and applies Korean leetspeak substitutions (야민정음 style).

    Example (locale="en"):
        Input: "hello"
        Output: "h3110"

    Example (locale="ko"):
        Input: "사이트"
        Output: "4ㅏ01Eㅡ"
    """

    _DEFAULT_EN_SUBSTITUTIONS = {
        "a": ["4", "@", "/\\", "@", "^", "/-\\"],
        "b": ["8", "6", "13", "|3", "/3", "!3"],
        "c": ["(", "[", "<", "{"],
        "e": ["3"],
        "g": ["9"],
        "i": ["1", "!"],
        "l": ["1", "|"],
        "o": ["0"],
        "s": ["5", "$"],
        "t": ["7"],
        "z": ["2"],
    }

    _DEFAULT_KO_SUBSTITUTIONS = {
        # 자음 (Consonants)
        "ㄱ": ["7", ">"],
        "ㄴ": ["L", "<"],
        "ㄷ": ["["],
        "ㄹ": ["2", "己", "Z"],
        "ㅅ": ["4", "A"],
        "ㅇ": ["0", "O", "o", "@"],
        "ㅌ": ["E"],
        # 모음 (Vowels)
        "ㅑ": ["k"],
        "ㅣ": ["1", "!", "i", "l"],
        "ㅐ": ["H"],
    }

    # 한글 자모 분해 테이블은 hangeul_utils에서 import

    def __init__(
        self,
        *,
        locale: str = "en",
        deterministic: bool = True,
        custom_substitutions: Optional[dict[str, list[str]]] = None,
        word_selection_strategy: Optional[WordSelectionStrategy] = None,
    ):
        """
        Initialize the converter with optional deterministic mode and custom substitutions.

        Args:
            locale (str): The locale for leetspeak substitutions.
                "en" for English leetspeak (default).
                "ko" for Korean leetspeak (야민정음 style).
            deterministic (bool): If True, use the first substitution for each character.
                If False, randomly choose a substitution for each character.
            custom_substitutions (Optional[dict]): A dictionary of custom substitutions to override the defaults.
            word_selection_strategy (Optional[WordSelectionStrategy]): Strategy for selecting which words to convert.
                If None, all words will be converted.
        """
        super().__init__(word_selection_strategy=word_selection_strategy)

        if custom_substitutions:
            substitutions = custom_substitutions
        elif locale == "ko":
            substitutions = self._DEFAULT_KO_SUBSTITUTIONS
        else:
            substitutions = self._DEFAULT_EN_SUBSTITUTIONS

        self._leet_substitutions = substitutions
        self._deterministic = deterministic
        self._has_custom_substitutions = custom_substitutions is not None
        self._locale = locale

    def _build_identifier(self) -> ConverterIdentifier:
        """
        Build the converter identifier with leetspeak parameters.

        Returns:
            ConverterIdentifier: The identifier for this converter.
        """
        import hashlib
        import json

        # Hash custom substitutions if provided
        substitutions_hash = None
        if self._has_custom_substitutions:
            substitutions_str = json.dumps(self._leet_substitutions, sort_keys=True)
            substitutions_hash = hashlib.sha256(substitutions_str.encode("utf-8")).hexdigest()[:16]

        return self._create_identifier(
            converter_specific_params={
                "locale": self._locale,
                "deterministic": self._deterministic,
                "custom_substitutions_hash": substitutions_hash,
            },
        )

    def _pick(self, key: str) -> str:
        """Pick a substitution based on deterministic setting."""
        candidates = self._leet_substitutions[key]
        if self._deterministic:
            return candidates[0]
        return random.choice(candidates)

    async def convert_word_async(self, word: str) -> str:
        """
        Convert a single word into the target format supported by the converter.

        Args:
            word (str): The word to be converted.

        Returns:
            str: The converted word.
        """
        if self._locale == "ko":
            return self._convert_korean_word(word)

        converted_word = []
        for char in word:
            lower_char = char.lower()
            if lower_char in self._leet_substitutions:
                converted_word.append(self._pick(lower_char))
            else:
                converted_word.append(char)
        return "".join(converted_word)

    def _convert_korean_word(self, word: str) -> str:
        """
        Convert a Korean word by decomposing Hangeul into jamo and applying substitutions.

        Jamo that have no substitution are kept as-is (original jamo character).

        Args:
            word (str): The word to convert.

        Returns:
            str: The converted word.
        """
        result = []
        for char in word:
            if "\uAC00" <= char <= "\uD7A3":
                code = ord(char) - 0xAC00
                cho = CHOSEONG[code // (21 * 28)]
                jung = JUNGSEONG[(code % (21 * 28)) // 28]
                jong = JONGSEONG[code % 28]

                jamo = [cho, jung] + ([jong] if jong else [])
                has_sub = any(j in self._leet_substitutions for j in jamo)

                if has_sub:
                    # 치환 대상이 있으면 자모 분리 후 치환
                    for j in jamo:
                        result.append(self._pick(j) if j in self._leet_substitutions else j)
                else:
                    # 치환 대상 없으면 원래 음절 유지
                    result.append(char)
            else:
                # 비한글 문자 (영문, 숫자 등)는 영문 leetspeak도 시도
                lower_char = char.lower()
                if lower_char in self._leet_substitutions:
                    result.append(self._pick(lower_char))
                else:
                    result.append(char)
        return "".join(result)
