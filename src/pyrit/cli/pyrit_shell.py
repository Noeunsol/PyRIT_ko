# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
PyRIT Shell - Interactive REPL for PyRIT.

This module provides an interactive shell where PyRIT modules are loaded once
at startup, making subsequent commands instant.
"""

from __future__ import annotations

import asyncio
import cmd
import sys
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrit.models.scenario_result import ScenarioResult

from pyrit.cli import frontend_core

# ---------------------------------------------------------------------------
# Shell locale labels
# ---------------------------------------------------------------------------

_SHELL_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "waiting_init": "Waiting for PyRIT initialization to complete...",
        "error_listing_scenarios": "Error listing scenarios: {error}",
        "error_listing_initializers": "Error listing initializers: {error}",
        "error_specify_scenario": "Error: Specify a scenario name",
        "usage_run": "\nUsage: run <scenario_name> [options]",
        "note_initializer": "\nNote: Every scenario requires an initializer.",
        "options_header": "\nOptions:",
        "example_header": "\nExample:",
        "example_run": "  run foundry --initializers openai_objective_target load_default_datasets",
        "help_run_hint": "\nType 'help run' for more details and examples",
        "error_prefix": "Error: {error}",
        "error_running": "Error running scenario: {error}",
        "no_history": "No scenario runs in history.",
        "history_header": "\nScenario Run History:",
        "total_runs": "\nTotal runs: {count}",
        "history_hint_specific": "\nUse 'print-scenario <number>' to view detailed results for a specific run.",
        "history_hint_all": "Use 'print-scenario' to view detailed results for all runs.",
        "printing_all": "\nPrinting all scenario results:",
        "scenario_run": "Scenario Run #{idx}: {command}",
        "error_scenario_range": "Error: Scenario number must be between 1 and {max}",
        "error_invalid_number": "Error: Invalid scenario number '{arg}'. Must be an integer.",
        "shell_startup_options": "Shell Startup Options:",
        "run_command_options": "Run Command Options (specified when running scenarios):",
        "db_help": "      Default database type: InMemory, SQLite, or AzureSQL",
        "db_default": "      Default: SQLite",
        "db_override": "      Can be overridden per-run with 'run <scenario> --database <type>'",
        "log_help": "      Default logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL",
        "log_default": "      Default: WARNING",
        "log_override": "      Can be overridden per-run with 'run <scenario> --log-level <level>'",
        "init_required": "      Every scenario requires at least one initializer",
        "init_example": "      Example: run foundry --initializers openai_objective_target load_default_datasets",
        "scripts_example": "      Example: run foundry --initialization-scripts ./my_init.py",
        "strategies_example": "      Example: run garak.encoding --strategies base64 rot13",
        "labels_example": '      Example: run foundry --memory-labels \'{"env":"test"}\'',
        "start_shell_header": "Start the shell like:",
        "start_shell_example1": "  pyrit_shell",
        "start_shell_example2": "  pyrit_shell --database InMemory --log-level DEBUG",
        "goodbye": "\nGoodbye!",
        "interrupted": "\n\nInterrupted. Goodbye!",
        "unknown_command": "Unknown command: {line}",
        "help_hint": "Type 'help' or '?' for available commands",
        "override_db": "  --database <type>               Override default database ({in_memory}, {sqlite}, {azure_sql})",
        "override_log": "  --log-level <level>             Override default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    },
    "ko": {
        "waiting_init": "PyRIT 초기화 완료 대기 중...",
        "error_listing_scenarios": "시나리오 목록 조회 오류: {error}",
        "error_listing_initializers": "초기화기 목록 조회 오류: {error}",
        "error_specify_scenario": "오류: 시나리오 이름을 지정하세요",
        "usage_run": "\n사용법: run <시나리오_이름> [옵션]",
        "note_initializer": "\n참고: 모든 시나리오는 초기화기가 필요합니다.",
        "options_header": "\n옵션:",
        "example_header": "\n예시:",
        "example_run": "  run foundry --initializers openai_objective_target load_default_datasets",
        "help_run_hint": "\n자세한 내용은 'help run'을 입력하세요",
        "error_prefix": "오류: {error}",
        "error_running": "시나리오 실행 오류: {error}",
        "no_history": "시나리오 실행 기록이 없습니다.",
        "history_header": "\n시나리오 실행 기록:",
        "total_runs": "\n전체 실행: {count}회",
        "history_hint_specific": "\n특정 실행의 상세 결과를 보려면 'print-scenario <번호>'를 입력하세요.",
        "history_hint_all": "모든 실행의 상세 결과를 보려면 'print-scenario'를 입력하세요.",
        "printing_all": "\n모든 시나리오 결과 출력:",
        "scenario_run": "시나리오 실행 #{idx}: {command}",
        "error_scenario_range": "오류: 시나리오 번호는 1에서 {max} 사이여야 합니다",
        "error_invalid_number": "오류: 잘못된 시나리오 번호 '{arg}'. 정수여야 합니다.",
        "shell_startup_options": "셸 시작 옵션:",
        "run_command_options": "실행 명령 옵션 (시나리오 실행 시 지정):",
        "db_help": "      기본 데이터베이스 유형: InMemory, SQLite, AzureSQL",
        "db_default": "      기본값: SQLite",
        "db_override": "      실행별 덮어쓰기: 'run <시나리오> --database <유형>'",
        "log_help": "      기본 로깅 수준: DEBUG, INFO, WARNING, ERROR, CRITICAL",
        "log_default": "      기본값: WARNING",
        "log_override": "      실행별 덮어쓰기: 'run <시나리오> --log-level <수준>'",
        "init_required": "      모든 시나리오는 하나 이상의 초기화기가 필요합니다",
        "init_example": "      예시: run foundry --initializers openai_objective_target load_default_datasets",
        "scripts_example": "      예시: run foundry --initialization-scripts ./my_init.py",
        "strategies_example": "      예시: run garak.encoding --strategies base64 rot13",
        "labels_example": '      예시: run foundry --memory-labels \'{"env":"test"}\'',
        "start_shell_header": "셸 시작 방법:",
        "start_shell_example1": "  pyrit_shell",
        "start_shell_example2": "  pyrit_shell --database InMemory --log-level DEBUG",
        "goodbye": "\n안녕히 가세요!",
        "interrupted": "\n\n중단되었습니다. 안녕히 가세요!",
        "unknown_command": "알 수 없는 명령: {line}",
        "help_hint": "사용 가능한 명령은 'help' 또는 '?'를 입력하세요",
        "override_db": "  --database <유형>               기본 데이터베이스 덮어쓰기 ({in_memory}, {sqlite}, {azure_sql})",
        "override_log": "  --log-level <수준>             기본 로그 수준 덮어쓰기 (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    },
}

_INTRO_EN = """
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                              ║
║                       ██████╗ ██╗   ██╗██████╗ ██╗████████╗                                  ║
║                       ██╔══██╗╚██╗ ██╔╝██╔══██╗██║╚══██╔══╝                                  ║
║                       ██████╔╝ ╚████╔╝ ██████╔╝██║   ██║                                     ║
║                       ██╔═══╝   ╚██╔╝  ██╔══██╗██║   ██║                                     ║
║                       ██║        ██║   ██║  ██║██║   ██║                                     ║
║                       ╚═╝        ╚═╝   ╚═╝  ╚═╝╚═╝   ╚═╝                                     ║
║                                                                                              ║
║                          Python Risk Identification Tool                                     ║
║                                Interactive Shell                                             ║
║                                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                              ║
║  Commands:                                                                                   ║
║    • list-scenarios        - See all available scenarios                                     ║
║    • list-initializers     - See all available initializers                                  ║
║    • run <scenario> [opts] - Execute a security scenario                                     ║
║    • scenario-history      - View your session history                                       ║
║    • print-scenario [N]    - Display detailed results                                        ║
║    • help [command]        - Get help on any command                                         ║
║    • exit                  - Quit the shell                                                  ║
║                                                                                              ║
║  Quick Start:                                                                                ║
║    pyrit> list-scenarios                                                                     ║
║    pyrit> run foundry --initializers openai_objective_target load_default_datasets           ║
║                                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
"""

_INTRO_KO = """
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                              ║
║                       ██████╗ ██╗   ██╗██████╗ ██╗████████╗                                  ║
║                       ██╔══██╗╚██╗ ██╔╝██╔══██╗██║╚══██╔══╝                                  ║
║                       ██████╔╝ ╚████╔╝ ██████╔╝██║   ██║                                     ║
║                       ██╔═══╝   ╚██╔╝  ██╔══██╗██║   ██║                                     ║
║                       ██║        ██║   ██║  ██║██║   ██║                                     ║
║                       ╚═╝        ╚═╝   ╚═╝  ╚═╝╚═╝   ╚═╝                                     ║
║                                                                                              ║
║                       Python 위험 식별 도구 (PyRIT)                                          ║
║                              대화형 셸                                                       ║
║                                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                              ║
║  명령어:                                                                                     ║
║    • list-scenarios        - 사용 가능한 시나리오 목록 보기                                  ║
║    • list-initializers     - 사용 가능한 초기화기 목록 보기                                  ║
║    • run <시나리오> [옵션] - 보안 시나리오 실행                                              ║
║    • scenario-history      - 세션 기록 보기                                                  ║
║    • print-scenario [N]    - 상세 결과 표시                                                  ║
║    • help [명령]           - 명령 도움말 보기                                                ║
║    • exit                  - 셸 종료                                                         ║
║                                                                                              ║
║  빠른 시작:                                                                                  ║
║    pyrit> list-scenarios                                                                     ║
║    pyrit> run foundry --initializers openai_objective_target load_default_datasets           ║
║                                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝
"""


def _shell_label(key: str, locale: str = "en", **kwargs) -> str:
    """Resolve a shell label by key and locale."""
    labels = _SHELL_LABELS.get(locale, _SHELL_LABELS["en"])
    template = labels.get(key, _SHELL_LABELS["en"].get(key, key))
    return template.format(**kwargs) if kwargs else template


class PyRITShell(cmd.Cmd):
    """
    Interactive shell for PyRIT.

    Commands:
        list-scenarios             - List all available scenarios
        list-initializers          - List all available initializers
        run <scenario> [opts]      - Run a scenario with optional parameters
        scenario-history           - List all previous scenario runs
        print-scenario [N]         - Print detailed results for scenario run(s)
        help [command]             - Show help for a command
        clear                      - Clear the screen
        exit (quit, q)             - Exit the shell

    Shell Startup Options:
        --database <type>       Database type (InMemory, SQLite, AzureSQL) - default for all runs
        --log-level <level>     Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) - default for all runs
        --env-files <path> ...  Environment files to load in order - default for all runs
        --target-lang <en|ko>   CLI display language

    Run Command Options:
        --initializers <name> ...       Built-in initializers to run before the scenario
        --initialization-scripts <...>  Custom Python scripts to run before the scenario
        --env-files <path> ...          Environment files to load in order (overrides startup default)
        --strategies, -s <s1> ...       Strategy names to use
        --target-lang <en|ko>           Target language (propagated to memory labels as locale)
        --max-concurrency <N>           Maximum concurrent operations
        --max-retries <N>               Maximum retry attempts
        --memory-labels <JSON>          JSON string of labels
        --database <type>               Override default database for this run
        --log-level <level>             Override default log level for this run
    """

    prompt = "pyrit> "

    def __init__(
        self,
        context: frontend_core.FrontendCore,
    ):
        """
        Initialize the PyRIT shell.

        Args:
            context: PyRIT context with loaded registries.
        """
        super().__init__()
        self.context = context
        self._locale = context._locale
        self.default_database = context._database
        self.default_log_level = context._log_level
        self.default_env_files = context._env_files

        # Set intro based on locale
        self.intro = _INTRO_KO if self._locale == "ko" else _INTRO_EN

        # Track scenario execution history: list of (command_string, ScenarioResult) tuples
        self._scenario_history: list[tuple[str, ScenarioResult]] = []

        # Initialize PyRIT in background thread for faster startup
        self._init_thread = threading.Thread(target=self._background_init, daemon=True)
        self._init_complete = threading.Event()
        self._init_thread.start()

    def _L(self, key: str, **kwargs) -> str:
        """Shorthand for locale label lookup."""
        return _shell_label(key, self._locale, **kwargs)

    def _background_init(self) -> None:
        """Initialize PyRIT modules in the background. This dramatically speeds up shell startup."""
        asyncio.run(self.context.initialize_async())
        self._init_complete.set()

    def _ensure_initialized(self) -> None:
        """Wait for initialization to complete if not already done."""
        if not self._init_complete.is_set():
            print(self._L("waiting_init"))
            sys.stdout.flush()
            self._init_complete.wait()

    def do_list_scenarios(self, arg: str) -> None:
        """List all available scenarios."""
        self._ensure_initialized()
        try:
            asyncio.run(frontend_core.print_scenarios_list_async(context=self.context))
        except Exception as e:
            print(self._L("error_listing_scenarios", error=e))

    def do_list_initializers(self, arg: str) -> None:
        """List all available initializers."""
        self._ensure_initialized()
        try:
            # Discover from scenarios directory by default (same as scan)
            discovery_path = frontend_core.get_default_initializer_discovery_path()
            asyncio.run(
                frontend_core.print_initializers_list_async(context=self.context, discovery_path=discovery_path)
            )
        except Exception as e:
            print(self._L("error_listing_initializers", error=e))

    def do_run(self, line: str) -> None:
        """
        Run a scenario.

        Usage:
            run <scenario_name> [options]

        Options:
            --initializers <name> ...       Built-in initializers to run before the scenario
            --initialization-scripts <...>  Custom Python scripts to run before the scenario
            --env-files <path> ...          Environment files to load in order
            --strategies, -s <s1> <s2> ...  Strategy names to use
            --max-concurrency <N>           Maximum concurrent operations
            --max-retries <N>               Maximum retry attempts
            --memory-labels <JSON>          JSON string of labels (e.g., '{"key":"value"}')
            --database <type>               Override default database (InMemory, SQLite, AzureSQL)
            --log-level <level>             Override default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        Examples:
            run garak.encoding --initializers openai_objective_target load_default_datasets
            run garak.encoding --initializers custom_target load_default_datasets --strategies base64 rot13
            run foundry --initializers openai_objective_target load_default_datasets --max-concurrency 10 --max-retries 3
            run garak.encoding --initializers custom_target load_default_datasets --memory-labels '{"run_id":"test123","env":"dev"}'
            run foundry --initializers openai_objective_target load_default_datasets -s jailbreak crescendo
            run garak.encoding --initializers openai_objective_target load_default_datasets --database InMemory --log-level DEBUG
            run foundry --initialization-scripts ./my_custom_init.py -s all

        Note:
            Every scenario requires an initializer (--initializers or --initialization-scripts).
            Database and log-level defaults are set at shell startup but can be overridden per-run.
            Initializers are specified per-run to allow different setups for different scenarios.
        """
        self._ensure_initialized()
        if not line.strip():
            print(self._L("error_specify_scenario"))
            print(self._L("usage_run"))
            print(self._L("note_initializer"))
            print(self._L("options_header"))
            print(f"  --initializers <name> ...       {frontend_core._arg_help('initializers', self._locale)} (REQUIRED)")
            print(
                f"  --initialization-scripts <...>  {frontend_core._arg_help('initialization_scripts', self._locale)} (alternative to --initializers)"
            )
            print(f"  --strategies, -s <s1> <s2> ...  {frontend_core._arg_help('scenario_strategies', self._locale)}")
            print(f"  --target-lang <en|ko>           {frontend_core._arg_help('target_lang', self._locale)}")
            print(f"  --max-concurrency <N>           {frontend_core._arg_help('max_concurrency', self._locale)}")
            print(f"  --max-retries <N>               {frontend_core._arg_help('max_retries', self._locale)}")
            print(f"  --memory-labels <JSON>          {frontend_core._arg_help('memory_labels', self._locale)}")
            print(
                self._L(
                    "override_db",
                    in_memory=frontend_core.IN_MEMORY,
                    sqlite=frontend_core.SQLITE,
                    azure_sql=frontend_core.AZURE_SQL,
                )
            )
            print(self._L("override_log"))
            print(self._L("example_header"))
            print(self._L("example_run"))
            print(self._L("help_run_hint"))
            return

        # Parse arguments using shared parser
        try:
            args = frontend_core.parse_run_arguments(args_string=line)
        except ValueError as e:
            print(self._L("error_prefix", error=e))
            return

        # Resolve initialization scripts if provided
        resolved_scripts = None
        if args["initialization_scripts"]:
            try:
                resolved_scripts = frontend_core.resolve_initialization_scripts(
                    script_paths=args["initialization_scripts"]
                )
            except FileNotFoundError as e:
                print(self._L("error_prefix", error=e))
                return

        # Resolve env files if provided
        resolved_env_files = None
        if args["env_files"]:
            try:
                resolved_env_files = frontend_core.resolve_env_files(env_file_paths=args["env_files"])
            except ValueError as e:
                print(self._L("error_prefix", error=e))
                return
        else:
            # Use default env files from shell startup
            resolved_env_files = self.default_env_files

        # Create a context for this run with overrides
        run_context = frontend_core.FrontendCore(
            database=args["database"] or self.default_database,
            initialization_scripts=resolved_scripts,
            initializer_names=args["initializers"],
            env_files=resolved_env_files,
            log_level=args["log_level"] or self.default_log_level,
            locale=self._locale,
        )
        # Use the existing registries (don't reinitialize)
        run_context._scenario_registry = self.context._scenario_registry
        run_context._initializer_registry = self.context._initializer_registry
        run_context._initialized = True

        try:
            result = asyncio.run(
                frontend_core.run_scenario_async(
                    scenario_name=args["scenario_name"],
                    context=run_context,
                    scenario_strategies=args["scenario_strategies"],
                    target_lang=args["target_lang"],
                    max_concurrency=args["max_concurrency"],
                    max_retries=args["max_retries"],
                    memory_labels=args["memory_labels"],
                    dataset_names=args["dataset_names"],
                    max_dataset_size=args["max_dataset_size"],
                )
            )
            # Store the command and result in history
            self._scenario_history.append((line, result))
        except ValueError as e:
            print(self._L("error_prefix", error=e))
        except Exception as e:
            print(self._L("error_running", error=e))
            import traceback

            traceback.print_exc()

    def do_scenario_history(self, arg: str) -> None:
        """
        Display history of scenario runs.

        Usage:
            scenario-history

        Shows a numbered list of all scenario runs with the commands used.
        """
        if not self._scenario_history:
            print(self._L("no_history"))
            return

        print(self._L("history_header"))
        print("=" * 80)
        for idx, (command, _) in enumerate(self._scenario_history, start=1):
            print(f"{idx}) {command}")
        print("=" * 80)
        print(self._L("total_runs", count=len(self._scenario_history)))
        print(self._L("history_hint_specific"))
        print(self._L("history_hint_all"))

    def do_print_scenario(self, arg: str) -> None:
        """
        Print detailed results for scenario runs.

        Usage:
            print-scenario          Print all scenario results
            print-scenario <N>      Print results for scenario run number N

        Examples:
            print-scenario          Show all previous scenario results
            print-scenario 1        Show results from first scenario run
            print-scenario 3        Show results from third scenario run
        """
        if not self._scenario_history:
            print(self._L("no_history"))
            return

        # Parse argument
        arg = arg.strip()

        if not arg:
            # Print all scenarios
            print(self._L("printing_all"))
            print("=" * 80)
            for idx, (command, result) in enumerate(self._scenario_history, start=1):
                print(f"\n{'#' * 80}")
                print(self._L("scenario_run", idx=idx, command=command))
                print(f"{'#' * 80}")
                from pyrit.scenario.printer.console_printer import (
                    ConsoleScenarioResultPrinter,
                )

                printer = ConsoleScenarioResultPrinter()
                asyncio.run(printer.print_summary_async(result))
        else:
            # Print specific scenario
            try:
                scenario_num = int(arg)
                if scenario_num < 1 or scenario_num > len(self._scenario_history):
                    print(self._L("error_scenario_range", max=len(self._scenario_history)))
                    return

                command, result = self._scenario_history[scenario_num - 1]
                print(f"\n{self._L('scenario_run', idx=scenario_num, command=command)}")
                print("=" * 80)
                from pyrit.scenario.printer.console_printer import (
                    ConsoleScenarioResultPrinter,
                )

                printer = ConsoleScenarioResultPrinter()
                asyncio.run(printer.print_summary_async(result))
            except ValueError:
                print(self._L("error_invalid_number", arg=arg))

    def do_help(self, arg: str) -> None:
        """Show help. Usage: help [command]."""
        if not arg:
            # Show general help
            super().do_help(arg)
            print("\n" + "=" * 70)
            print(self._L("shell_startup_options"))
            print("=" * 70)
            print("  --database <type>")
            print(self._L("db_help"))
            print(self._L("db_default"))
            print(self._L("db_override"))
            print()
            print("  --log-level <level>")
            print(self._L("log_help"))
            print(self._L("log_default"))
            print(self._L("log_override"))
            print()
            print("=" * 70)
            print(self._L("run_command_options"))
            print("=" * 70)
            print("  --initializers <name> [<name> ...]  (REQUIRED)")
            print(f"      {frontend_core._arg_help('initializers', self._locale)}")
            print(self._L("init_required"))
            print(self._L("init_example"))
            print()
            print("  --initialization-scripts <path> [<path> ...]  (Alternative to --initializers)")
            print(f"      {frontend_core._arg_help('initialization_scripts', self._locale)}")
            print(self._L("scripts_example"))
            print()
            print("  --strategies, -s <s1> [<s2> ...]")
            print(f"      {frontend_core._arg_help('scenario_strategies', self._locale)}")
            print(self._L("strategies_example"))
            print()
            print("  --max-concurrency <N>")
            print(f"      {frontend_core._arg_help('max_concurrency', self._locale)}")
            print()
            print("  --max-retries <N>")
            print(f"      {frontend_core._arg_help('max_retries', self._locale)}")
            print()
            print("  --memory-labels <JSON>")
            print(f"      {frontend_core._arg_help('memory_labels', self._locale)}")
            print(self._L("labels_example"))
            print()
            print(self._L("start_shell_header"))
            print(self._L("start_shell_example1"))
            print(self._L("start_shell_example2"))
        else:
            # Show help for specific command
            super().do_help(arg)

    def do_exit(self, arg: str) -> bool:
        """
        Exit the shell. Aliases: quit, q.

        Returns:
            bool: True to exit the shell.
        """
        print(self._L("goodbye"))
        return True

    def do_clear(self, arg: str) -> None:
        """Clear the screen."""
        import os

        os.system("cls" if os.name == "nt" else "clear")

    # Shortcuts and aliases
    do_quit = do_exit
    do_q = do_exit
    do_EOF = do_exit  # Ctrl+D on Unix, Ctrl+Z on Windows

    def emptyline(self) -> bool:
        """
        Don't repeat last command on empty line.

        Returns:
            bool: False to prevent repeating the last command.
        """
        return False

    def default(self, line: str) -> None:
        """Handle unknown commands and convert hyphens to underscores."""
        # Try converting hyphens to underscores for command lookup
        parts = line.split(None, 1)
        if parts:
            cmd_with_underscores = parts[0].replace("-", "_")
            method_name = f"do_{cmd_with_underscores}"

            if hasattr(self, method_name):
                # Call the method with the rest of the line as argument
                arg = parts[1] if len(parts) > 1 else ""
                getattr(self, method_name)(arg)
                return

        print(self._L("unknown_command", line=line))
        print(self._L("help_hint"))


def main() -> int:
    """
    Entry point for pyrit_shell.

    Returns:
        int: Exit code.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="pyrit_shell",
        description="PyRIT Interactive Shell - Load modules once, run commands instantly",
    )

    parser.add_argument(
        "--database",
        choices=[frontend_core.IN_MEMORY, frontend_core.SQLITE, frontend_core.AZURE_SQL],
        default=frontend_core.SQLITE,
        help=f"Default database type to use ({frontend_core.IN_MEMORY}, {frontend_core.SQLITE}, {frontend_core.AZURE_SQL}) (default: {frontend_core.SQLITE}, can be overridden per-run)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        help="Default logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: WARNING, can be overridden per-run)",
    )

    parser.add_argument(
        "--env-files",
        type=str,
        nargs="+",
        help="Environment files to load in order (default for all runs, can be overridden per-run)",
    )

    parser.add_argument(
        "--target-lang",
        type=str,
        choices=["en", "ko"],
        default="en",
        help="CLI display language (en|ko) (default: en)",
    )

    args = parser.parse_args()

    locale = args.target_lang

    # Resolve env files if provided
    env_files = None
    if args.env_files:
        try:
            env_files = frontend_core.resolve_env_files(env_file_paths=args.env_files)
        except ValueError as e:
            print(f"Error: {e}")
            return 1

    # Create context (initializers are specified per-run, not at startup)
    context = frontend_core.FrontendCore(
        database=args.database,
        initialization_scripts=None,
        initializer_names=None,
        env_files=env_files,
        log_level=args.log_level,
        locale=locale,
    )

    # Start shell
    try:
        shell = PyRITShell(context)
        shell.cmdloop()
        return 0
    except KeyboardInterrupt:
        print(_shell_label("interrupted", locale))
        return 0
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
