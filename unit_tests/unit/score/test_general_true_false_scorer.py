# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from textwrap import dedent
from unittest.mock import AsyncMock, MagicMock

import pytest
from unit.mocks import get_mock_target_identifier

from pyrit.models import Message, MessagePiece
from pyrit.score import SelfAskGeneralTrueFalseScorer


@pytest.fixture
def general_scorer_response() -> Message:
    json_response = (
        dedent(
            """
        {"score_value": "True",
         "rationale": "This is the rationale.",
         "description": "This is the description."}
        """
        )
        .strip()
        .replace("\n", " ")
    )

    return Message(message_pieces=[MessagePiece(role="assistant", original_value=json_response)])


@pytest.mark.asyncio
async def test_general_scorer_score_async(patch_central_database, general_scorer_response: Message):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[general_scorer_response])

    scorer = SelfAskGeneralTrueFalseScorer(
        chat_target=chat_target,
        system_prompt_format_string="This is a system prompt.",
        category="test_category",
    )
    assert scorer

    score = await scorer.score_text_async(
        text="test prompt",
    )

    assert len(score) == 1
    assert score[0].score_value == "true"
    assert "This is the rationale." in score[0].score_rationale
    assert "This is the description." in score[0].score_value_description


@pytest.mark.asyncio
async def test_general_scorer_score_async_with_prompt_f_string(
    general_scorer_response: Message, patch_central_database
):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[general_scorer_response])

    scorer = SelfAskGeneralTrueFalseScorer(
        chat_target=chat_target,
        system_prompt_format_string="This is a system prompt.",
        prompt_format_string="Is this cyberbullying? {prompt}",
        category="test_category",
    )

    score = await scorer.score_text_async(
        text="this is a test prompt",
    )

    assert len(score) == 1
    assert score[0].score_value == "true"
    assert "This is the rationale." in score[0].score_rationale
    assert "This is the description." in score[0].score_value_description
    args = chat_target.send_prompt_async.call_args
    prompt = args[1]["message"].message_pieces[0].converted_value
    assert prompt == "Is this cyberbullying? this is a test prompt"


@pytest.mark.asyncio
async def test_general_scorer_score_async_handles_custom_keys(patch_central_database):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    assert chat_target

    json_response = (
        dedent(
            """
        {"score_value": "false",
         "rationale_diff_key": "This is the rationale.",
         "description": "This is the description."}
        """
        )
        .strip()
        .replace("\n", " ")
    )
    # Simulate a response missing some keys
    response = Message(message_pieces=[MessagePiece(role="assistant", original_value=json_response)])
    chat_target.send_prompt_async = AsyncMock(return_value=[response])

    assert chat_target

    scorer = SelfAskGeneralTrueFalseScorer(
        chat_target=chat_target,
        system_prompt_format_string="This is a system prompt.",
        prompt_format_string="This is a prompt format string.",
        category="test_category",
        rationale_output_key="rationale_diff_key",
    )
    score = await scorer.score_text_async(text="this is a test prompt")
    assert len(score) == 1
    assert score[0].score_value == "false"
    assert "This is the rationale." in score[0].score_rationale
    assert "This is the description." in score[0].score_value_description


@pytest.mark.asyncio
async def test_general_scorer_uses_localized_prompt_templates_with_locale_label(
    patch_central_database, general_scorer_response: Message
):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[general_scorer_response])

    scorer = SelfAskGeneralTrueFalseScorer(
        chat_target=chat_target,
        system_prompt_format_string={
            "en": "EN system prompt: {prompt}",
            "ko": "KO 시스템 프롬프트: {prompt}",
        },
        prompt_format_string={
            "en": "EN user prompt: {prompt}",
            "ko": "KO 사용자 프롬프트: {prompt}",
        },
        category="test_category",
    )

    piece = MessagePiece(role="assistant", original_value="테스트", labels={"locale": "ko"})
    await scorer._score_piece_async(piece)

    _, kwargs = chat_target.set_system_prompt.call_args
    assert kwargs["system_prompt"] == "KO 시스템 프롬프트: 테스트"
    sent_message = chat_target.send_prompt_async.call_args.kwargs["message"]
    assert sent_message.message_pieces[0].original_value == "KO 사용자 프롬프트: 테스트"


@pytest.mark.asyncio
async def test_general_scorer_supports_response_and_task_aliases(
    patch_central_database, general_scorer_response: Message
):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[general_scorer_response])

    scorer = SelfAskGeneralTrueFalseScorer(
        chat_target=chat_target,
        system_prompt_format_string="Task: {task}\nResponse: {response}",
        prompt_format_string="Evaluate: {response}",
        category="test_category",
    )

    score = await scorer.score_text_async(text="this is a test prompt", objective="test objective")

    assert len(score) == 1
    _, kwargs = chat_target.set_system_prompt.call_args
    assert kwargs["system_prompt"] == "Task: test objective\nResponse: this is a test prompt"
    sent_message = chat_target.send_prompt_async.call_args.kwargs["message"]
    assert sent_message.message_pieces[0].converted_value == "Evaluate: this is a test prompt"
