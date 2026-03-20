# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import pytest

from pyrit.prompt_converter import AtbashConverter, ConverterResult


@pytest.mark.asyncio
async def test_atbash_converter_korean_locale_basic():
    """Test Atbash Korean locale produces different output from input."""
    converter = AtbashConverter(locale="ko")
    result = await converter.convert_async(prompt="가나다")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    assert result.output_text != "가나다"


@pytest.mark.asyncio
async def test_atbash_converter_korean_locale_involution():
    """Atbash applied twice should return original for basic jamo syllables."""
    converter = AtbashConverter(locale="ko")
    # Use only basic vowels (no compound vowels like ㅔ,ㅐ) for clean round-trip
    first = await converter.convert_async(prompt="가나다라마")
    second = await converter.convert_async(prompt=first.output_text)

    assert second.output_text == "가나다라마"


@pytest.mark.asyncio
async def test_atbash_converter_korean_locale_single_syllable():
    """Test single syllable: 가 (ㄱ+ㅏ) → Atbash reversal."""
    converter = AtbashConverter(locale="ko")
    result = await converter.convert_async(prompt="가")

    # ㄱ↔ㅎ (BASIC_CONS reversed), ㅏ↔ㅣ (BASIC_VOWS reversed)
    assert result.output_text != "가"


@pytest.mark.asyncio
async def test_atbash_converter_korean_locale_with_jongseong():
    """Test syllable with final consonant is properly reversed."""
    converter = AtbashConverter(locale="ko")
    result = await converter.convert_async(prompt="한")

    assert result.output_text != "한"
    # Involution check
    back = await converter.convert_async(prompt=result.output_text)
    assert back.output_text == "한"


@pytest.mark.asyncio
async def test_atbash_converter_korean_locale_mixed_text():
    """Test mixed Korean and English text."""
    converter = AtbashConverter(locale="ko")
    result = await converter.convert_async(prompt="Hello 가")

    # English "Hello" → Atbash: "Svool"
    assert "Svool" in result.output_text


@pytest.mark.asyncio
async def test_atbash_converter_english_locale_default():
    """Test that default locale uses standard Atbash."""
    converter = AtbashConverter()
    result = await converter.convert_async(prompt="Hello")

    assert result.output_text == "Svool"


@pytest.mark.asyncio
async def test_atbash_converter_korean_locale_sentence():
    """Test a full Korean sentence with involution (basic jamo only)."""
    converter = AtbashConverter(locale="ko")
    # Use syllables with basic vowels only for clean round-trip
    sentence = "바다 하나 두고"
    first = await converter.convert_async(prompt=sentence)
    second = await converter.convert_async(prompt=first.output_text)

    assert second.output_text == sentence
