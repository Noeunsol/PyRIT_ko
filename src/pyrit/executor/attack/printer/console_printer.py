# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import textwrap
import unicodedata
from datetime import datetime
from typing import Any

from colorama import Back, Fore, Style

from pyrit.common.display_response import display_image_response


def _east_asian_len(text: str) -> int:
    """Calculate display width accounting for East Asian wide characters."""
    width = 0
    for ch in text:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            width += 2
        else:
            width += 1
    return width


def _cjk_wrap(text: str, width: int) -> list[str]:
    """Simple CJK-aware word-wrap that splits on spaces and respects display width."""
    words = text.split(" ")
    lines: list[str] = []
    current_line = ""
    current_width = 0

    for word in words:
        word_width = _east_asian_len(word)
        if current_line:
            # +1 for the space between words
            if current_width + 1 + word_width <= width:
                current_line += " " + word
                current_width += 1 + word_width
            else:
                lines.append(current_line)
                current_line = word
                current_width = word_width
        else:
            current_line = word
            current_width = word_width

    if current_line:
        lines.append(current_line)

    return lines
from pyrit.executor.attack.printer.attack_result_printer import AttackResultPrinter
from pyrit.memory import CentralMemory
from pyrit.models import AttackOutcome, AttackResult, ConversationType, Score

_CONSOLE_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "turn_user": "🔹 Turn {turn_number} - USER",
        "system": "🔧 SYSTEM",
        "assistant_simulated": "ASSISTANT (SIMULATED)",
        "original": "Original:",
        "converted": "Converted:",
        "scores": "📊 Scores:",
        "score_label": "📊 Score:",
        "no_conversation_id": "No conversation ID available",
        "no_conversation_found": "No conversation found for ID: {conversation_id}",
        "no_messages": "No messages to display.",
        "attack_result": "ATTACK RESULT: {outcome}",
        "report_generated": "Report generated at: {timestamp}",
        "basic_info": "📋 Basic Information",
        "objective": "• Objective: {objective}",
        "attack_type": "• Attack Type: {attack_type}",
        "conversation_id": "• Conversation ID: {conversation_id}",
        "execution_metrics": "⚡ Execution Metrics",
        "turns_executed": "• Turns Executed: {turns}",
        "execution_time": "• Execution Time: {time}",
        "outcome_header": "🎯 Outcome",
        "status": "• Status: {icon} {outcome}",
        "reason": "• Reason: {reason}",
        "final_score": " Final Score",
        "scorer": "Scorer: {name}",
        "category": "• Category: {category}",
        "type": "• Type: {type}",
        "value": "• Value: {value}",
        "rationale": "• Rationale:",
        "additional_metadata": "Additional Metadata",
        "conversation_history": "Conversation History with Objective Target",
        "attack_summary": "Attack Summary",
        "pruned_conversations": "Pruned Conversations ({count} total)",
        "pruned_label": "🗑️ PRUNED #{idx}",
        "no_messages_for_conv": "No messages found for conversation: {conversation_id}",
        "last_message": "Last Message ({role}):",
        "adversarial_conversation": "Adversarial Conversation (Red Team LLM)",
        "showing_best_branch": "📌 Showing best-scoring branch's adversarial conversation",
    },
    "ko": {
        "turn_user": "🔹 턴 {turn_number} - 사용자",
        "system": "🔧 시스템",
        "assistant_simulated": "어시스턴트 (시뮬레이션)",
        "original": "원본:",
        "converted": "변환:",
        "scores": "📊 점수:",
        "score_label": "📊 점수:",
        "no_conversation_id": "대화 ID가 없습니다",
        "no_conversation_found": "ID에 해당하는 대화를 찾을 수 없습니다: {conversation_id}",
        "no_messages": "표시할 메시지가 없습니다.",
        "attack_result": "공격 결과: {outcome}",
        "report_generated": "보고서 생성 시간: {timestamp}",
        "basic_info": "📋 기본 정보",
        "objective": "• 목표: {objective}",
        "attack_type": "• 공격 유형: {attack_type}",
        "conversation_id": "• 대화 ID: {conversation_id}",
        "execution_metrics": "⚡ 실행 지표",
        "turns_executed": "• 실행 턴 수: {turns}",
        "execution_time": "• 실행 시간: {time}",
        "outcome_header": "🎯 결과",
        "status": "• 상태: {icon} {outcome}",
        "reason": "• 사유: {reason}",
        "final_score": " 최종 점수",
        "scorer": "스코어러: {name}",
        "category": "• 카테고리: {category}",
        "type": "• 유형: {type}",
        "value": "• 값: {value}",
        "rationale": "• 근거:",
        "additional_metadata": "추가 메타데이터",
        "conversation_history": "목표 대상과의 대화 기록",
        "attack_summary": "공격 요약",
        "pruned_conversations": "가지치기된 대화 ({count}개)",
        "pruned_label": "🗑️ 가지치기 #{idx}",
        "no_messages_for_conv": "대화 메시지를 찾을 수 없습니다: {conversation_id}",
        "last_message": "마지막 메시지 ({role}):",
        "adversarial_conversation": "적대적 대화 (레드팀 LLM)",
        "showing_best_branch": "📌 최고 점수 분기의 적대적 대화를 표시합니다",
    },
}


class ConsoleAttackResultPrinter(AttackResultPrinter):
    """
    Console printer for attack results with enhanced formatting.

    This printer formats attack results for console display with optional color coding,
    proper indentation, text wrapping, and visual separators. Colors can be disabled
    for consoles that don't support ANSI characters.
    """

    def __init__(self, *, width: int = 100, indent_size: int = 2, enable_colors: bool = True, locale: str = "en"):
        """
        Initialize the console printer.

        Args:
            width (int): Maximum width for text wrapping. Must be positive.
                Defaults to 100.
            indent_size (int): Number of spaces for indentation. Must be non-negative.
                Defaults to 2.
            enable_colors (bool): Whether to enable ANSI color output. When False,
                all output will be plain text without colors. Defaults to True.
            locale (str): Locale for UI labels. Supports "en" and "ko". Defaults to "en".

        Raises:
            ValueError: If width <= 0 or indent_size < 0.
        """
        self._memory = CentralMemory.get_memory_instance()
        self._width = width
        self._indent = " " * indent_size
        self._enable_colors = enable_colors
        self._labels = _CONSOLE_LABELS.get(locale, _CONSOLE_LABELS["en"])

    def _print_colored(self, text: str, *colors: str) -> None:
        """
        Print text with color formatting if colors are enabled.

        Args:
            text (str): The text to print.
            *colors: Variable number of colorama color constants to apply.
        """
        if self._enable_colors and colors:
            color_prefix = "".join(colors)
            print(f"{color_prefix}{text}{Style.RESET_ALL}")
        else:
            print(text)

    async def print_result_async(
        self,
        result: AttackResult,
        *,
        include_auxiliary_scores: bool = False,
        include_pruned_conversations: bool = False,
        include_adversarial_conversation: bool = False,
    ) -> None:
        """
        Print the complete attack result to console.

        This method orchestrates the printing of all components of an attack result,
        including header, summary, conversation history, metadata, and footer.

        Args:
            result (AttackResult): The attack result to print. Must not be None.
            include_auxiliary_scores (bool): Whether to include auxiliary scores in the output.
                Defaults to False.
            include_pruned_conversations (bool): Whether to include pruned conversations.
                For each pruned conversation, only the last message and its score are shown.
                Defaults to False.
            include_adversarial_conversation (bool): Whether to include the adversarial
                conversation (the red teaming LLM's reasoning). Only shown for successful
                attacks to avoid overwhelming output. Defaults to False.
        """
        # Print header with outcome
        self._print_header(result)

        # Print summary information
        await self.print_summary_async(result)

        # Print conversation
        self._print_section_header(self._labels["conversation_history"])
        await self.print_conversation_async(result, include_scores=include_auxiliary_scores)

        # Print pruned conversations if requested
        if include_pruned_conversations:
            await self._print_pruned_conversations_async(result)

        # Print adversarial conversation if requested (only for successful attacks)
        if include_adversarial_conversation:
            await self._print_adversarial_conversation_async(result)

        # Print metadata if available
        if result.metadata:
            self._print_metadata(result.metadata)

        # Print footer
        self._print_footer()

    async def print_conversation_async(
        self, result: AttackResult, *, include_scores: bool = False, include_reasoning_trace: bool = False
    ) -> None:
        """
        Print the conversation history to console with enhanced formatting.

        Displays the full conversation between user and assistant, including:
        - Turn numbers
        - Role indicators (USER/ASSISTANT)
        - Original and converted values when different
        - Images if present
        - Scores for each response

        Args:
            result (AttackResult): The attack result containing the conversation_id.
                Must have a valid conversation_id attribute.
            include_scores (bool): Whether to include scores in the output.
                Defaults to False.
            include_reasoning_trace (bool): Whether to include model reasoning trace in the output
                for applicable models. Defaults to False.
        """
        if not result.conversation_id:
            self._print_colored(f"{self._indent} {self._labels['no_conversation_id']}", Fore.YELLOW)
            return

        messages = list(self._memory.get_conversation(conversation_id=result.conversation_id))

        if not messages:
            self._print_colored(f"{self._indent} {self._labels['no_conversation_found'].format(conversation_id=result.conversation_id)}", Fore.YELLOW)
            return

        await self.print_messages_async(
            messages=messages,
            include_scores=include_scores,
            include_reasoning_trace=include_reasoning_trace,
        )

    async def print_messages_async(
        self,
        messages: list[Any],
        *,
        include_scores: bool = False,
        include_reasoning_trace: bool = False,
    ) -> None:
        """
        Print a list of messages to console with enhanced formatting.

        This method can be called directly with a list of Message objects,
        without needing an AttackResult. Useful for printing prepended_conversation
        or any other list of messages.

        Displays:
        - Turn numbers
        - Role indicators (USER/ASSISTANT/SYSTEM)
        - Original and converted values when different
        - Images if present
        - Scores for each response (if include_scores=True)

        Args:
            messages (list): List of Message objects to print.
            include_scores (bool): Whether to include scores in the output.
                Defaults to False.
            include_reasoning_trace (bool): Whether to include model reasoning trace in the output
                for applicable models. Defaults to False.
        """
        if not messages:
            self._print_colored(f"{self._indent} {self._labels['no_messages']}", Fore.YELLOW)
            return

        turn_number = 0
        for message in messages:
            # Increment turn number once per message with role="user"
            if message.api_role == "user":
                turn_number += 1
                # User message header
                print()
                self._print_colored("─" * self._width, Fore.BLUE)
                self._print_colored(self._labels["turn_user"].format(turn_number=turn_number), Style.BRIGHT, Fore.BLUE)
                self._print_colored("─" * self._width, Fore.BLUE)
            elif message.api_role == "system":
                # System message header (not counted as a turn)
                print()
                self._print_colored("─" * self._width, Fore.MAGENTA)
                self._print_colored(self._labels["system"], Style.BRIGHT, Fore.MAGENTA)
                self._print_colored("─" * self._width, Fore.MAGENTA)
            else:
                # Assistant or other role message header
                print()
                self._print_colored("─" * self._width, Fore.YELLOW)
                role_label = self._labels["assistant_simulated"] if message.is_simulated else message.api_role.upper()
                self._print_colored(f"🔸 {role_label}", Style.BRIGHT, Fore.YELLOW)
                self._print_colored("─" * self._width, Fore.YELLOW)

            # Now print all pieces in this message
            for piece in message.message_pieces:
                # Skip reasoning traces unless explicitly requested
                if piece.original_value_data_type == "reasoning" and not include_reasoning_trace:
                    continue

                # Handle converted values for user and assistant messages
                if piece.converted_value != piece.original_value:
                    self._print_colored(f"{self._indent} {self._labels['original']}", Fore.CYAN)
                    self._print_wrapped_text(piece.original_value, Fore.WHITE)
                    print()
                    self._print_colored(f"{self._indent} {self._labels['converted']}", Fore.CYAN)
                    self._print_wrapped_text(piece.converted_value, Fore.WHITE)
                elif piece.api_role == "user":
                    self._print_wrapped_text(piece.converted_value, Fore.BLUE)
                elif piece.api_role == "system":
                    self._print_wrapped_text(piece.converted_value, Fore.MAGENTA)
                else:
                    self._print_wrapped_text(piece.converted_value, Fore.YELLOW)

                # Display images if present
                await display_image_response(piece)

                # Print scores with better formatting (only if scores are requested)
                if include_scores:
                    scores = self._memory.get_prompt_scores(prompt_ids=[str(piece.id)])
                    if scores:
                        print()
                        self._print_colored(f"{self._indent}{self._labels['scores']}", Style.DIM, Fore.MAGENTA)
                        for score in scores:
                            self._print_score(score)

        print()
        self._print_colored("─" * self._width, Fore.BLUE)

    async def print_summary_async(self, result: AttackResult) -> None:
        """
        Print a summary of the attack result with enhanced formatting.

        Displays:
        - Basic information (objective, attack type, conversation ID)
        - Execution metrics (turns executed, execution time)
        - Outcome information (status, reason)
        - Final score if available

        Args:
            result (AttackResult): The attack result to summarize. Must contain
                objective, attack_identifier, conversation_id, executed_turns,
                execution_time_ms, outcome, and optionally outcome_reason and
                last_score attributes.
        """
        self._print_section_header(self._labels["attack_summary"])

        # Basic information
        self._print_colored(f"{self._indent}{self._labels['basic_info']}", Style.BRIGHT)
        self._print_colored(f"{self._indent * 2}{self._labels['objective'].format(objective=result.objective)}", Fore.CYAN)

        # Extract attack type name from attack_identifier
        attack_type = "Unknown"
        if isinstance(result.attack_identifier, dict) and "__type__" in result.attack_identifier:
            attack_type = result.attack_identifier["__type__"]
        elif isinstance(result.attack_identifier, str):
            attack_type = result.attack_identifier

        self._print_colored(f"{self._indent * 2}{self._labels['attack_type'].format(attack_type=attack_type)}", Fore.CYAN)
        self._print_colored(f"{self._indent * 2}{self._labels['conversation_id'].format(conversation_id=result.conversation_id)}", Fore.CYAN)

        # Execution metrics
        print()
        self._print_colored(f"{self._indent}{self._labels['execution_metrics']}", Style.BRIGHT)
        self._print_colored(f"{self._indent * 2}{self._labels['turns_executed'].format(turns=result.executed_turns)}", Fore.GREEN)
        self._print_colored(
            f"{self._indent * 2}{self._labels['execution_time'].format(time=self._format_time(result.execution_time_ms))}", Fore.GREEN
        )

        # Outcome information
        print()
        self._print_colored(f"{self._indent}{self._labels['outcome_header']}", Style.BRIGHT)
        outcome_icon = self._get_outcome_icon(result.outcome)
        outcome_color = self._get_outcome_color(result.outcome)
        self._print_colored(f"{self._indent * 2}{self._labels['status'].format(icon=outcome_icon, outcome=result.outcome.value.upper())}", outcome_color)

        if result.outcome_reason:
            self._print_colored(f"{self._indent * 2}{self._labels['reason'].format(reason=result.outcome_reason)}", Fore.WHITE)

        # Final score
        if result.last_score:
            print()
            self._print_colored(f"{self._indent}{self._labels['final_score']}", Style.BRIGHT)
            self._print_score(result.last_score, indent_level=2)

    def _print_header(self, result: AttackResult) -> None:
        """
        Print the header with outcome-based coloring and styling.

        Creates a visually prominent header that displays the attack outcome
        with appropriate color coding and icons.

        Args:
            result (AttackResult): The attack result containing the outcome.
                Must have an outcome attribute of type AttackOutcome.
        """
        color = self._get_outcome_color(result.outcome)
        icon = self._get_outcome_icon(result.outcome)

        print()
        self._print_colored("═" * self._width, color)

        # Center the header text
        header_text = f"{icon} {self._labels['attack_result'].format(outcome=result.outcome.value.upper())} {icon}"
        self._print_colored(header_text.center(self._width), Style.BRIGHT, color)
        self._print_colored("═" * self._width, color)

    def _print_footer(self) -> None:
        """
        Print a footer with timestamp.

        Displays the current timestamp when the report was generated.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print()
        self._print_colored("─" * self._width, Style.DIM, Fore.WHITE)
        footer_text = self._labels["report_generated"].format(timestamp=timestamp)
        self._print_colored(footer_text.center(self._width), Style.DIM, Fore.WHITE)

    def _print_section_header(self, title: str) -> None:
        """
        Print a section header with consistent styling.

        Creates a visually distinct section header with background color
        and separator line.

        Args:
            title (str): The title text to display in the section header.
        """
        print()
        self._print_colored(f" {title} ", Style.BRIGHT, Back.BLUE, Fore.WHITE)
        self._print_colored("─" * self._width, Fore.BLUE)

    def _print_metadata(self, metadata: dict[str, Any]) -> None:
        """
        Print metadata in a formatted way.

        Displays key-value pairs from the metadata dictionary in a
        consistent bullet-point format.

        Args:
            metadata (dict[str, Any]): Dictionary containing metadata key-value pairs.
                Keys and values should be convertible to strings.
        """
        self._print_section_header(self._labels["additional_metadata"])
        for key, value in metadata.items():
            self._print_colored(f"{self._indent}• {key}: {value}", Fore.CYAN)

    def _print_score(self, score: Score, indent_level: int = 3) -> None:
        """
        Print a score with proper formatting.

        Displays score information including type, value, and rationale
        with appropriate color coding based on score type.

        Args:
            score (Score): Score object to be printed.
            indent_level (int): Number of indent units to apply. Defaults to 3.
        """
        indent = self._indent * indent_level
        scorer_name = score.scorer_class_identifier.class_name
        print(f"{indent}{self._labels['scorer'].format(name=scorer_name)}")
        self._print_colored(f"{indent}{self._labels['category'].format(category=score.score_category or 'N/A')}", Fore.LIGHTMAGENTA_EX)
        self._print_colored(f"{indent}{self._labels['type'].format(type=score.score_type)}", Fore.CYAN)

        # Determine color based on score type and value
        if score.score_type == "true_false":
            score_color = Fore.GREEN if score.get_value() else Fore.RED
        else:
            score_color = Fore.YELLOW

        self._print_colored(f"{indent}{self._labels['value'].format(value=score.score_value)}", score_color)

        if score.score_rationale:
            print(f"{indent}{self._labels['rationale']}")
            # Create a custom wrapper for rationale with proper indentation
            rationale_width = self._width - _east_asian_len(indent) - 2
            rationale_indent = indent + "  "
            # Split by newlines first to preserve them
            lines = score.score_rationale.split("\n")
            for line in lines:
                if line.strip():
                    wrapped_lines = _cjk_wrap(line, rationale_width)
                    for wrapped_line in wrapped_lines:
                        self._print_colored(f"{rationale_indent}{wrapped_line}", Fore.WHITE)
                else:
                    self._print_colored(f"{rationale_indent}")

    def _print_wrapped_text(self, text: str, color: str) -> None:
        """
        Print text with proper wrapping and indentation, preserving newlines.

        Wraps long lines while preserving the original line breaks and
        applying consistent indentation and coloring.

        Args:
            text (str): The text to print. Can contain newlines.
            color (str): Colorama color constant to apply to the text
                (e.g., Fore.BLUE, Fore.RED).
        """
        wrap_width = self._width - _east_asian_len(self._indent)

        # Split by newlines first to preserve them
        lines = text.split("\n")
        for line_num, line in enumerate(lines):
            if line.strip():
                wrapped_lines = _cjk_wrap(line, wrap_width)
                for i, wrapped_line in enumerate(wrapped_lines):
                    if line_num == 0 and i == 0:
                        self._print_colored(f"{self._indent}{wrapped_line}", color)
                    else:
                        self._print_colored(f"{self._indent * 2}{wrapped_line}", color)
            else:
                self._print_colored(f"{self._indent}", color)

    async def _print_pruned_conversations_async(self, result: AttackResult) -> None:
        """
        Print pruned conversations showing only the last message and score for each.

        Pruned conversations represent branches that were abandoned during the attack.
        For each pruned conversation, only the final message and its associated score
        are displayed to provide context without overwhelming output.

        Args:
            result (AttackResult): The attack result containing related conversations.
        """
        pruned_refs = result.get_conversations_by_type(ConversationType.PRUNED)

        if not pruned_refs:
            return

        self._print_section_header(self._labels["pruned_conversations"].format(count=len(pruned_refs)))

        for idx, ref in enumerate(pruned_refs, 1):
            # Print conversation header with description if available
            print()
            self._print_colored("─" * self._width, Fore.RED)
            label = self._labels["pruned_label"].format(idx=idx)
            if ref.description:
                label += f" - {ref.description}"
            self._print_colored(label, Style.BRIGHT, Fore.RED)
            self._print_colored("─" * self._width, Fore.RED)

            # Get the conversation messages
            messages = list(self._memory.get_conversation(conversation_id=ref.conversation_id))

            if not messages:
                self._print_colored(
                    f"{self._indent}{self._labels['no_messages_for_conv'].format(conversation_id=ref.conversation_id)}", Fore.YELLOW
                )
                continue

            # Get only the last message
            last_message = messages[-1]

            # Print the last message
            role_label = last_message.api_role.upper()
            self._print_colored(f"{self._indent}{self._labels['last_message'].format(role=role_label)}", Style.BRIGHT, Fore.WHITE)

            for piece in last_message.message_pieces:
                self._print_wrapped_text(piece.converted_value, Fore.WHITE)

                # Print associated scores
                scores = self._memory.get_prompt_scores(prompt_ids=[str(piece.id)])
                if scores:
                    print()
                    self._print_colored(f"{self._indent}{self._labels['score_label']}", Style.DIM, Fore.MAGENTA)
                    for score in scores:
                        self._print_score(score)

        print()
        self._print_colored("─" * self._width, Fore.RED)

    async def _print_adversarial_conversation_async(self, result: AttackResult) -> None:
        """
        Print the adversarial conversation for the best-scoring attack branch.

        The adversarial conversation shows the red teaming LLM's reasoning and
        strategy development. For attacks with multiple adversarial conversations
        (e.g., TAP), only the best-scoring branch's adversarial conversation is
        shown if available.

        Args:
            result (AttackResult): The attack result containing related conversations.
        """
        adversarial_refs = result.get_conversations_by_type(ConversationType.ADVERSARIAL)

        if not adversarial_refs:
            return

        self._print_section_header(self._labels["adversarial_conversation"])

        # Check if result has a best_adversarial_conversation_id (e.g., TAP attack)
        # If so, only show that conversation instead of all adversarial conversations
        best_adversarial_id = result.metadata.get("best_adversarial_conversation_id")
        if best_adversarial_id:
            # Filter to only the best adversarial conversation
            adversarial_refs = [ref for ref in adversarial_refs if ref.conversation_id == best_adversarial_id]
            if adversarial_refs:
                self._print_colored(
                    f"{self._indent}{self._labels['showing_best_branch']}",
                    Style.DIM,
                    Fore.CYAN,
                )

        for ref in adversarial_refs:
            if ref.description:
                self._print_colored(f"{self._indent}📝 {ref.description}", Style.DIM, Fore.CYAN)

            messages = list(self._memory.get_conversation(conversation_id=ref.conversation_id))

            if not messages:
                self._print_colored(
                    f"{self._indent}{self._labels['no_messages_for_conv'].format(conversation_id=ref.conversation_id)}", Fore.YELLOW
                )
                continue

            await self.print_messages_async(messages=messages, include_scores=False)

    def _get_outcome_color(self, outcome: AttackOutcome) -> str:
        """
        Get the color for an outcome.

        Maps AttackOutcome enum values to appropriate Colorama color constants.

        Args:
            outcome (AttackOutcome): The attack outcome enum value.

        Returns:
            str: Colorama color constant (Fore.GREEN, Fore.RED, Fore.YELLOW,
                or Fore.WHITE for unknown outcomes).
        """
        return str(
            {
                AttackOutcome.SUCCESS: Fore.GREEN,
                AttackOutcome.FAILURE: Fore.RED,
                AttackOutcome.UNDETERMINED: Fore.YELLOW,
            }.get(outcome, Fore.WHITE)
        )
