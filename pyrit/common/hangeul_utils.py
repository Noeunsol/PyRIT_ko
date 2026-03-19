# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Hangeul decomposition and jamo manipulation utilities.

Shared by converters that need to decompose Korean syllables into jamo
(ROT13, Atbash, Morse, NATO, Braille, Leetspeak, etc.).
"""

# Hangeul syllable decomposition tables
CHOSEONG = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
JUNGSEONG = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
JONGSEONG = [
    "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ",
    "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]

CHO_IDX = {ch: i for i, ch in enumerate(CHOSEONG)}
JUNG_IDX = {ch: i for i, ch in enumerate(JUNGSEONG)}
JONG_IDX = {ch: i for i, ch in enumerate(JONGSEONG)}

# 겹자모 → 기본 자모 분해 (쌍자음, 복합모음, 겹받침)
COMPOUND = {
    # 쌍자음
    "ㄲ": "ㄱㄱ", "ㄸ": "ㄷㄷ", "ㅃ": "ㅂㅂ", "ㅆ": "ㅅㅅ", "ㅉ": "ㅈㅈ",
    # 겹받침
    "ㄳ": "ㄱㅅ", "ㄵ": "ㄴㅈ", "ㄶ": "ㄴㅎ", "ㄺ": "ㄹㄱ", "ㄻ": "ㄹㅁ",
    "ㄼ": "ㄹㅂ", "ㄽ": "ㄹㅅ", "ㄾ": "ㄹㅌ", "ㄿ": "ㄹㅍ", "ㅀ": "ㄹㅎ",
    "ㅄ": "ㅂㅅ",
    # 복합 모음
    "ㅐ": "ㅏㅣ", "ㅒ": "ㅑㅣ", "ㅔ": "ㅓㅣ", "ㅖ": "ㅕㅣ",
    "ㅘ": "ㅗㅏ", "ㅙ": "ㅗㅏㅣ", "ㅚ": "ㅗㅣ",
    "ㅝ": "ㅜㅓ", "ㅞ": "ㅜㅓㅣ", "ㅟ": "ㅜㅣ", "ㅢ": "ㅡㅣ",
}

# 기본 자모 (쌍자음/복합모음 제외)
BASIC_CONS = "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ"  # 14자
BASIC_VOWS = "ㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ"            # 10자


def decompose_jamo(jamo: str) -> list[str]:
    """Decompose compound jamo into basic jamo list."""
    if jamo in COMPOUND:
        return list(COMPOUND[jamo])
    return [jamo]


def decompose_hangeul(text: str) -> list[str]:
    """Decompose Hangeul syllables into basic jamo list.

    Non-Hangeul characters (spaces, ASCII, etc.) are passed through as-is.

    Example:
        "안녕" → ["ㅇ", "ㅏ", "ㄴ", "ㄴ", "ㅕ", "ㅇ"]
        "Hello 안녕" → ["H", "e", "l", "l", "o", " ", "ㅇ", "ㅏ", "ㄴ", "ㄴ", "ㅕ", "ㅇ"]
    """
    result: list[str] = []
    for char in text:
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            code -= 0xAC00
            cho = CHOSEONG[code // (21 * 28)]
            jung = JUNGSEONG[(code % (21 * 28)) // 28]
            jong = JONGSEONG[code % 28]
            result.extend(decompose_jamo(cho))
            result.extend(decompose_jamo(jung))
            if jong:
                result.extend(decompose_jamo(jong))
        else:
            result.append(char)
    return result


def compose_hangeul(cho: str, jung: str, jong: str = "") -> str:
    """Compose a Hangeul syllable from choseong, jungseong, and optional jongseong.

    Args:
        cho: Initial consonant (e.g. "ㄱ")
        jung: Vowel (e.g. "ㅏ")
        jong: Final consonant (e.g. "ㄴ"), empty string for no final consonant.

    Returns:
        Composed Hangeul syllable (e.g. "간")
    """
    if cho not in CHO_IDX or jung not in JUNG_IDX or jong not in JONG_IDX:
        return cho + jung + jong  # fallback: return raw jamo
    return chr(0xAC00 + CHO_IDX[cho] * 21 * 28 + JUNG_IDX[jung] * 28 + JONG_IDX[jong])
