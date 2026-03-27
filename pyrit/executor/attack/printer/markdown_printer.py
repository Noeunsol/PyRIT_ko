# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
from datetime import datetime
from typing import List

from pyrit.executor.attack.printer.attack_result_printer import AttackResultPrinter
from pyrit.memory import CentralMemory
from pyrit.models import AttackResult, ConversationType, Message, MessagePiece, Score

_MD_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "attack_result": "Attack Result: {outcome}",
        "conversation_history": "Conversation History",
        "additional_metadata": "Additional Metadata",
        "report_generated": "Report generated at {timestamp}",
        "no_conversation_id": "No conversation ID available",
        "no_conversation_found": "No conversation found for ID: {conversation_id}",
        "system_message": "System Message",
        "turn": "Turn {turn_number}",
        "user": "User",
        "assistant_simulated": "Assistant (Simulated)",
        "original": "Original:",
        "converted": "Converted:",
        "error_response": "Error Response:",
        "error_type": "Error Type: {error}",
        "scores": "Scores",
        "score_type": "Score Type:",
        "score_value": "Value:",
        "score_category": "Category:",
        "score_rationale": "Rationale:",
        "score_metadata": "Metadata:",
        "attack_summary": "Attack Summary",
        "basic_info": "Basic Information",
        "field": "Field",
        "value_header": "Value",
        "objective": "Objective",
        "attack_type": "Attack Type",
        "conversation_id": "Conversation ID",
        "execution_metrics": "Execution Metrics",
        "metric": "Metric",
        "turns_executed": "Turns Executed",
        "execution_time": "Execution Time",
        "outcome_header": "Outcome",
        "status": "Status:",
        "reason": "Reason:",
        "final_score": "Final Score",
        "pruned_conversations": "Pruned Conversations ({count} total)",
        "pruned_showing": "Showing only the last message and score for each pruned branch.",
        "pruned_label": "🗑️ Pruned #{idx}",
        "no_messages_for_conv": "No messages found for conversation: `{conversation_id}`",
        "last_message": "Last Message ({role}):",
        "score_label": "Score:",
        "adversarial_conversation": "Adversarial Conversation (Red Team LLM)",
        "adversarial_description": "This shows the reasoning and strategy of the red teaming LLM.",
        "showing_best_branch": "📌 Showing best-scoring branch's adversarial conversation",
        "turn_user": "Turn {turn_number} - USER",
        "system_label": "SYSTEM",
    },
    "ko": {
        "attack_result": "공격 결과: {outcome}",
        "conversation_history": "대화 기록",
        "additional_metadata": "추가 메타데이터",
        "report_generated": "보고서 생성 시간 {timestamp}",
        "no_conversation_id": "대화 ID가 없습니다",
        "no_conversation_found": "ID에 해당하는 대화를 찾을 수 없습니다: {conversation_id}",
        "system_message": "시스템 메시지",
        "turn": "턴 {turn_number}",
        "user": "사용자",
        "assistant_simulated": "어시스턴트 (시뮬레이션)",
        "original": "원본:",
        "converted": "변환:",
        "error_response": "오류 응답:",
        "error_type": "오류 유형: {error}",
        "scores": "점수",
        "score_type": "점수 유형:",
        "score_value": "값:",
        "score_category": "카테고리:",
        "score_rationale": "근거:",
        "score_metadata": "메타데이터:",
        "attack_summary": "공격 요약",
        "basic_info": "기본 정보",
        "field": "항목",
        "value_header": "값",
        "objective": "목표",
        "attack_type": "공격 유형",
        "conversation_id": "대화 ID",
        "execution_metrics": "실행 지표",
        "metric": "지표",
        "turns_executed": "실행 턴 수",
        "execution_time": "실행 시간",
        "outcome_header": "결과",
        "status": "상태:",
        "reason": "사유:",
        "final_score": "최종 점수",
        "pruned_conversations": "가지치기된 대화 ({count}개)",
        "pruned_showing": "각 가지치기된 분기의 마지막 메시지와 점수만 표시합니다.",
        "pruned_label": "🗑️ 가지치기 #{idx}",
        "no_messages_for_conv": "대화 메시지를 찾을 수 없습니다: `{conversation_id}`",
        "last_message": "마지막 메시지 ({role}):",
        "score_label": "점수:",
        "adversarial_conversation": "적대적 대화 (레드팀 LLM)",
        "adversarial_description": "레드팀 LLM의 추론 및 전략을 보여줍니다.",
        "showing_best_branch": "📌 최고 점수 분기의 적대적 대화를 표시합니다",
        "turn_user": "턴 {turn_number} - 사용자",
        "system_label": "시스템",
    },
}


class MarkdownAttackResultPrinter(AttackResultPrinter):
    """
    Markdown printer for attack results optimized for Jupyter notebooks.

    This printer formats attack results as markdown, making them ideal for display
    in Jupyter notebooks where LLM responses often contain code blocks and other
    markdown formatting that should be properly rendered.
    """

    def __init__(self, *, display_inline: bool = True, locale: str = "en"):
        """
        Initialize the markdown printer.

        Args:
            display_inline (bool): If True, uses IPython.display to render markdown
                inline in Jupyter notebooks. If False, prints markdown strings.
                Defaults to True.
            locale (str): Locale for UI labels. Supports "en" and "ko". Defaults to "en".
        """
        self._memory = CentralMemory.get_memory_instance()
        self._display_inline = display_inline
        self._labels = _MD_LABELS.get(locale, _MD_LABELS["en"])

    def _render_markdown(self, markdown_lines: List[str]) -> None:
        """
        Render the markdown content using appropriate display method.

        Attempts to use IPython.display.Markdown for Jupyter notebook rendering
        when display_inline is True, falling back to print() if not available.

        Args:
            markdown_lines (List[str]): List of markdown strings to render.
        """
        full_markdown = "\n".join(markdown_lines)

        if self._display_inline:
            try:
                from IPython.display import Markdown, display

                display(Markdown(full_markdown))  # type: ignore[no-untyped-call]
            except (ImportError, NameError):
                # Fallback to print if IPython is not available
                print(full_markdown)
        else:
            print(full_markdown)

    def _format_score(self, score: Score, indent: str = "") -> str:
        """
        Format a score object as markdown with proper styling.

        Converts a Score object into formatted markdown text with appropriate
        emphasis and structure. Handles different score value types and includes
        rationale and metadata when available.

        Args:
            score (Score): The score object to format.
            indent (str): String prefix for indentation. Defaults to "".

        Returns:
            str: Formatted markdown representation of the score.
        """
        lines = []

        # Score value with appropriate formatting
        score_value = score.get_value()
        if isinstance(score_value, bool):
            value_str = str(score_value)
        elif isinstance(score_value, (int, float)):
            value_str = f"**{score_value:.2f}**" if isinstance(score_value, float) else f"**{score_value}**"
        else:
            value_str = f"**{score_value}**"

        lines.append(f"{indent}- **{self._labels['score_type']}** {score.score_type}")
        lines.append(f"{indent}- **{self._labels['score_value']}** {value_str}")
        category_str = ", ".join(score.score_category) if score.score_category else "N/A"
        lines.append(f"{indent}- **{self._labels['score_category']}** {category_str}")

        if score.score_rationale:
            # Handle multi-line rationale
            rationale_lines = score.score_rationale.split("\n")
            if len(rationale_lines) > 1:
                lines.append(f"{indent}- **{self._labels['score_rationale']}**")
                for line in rationale_lines:
                    lines.append(f"{indent}  {line}")
            else:
                lines.append(f"{indent}- **{self._labels['score_rationale']}** {score.score_rationale}")

        if score.score_metadata:
            lines.append(f"{indent}- **{self._labels['score_metadata']}** `{score.score_metadata}`")

        return "\n".join(lines)

    async def print_result_async(
        self,
        result: AttackResult,
        *,
        include_auxiliary_scores: bool = False,
        include_pruned_conversations: bool = False,
        include_adversarial_conversation: bool = False,
    ) -> None:
        """
        Print the complete attack result as formatted markdown.

        Generates a comprehensive markdown report including attack summary,
        conversation history, scores, and metadata. The output is optimized
        for display in Jupyter notebooks.

        Args:
            result (AttackResult): The attack result to print.
            include_auxiliary_scores (bool): Whether to include auxiliary scores
                in the conversation display. Defaults to False.
            include_pruned_conversations (bool): Whether to include pruned conversations.
                For each pruned conversation, only the last message and its score are shown.
                Defaults to False.
            include_adversarial_conversation (bool): Whether to include the adversarial
                conversation (the red teaming LLM's reasoning). Only shown for successful
                attacks to avoid overwhelming output. Defaults to False.
        """
        markdown_lines = []

        # Header with outcome
        outcome_emoji = self._get_outcome_icon(result.outcome)
        markdown_lines.append(f"# {outcome_emoji} {self._labels['attack_result'].format(outcome=result.outcome.value.upper())}\n")
        markdown_lines.append("---\n")

        # Summary section
        summary_lines = await self._get_summary_markdown_async(result)
        markdown_lines.extend(summary_lines)
        markdown_lines.append("---\n")

        # Conversation history
        markdown_lines.append(f"\n## {self._labels['conversation_history']}\n")
        conversation_lines = await self._get_conversation_markdown_async(
            result=result, include_scores=include_auxiliary_scores
        )
        markdown_lines.extend(conversation_lines)

        # Pruned conversations if requested
        if include_pruned_conversations:
            pruned_lines = await self._get_pruned_conversations_markdown_async(result)
            if pruned_lines:
                markdown_lines.extend(pruned_lines)

        # Adversarial conversation if requested (only for successful attacks)
        if include_adversarial_conversation:
            adversarial_lines = await self._get_adversarial_conversation_markdown_async(result)
            if adversarial_lines:
                markdown_lines.extend(adversarial_lines)

        # Metadata if available
        if result.metadata:
            markdown_lines.append(f"\n## {self._labels['additional_metadata']}\n")
            for key, value in result.metadata.items():
                # Only include metadata that can be converted to string
                try:
                    # Try to convert to string
                    str_value = str(value)
                    markdown_lines.append(f"- **{key}:** {str_value}")
                except Exception:
                    # Skip values that can't be stringified
                    pass

        # Footer
        markdown_lines.append("\n---")
        markdown_lines.append(f"*{self._labels['report_generated'].format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}*")

        self._render_markdown(markdown_lines)

    async def print_conversation_async(self, result: AttackResult, *, include_scores: bool = False) -> None:
        """
        Print only the conversation history as formatted markdown.

        Extracts and displays the conversation messages from the attack result
        without the summary or metadata sections. Useful for focusing on the
        actual interaction flow.

        Args:
            result (AttackResult): The attack result containing the conversation
                to display.
            include_scores (bool): Whether to include scores
                for each message. Defaults to False.
        """
        markdown_lines = await self._get_conversation_markdown_async(result=result, include_scores=include_scores)
        self._render_markdown(markdown_lines)

    async def print_summary_async(self, result: AttackResult) -> None:
        """
        Print a summary of the attack result as formatted markdown.

        Displays key information about the attack including objective, outcome,
        execution metrics, and final score without the full conversation history.
        Useful for getting a quick overview of the attack results.

        Args:
            result (AttackResult): The attack result to summarize.
        """
        markdown_lines = await self._get_summary_markdown_async(result)
        self._render_markdown(markdown_lines)

    async def _get_conversation_markdown_async(
        self, *, result: AttackResult, include_scores: bool = False
    ) -> List[str]:
        """
        Generate markdown lines for the conversation history.

        Retrieves conversation messages from memory and formats them as markdown,
        organizing by turns and message roles. Handles system messages, user
        inputs, and assistant responses with appropriate formatting.

        Args:
            result (AttackResult): The attack result containing the conversation ID.
            include_scores (bool): Whether to include scores
                for each message. Defaults to False.

        Returns:
            List[str]: List of markdown strings representing the formatted
                conversation history.
        """
        markdown_lines = []

        if not result.conversation_id:
            markdown_lines.append(f"*{self._labels['no_conversation_id']}*\n")
            return markdown_lines

        messages = self._memory.get_conversation(conversation_id=result.conversation_id)

        if not messages:
            markdown_lines.append(f"*{self._labels['no_conversation_found'].format(conversation_id=result.conversation_id)}*\n")
            return markdown_lines

        turn_number = 0

        for message in messages:
            if not message.message_pieces:
                continue

            message_role = message.get_piece().api_role

            if message_role == "system":
                markdown_lines.extend(self._format_system_message(message))
            elif message_role == "user":
                turn_number += 1
                markdown_lines.extend(await self._format_user_message_async(message=message, turn_number=turn_number))
            else:  # assistant or other response roles
                markdown_lines.extend(await self._format_assistant_message_async(message=message))

            # Add scores if requested
            if include_scores:
                markdown_lines.extend(self._format_message_scores(message))

        return markdown_lines

    def _format_system_message(self, message: Message) -> List[str]:
        """
        Format a system message as markdown.

        Creates markdown representation of system-level messages, typically
        containing instructions or context for the conversation.

        Args:
            message (Message): The system message to format.

        Returns:
            List[str]: List of markdown strings representing the system message.
        """
        lines = [f"\n### {self._labels['system_message']}\n"]
        for piece in message.message_pieces:
            lines.append(f"{piece.converted_value}\n")
        return lines

    async def _format_user_message_async(self, *, message: Message, turn_number: int) -> List[str]:
        """
        Format a user message as markdown with turn numbering.

        Creates markdown representation of user input messages, including turn
        numbers for easy conversation tracking. Shows both original and converted
        values when they differ.

        Args:
            message (Message): The user message to format.
            turn_number (int): The conversation turn number for this message.

        Returns:
            List[str]: List of markdown strings representing the user message.
        """
        lines = [f"\n### {self._labels['turn'].format(turn_number=turn_number)}\n", f"#### {self._labels['user']}\n"]

        for piece in message.message_pieces:
            lines.extend(await self._format_piece_content_async(piece=piece, show_original=True))

        return lines

    async def _format_assistant_message_async(self, *, message: Message) -> List[str]:
        """
        Format an assistant or system response message as markdown.

        Creates markdown representation of response messages from assistants
        or other system components. Automatically capitalizes the role name
        for display purposes.

        Args:
            message (Message): The response message to format.

        Returns:
            List[str]: List of markdown strings representing the response message.
        """
        lines = []
        piece = message.message_pieces[0]
        role_name = self._labels["assistant_simulated"] if piece.is_simulated else piece.api_role.capitalize()

        lines.append(f"\n#### {role_name}\n")

        for piece in message.message_pieces:
            lines.extend(await self._format_piece_content_async(piece=piece, show_original=False))

        return lines

    def _get_audio_mime_type(self, *, audio_path: str) -> str:
        """
        Determine the MIME type for an audio file based on its file extension.

        Args:
            audio_path (str): The path to the audio file.

        Returns:
            str: The appropriate MIME type for the audio file.
        """
        if audio_path.lower().endswith(".wav"):
            return "audio/wav"
        elif audio_path.lower().endswith(".ogg"):
            return "audio/ogg"
        elif audio_path.lower().endswith(".m4a"):
            return "audio/mp4"
        else:
            return "audio/mpeg"  # Default fallback for .mp3, .mpeg, and unknown formats

    def _format_image_content(self, *, image_path: str) -> List[str]:
        """
        Format image content as markdown.

        Args:
            image_path (str): The path to the image file.

        Returns:
            List[str]: List of markdown lines for the image.
        """
        relative_path = os.path.relpath(image_path)
        posix_path = relative_path.replace("\\", "/")
        return [f"![Image]({posix_path})\n"]

    def _format_audio_content(self, *, audio_path: str) -> List[str]:
        """
        Format audio content as HTML5 audio player.

        Args:
            audio_path (str): The path to the audio file.

        Returns:
            List[str]: List of markdown lines for the audio player.
        """
        lines = []
        lines.append("<audio controls>")

        audio_type = self._get_audio_mime_type(audio_path=audio_path)

        lines.append(f'<source src="{audio_path}" type="{audio_type}">')
        lines.append("Your browser does not support the audio element.")
        lines.append("</audio>\n")

        return lines

    def _format_error_content(self, *, piece: MessagePiece) -> List[str]:
        """
        Format error response content with proper styling.

        Args:
            piece (MessagePiece): The message piece containing the error.

        Returns:
            List[str]: List of markdown lines for the error response.
        """
        lines = []
        lines.append(f"**{self._labels['error_response']}**\n")
        lines.append(f"*{self._labels['error_type'].format(error=piece.response_error)}*\n")
        lines.append("```json")
        lines.append(piece.converted_value)
        lines.append("```\n")

        return lines

    def _format_text_content(self, *, piece: MessagePiece, show_original: bool) -> List[str]:
        """
        Format regular text content.

        Args:
            piece (MessagePiece): The message piece containing the text.
            show_original (bool): Whether to show original value if different.

        Returns:
            List[str]: List of markdown lines for the text content.
        """
        lines = []

        if show_original and piece.converted_value != piece.original_value:
            lines.append(f"**{self._labels['original']}**\n")
            lines.append(f"{piece.original_value}\n")
            lines.append(f"\n**{self._labels['converted']}**\n")

        lines.append(f"{piece.converted_value}\n")

        return lines

    async def _format_piece_content_async(self, *, piece: MessagePiece, show_original: bool) -> List[str]:
        """
        Format a single piece content based on its data type.

        Handles different content types including text, images, audio, and error responses.

        Args:
            piece (MessagePiece): The message piece to format.
            show_original (bool): Whether to show original value if different
                from converted value.

        Returns:
            List[str]: List of markdown lines representing this piece.
        """
        if piece.converted_value_data_type == "image_path":
            return self._format_image_content(image_path=piece.converted_value)
        elif piece.converted_value_data_type == "audio_path":
            return self._format_audio_content(audio_path=piece.converted_value)
        else:
            # Handle text content (including errors)
            if piece.has_error():
                return self._format_error_content(piece=piece)
            else:
                return self._format_text_content(piece=piece, show_original=show_original)

    def _format_message_scores(self, message: Message) -> List[str]:
        """
        Format scores for all pieces in a message as markdown.

        Retrieves and formats all scores associated with the message pieces
        in the given message. Creates a dedicated scores section with
        appropriate markdown formatting.

        Args:
            message (Message): The message containing pieces
                to format scores for.

        Returns:
            List[str]: List of markdown strings representing the scores.
        """
        lines = []
        for piece in message.message_pieces:
            scores = self._memory.get_prompt_scores(prompt_ids=[str(piece.id)])
            if scores:
                lines.append(f"\n##### {self._labels['scores']}\n")
                for score in scores:
                    lines.append(self._format_score(score, indent=""))
                lines.append("")
        return lines

    async def _get_summary_markdown_async(self, result: AttackResult) -> List[str]:
        """
        Generate markdown lines for the attack summary.

        Creates a comprehensive summary including basic information tables,
        execution metrics, outcome status, and final scores. Uses markdown
        tables for structured data presentation.

        Args:
            result (AttackResult): The attack result to summarize.

        Returns:
            List[str]: List of markdown strings representing the formatted summary.
        """
        markdown_lines = []
        markdown_lines.append(f"## {self._labels['attack_summary']}\n")

        # Basic Information Table
        markdown_lines.append(f"### {self._labels['basic_info']}\n")
        markdown_lines.append(f"| {self._labels['field']} | {self._labels['value_header']} |")
        markdown_lines.append("|-------|-------|")
        markdown_lines.append(f"| **{self._labels['objective']}** | {result.objective} |")

        attack_type = result.attack_identifier.get("__type__", "Unknown")

        markdown_lines.append(f"| **{self._labels['attack_type']}** | `{attack_type}` |")
        markdown_lines.append(f"| **{self._labels['conversation_id']}** | `{result.conversation_id}` |")

        # Execution Metrics
        markdown_lines.append(f"\n### {self._labels['execution_metrics']}\n")
        markdown_lines.append(f"| {self._labels['metric']} | {self._labels['value_header']} |")
        markdown_lines.append("|--------|-------|")
        markdown_lines.append(f"| **{self._labels['turns_executed']}** | {result.executed_turns} |")
        markdown_lines.append(f"| **{self._labels['execution_time']}** | {self._format_time(result.execution_time_ms)} |")

        # Outcome
        outcome_emoji = self._get_outcome_icon(result.outcome)
        markdown_lines.append(f"\n### {self._labels['outcome_header']}\n")
        markdown_lines.append(f"**{self._labels['status']}** {outcome_emoji} **{result.outcome.value.upper()}**\n")

        if result.outcome_reason:
            markdown_lines.append(f"**{self._labels['reason']}** {result.outcome_reason}\n")

        # Final Score
        if result.last_score:
            markdown_lines.append(f"\n### {self._labels['final_score']}\n")
            markdown_lines.append(self._format_score(result.last_score))

        return markdown_lines

    async def _get_pruned_conversations_markdown_async(self, result: AttackResult) -> List[str]:
        """
        Generate markdown lines for pruned conversations.

        For each pruned conversation, displays only the last message and its
        associated score to provide context without overwhelming output.

        Args:
            result (AttackResult): The attack result containing related conversations.

        Returns:
            List[str]: List of markdown strings for pruned conversations, or empty list if none.
        """
        pruned_refs = result.get_conversations_by_type(ConversationType.PRUNED)

        if not pruned_refs:
            return []

        markdown_lines = []
        markdown_lines.append(f"\n## {self._labels['pruned_conversations'].format(count=len(pruned_refs))}\n")
        markdown_lines.append(f"*{self._labels['pruned_showing']}*\n")

        for idx, ref in enumerate(pruned_refs, 1):
            # Header for this pruned conversation
            label = f"### {self._labels['pruned_label'].format(idx=idx)}"
            if ref.description:
                label += f" - {ref.description}"
            markdown_lines.append(f"\n{label}\n")

            # Get the conversation messages
            messages = list(self._memory.get_conversation(conversation_id=ref.conversation_id))

            if not messages:
                markdown_lines.append(f"*{self._labels['no_messages_for_conv'].format(conversation_id=ref.conversation_id)}*\n")
                continue

            # Get only the last message
            last_message = messages[-1]
            role_label = last_message.api_role.upper()

            markdown_lines.append(f"**{self._labels['last_message'].format(role=role_label)}**\n")

            for piece in last_message.message_pieces:
                # Format the message content
                content = piece.converted_value or ""
                if "\n" in content:
                    markdown_lines.append("```")
                    markdown_lines.append(content)
                    markdown_lines.append("```")
                else:
                    markdown_lines.append(f"> {content}\n")

                # Get and format associated scores
                scores = self._memory.get_prompt_scores(prompt_ids=[str(piece.id)])
                if scores:
                    markdown_lines.append(f"\n**{self._labels['score_label']}**\n")
                    for score in scores:
                        markdown_lines.append(self._format_score(score, indent=""))

        return markdown_lines

    async def _get_adversarial_conversation_markdown_async(self, result: AttackResult) -> List[str]:
        """
        Generate markdown lines for the adversarial conversation.

        The adversarial conversation shows the red teaming LLM's reasoning.
        For attacks with multiple adversarial conversations (e.g., TAP), only the
        best-scoring branch's adversarial conversation is shown if available.

        Args:
            result (AttackResult): The attack result containing related conversations.

        Returns:
            List[str]: List of markdown strings for the adversarial conversation, or empty list.
        """
        adversarial_refs = result.get_conversations_by_type(ConversationType.ADVERSARIAL)

        if not adversarial_refs:
            return []

        markdown_lines = []
        markdown_lines.append(f"\n## {self._labels['adversarial_conversation']}\n")
        markdown_lines.append(f"*{self._labels['adversarial_description']}*\n")

        # Check if result has a best_adversarial_conversation_id (e.g., TAP attack)
        # If so, only show that conversation instead of all adversarial conversations
        best_adversarial_id = result.metadata.get("best_adversarial_conversation_id")
        if best_adversarial_id:
            # Filter to only the best adversarial conversation
            adversarial_refs = [ref for ref in adversarial_refs if ref.conversation_id == best_adversarial_id]
            if adversarial_refs:
                markdown_lines.append(f"*{self._labels['showing_best_branch']}*\n")

        for ref in adversarial_refs:
            if ref.description:
                markdown_lines.append(f"*📝 {ref.description}*\n")

            messages = list(self._memory.get_conversation(conversation_id=ref.conversation_id))

            if not messages:
                markdown_lines.append(f"*{self._labels['no_messages_for_conv'].format(conversation_id=ref.conversation_id)}*\n")
                continue

            # Format each message in the adversarial conversation
            turn_number = 0
            for message in messages:
                if message.api_role == "user":
                    turn_number += 1
                    markdown_lines.append(f"\n#### {self._labels['turn_user'].format(turn_number=turn_number)}\n")
                elif message.api_role == "system":
                    markdown_lines.append(f"\n#### {self._labels['system_label']}\n")
                else:
                    markdown_lines.append(f"\n#### {message.api_role.upper()}\n")

                for piece in message.message_pieces:
                    content = piece.converted_value or ""
                    if len(content) > 200 or "\n" in content:
                        markdown_lines.append("```")
                        markdown_lines.append(content)
                        markdown_lines.append("```")
                    else:
                        markdown_lines.append(f"> {content}\n")

        return markdown_lines
