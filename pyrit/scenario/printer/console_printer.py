# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import textwrap
from typing import Optional

from colorama import Fore, Style

from pyrit.models.scenario_result import ScenarioResult
from pyrit.scenario.printer.scenario_result_printer import ScenarioResultPrinter
from pyrit.score.printer import ConsoleScorerPrinter, ScorerPrinter

_SCENARIO_PRINTER_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "header": "SCENARIO RESULTS: {name}",
        "scenario_info": "Scenario Information",
        "scenario_details": "Scenario Details",
        "name": "Name: {name}",
        "version": "Scenario Version: {version}",
        "pyrit_version": "PyRIT Version: {version}",
        "description": "Description:",
        "target_info": "Target Information",
        "target_type": "Target Type: {type}",
        "target_model": "Target Model: {model}",
        "target_endpoint": "Target Endpoint: {endpoint}",
        "overall_stats": "Overall Statistics",
        "summary": "Summary",
        "total_strategies": "Total Strategies: {count}",
        "total_results": "Total Attack Results: {count}",
        "overall_rate": "Overall Success Rate: {rate}%",
        "unique_objectives": "Unique Objectives: {count}",
        "per_strategy": "Per-Strategy Breakdown",
        "strategy": "Strategy: {name}",
        "num_results": "Number of Results: {count}",
        "success_rate": "Success Rate: {rate}%",
    },
    "ko": {
        "header": "시나리오 결과: {name}",
        "scenario_info": "시나리오 정보",
        "scenario_details": "시나리오 상세",
        "name": "이름: {name}",
        "version": "시나리오 버전: {version}",
        "pyrit_version": "PyRIT 버전: {version}",
        "description": "설명:",
        "target_info": "타겟 정보",
        "target_type": "타겟 유형: {type}",
        "target_model": "타겟 모델: {model}",
        "target_endpoint": "타겟 엔드포인트: {endpoint}",
        "overall_stats": "전체 통계",
        "summary": "요약",
        "total_strategies": "전체 전략: {count}개",
        "total_results": "전체 공격 결과: {count}개",
        "overall_rate": "전체 성공률: {rate}%",
        "unique_objectives": "고유 목표: {count}개",
        "per_strategy": "전략별 상세",
        "strategy": "전략: {name}",
        "num_results": "결과 수: {count}개",
        "success_rate": "성공률: {rate}%",
    },
}


class ConsoleScenarioResultPrinter(ScenarioResultPrinter):
    """
    Console printer for scenario results with enhanced formatting.

    This printer formats scenario results for console display with optional color coding,
    proper indentation, and visual separators. Colors can be disabled for consoles
    that don't support ANSI characters.
    """

    def __init__(
        self,
        *,
        width: int = 100,
        indent_size: int = 2,
        enable_colors: bool = True,
        scorer_printer: Optional[ScorerPrinter] = None,
        locale: str = "en",
    ):
        """
        Initialize the console printer.

        Args:
            width (int): Maximum width for text wrapping. Must be positive.
                Defaults to 100.
            indent_size (int): Number of spaces for indentation. Must be non-negative.
                Defaults to 2.
            enable_colors (bool): Whether to enable ANSI color output. When False,
                all output will be plain text without colors. Defaults to True.
            scorer_printer (Optional[ScorerPrinter]): Printer for scorer information.
                If not provided, a ConsoleScorerPrinter with matching settings is created.

        Raises:
            ValueError: If width <= 0 or indent_size < 0.
        """
        self._width = width
        self._indent = " " * indent_size
        self._enable_colors = enable_colors
        self._locale = locale if locale in ("en", "ko") else "en"
        self._labels = _SCENARIO_PRINTER_LABELS.get(self._locale, _SCENARIO_PRINTER_LABELS["en"])
        self._scorer_printer = scorer_printer or ConsoleScorerPrinter(
            indent_size=indent_size, enable_colors=enable_colors, locale=self._locale
        )

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

    def _print_section_header(self, title: str) -> None:
        """
        Print a section header with visual separation.

        Args:
            title (str): The section title to display.
        """
        print()
        self._print_colored(f"▼ {title}", Style.BRIGHT, Fore.CYAN)
        self._print_colored("─" * self._width, Fore.CYAN)

    async def print_summary_async(self, result: ScenarioResult) -> None:
        """
        Print a summary of the scenario result with per-strategy breakdown.

        Displays:
        - Scenario identification (name, version, PyRIT version)
        - Target and scorer information
        - Overall statistics
        - Per-strategy success rates and result counts

        Args:
            result (ScenarioResult): The scenario result to summarize
        """
        # Print header
        self._print_header(result)

        # Scenario information
        self._print_section_header(self._labels["scenario_info"])
        self._print_colored(f"{self._indent}📋 {self._labels['scenario_details']}", Style.BRIGHT)
        self._print_colored(f"{self._indent * 2}• {self._labels['name'].format(name=result.scenario_identifier.name)}", Fore.CYAN)
        self._print_colored(f"{self._indent * 2}• {self._labels['version'].format(version=result.scenario_identifier.version)}", Fore.CYAN)
        self._print_colored(f"{self._indent * 2}• {self._labels['pyrit_version'].format(version=result.scenario_identifier.pyrit_version)}", Fore.CYAN)

        # Format description with text wrapping at 120 characters
        if result.scenario_identifier.description:
            self._print_colored(f"{self._indent * 2}• {self._labels['description']}", Fore.CYAN)
            desc_indent = self._indent * 4
            available_width = 120 - len(desc_indent)
            wrapped_lines = textwrap.wrap(
                result.scenario_identifier.description, width=available_width, break_long_words=False
            )
            for line in wrapped_lines:
                self._print_colored(f"{desc_indent}{line}", Fore.CYAN)

        # Target information
        print()
        target_id = result.objective_target_identifier
        target_type = target_id.class_name if target_id else "Unknown"
        target_model = target_id.model_name if target_id else "Unknown"
        target_endpoint = target_id.endpoint if target_id else "Unknown"

        self._print_colored(f"{self._indent}🎯 {self._labels['target_info']}", Style.BRIGHT)
        self._print_colored(f"{self._indent * 2}• {self._labels['target_type'].format(type=target_type)}", Fore.CYAN)
        self._print_colored(f"{self._indent * 2}• {self._labels['target_model'].format(model=target_model)}", Fore.CYAN)
        self._print_colored(f"{self._indent * 2}• {self._labels['target_endpoint'].format(endpoint=target_endpoint)}", Fore.CYAN)

        # Scorer information - use ScorerIdentifier from result
        scorer_identifier = result.objective_scorer_identifier
        if scorer_identifier:
            self._scorer_printer.print_objective_scorer(scorer_identifier=scorer_identifier)

        # Overall statistics
        self._print_section_header(self._labels["overall_stats"])
        total_results = sum(len(results) for results in result.attack_results.values())
        total_strategies = len(result.get_strategies_used())
        overall_rate = result.objective_achieved_rate()

        self._print_colored(f"{self._indent}📈 {self._labels['summary']}", Style.BRIGHT)
        self._print_colored(f"{self._indent * 2}• {self._labels['total_strategies'].format(count=total_strategies)}", Fore.GREEN)
        self._print_colored(f"{self._indent * 2}• {self._labels['total_results'].format(count=total_results)}", Fore.GREEN)
        self._print_colored(
            f"{self._indent * 2}• {self._labels['overall_rate'].format(rate=overall_rate)}", self._get_rate_color(overall_rate)
        )

        objectives = result.get_objectives()
        self._print_colored(f"{self._indent * 2}• {self._labels['unique_objectives'].format(count=len(objectives))}", Fore.GREEN)

        # Per-strategy breakdown
        self._print_section_header(self._labels["per_strategy"])
        strategies = result.get_strategies_used()

        for strategy in strategies:
            results_for_strategy = result.attack_results[strategy]
            strategy_rate = result.objective_achieved_rate(atomic_attack_name=strategy)

            print()
            self._print_colored(f"{self._indent}🔸 {self._labels['strategy'].format(name=strategy)}", Style.BRIGHT)
            self._print_colored(f"{self._indent * 2}• {self._labels['num_results'].format(count=len(results_for_strategy))}", Fore.YELLOW)
            self._print_colored(
                f"{self._indent * 2}• {self._labels['success_rate'].format(rate=strategy_rate)}", self._get_rate_color(strategy_rate)
            )

        # Print footer
        self._print_footer()

    def _print_header(self, result: ScenarioResult) -> None:
        """
        Print the header with scenario name.

        Args:
            result (ScenarioResult): The scenario result.
        """
        print()
        self._print_colored("=" * self._width, Fore.CYAN)
        header_text = f"📊 {self._labels['header'].format(name=result.scenario_identifier.name)}"
        self._print_colored(header_text.center(self._width), Style.BRIGHT, Fore.CYAN)
        self._print_colored("=" * self._width, Fore.CYAN)

    def _print_footer(self) -> None:
        """
        Print a footer separator.
        """
        print()
        self._print_colored("=" * self._width, Fore.CYAN)
        print()

    def _get_rate_color(self, rate: int) -> str:
        """
        Get color based on success rate.

        Args:
            rate (int): Success rate percentage (0-100)

        Returns:
            str: Colorama color constant
        """
        if rate >= 75:
            return str(Fore.RED)  # High success (bad for security)
        elif rate >= 50:
            return str(Fore.YELLOW)  # Medium success
        elif rate >= 25:
            return str(Fore.CYAN)  # Low success
        else:
            return str(Fore.GREEN)  # Very low success (good for security)
