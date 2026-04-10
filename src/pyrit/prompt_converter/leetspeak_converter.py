# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import random
from typing import Optional

from pyrit.identifiers import ConverterIdentifier
from pyrit.prompt_converter.text_selection_strategy import WordSelectionStrategy
from pyrit.prompt_converter.word_level_converter import WordLevelConverter


class LeetspeakConverter(WordLevelConverter):
    """
    Converts a string to a leetspeak version.

    When locale is "ko", applies direct Korean token substitutions
    (야민정음 style) without decomposing syllables into jamo.

    Example (locale="en"):
        Input: "hello"
        Output: "h3110"

    Example (locale="ko"):
        Input: "귀멍"
        Output: "커댕"
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
        "귀": ["커"],
        "커": ["귀"],
        "멍": ["댕"],
        "명": ["띵"],
        "팔": ["괄"],
        "비": ["네"],
        "면": ["띤", "댼"],
        "대": ["머"],
        "광": ["팡"],
        "위": ["읶"],
        "식": ["싀"],
        "근": ["ㄹ"],
        "펑": ["떵"],
        "파": ["과"],
        "피": ["끠"],
        "괴": ["미"],
        "지": ["거"],
        "거": ["지"],
        "꺼": ["77ㅓ"],
        "공": ["끙"],
        "돼": ["태"],
        "태": ["EH"],
        "의": ["익"],
        "왕": ["앟"],
        "야": ["OF"],
        "개": ["7ㅐ", "7H"],
        "새": ["AH", "Aㅐ"],
        "끼": ["77ㅣ", "77l"],
        "미": ["ㅁl"],
        "니": ["Lㅣ", "Ll"],
        "사": ["ㅅr"],
        "나": ["Lr"],
        "자": ["ㅈr"],
        "유": ["윾"],
        "관": ["판"],
        "빙": ["넹"],
        "다": ["[ㅏ"],
        "고": ["끄"],
    }

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
            deterministic (bool): If True, use the first substitution for each mapping key.
                If False, randomly choose a substitution for each mapping key.
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
        self._sorted_substitution_keys = sorted(self._leet_substitutions.keys(), key=len, reverse=True)

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
        Convert a Korean word by applying direct token substitutions.
        Tokens are matched greedily (longest key first).

        Args:
            word (str): The word to convert.

        Returns:
            str: The converted word.
        """
        result = []
        i = 0
        while i < len(word):
            matched_key = next((k for k in self._sorted_substitution_keys if word.startswith(k, i)), None)
            if matched_key is not None:
                result.append(self._pick(matched_key))
                i += len(matched_key)
                continue

            char = word[i]
            # ko 기본 매핑에 없는 비한글/영문 문자는 기본 영문 leetspeak로 fallback
            if not self._has_custom_substitutions:
                lower_char = char.lower()
                if lower_char in self._DEFAULT_EN_SUBSTITUTIONS:
                    candidates = self._DEFAULT_EN_SUBSTITUTIONS[lower_char]
                    result.append(candidates[0] if self._deterministic else random.choice(candidates))
                else:
                    result.append(char)
            else:
                result.append(char)
            i += 1
        return "".join(result)
