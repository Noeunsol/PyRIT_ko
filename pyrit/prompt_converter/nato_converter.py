# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.


from pyrit.models import PromptDataType
from pyrit.prompt_converter.prompt_converter import ConverterResult, PromptConverter


class NatoConverter(PromptConverter):
    """
    Converts text into NATO phonetic alphabet representation.

    This converter transforms standard text into NATO phonetic alphabet format,
    where each letter is replaced with its corresponding NATO phonetic code word
    (e.g., "A" becomes "Alfa", "B" becomes "Bravo"). Only alphabetic characters
    are converted; non-alphabetic characters are ignored.

    When locale is set to "ko", Korean text (Hangul) is decomposed into jamo
    (초성, 중성, 종성) and converted using the Korean phonetic alphabet
    (한국어 통신 부호). English letters and digits are also converted using
    Korean code words. Mixed Korean/English text is supported.

    Reference:
        - NATO: https://en.wikipedia.org/wiki/NATO_phonetic_alphabet
        - Korean: 한국어 통신 부호 (Korean Phonetic Alphabet)

    Example (locale="en"):
        Input: "Hello"
        Output: "Hotel Echo Lima Lima Oscar"

    Example (locale="ko"):
        Input: "안녕"
        Output: "잉어 아버지 나폴리 나폴리 연못 잉어"
    """

    SUPPORTED_INPUT_TYPES = ("text",)
    SUPPORTED_OUTPUT_TYPES = ("text",)

    _NATO_MAP = {
        "A": "Alfa",
        "B": "Bravo",
        "C": "Charlie",
        "D": "Delta",
        "E": "Echo",
        "F": "Foxtrot",
        "G": "Golf",
        "H": "Hotel",
        "I": "India",
        "J": "Juliett",
        "K": "Kilo",
        "L": "Lima",
        "M": "Mike",
        "N": "November",
        "O": "Oscar",
        "P": "Papa",
        "Q": "Quebec",
        "R": "Romeo",
        "S": "Sierra",
        "T": "Tango",
        "U": "Uniform",
        "V": "Victor",
        "W": "Whiskey",
        "X": "Xray",
        "Y": "Yankee",
        "Z": "Zulu",
    }

    # 한국어 통신 부호 - 자음 (초성/종성)
    _KO_CONSONANT_MAP = {
        "ㄱ": "기러기",
        "ㄴ": "나폴리",
        "ㄷ": "도라지",
        "ㄹ": "로마",
        "ㅁ": "미나리",
        "ㅂ": "바가지",
        "ㅅ": "서울",
        "ㅇ": "잉어",
        "ㅈ": "지게",
        "ㅊ": "치마",
        "ㅋ": "키다리",
        "ㅌ": "통신",
        "ㅍ": "파고다",
        "ㅎ": "한강",
    }

    # 한국어 통신 부호 - 모음 (중성)
    _KO_VOWEL_MAP = {
        "ㅏ": "아버지",
        "ㅑ": "야자수",
        "ㅓ": "어머니",
        "ㅕ": "연못",
        "ㅗ": "오징어",
        "ㅛ": "요지경",
        "ㅜ": "우편",
        "ㅠ": "유달산",
        "ㅡ": "은방울",
        "ㅣ": "이순신",
        "ㅐ": "앵무새",
        "ㅔ": "엑스레이",
    }

    # 한국어 통신 부호 - 숫자
    _KO_DIGIT_MAP = {
        "0": "공",
        "1": "하나",
        "2": "둘",
        "3": "삼",
        "4": "넷",
        "5": "오",
        "6": "여섯",
        "7": "칠",
        "8": "팔",
        "9": "아홉",
    }

    # 한글 자모 분해 테이블
    _CHOSEONG = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
    _JUNGSEONG = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
    _JONGSEONG = [
        "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ",
        "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ",
        "ㅋ", "ㅌ", "ㅍ", "ㅎ",
    ]

    # 겹자음 분해 매핑 (종성용)
    _DOUBLE_JONGSEONG = {
        "ㄲ": ("ㄱ", "ㄱ"),
        "ㄳ": ("ㄱ", "ㅅ"),
        "ㄵ": ("ㄴ", "ㅈ"),
        "ㄶ": ("ㄴ", "ㅎ"),
        "ㄺ": ("ㄹ", "ㄱ"),
        "ㄻ": ("ㄹ", "ㅁ"),
        "ㄼ": ("ㄹ", "ㅂ"),
        "ㄽ": ("ㄹ", "ㅅ"),
        "ㄾ": ("ㄹ", "ㅌ"),
        "ㄿ": ("ㄹ", "ㅍ"),
        "ㅀ": ("ㄹ", "ㅎ"),
        "ㅄ": ("ㅂ", "ㅅ"),
        "ㅆ": ("ㅅ", "ㅅ"),
    }

    # 겹자음 분해 매핑 (초성용)
    _DOUBLE_CHOSEONG = {
        "ㄲ": ("ㄱ", "ㄱ"),
        "ㄸ": ("ㄷ", "ㄷ"),
        "ㅃ": ("ㅂ", "ㅂ"),
        "ㅆ": ("ㅅ", "ㅅ"),
        "ㅉ": ("ㅈ", "ㅈ"),
    }

    # 복합 모음 분해 매핑
    _COMPOUND_VOWEL = {
        "ㅘ": ("ㅗ", "ㅏ"),
        "ㅙ": ("ㅗ", "ㅐ"),
        "ㅚ": ("ㅗ", "ㅣ"),
        "ㅝ": ("ㅜ", "ㅓ"),
        "ㅞ": ("ㅜ", "ㅔ"),
        "ㅟ": ("ㅜ", "ㅣ"),
        "ㅢ": ("ㅡ", "ㅣ"),
        "ㅒ": ("ㅑ", "ㅣ"),
        "ㅖ": ("ㅕ", "ㅣ"),
    }

    def __init__(self, *, locale: str = "en") -> None:
        """
        Initialize the NatoConverter.

        Args:
            locale (str): The locale for phonetic conversion.
                "en" for NATO phonetic alphabet (default).
                "ko" for Korean phonetic alphabet (한국어 통신 부호).
        """
        super().__init__()
        self._locale = locale

    async def convert_async(self, *, prompt: str, input_type: PromptDataType = "text") -> ConverterResult:
        """
        Convert the given text into phonetic alphabet representation.

        Args:
            prompt (str): The text to be converted.
            input_type (PromptDataType, optional): Type of input data. Defaults to "text".

        Returns:
            ConverterResult: The text converted to phonetic alphabet format.

        Raises:
            ValueError: If the input type is not supported (only "text" is supported).
        """
        if not self.input_supported(input_type):
            raise ValueError("Input type not supported")

        if self._locale == "ko":
            result = self._convert_to_korean_phonetic(prompt)
        else:
            result = self._convert_to_nato(prompt)

        return ConverterResult(output_text=result, output_type="text")

    def _convert_to_nato(self, text: str) -> str:
        """
        Convert text to NATO phonetic alphabet representation.

        Args:
            text (str): The text to convert.

        Returns:
            str: The NATO phonetic alphabet representation, with code words separated by spaces.
        """
        output = []
        for char in text.upper():
            if char in self._NATO_MAP:
                output.append(self._NATO_MAP[char])

        return " ".join(output)

    @staticmethod
    def _decompose_hangul(char: str) -> list[str]:
        """
        Decompose a single Hangul syllable into its constituent jamo.

        Args:
            char (str): A single Hangul syllable character.

        Returns:
            list[str]: List of jamo characters [초성, 중성, (종성)].
        """
        code = ord(char) - 0xAC00
        cho = code // (21 * 28)
        jung = (code % (21 * 28)) // 28
        jong = code % 28

        jamo = [
            NatoConverter._CHOSEONG[cho],
            NatoConverter._JUNGSEONG[jung],
        ]
        if jong > 0:
            jamo.append(NatoConverter._JONGSEONG[jong])

        return jamo

    def _jamo_to_phonetic(self, jamo: str, jamo_type: str) -> list[str]:
        """
        Convert a single jamo to its Korean phonetic code word(s).

        Handles decomposition of double consonants (겹자음) and compound vowels (복합 모음).

        Args:
            jamo (str): A single jamo character.
            jamo_type (str): One of "choseong", "jungseong", "jongseong".

        Returns:
            list[str]: List of phonetic code words.
        """
        # 겹자음 분해 (초성)
        if jamo_type == "choseong" and jamo in self._DOUBLE_CHOSEONG:
            parts = self._DOUBLE_CHOSEONG[jamo]
            return [self._KO_CONSONANT_MAP[p] for p in parts if p in self._KO_CONSONANT_MAP]

        # 겹자음 분해 (종성)
        if jamo_type == "jongseong" and jamo in self._DOUBLE_JONGSEONG:
            parts = self._DOUBLE_JONGSEONG[jamo]
            return [self._KO_CONSONANT_MAP[p] for p in parts if p in self._KO_CONSONANT_MAP]

        # 복합 모음 분해
        if jamo_type == "jungseong" and jamo in self._COMPOUND_VOWEL:
            parts = self._COMPOUND_VOWEL[jamo]
            return [self._KO_VOWEL_MAP[p] for p in parts if p in self._KO_VOWEL_MAP]

        # 단일 자모
        if jamo in self._KO_CONSONANT_MAP:
            return [self._KO_CONSONANT_MAP[jamo]]
        if jamo in self._KO_VOWEL_MAP:
            return [self._KO_VOWEL_MAP[jamo]]

        return []

    def _convert_to_korean_phonetic(self, text: str) -> str:
        """
        Convert text to Korean phonetic alphabet representation.

        Handles Hangul syllables (decomposed into jamo), English letters
        (converted via NATO map with Korean code words), and digits.

        Args:
            text (str): The text to convert.

        Returns:
            str: The Korean phonetic alphabet representation.
        """
        output = []

        for char in text:
            # 한글 음절 (가~힣)
            if "가" <= char <= "힣":
                jamo_list = self._decompose_hangul(char)
                types = ["choseong", "jungseong", "jongseong"]
                for i, jamo in enumerate(jamo_list):
                    output.extend(self._jamo_to_phonetic(jamo, types[i]))

            # 숫자
            elif char in self._KO_DIGIT_MAP:
                output.append(self._KO_DIGIT_MAP[char])

            # 영문자 → NATO 매핑 (영문도 지원)
            elif char.upper() in self._NATO_MAP:
                output.append(self._NATO_MAP[char.upper()])

        return " ".join(output)
