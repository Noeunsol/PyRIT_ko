# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import pytest

from pyrit.prompt_converter import ConverterResult, ROT13Converter


@pytest.mark.asyncio
async def test_rot13_converter_korean_locale_basic():
    """Test ROT13 Korean locale produces different output from input."""
    converter = ROT13Converter(locale="ko")
    result = await converter.convert_async(prompt="가나다")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    assert result.output_text != "가나다"


@pytest.mark.asyncio
async def test_rot13_converter_korean_locale_involution():
    """ROT13 applied twice should return original for basic jamo syllables."""
    converter = ROT13Converter(locale="ko")
    # Use only basic vowels (no compound vowels like ㅔ,ㅐ) for clean round-trip
    first = await converter.convert_async(prompt="가나다라마")
    second = await converter.convert_async(prompt=first.output_text)

    assert second.output_text == "가나다라마"


@pytest.mark.asyncio
async def test_rot13_converter_korean_locale_single_syllable():
    """Test single syllable: 가 (ㄱ+ㅏ) → ㅇ+ㅛ = 요."""
    converter = ROT13Converter(locale="ko")
    result = await converter.convert_async(prompt="가")

    # BASIC_CONS: ㄱ at index 0, rotate by 7 → ㅇ
    # BASIC_VOWS: ㅏ at index 0, rotate by 5 → ㅛ
    assert result.output_text == "요"


@pytest.mark.asyncio
async def test_rot13_converter_korean_locale_with_jongseong():
    """Test syllable with final consonant: 간 (ㄱ+ㅏ+ㄴ)."""
    converter = ROT13Converter(locale="ko")
    result = await converter.convert_async(prompt="간")

    # ㄱ→ㅈ, ㅏ→ㅛ, ㄴ→ㅊ → 죧? need compose(ㅈ,ㅛ,ㅊ)
    assert result.output_text != "간"
    # Verify involution
    back = await converter.convert_async(prompt=result.output_text)
    assert back.output_text == "간"


@pytest.mark.asyncio
async def test_rot13_converter_korean_locale_mixed_text():
    """Test mixed Korean and English text."""
    converter = ROT13Converter(locale="ko")
    result = await converter.convert_async(prompt="Hello 가")

    # English part uses standard ROT13, Korean part uses Korean ROT
    assert "Uryyb" in result.output_text  # "Hello" → "Uryyb"
    assert "요" in result.output_text      # "가" → "요"


@pytest.mark.asyncio
async def test_rot13_converter_korean_locale_preserves_spaces():
    """Test that spaces are preserved in Korean ROT13."""
    converter = ROT13Converter(locale="ko")
    result = await converter.convert_async(prompt="가 나")

    assert " " in result.output_text


@pytest.mark.asyncio
async def test_rot13_converter_english_locale_default():
    """Test that default locale uses standard ROT13."""
    converter = ROT13Converter()
    result = await converter.convert_async(prompt="Hello")

    assert result.output_text == "Uryyb"
