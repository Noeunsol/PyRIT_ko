# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import pytest

from pyrit.prompt_converter import BrailleConverter, ConverterResult


@pytest.mark.asyncio
async def test_braille_converter_simple_text():
    """Test basic Braille conversion."""
    converter = BrailleConverter()
    prompt = "hello"

    result = await converter.convert_async(prompt=prompt, input_type="text")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    # Verify it returns some braille characters
    assert result.output_text != ""
    assert result.output_text != prompt


@pytest.mark.asyncio
async def test_braille_converter_with_space():
    """Test Braille conversion with spaces."""
    converter = BrailleConverter()
    prompt = "hi there"

    result = await converter.convert_async(prompt=prompt, input_type="text")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    # Should preserve space
    assert " " in result.output_text


@pytest.mark.asyncio
async def test_braille_converter_uppercase():
    """Test Braille conversion with uppercase letters."""
    converter = BrailleConverter()
    prompt = "Hello"

    result = await converter.convert_async(prompt=prompt, input_type="text")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    # Should have some output
    assert len(result.output_text) > 0


@pytest.mark.asyncio
async def test_braille_converter_numbers():
    """Test Braille conversion with numbers."""
    converter = BrailleConverter()
    prompt = "123"

    result = await converter.convert_async(prompt=prompt, input_type="text")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    assert len(result.output_text) > 0


@pytest.mark.asyncio
async def test_braille_converter_punctuation():
    """Test Braille conversion with punctuation."""
    converter = BrailleConverter()
    prompt = "Hello, world!"

    result = await converter.convert_async(prompt=prompt, input_type="text")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    assert len(result.output_text) > 0


@pytest.mark.asyncio
async def test_braille_converter_input_type_not_supported():
    """Test that non-text input types raise ValueError."""
    converter = BrailleConverter()

    with pytest.raises(ValueError, match="Input type not supported"):
        await converter.convert_async(prompt="test", input_type="image_path")


def test_braille_converter_input_supported():
    """Test input_supported method."""
    converter = BrailleConverter()
    assert converter.input_supported("text") is True
    assert converter.input_supported("image_path") is False


def test_braille_converter_output_supported():
    """Test output_supported method."""
    converter = BrailleConverter()
    assert converter.output_supported("text") is True
    assert converter.output_supported("image_path") is False


# --- Korean locale tests ---


@pytest.mark.asyncio
async def test_braille_converter_korean_locale_basic():
    """Test Korean braille conversion produces output."""
    converter = BrailleConverter(locale="ko")
    result = await converter.convert_async(prompt="가", input_type="text")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    assert len(result.output_text) > 0
    assert result.output_text != "가"


@pytest.mark.asyncio
async def test_braille_converter_korean_locale_example():
    """Test docstring example: 안녕 → ⠣⠒⠉⠱⠶."""
    converter = BrailleConverter(locale="ko")
    result = await converter.convert_async(prompt="안녕", input_type="text")

    assert result.output_text == "⠣⠒⠉⠱⠶"


@pytest.mark.asyncio
async def test_braille_converter_korean_locale_ieung_omitted():
    """Test that initial ㅇ is omitted per Korean braille rules (다만1)."""
    converter = BrailleConverter(locale="ko")
    result = await converter.convert_async(prompt="아", input_type="text")

    # ㅇ initial is omitted, only ㅏ should be present
    # ㅏ = \u2823
    assert "\u2823" in result.output_text


@pytest.mark.asyncio
async def test_braille_converter_korean_locale_with_space():
    """Test Korean braille with spaces."""
    converter = BrailleConverter(locale="ko")
    result = await converter.convert_async(prompt="가 나", input_type="text")

    assert " " in result.output_text


@pytest.mark.asyncio
async def test_braille_converter_korean_locale_ssang_consonant():
    """Test double consonant (된소리): 까 has 된소리표."""
    converter = BrailleConverter(locale="ko")
    result = await converter.convert_async(prompt="까", input_type="text")

    # ㄲ = 된소리표(\u2820) + ㄱ(\u2808)
    assert "\u2820\u2808" in result.output_text


@pytest.mark.asyncio
async def test_braille_converter_korean_locale_with_digits():
    """Test Korean braille with digits (수표 prefix)."""
    converter = BrailleConverter(locale="ko")
    result = await converter.convert_async(prompt="1", input_type="text")

    # Should have 수표 \u283C followed by digit
    assert "\u283C" in result.output_text
