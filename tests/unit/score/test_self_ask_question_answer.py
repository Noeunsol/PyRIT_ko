# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from textwrap import dedent
from unittest.mock import AsyncMock, MagicMock

import pytest
from unit.mocks import get_mock_target_identifier

from pyrit.models import Message, MessagePiece
from pyrit.score import SelfAskQuestionAnswerScorer


@pytest.fixture
def scorer_true_false_response() -> Message:
    json_response = (
        dedent(
            """
        {"score_value": "True", "description": "This is true", "rationale": "rationale for true"}
        """
        )
        .strip()
        .replace("\n", " ")
    )

    return Message(message_pieces=[MessagePiece(role="assistant", original_value=json_response)])


@pytest.mark.asyncio
async def test_self_ask_question_answer_uses_korean_system_prompt_and_question_asset(
    patch_central_database, scorer_true_false_response: Message
):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])

    scorer = SelfAskQuestionAnswerScorer(chat_target=chat_target)
    piece = MessagePiece(role="assistant", original_value="정답은 파리입니다.", labels={"locale": "ko"})

    await scorer._score_piece_async(piece, objective="질문: 프랑스 수도는?")

    _, kwargs = chat_target.set_system_prompt.call_args
    assert "메시지 응답이 질문에 대한 정답이다." in kwargs["system_prompt"]


@pytest.mark.asyncio
async def test_self_ask_question_answer_uses_korean_user_prompt_with_target_lang_alias(
    patch_central_database, scorer_true_false_response: Message
):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])

    scorer = SelfAskQuestionAnswerScorer(chat_target=chat_target)
    piece = MessagePiece(role="assistant", original_value="정답은 파리입니다.", labels={"target_lang": "ko-KR"})

    await scorer._score_piece_async(piece, objective="질문: 프랑스 수도는?")

    args = chat_target.send_prompt_async.call_args
    prompt = args.kwargs["message"].message_pieces[0].converted_value
    assert "응답이 정답인지 평가하세요" in prompt
