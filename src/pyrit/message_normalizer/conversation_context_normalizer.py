# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List, Optional

from pyrit.common.locale_utils import normalize_locale_value, resolve_locale_from_labels
from pyrit.message_normalizer.message_normalizer import MessageStringNormalizer
from pyrit.models import Message, MessagePiece


class ConversationContextNormalizer(MessageStringNormalizer):
    """
    Normalizer that formats conversation history as turn-based text.

    This is the standard format used by attacks like Crescendo and TAP
    for including conversation context in adversarial chat prompts.
    The output format is:

        Turn 1:
        User: <content>
        Assistant: <content>

        Turn 2:
        User: <content>
        ...
    """

    _LOCALIZED_LABELS = {
        "en": {
            "turn": "Turn {turn_number}:",
            "user": "User",
            "assistant": "Assistant",
            "original_suffix": " (original: {original})",
        },
        "ko": {
            "turn": "턴 {turn_number}:",
            "user": "사용자",
            "assistant": "어시스턴트",
            "original_suffix": " (원문: {original})",
        },
    }

    def __init__(self, *, locale: Optional[str] = None):
        """
        Initialize the normalizer.

        Args:
            locale: Optional locale override ("en" or "ko"). If not provided,
                locale is inferred from message labels and defaults to "en".
        """
        normalized_locale = normalize_locale_value(locale) if locale else ""
        self._locale = normalized_locale if normalized_locale in self._LOCALIZED_LABELS else None

    def _resolve_locale(self, messages: List[Message]) -> str:
        """Resolve locale from explicit override or first message-piece labels."""
        if self._locale:
            return self._locale

        for message in messages:
            for piece in message.message_pieces:
                if piece.labels:
                    return resolve_locale_from_labels(
                        labels=piece.labels,
                        supported_locales=self._LOCALIZED_LABELS,
                        default_locale="en",
                    )

        return "en"

    async def normalize_string_async(self, messages: List[Message]) -> str:
        """
        Normalize a list of messages into a turn-based context string.

        Args:
            messages: The list of Message objects to normalize.

        Returns:
            A formatted string with turn numbers and role prefixes.

        Raises:
            ValueError: If the messages list is empty.
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")

        locale = self._resolve_locale(messages)
        labels = self._LOCALIZED_LABELS[locale]
        context_parts: List[str] = []
        turn_number = 0

        for message in messages:
            for piece in message.message_pieces:
                # Skip system messages in context formatting
                if piece.api_role == "system":
                    continue

                # Start a new turn when we see a user message
                if piece.api_role == "user":
                    turn_number += 1
                    context_parts.append(labels["turn"].format(turn_number=turn_number))

                # Format the piece content
                content = self._format_piece_content(piece, locale=locale)
                role_label = labels["user"] if piece.api_role == "user" else labels["assistant"]
                context_parts.append(f"{role_label}: {content}")

        return "\n".join(context_parts)

    def _format_piece_content(self, piece: MessagePiece, *, locale: str = "en") -> str:
        """
        Format a single message piece into a content string.

        For text pieces, shows original and converted values (if different).
        For non-text pieces, uses context_description metadata or a placeholder.

        Args:
            piece: The message piece to format.

        Returns:
            The formatted content string.
        """
        data_type = piece.converted_value_data_type or piece.original_value_data_type

        # For non-text pieces, use metadata description or placeholder
        if data_type != "text":
            if piece.prompt_metadata and "context_description" in piece.prompt_metadata:
                description = piece.prompt_metadata["context_description"]
                return f"[{data_type.capitalize()} - {description}]"
            else:
                return f"[{data_type.capitalize()}]"

        # For text pieces, include both original and converted if different
        original = piece.original_value
        converted = piece.converted_value

        if original != converted:
            localized_suffix = self._LOCALIZED_LABELS.get(locale, self._LOCALIZED_LABELS["en"])["original_suffix"]
            return f"{converted}{localized_suffix.format(original=original)}"
        else:
            return converted
