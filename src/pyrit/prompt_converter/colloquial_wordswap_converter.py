# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import random
import re
from typing import Dict, List, Optional

from pyrit.identifiers import ConverterIdentifier
from pyrit.models import PromptDataType
from pyrit.prompt_converter.prompt_converter import ConverterResult, PromptConverter


class ColloquialWordswapConverter(PromptConverter):
    """
    Converts text by replacing words with colloquial equivalents.

    When locale is "en" (default), replaces English words with Singaporean
    colloquial terms. When locale is "ko", replaces Korean words with
    Korean colloquial/dialect equivalents, handling Korean particles (조사)
    that attach to word stems.

    Example (locale="en"):
        Input: "My father is here"
        Output: "My papa is here"

    Example (locale="ko"):
        Input: "아버지가 오셨다"
        Output: "아빠가 오셨다"
    """

    SUPPORTED_INPUT_TYPES = ("text",)
    SUPPORTED_OUTPUT_TYPES = ("text",)

    _DEFAULT_EN_SUBSTITUTIONS = {
        "father": ["papa", "lao bei", "lim pei", "bapa", "appa"],
        "mother": ["mama", "amma", "ibu"],
        "grandfather": ["ah gong", "thatha", "dato"],
        "grandmother": ["ah ma", "patti", "nenek"],
        "girl": ["ah ger", "ponnu"],
        "boy": ["ah boy", "boi", "payyan"],
        "son": ["ah boy", "boi", "payyan"],
        "daughter": ["ah ger", "ponnu"],
        "aunt": ["makcik", "maami"],
        "aunty": ["makcik", "maami"],
        "man": ["ah beng", "shuai ge"],
        "woman": ["ah lian", "xiao mei"],
        "uncle": ["encik", "unker"],
        "sister": ["xjj", "jie jie", "zhezhe", "kaka", "akka", "thangatchi"],
        "brother": ["bro", "boiboi", "di di", "xdd", "anneh", "thambi"],
    }

    _DEFAULT_KO_SUBSTITUTIONS = {
        "아버지": ["아빠", "아부지", "울 아빠", "대디", "세대주"],
        "어머니": ["엄마", "어무니", "마미", "울 엄마", "안주인"],
        "할아버지": ["할부지", "할배", "할아버님", "하르방", "영감탱"],
        "할머니": ["할무니", "할매", "할머님", "할망", "할미"],
        "여자아이": ["공주님", "여자애", "기집애", "가시나"],
        "남자아이": ["왕자님", "남자애", "머스마", "사내자식"],
        "아들": ["우리 아들", "아덜래미", "우리 장남", "막둥이"],
        "딸": ["우리 딸", "딸내미", "공주", "큰애"],
        "이모": ["이모", "고모", "숙모", "큰엄마", "이모님"],
        "아줌마": ["아줌마", "아지매", "아즈망"],
        "남자": ["아재", "오빠", "형씨", "총각", "아저씨", "청년"],
        "여자": ["언니", "이모", "아가씨", "새댁", "아주머니"],
        "삼촌": ["삼촌", "삼춘", "아재", "아저씨", "은사님"],
        "언니": ["언니", "누나", "누님", "울 언니", "누이", "웅니"],
        "오빠": ["오빠", "형", "형님", "울 오빠", "오라버니", "형아"],
    }

    def __init__(
        self,
        *,
        locale: str = "en",
        deterministic: bool = False,
        custom_substitutions: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """
        Initialize the converter with optional deterministic mode and custom substitutions.

        Args:
            locale (str): The locale for colloquial substitutions.
                "en" for Singaporean English colloquial (default).
                "ko" for Korean colloquial/dialect equivalents.
            deterministic (bool): If True, use the first substitution for each wordswap.
                If False, randomly choose a substitution for each wordswap. Defaults to False.
            custom_substitutions (Optional[Dict[str, List[str]]]): A dictionary of custom
                substitutions to override the defaults. Defaults to None.
        """
        if custom_substitutions:
            default_substitutions = custom_substitutions
        elif locale == "ko":
            default_substitutions = self._DEFAULT_KO_SUBSTITUTIONS
        else:
            default_substitutions = self._DEFAULT_EN_SUBSTITUTIONS

        self._colloquial_substitutions = default_substitutions
        self._deterministic = deterministic
        self._locale = locale

    def _build_identifier(self) -> ConverterIdentifier:
        """
        Build identifier with colloquial wordswap parameters.

        Returns:
            ConverterIdentifier: The identifier for this converter.
        """
        return self._create_identifier(
            converter_specific_params={
                "locale": self._locale,
                "deterministic": self._deterministic,
                "substitution_keys": sorted(self._colloquial_substitutions.keys()),
            }
        )

    def _pick_substitution(self, key: str) -> str:
        """Pick a substitution based on deterministic setting."""
        candidates = self._colloquial_substitutions[key]
        if self._deterministic:
            return candidates[0]
        return random.choice(candidates)

    def _convert_english(self, prompt: str) -> str:
        """Convert English text using word-level matching."""
        words = re.findall(r"\w+|\S+", prompt)
        converted_prompt = []

        for word in words:
            lower_word = word.lower()
            if lower_word in self._colloquial_substitutions:
                converted_prompt.append(self._pick_substitution(lower_word))
            else:
                converted_prompt.append(word)

        final_prompt = " ".join(converted_prompt)
        final_prompt = re.sub(r'\s([?.!,\'"])', r"\1", final_prompt)
        return final_prompt.strip()

    def _convert_korean(self, prompt: str) -> str:
        """
        Convert Korean text using stem matching.

        Korean particles (조사) attach directly to words without spaces,
        so we match word stems and preserve the trailing particles.

        Example: "아버지가" → stem "아버지" matched → "아빠" + "가" → "아빠가"
        """
        # Build regex pattern: match longest stems first to avoid partial matches
        # e.g., "할아버지" should match before "아버지"
        stems = sorted(self._colloquial_substitutions.keys(), key=len, reverse=True)
        pattern = re.compile("(" + "|".join(re.escape(s) for s in stems) + ")")

        def replace_match(match: re.Match) -> str:
            return self._pick_substitution(match.group(0))

        return pattern.sub(replace_match, prompt)

    async def convert_async(self, *, prompt: str, input_type: PromptDataType = "text") -> ConverterResult:
        """
        Convert the given prompt by replacing words with colloquial terms.

        Args:
            prompt (str): The input text prompt to be converted.
            input_type (PromptDataType): The type of the input prompt. Defaults to "text".

        Returns:
            ConverterResult: The result containing the converted prompt.

        Raises:
            ValueError: If the input type is not supported.
        """
        if not self.input_supported(input_type):
            raise ValueError("Input type not supported")

        if self._locale == "ko":
            final_prompt = self._convert_korean(prompt)
        else:
            final_prompt = self._convert_english(prompt)

        return ConverterResult(output_text=final_prompt, output_type="text")
