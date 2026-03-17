# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import pytest

from pyrit.prompt_converter import AskToDecodeConverter, ConverterResult


@pytest.mark.asyncio
async def test_ask_to_decode_converter_with_custom_template():
    """Test converter with a custom template."""
    template = "Decode this: {encoded_text}"
    converter = AskToDecodeConverter(template=template)
    prompt = "SGVsbG8gV29ybGQ="  # Base64 encoded "Hello World"

    result = await converter.convert_async(prompt=prompt, input_type="text")

    assert isinstance(result, ConverterResult)
    assert result.output_text == "Decode this: SGVsbG8gV29ybGQ="
    assert result.output_type == "text"


@pytest.mark.asyncio
async def test_ask_to_decode_converter_with_encoding_name_and_template():
    """Test converter with encoding name and custom template."""
    template = "{encoding_name}: {encoded_text}"
    converter = AskToDecodeConverter(template=template, encoding_name="Base64")
    prompt = "SGVsbG8gV29ybGQ="

    result = await converter.convert_async(prompt=prompt, input_type="text")

    assert isinstance(result, ConverterResult)
    assert result.output_text == "Base64: SGVsbG8gV29ybGQ="
    assert result.output_type == "text"


@pytest.mark.asyncio
async def test_ask_to_decode_converter_random_template():
    """Test converter with random template selection."""
    converter = AskToDecodeConverter()
    prompt = "test_encoded_text"

    result = await converter.convert_async(prompt=prompt, input_type="text")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    # The result should contain the encoded text somewhere
    assert "test_encoded_text" in result.output_text


@pytest.mark.asyncio
async def test_ask_to_decode_converter_random_template_with_encoding_name():
    """Test converter with random template and encoding name."""
    converter = AskToDecodeConverter(encoding_name="ROT13")
    prompt = "grfg"

    result = await converter.convert_async(prompt=prompt, input_type="text")

    assert isinstance(result, ConverterResult)
    assert result.output_type == "text"
    # The result should contain the encoded text
    assert "grfg" in result.output_text


@pytest.mark.asyncio
async def test_ask_to_decode_converter_input_type_not_supported():
    """Test that non-text input types raise ValueError."""
    converter = AskToDecodeConverter()

    with pytest.raises(ValueError, match="Input type not supported"):
        await converter.convert_async(prompt="test", input_type="image_path")


def test_ask_to_decode_converter_input_supported():
    """Test input_supported method."""
    converter = AskToDecodeConverter()
    assert converter.input_supported("text") is True
    assert converter.input_supported("image_path") is False


def test_ask_to_decode_converter_output_supported():
    """Test output_supported method."""
    converter = AskToDecodeConverter()
    assert converter.output_supported("text") is True
    assert converter.output_supported("image_path") is False


@pytest.mark.asyncio
async def test_ask_to_decode_converter_korean_locale_with_custom_template():
    """Test converter with Korean locale uses Korean templates."""
    converter = AskToDecodeConverter(locale="ko")
    prompt = "test_encoded_text"

    result = await converter.convert_async(prompt=prompt, input_type="text")

    assert isinstance(result, ConverterResult)
    assert "test_encoded_text" in result.output_text


@pytest.mark.asyncio
async def test_ask_to_decode_converter_korean_locale_specific_template():
    """Test Korean locale with a specific Korean template."""
    template = "인코딩된 텍스트: {encoded_text}\n디코딩 결과:"
    converter = AskToDecodeConverter(template=template, locale="ko")
    prompt = "SGVsbG8="

    result = await converter.convert_async(prompt=prompt, input_type="text")

    assert result.output_text == "인코딩된 텍스트: SGVsbG8=\n디코딩 결과:"


def test_ask_to_decode_converter_korean_locale_templates_populated():
    """Test that Korean locale populates templates from the ko locale dict."""
    converter = AskToDecodeConverter(locale="ko")
    # Korean templates should include Korean strings
    assert any("인코딩" in t or "디코딩" in t or "뜻" in t for t in converter._all_templates)
