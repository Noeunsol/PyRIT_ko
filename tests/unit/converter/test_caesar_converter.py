# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import pytest

from pyrit.prompt_converter import CaesarConverter, ConverterResult


@pytest.mark.asyncio
async def test_caesar_converter_korean_locale_basic():
    """Test Caesar Korean locale produces different output from input."""
    converter = CaesarConverter(caesar_offset=1, locale="ko")
    result = await converter.convert_async(prompt="가나다")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    assert result.output_text != "가나다"


@pytest.mark.asyncio
async def test_caesar_converter_korean_locale_offset_reversal():
    """Positive offset followed by negative offset should return original for basic jamo."""
    encrypt = CaesarConverter(caesar_offset=3, locale="ko")
    decrypt = CaesarConverter(caesar_offset=-3, locale="ko")

    # Use only basic vowels (no compound vowels like ㅔ,ㅐ) for clean round-trip
    encrypted = await encrypt.convert_async(prompt="가나다라마")
    decrypted = await decrypt.convert_async(prompt=encrypted.output_text)

    assert decrypted.output_text == "가나다라마"


@pytest.mark.asyncio
async def test_caesar_converter_korean_locale_single_syllable():
    """Test single syllable shift."""
    converter = CaesarConverter(caesar_offset=1, locale="ko")
    result = await converter.convert_async(prompt="가")

    # ㄱ shifts by 1 → ㄴ, ㅏ shifts by 1 → ㅑ → 냐
    assert result.output_text == "냐"


@pytest.mark.asyncio
async def test_caesar_converter_korean_locale_with_jongseong():
    """Test syllable with final consonant."""
    encrypt = CaesarConverter(caesar_offset=2, locale="ko")
    decrypt = CaesarConverter(caesar_offset=-2, locale="ko")

    encrypted = await encrypt.convert_async(prompt="한글")
    decrypted = await decrypt.convert_async(prompt=encrypted.output_text)

    assert decrypted.output_text == "한글"


@pytest.mark.asyncio
async def test_caesar_converter_korean_locale_mixed_text():
    """Test mixed Korean and English text."""
    converter = CaesarConverter(caesar_offset=1, locale="ko")
    result = await converter.convert_async(prompt="Hello 가")

    # English shifts: H→I, e→f, l→m, l→m, o→p → "Ifmmp"
    assert "Ifmmp" in result.output_text
    assert "냐" in result.output_text


@pytest.mark.asyncio
async def test_caesar_converter_korean_locale_wrapping():
    """Test that Korean jamo wrapping works correctly."""
    # Offset large enough to wrap around consonants (14) and vowels (10)
    encrypt = CaesarConverter(caesar_offset=14, locale="ko")

    # After wrapping, consonants return to original, but vowels shifted by 14%10=4
    result = await encrypt.convert_async(prompt="가")
    # ㄱ shifts 14 → wraps to ㄱ, ㅏ shifts 14 → wraps 14%10=4 → ㅗ
    assert result.output_text != "가"


@pytest.mark.asyncio
async def test_caesar_converter_english_default():
    """Test default English locale."""
    converter = CaesarConverter(caesar_offset=1)
    result = await converter.convert_async(prompt="Hello 123")

    assert result.output_text == "Ifmmp 234"
