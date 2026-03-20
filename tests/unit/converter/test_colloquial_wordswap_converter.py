# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import re

import pytest

from pyrit.prompt_converter.colloquial_wordswap_converter import (
    ColloquialWordswapConverter,
)


# Test for deterministic mode
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_text,expected_output",
    [
        ("grandfather", "ah gong"),  # Single wordswap
        ("mother and brother", "mama and bro"),  # Default substitution for mother and brother
        ("Hello, my Father!", "Hello, my papa!"),  # Combined substitutions with punctuation
    ],
)
async def test_colloquial_deterministic(input_text, expected_output):
    converter = ColloquialWordswapConverter(deterministic=True)
    result = await converter.convert_async(prompt=input_text)
    assert result.output_text == expected_output


# Test for non-deterministic mode
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_text",
    [
        "code",  # A different input set to reduce redundancy
        "mother",
        "uncle and brother",
    ],
)
async def test_colloquial_non_deterministic(input_text):
    converter = ColloquialWordswapConverter(deterministic=False)
    result = await converter.convert_async(prompt=input_text)

    # Valid substitution mappings in the input texts
    valid_substitutions = {
        "mother": ["mama", "amma", "ibu"],
        "uncle": ["encik", "unker"],
        "brother": ["bro", "boiboi", "di di", "xdd", "anneh", "thambi"],
    }

    # Split input and output into words, preserving multi-word substitutions as single tokens
    input_words = re.findall(r"\w+|\S+", input_text)
    output_words = re.findall(r"\w+|\S+", result.output_text)

    # Check that each wordswap is a valid substitution
    for input_word, output_word in zip(input_words, output_words):
        lower_input_word = input_word.lower()

        if lower_input_word in valid_substitutions:
            assert any(sub in output_word or output_word in sub for sub in valid_substitutions[lower_input_word])
        else:
            assert output_word == input_word


# Test for custom substitutions
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_text,custom_substitutions,expected_output",
    [
        ("father", {"father": ["appa", "darth vader"]}, "appa"),  # Custom substitution father -> appa
    ],
)
async def test_colloquial_custom_substitutions(input_text, custom_substitutions, expected_output):
    converter = ColloquialWordswapConverter(deterministic=True, custom_substitutions=custom_substitutions)
    result = await converter.convert_async(prompt=input_text)
    assert result.output_text == expected_output


# Test for empty custom substitutions
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_text,expected_output",
    [
        ("mother and father", "mama and papa"),  # Using default substitutions when custom is empty
    ],
)
async def test_colloquial_empty_custom_substitutions(input_text, expected_output):
    converter = ColloquialWordswapConverter(deterministic=True, custom_substitutions={})
    result = await converter.convert_async(prompt=input_text)
    assert result.output_text == expected_output


# Test multiple word prompts
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_text,expected_output",
    [
        ("father and mother", "papa and mama"),
        ("brother and sister", "bro and xjj"),
        ("aunt and uncle", "makcik and encik"),
    ],
)
async def test_multiple_words(input_text, expected_output):
    converter = ColloquialWordswapConverter(deterministic=True)
    result = await converter.convert_async(prompt=input_text)
    assert result.output_text == expected_output


# Test for awkward spacing
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_text,expected_output",
    [
        ("  father  and    mother ", "papa and mama"),
        ("sister   and   brother", "xjj and bro"),
    ],
)
async def test_awkward_spacing(input_text, expected_output):
    converter = ColloquialWordswapConverter(deterministic=True)
    result = await converter.convert_async(prompt=input_text)
    assert result.output_text == expected_output


# Test for punctuation handling
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_text,expected_output",
    [
        ("father, mother!", "papa, mama!"),
        ("aunt? uncle!", "makcik? encik!"),
    ],
)
async def test_punctuation_handling(input_text, expected_output):
    converter = ColloquialWordswapConverter(deterministic=True)
    result = await converter.convert_async(prompt=input_text)
    assert result.output_text == expected_output


def test_colloquial_converter_input_supported() -> None:
    converter = ColloquialWordswapConverter()
    assert converter.input_supported("text") is True
    assert converter.input_supported("image_path") is False


# --- Korean locale tests ---


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_text,expected_output",
    [
        ("아버지가 오셨다", "아빠가 오셨다"),
        ("어머니와 할아버지", "엄마와 할부지"),
    ],
)
async def test_colloquial_korean_deterministic(input_text, expected_output):
    """Test Korean colloquial substitution with deterministic mode."""
    converter = ColloquialWordswapConverter(locale="ko", deterministic=True)
    result = await converter.convert_async(prompt=input_text)
    assert result.output_text == expected_output


@pytest.mark.asyncio
async def test_colloquial_korean_particle_preservation():
    """Test that Korean particles (조사) are preserved after substitution."""
    converter = ColloquialWordswapConverter(locale="ko", deterministic=True)
    # "아버지가" → stem "아버지" → "아빠" + particle "가" → "아빠가"
    result = await converter.convert_async(prompt="아버지가")
    assert result.output_text == "아빠가"


@pytest.mark.asyncio
async def test_colloquial_korean_longest_match_first():
    """Test that longer stems are matched first: 할아버지 before 아버지."""
    converter = ColloquialWordswapConverter(locale="ko", deterministic=True)
    result = await converter.convert_async(prompt="할아버지와 아버지")
    # 할아버지 → 할부지, 아버지 → 아빠
    assert "할부지" in result.output_text
    assert "아빠" in result.output_text


@pytest.mark.asyncio
async def test_colloquial_korean_no_match_preserved():
    """Test that words without substitutions are preserved."""
    converter = ColloquialWordswapConverter(locale="ko", deterministic=True)
    result = await converter.convert_async(prompt="컴퓨터를 켰다")
    assert result.output_text == "컴퓨터를 켰다"


@pytest.mark.asyncio
async def test_colloquial_korean_non_deterministic():
    """Test Korean non-deterministic mode picks from valid substitutions."""
    converter = ColloquialWordswapConverter(locale="ko", deterministic=False)
    result = await converter.convert_async(prompt="아버지")
    valid = ["아빠", "아부지", "울 아빠", "대디", "세대주"]
    assert result.output_text in valid
