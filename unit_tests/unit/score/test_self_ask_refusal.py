# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import tempfile
from textwrap import dedent
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from unit.mocks import get_mock_target_identifier

from pyrit.exceptions.exception_classes import InvalidJsonException
from pyrit.memory import CentralMemory
from pyrit.memory.memory_interface import MemoryInterface
from pyrit.models import Message, MessagePiece
from pyrit.score import SelfAskRefusalScorer


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
async def test_refusal_scorer_score(scorer_true_false_response: Message, patch_central_database):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")

    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    score = await scorer.score_text_async("true false")

    assert len(score) == 1
    assert score[0].get_value() is True
    assert score[0].score_value_description == "This is true"
    assert score[0].score_rationale == "rationale for true"
    assert score[0].scorer_class_identifier.class_name == "SelfAskRefusalScorer"


@pytest.mark.asyncio
async def test_refusal_scorer_set_system_prompt(scorer_true_false_response: Message, patch_central_database):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    await scorer.score_text_async("true false")

    chat_target.set_system_prompt.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "locale, objective, expected_substring",
    [
        ("en", "task", "You are an evaluator tasked with determining if the AI response"),
        ("ko", "목표", "목표 `conversation_objective`를 완료하지 않겠다는 거절인지 판단하는 임무를 맡습니다."),
    ],
)
async def test_refusal_scorer_uses_locale_specific_system_prompt(
    scorer_true_false_response: Message,
    patch_central_database,
    locale: str,
    objective: str,
    expected_substring: str,
):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    piece = MessagePiece(role="assistant", original_value="test response", labels={"locale": locale})
    await scorer._score_piece_async(piece, objective=objective)

    _, kwargs = chat_target.set_system_prompt.call_args
    assert expected_substring in kwargs["system_prompt"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "locale, expected_substring",
    [
        ("en", "constitutes a refusal to complete the implied objective"),
        ("ko", "암묵적 목표를 완수하지 않겠다는 거절인지 판단하는 임무를 맡습니다."),
    ],
)
async def test_refusal_scorer_uses_locale_specific_system_prompt_without_objective(
    scorer_true_false_response: Message,
    patch_central_database,
    locale: str,
    expected_substring: str,
):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    piece = MessagePiece(role="assistant", original_value="test response", labels={"locale": locale})
    await scorer._score_piece_async(piece, objective=None)

    _, kwargs = chat_target.set_system_prompt.call_args
    assert expected_substring in kwargs["system_prompt"]


@pytest.mark.asyncio
async def test_refusal_scorer_falls_back_to_english_for_unsupported_locale(
    scorer_true_false_response: Message, patch_central_database
):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    piece = MessagePiece(role="assistant", original_value="réponse", labels={"locale": "fr"})
    await scorer._score_piece_async(piece, objective="task")

    _, kwargs = chat_target.set_system_prompt.call_args
    assert "You are an evaluator tasked with determining if the AI response" in kwargs["system_prompt"]


@pytest.mark.asyncio
async def test_refusal_scorer_korean_locale_uses_korean_scoring_labels(
    scorer_true_false_response: Message, patch_central_database
):
    """Test that locale='ko' uses Korean labels (대화_목표/평가_대상_응답) in the scoring prompt."""
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    piece = MessagePiece(role="assistant", original_value="거절합니다", labels={"locale": "ko"})
    await scorer._score_piece_async(piece, objective="해로운 작업")

    _, kwargs = chat_target.send_prompt_async.call_args
    sent_text = kwargs["message"].message_pieces[0].original_value
    assert "대화_목표: 해로운 작업" in sent_text
    assert "평가_대상_응답: 거절합니다" in sent_text


@pytest.mark.asyncio
async def test_refusal_scorer_korean_locale_without_objective(
    scorer_true_false_response: Message, patch_central_database
):
    """Test Korean locale without objective uses only response label."""
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    piece = MessagePiece(role="assistant", original_value="거절합니다", labels={"locale": "ko"})
    await scorer._score_piece_async(piece, objective=None)

    _, kwargs = chat_target.send_prompt_async.call_args
    sent_text = kwargs["message"].message_pieces[0].original_value
    assert sent_text == "평가_대상_응답: 거절합니다"


@pytest.mark.asyncio
async def test_refusal_scorer_no_task(scorer_true_false_response: Message, patch_central_database):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    await scorer.score_text_async("true false")

    _, kwargs = chat_target.send_prompt_async.call_args
    assert kwargs["message"].message_pieces[0].original_value == "response_to_evaluate_input: true false"


@pytest.mark.asyncio
async def test_refusal_scorer_with_task(scorer_true_false_response: Message, patch_central_database):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    await scorer.score_text_async("true false", objective="task")

    _, kwargs = chat_target.send_prompt_async.call_args

    expected = "conversation_objective: task\nresponse_to_evaluate_input: true false"
    assert kwargs["message"].message_pieces[0].original_value == expected


@pytest.mark.asyncio
async def test_refusal_scorer_image_non_block(scorer_true_false_response: Message, patch_central_database):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])

    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    with tempfile.NamedTemporaryFile(delete=True) as temp_image:
        result = await scorer.score_image_async(temp_image.name)
        assert result[0].get_value() is False

    # Any image doesn't need LLM evaluation, it just checks whether it was blocked
    chat_target.send_prompt_async.assert_not_called()


@pytest.mark.asyncio
async def test_refusal_scorer_adds_to_memory(scorer_true_false_response: Message):
    memory = MagicMock(MemoryInterface)
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    chat_target.send_prompt_async = AsyncMock(return_value=[scorer_true_false_response])
    with patch.object(CentralMemory, "get_memory_instance", return_value=memory):
        scorer = SelfAskRefusalScorer(chat_target=chat_target)
        await scorer.score_text_async(text="string")

        memory.add_scores_to_memory.assert_called_once()


@pytest.mark.asyncio
async def test_refusal_scorer_bad_json_exception_retries(patch_central_database):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")

    bad_json_resp = Message(message_pieces=[MessagePiece(role="assistant", original_value="this is not a json")])
    chat_target.send_prompt_async = AsyncMock(return_value=[bad_json_resp])
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    with pytest.raises(InvalidJsonException, match="Error in scorer SelfAskRefusalScorer"):
        await scorer.score_text_async("this has no bullying")

    # RETRY_MAX_NUM_ATTEMPTS is set to 2 in conftest.py
    assert chat_target.send_prompt_async.call_count == 2


@pytest.mark.asyncio
async def test_self_ask_objective_scorer_bad_json_exception_retries(patch_central_database):
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")

    json_response = (
        dedent(
            """
            {"bad_value_key": "True", "rationale": "rationale for true"}
            """
        )
        .strip()
        .replace("\n", " ")
    )

    bad_json_resp = Message(message_pieces=[MessagePiece(role="assistant", original_value=json_response)])

    chat_target.send_prompt_async = AsyncMock(return_value=[bad_json_resp])

    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    with pytest.raises(InvalidJsonException, match="Error in scorer SelfAskRefusalScorer"):
        await scorer.score_text_async("this has no bullying")

    # RETRY_MAX_NUM_ATTEMPTS is set to 2 in conftest.py
    assert chat_target.send_prompt_async.call_count == 2


@pytest.mark.asyncio
async def test_score_async_filtered_response(patch_central_database):
    memory = CentralMemory.get_memory_instance()
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    request = MessagePiece(role="assistant", original_value="blocked response", response_error="blocked").to_message()
    memory.add_message_pieces_to_memory(message_pieces=request.message_pieces)
    scores = await scorer.score_async(request)

    assert len(scores) == 1
    assert scores[0].score_value == "true"
    assert scores[0].score_value_description == "Refusal detected"
    assert scores[0].score_rationale == "Content was filtered, constituting a refusal."
    assert scores[0].scorer_class_identifier.class_name == "SelfAskRefusalScorer"


@pytest.mark.asyncio
async def test_score_async_filtered_response_korean_locale(patch_central_database):
    memory = CentralMemory.get_memory_instance()
    chat_target = MagicMock()
    chat_target.get_identifier.return_value = get_mock_target_identifier("MockChatTarget")
    scorer = SelfAskRefusalScorer(chat_target=chat_target)

    request = MessagePiece(
        role="assistant",
        original_value="차단된 응답",
        response_error="blocked",
        labels={"locale": "ko"},
    ).to_message()
    memory.add_message_pieces_to_memory(message_pieces=request.message_pieces)
    scores = await scorer.score_async(request)

    assert len(scores) == 1
    assert scores[0].score_value == "true"
    assert scores[0].score_value_description == "거절 감지됨"
    assert scores[0].score_rationale == "콘텐츠가 필터링되어 거절로 판단했습니다."
    assert scores[0].scorer_class_identifier.class_name == "SelfAskRefusalScorer"
