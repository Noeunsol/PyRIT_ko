# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.


from pyrit.models import PromptDataType
from pyrit.prompt_converter.prompt_converter import ConverterResult, PromptConverter


class BrailleConverter(PromptConverter):
    """
    Converts text into Braille Unicode representation.

    This converter transforms standard text into Braille patterns using Unicode
    Braille characters (U+2800 to U+28FF). It supports lowercase and uppercase
    letters, numbers, common punctuation, and spaces. Uppercase letters are
    prefixed with the Braille capitalization indicator.

    When locale is set to "ko", Korean text (Hangeul) is decomposed into jamo
    (초성, 중성, 종성) and converted using the Korean Braille standard
    (한국 점자 규정, 문화체육관광부고시 제2024-0005호).

    The Braille mapping is based on the implementation from Garak:
    https://github.com/NVIDIA/garak/blob/main/garak/probes/encoding.py

    Reference:
        - English: https://github.com/NVIDIA/garak/blob/main/garak/probes/encoding.py
        - Korean: 개정 한국 점자 규정 (2024), 문화체육관광부 (https://www.korean.go.kr/front/etcData/etcDataView.do?mn_id=46&etc_seq=710&pageIndex=1)

    Example (locale="en"):
        Input: "Hello"
        Output: "⠠⠓⠑⠇⠇⠕"

    Example (locale="ko"):
        Input: "안녕"
        Output: "⠣⠒⠉⠱⠶"
    """

    SUPPORTED_INPUT_TYPES = ("text",)
    SUPPORTED_OUTPUT_TYPES = ("text",)

    # 한글 점자 - 초성 (Initial consonants, 제1항)
    # ㅇ is omitted when initial (다만1)
    _KO_CHOSEONG_MAP = {
        "ㄱ": "\u2808",       # dot 4
        "ㄲ": "\u2820\u2808", # 된소리표(dot6) + ㄱ
        "ㄴ": "\u2809",       # dots 1,4
        "ㄷ": "\u280A",       # dots 2,4
        "ㄸ": "\u2820\u280A", # 된소리표 + ㄷ
        "ㄹ": "\u2810",       # dot 5
        "ㅁ": "\u2811",       # dots 1,5
        "ㅂ": "\u2818",       # dots 4,5
        "ㅃ": "\u2820\u2818", # 된소리표 + ㅂ
        "ㅅ": "\u2820",       # dot 6
        "ㅆ": "\u2820\u2820", # 된소리표 + ㅅ
        "ㅇ": "",             # omitted (다만1)
        "ㅈ": "\u2828",       # dots 4,6
        "ㅉ": "\u2820\u2828", # 된소리표 + ㅈ
        "ㅊ": "\u2830",       # dots 5,6
        "ㅋ": "\u280B",       # dots 1,2,4
        "ㅌ": "\u2813",       # dots 1,2,5
        "ㅍ": "\u2819",       # dots 1,4,5
        "ㅎ": "\u281A",       # dots 2,4,5
    }

    # 한글 점자 - 중성 (Vowels, 제6항·제7항)
    _KO_JUNGSEONG_MAP = {
        "ㅏ": "\u2823",              # dots 1,2,6
        "ㅐ": "\u2817",              # dots 1,2,3,5
        "ㅑ": "\u281C",              # dots 3,4,5
        "ㅒ": "\u281C\u2817",        # ㅑ + ㅐ
        "ㅓ": "\u280E",              # dots 2,3,4
        "ㅔ": "\u281D",              # dots 1,3,4,5
        "ㅕ": "\u2831",              # dots 1,5,6
        "ㅖ": "\u280C",              # dots 3,4 (약자)
        "ㅗ": "\u2825",              # dots 1,3,6
        "ㅘ": "\u2827",              # dots 1,2,3,6
        "ㅙ": "\u2827\u2817",        # ㅘ + ㅐ
        "ㅚ": "\u283D",              # dots 1,3,4,5,6
        "ㅛ": "\u282C",              # dots 3,4,6
        "ㅜ": "\u280D",              # dots 1,3,4
        "ㅝ": "\u280F",              # dots 1,2,3,4
        "ㅞ": "\u280F\u2817",        # ㅝ + ㅐ
        "ㅟ": "\u280D\u2817",        # ㅜ + ㅐ
        "ㅠ": "\u2829",              # dots 1,4,6
        "ㅡ": "\u282A",              # dots 2,4,6
        "ㅢ": "\u283A",              # dots 2,4,5,6
        "ㅣ": "\u2815",              # dots 1,3,5
    }

    # 한글 점자 - 종성 (Final consonants, 제3항)
    # 초성과 다른 점 배열 사용
    _KO_JONGSEONG_MAP = {
        "":   "",                     # no final consonant
        "ㄱ": "\u2801",              # dot 1
        "ㄲ": "\u2801\u2801",        # ㄱ+ㄱ (제4항)
        "ㄳ": "\u2801\u2804",        # ㄱ+ㅅ (제5항)
        "ㄴ": "\u2812",              # dots 2,5
        "ㄵ": "\u2812\u2805",        # ㄴ+ㅈ
        "ㄶ": "\u2812\u2834",        # ㄴ+ㅎ
        "ㄷ": "\u2814",              # dots 3,5
        "ㄹ": "\u2802",              # dot 2
        "ㄺ": "\u2802\u2801",        # ㄹ+ㄱ
        "ㄻ": "\u2802\u2822",        # ㄹ+ㅁ
        "ㄼ": "\u2802\u2803",        # ㄹ+ㅂ
        "ㄽ": "\u2802\u2804",        # ㄹ+ㅅ
        "ㄾ": "\u2802\u2826",        # ㄹ+ㅌ
        "ㄿ": "\u2802\u2832",        # ㄹ+ㅍ
        "ㅀ": "\u2802\u2834",        # ㄹ+ㅎ
        "ㅁ": "\u2822",              # dots 2,6
        "ㅂ": "\u2803",              # dots 1,2
        "ㅄ": "\u2803\u2804",        # ㅂ+ㅅ
        "ㅅ": "\u2804",              # dot 3
        "ㅆ": "\u280C",              # dots 3,4 (약자, 제4항)
        "ㅇ": "\u2836",              # dots 2,3,5,6
        "ㅈ": "\u2805",              # dots 1,3
        "ㅊ": "\u2806",              # dots 2,3
        "ㅋ": "\u2816",              # dots 2,3,5
        "ㅌ": "\u2826",              # dots 2,3,6
        "ㅍ": "\u2832",              # dots 2,5,6
        "ㅎ": "\u2834",              # dots 3,5,6
    }

    # 한글 자모 분해 테이블
    _CHOSEONG_LIST = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
    _JUNGSEONG_LIST = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
    _JONGSEONG_LIST = [
        "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ",
        "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ",
        "ㅋ", "ㅌ", "ㅍ", "ㅎ",
    ]

    def __init__(self, *, locale: str = "en") -> None:
        """
        Initialize the BrailleConverter.

        Args:
            locale (str): The locale for braille conversion.
                "en" for English/Latin braille (default).
                "ko" for Korean braille (한국 점자 규정 2024).
        """
        super().__init__()
        self._locale = locale

    async def convert_async(self, *, prompt: str, input_type: PromptDataType = "text") -> ConverterResult:
        """
        Convert the given text into Braille Unicode representation.

        Args:
            prompt (str): The text to be converted to Braille.
            input_type (PromptDataType, optional): Type of input data. Defaults to "text".

        Returns:
            ConverterResult: The text converted to Braille Unicode characters.

        Raises:
            ValueError: If the input type is not supported (only "text" is supported).
        """
        if not self.input_supported(input_type):
            raise ValueError("Input type not supported")

        if self._locale == "ko":
            result = self._convert_to_korean_braille(prompt)
        else:
            result = self._get_braile(prompt)

        return ConverterResult(output_text=result, output_type="text")

    def _get_braile(self, text: str) -> str:
        """
        Retrieve the braille representation of the input text.

        Taken from Garak https://github.com/NVIDIA/garak/blob/main/garak/probes/encoding.py

        Args:
            text (str): The input text to be converted to braille.

        Returns:
            str: The braille representation of the input text.
        """
        characterUnicodes = {
            "a": "\u2801",
            "b": "\u2803",
            "k": "\u2805",
            "l": "\u2807",
            "c": "\u2809",
            "i": "\u280a",
            "f": "\u280b",
            "m": "\u280d",
            "s": "\u280e",
            "p": "\u280f",
            "e": "\u2811",
            "h": "\u2813",
            "o": "\u2815",
            "r": "\u2817",
            "d": "\u2819",
            "j": "\u281a",
            "g": "\u281b",
            "n": "\u281d",
            "t": "\u281e",
            "q": "\u281f",
            "u": "\u2825",
            "v": "\u2827",
            "x": "\u282d",
            "z": "\u2835",
            "w": "\u283a",
            "y": "\u283d",
            "num": "\u283c",
            "caps": "\u2820",
            ".": "\u2832",
            "'": "\u2804",
            ",": "\u2802",
            "-": "\u2824",
            "/": "\u280c",
            "!": "\u2816",
            "?": "\u2826",
            "$": "\u2832",
            ":": "\u2812",
            ";": "\u2830",
            "(": "\u2836",
            ")": "\u2836",
            "1": "\u2801",
            "2": "\u2803",
            "3": "\u2809",
            "4": "\u2819",
            "5": "\u2811",
            "6": "\u280b",
            "7": "\u281b",
            "8": "\u2813",
            "9": "\u280a",
            "0": "\u281a",
            " ": " ",
        }
        numberPunctuations = [".", ",", "-", "/", "$"]
        escapeCharacters = ["\n", "\r", "\t"]

        output = ""

        for char in text:
            is_number = False
            if char in escapeCharacters:
                output += char
            elif char.isupper():
                if char.lower() in characterUnicodes:
                    output += characterUnicodes["caps"]
                    output += characterUnicodes[char.lower()]
            elif char in characterUnicodes:
                if char.isdigit():
                    if not is_number:
                        is_number = True
                        output += characterUnicodes["num"]
                output += characterUnicodes[char]
            if is_number and char not in numberPunctuations:
                is_number = False

        return output

    def _convert_to_korean_braille(self, text: str) -> str:
        """
        Convert text to Korean braille (한국 점자) representation.

        Handles Hangeul syllables (decomposed into 초성/중성/종성),
        English letters (using standard English braille), digits,
        and spaces.

        Based on: 개정 한국 점자 규정 (2024), 문화체육관광부고시 제2024-0005호

        Args:
            text (str): The text to convert.

        Returns:
            str: The Korean braille Unicode representation.
        """
        # 한국 점자 수표 (제40항): dots 3,4,5,6
        _KO_NUM_SIGN = "\u283C"

        # 한국 점자 숫자 (제40항): 수표 뒤에 영문 점자와 동일한 패턴
        _KO_DIGIT_MAP = {
            "1": "\u2801", "2": "\u2803", "3": "\u2809",
            "4": "\u2819", "5": "\u2811", "6": "\u280B",
            "7": "\u281B", "8": "\u2813", "9": "\u280A",
            "0": "\u281A",
        }

        output = []
        is_number = False

        for char in text:
            # 한글 음절 (가~힣)
            if "\uAC00" <= char <= "\uD7A3":
                is_number = False
                code = ord(char) - 0xAC00
                cho_idx = code // (21 * 28)
                jung_idx = (code % (21 * 28)) // 28
                jong_idx = code % 28

                cho = self._CHOSEONG_LIST[cho_idx]
                jung = self._JUNGSEONG_LIST[jung_idx]
                jong = self._JONGSEONG_LIST[jong_idx]

                # 초성 (ㅇ is omitted per 다만1)
                if cho in self._KO_CHOSEONG_MAP:
                    output.append(self._KO_CHOSEONG_MAP[cho])

                # 중성
                if jung in self._KO_JUNGSEONG_MAP:
                    output.append(self._KO_JUNGSEONG_MAP[jung])

                # 종성
                if jong and jong in self._KO_JONGSEONG_MAP:
                    output.append(self._KO_JONGSEONG_MAP[jong])

            # 숫자
            elif char.isdigit():
                if not is_number:
                    is_number = True
                    output.append(_KO_NUM_SIGN)
                output.append(_KO_DIGIT_MAP[char])

            # 공백
            elif char == " ":
                is_number = False
                output.append(" ")

            # 줄바꿈 등
            elif char in ("\n", "\r", "\t"):
                is_number = False
                output.append(char)

            # 영문자 (한국어 문장 내 영문은 로마자표로 묶어야 하나,
            # red-teaming 목적으로는 단순 영문 점자 변환)
            elif char.isascii() and char.isalpha():
                is_number = False
                english_result = self._get_braile(char)
                output.append(english_result)

            else:
                is_number = False

        return "".join(output)
