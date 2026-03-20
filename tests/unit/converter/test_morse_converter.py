# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import pytest

from pyrit.prompt_converter import ConverterResult, MorseConverter


@pytest.mark.asyncio
async def test_morse_converter_korean_locale_basic():
    """Test Morse Korean locale produces valid output."""
    converter = MorseConverter(locale="ko")
    result = await converter.convert_async(prompt="가")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    # 가 = ㄱ+ㅏ → ".-.." + "."
    assert result.output_text == ".-.." + " " + "."


@pytest.mark.asyncio
async def test_morse_converter_korean_locale_with_jongseong():
    """Test syllable with final consonant: 간 = ㄱ+ㅏ+ㄴ."""
    converter = MorseConverter(locale="ko")
    result = await converter.convert_async(prompt="간")

    # ㄱ=".-..", ㅏ=".", ㄴ="..-."
    assert result.output_text == ".-.." + " " + "." + " " + "..-."


@pytest.mark.asyncio
async def test_morse_converter_korean_locale_space():
    """Test that space becomes / in Korean morse."""
    converter = MorseConverter(locale="ko")
    result = await converter.convert_async(prompt="가 나")

    assert "/" in result.output_text


@pytest.mark.asyncio
async def test_morse_converter_korean_locale_full_jamo():
    """Test all 14 basic consonants have morse mappings."""
    converter = MorseConverter(locale="ko")
    # 가나다라마바사아자차카타파하 covers all 14 basic consonants
    result = await converter.convert_async(prompt="가나다라마바사아자차카타파하")

    assert isinstance(result, ConverterResult)
    # Should not contain error sequence for valid Korean
    assert "........" not in result.output_text


@pytest.mark.asyncio
async def test_morse_converter_korean_locale_ssang_jamo():
    """Test double consonant (쌍자음): 까 = ㄲ+ㅏ → ㄱ+ㄱ+ㅏ."""
    converter = MorseConverter(locale="ko")
    result = await converter.convert_async(prompt="까")

    # ㄲ decomposes to ㄱ+ㄱ, then ㅏ
    # ㄱ=".-..", ㄱ=".-..", ㅏ="."
    assert result.output_text == ".-.." + " " + ".-.." + " " + "."


@pytest.mark.asyncio
async def test_morse_converter_korean_locale_mixed_text():
    """Test mixed Korean and English in Korean locale."""
    converter = MorseConverter(locale="ko")
    result = await converter.convert_async(prompt="A가")

    # A=".-", ㄱ=".-..", ㅏ="."
    assert ".-" in result.output_text


@pytest.mark.asyncio
async def test_morse_converter_english_locale_default():
    """Test default English locale."""
    converter = MorseConverter()
    result = await converter.convert_async(prompt="SOS")

    assert result.output_text == "... --- ..."
