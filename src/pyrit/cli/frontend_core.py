# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Shared core logic for PyRIT Frontends.

This module contains all the business logic for:
- Loading and discovering scenarios
- Running scenarios
- Formatting output
- Managing initialization scripts

Both pyrit_scan and pyrit_shell use these functions.
"""

from __future__ import annotations

import inspect
import json
import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Sequence

try:
    import termcolor

    HAS_TERMCOLOR = True
except ImportError:
    HAS_TERMCOLOR = False

    # Create a dummy termcolor module for fallback
    class termcolor:  # type: ignore
        """Dummy termcolor fallback for colored printing if termcolor is not installed."""

        @staticmethod
        def cprint(text: str, color: str = None, attrs: list = None) -> None:  # type: ignore
            """Print text without color."""
            print(text)


if TYPE_CHECKING:
    from pyrit.models.scenario_result import ScenarioResult
    from pyrit.registry import (
        InitializerMetadata,
        InitializerRegistry,
        ScenarioMetadata,
        ScenarioRegistry,
    )

logger = logging.getLogger(__name__)

# Database type constants
IN_MEMORY = "InMemory"
SQLITE = "SQLite"
AZURE_SQL = "AzureSQL"

# ---------------------------------------------------------------------------
# CLI locale labels
# ---------------------------------------------------------------------------

_CLI_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "discovering_scenarios": "Discovering user scenarios...",
        "running_initializers": "Running {count} initializer(s)...",
        "running_scenario": "\nRunning scenario: {name}",
        "scenario_not_found": "Scenario '{name}' not found.\nAvailable scenarios: {available}",
        "strategy_not_found": "Strategy '{name}' not found for scenario '{scenario}'. Available: {available}",
        "target_lang_invalid": "target_lang must be 'en' or 'ko', got: {value!r}",
        "no_scenarios": "No scenarios found.",
        "available_scenarios": "\nAvailable Scenarios:",
        "total_scenarios": "\nTotal scenarios: {count}",
        "no_initializers": "No initializers found.",
        "available_initializers": "\nAvailable Initializers:",
        "total_initializers": "\nTotal initializers: {count}",
        "class_label": "    Class: {name}",
        "description_label": "    Description:",
        "aggregate_strategies": "    Aggregate Strategies:",
        "available_strategies": "    Available Strategies ({count}):",
        "default_strategy": "    Default Strategy: {name}",
        "default_datasets": "    Default Datasets ({count}{suffix}):",
        "default_datasets_none": "    Default Datasets: None",
        "datasets_size_suffix": ", max {size} per dataset",
        "init_class": "    Class: {name}",
        "init_name": "    Name: {name}",
        "init_order": "    Execution Order: {order}",
        "init_env_vars": "    Required Environment Variables:",
        "init_env_vars_none": "    Required Environment Variables: None",
        "init_description": "    Description:",
        "invalid_db": "Invalid database type: {db}. Must be one of: {valid}",
        "invalid_log_level": "Invalid log level: {level}. Must be one of: {valid}",
        "env_file_not_found": "Environment file not found: {path}",
        "invalid_json": "Invalid JSON for memory labels: {error}",
        "labels_must_be_dict": "Memory labels must be a JSON object (dictionary)",
        "labels_must_be_strings": "All label keys and values must be strings. Got: {k}={v}",
        "no_scenario_name": "No scenario name provided",
        "requires_value": "{flag} requires a value",
        "target_lang_choices": "--target-lang must be one of: en, ko",
        "starting_pyrit": "Starting PyRIT...",
        "no_scenario_specified": "Error: No scenario specified. Use --help for usage information.",
        "objective_target_missing": (
            "Scenario '{name}' requires objective_target but none was provided. "
            "Add an initializer like 'openai_objective_target' (or pass objective_target explicitly)."
        ),
    },
    "ko": {
        "discovering_scenarios": "사용자 시나리오 탐색 중...",
        "running_initializers": "초기화기 {count}개 실행 중...",
        "running_scenario": "\n시나리오 실행: {name}",
        "scenario_not_found": "시나리오 '{name}'을(를) 찾을 수 없습니다.\n사용 가능한 시나리오: {available}",
        "strategy_not_found": "시나리오 '{scenario}'에서 전략 '{name}'을(를) 찾을 수 없습니다. 사용 가능: {available}",
        "target_lang_invalid": "target_lang은 'en' 또는 'ko'여야 합니다. 입력값: {value!r}",
        "no_scenarios": "시나리오가 없습니다.",
        "available_scenarios": "\n사용 가능한 시나리오:",
        "total_scenarios": "\n전체 시나리오: {count}개",
        "no_initializers": "초기화기가 없습니다.",
        "available_initializers": "\n사용 가능한 초기화기:",
        "total_initializers": "\n전체 초기화기: {count}개",
        "class_label": "    클래스: {name}",
        "description_label": "    설명:",
        "aggregate_strategies": "    집합 전략:",
        "available_strategies": "    사용 가능한 전략 ({count}개):",
        "default_strategy": "    기본 전략: {name}",
        "default_datasets": "    기본 데이터셋 ({count}개{suffix}):",
        "default_datasets_none": "    기본 데이터셋: 없음",
        "datasets_size_suffix": ", 데이터셋당 최대 {size}개",
        "init_class": "    클래스: {name}",
        "init_name": "    이름: {name}",
        "init_order": "    실행 순서: {order}",
        "init_env_vars": "    필수 환경 변수:",
        "init_env_vars_none": "    필수 환경 변수: 없음",
        "init_description": "    설명:",
        "invalid_db": "잘못된 데이터베이스 유형: {db}. 다음 중 하나여야 합니다: {valid}",
        "invalid_log_level": "잘못된 로그 수준: {level}. 다음 중 하나여야 합니다: {valid}",
        "env_file_not_found": "환경 파일을 찾을 수 없습니다: {path}",
        "invalid_json": "메모리 레이블 JSON이 잘못되었습니다: {error}",
        "labels_must_be_dict": "메모리 레이블은 JSON 객체(딕셔너리)여야 합니다",
        "labels_must_be_strings": "모든 레이블 키와 값은 문자열이어야 합니다. 입력값: {k}={v}",
        "no_scenario_name": "시나리오 이름이 지정되지 않았습니다",
        "requires_value": "{flag}에 값이 필요합니다",
        "target_lang_choices": "--target-lang은 en 또는 ko 중 하나여야 합니다",
        "starting_pyrit": "PyRIT 시작 중...",
        "no_scenario_specified": "오류: 시나리오가 지정되지 않았습니다. 사용법은 --help를 참조하세요.",
        "objective_target_missing": (
            "시나리오 '{name}' 실행에는 objective_target이 필요하지만 제공되지 않았습니다. "
            "'openai_objective_target' 같은 초기화기를 추가하세요 (또는 objective_target을 명시 전달)."
        ),
    },
}

DEFAULT_CLI_LOCALE = "en"


def _cli_label(label_key: str, locale: str = DEFAULT_CLI_LOCALE, **kwargs: Any) -> str:
    """Resolve a CLI label by key and locale, with optional format kwargs."""
    labels = _CLI_LABELS.get(locale, _CLI_LABELS["en"])
    template = labels.get(label_key, _CLI_LABELS["en"].get(label_key, label_key))
    return template.format(**kwargs) if kwargs else template


def _apply_openai_frontend_env_fallbacks() -> None:
    """
    CLI convenience: map common OpenAI env vars to the frontend defaults expected
    by some scenario initializers.

    This keeps existing behavior when DEFAULT_OPENAI_FRONTEND_* are explicitly set,
    but reduces friction when users already configured OPENAI_CHAT_* (used by SimpleInitializer)
    or the older OPENAI_CLI_* variables.
    """
    mapping = [
        ("DEFAULT_OPENAI_FRONTEND_ENDPOINT", ["OPENAI_CHAT_ENDPOINT", "OPENAI_CLI_ENDPOINT"]),
        ("DEFAULT_OPENAI_FRONTEND_KEY", ["OPENAI_CHAT_KEY", "OPENAI_CLI_KEY"]),
        ("DEFAULT_OPENAI_FRONTEND_MODEL", ["OPENAI_CHAT_MODEL", "OPENAI_CLI_MODEL"]),
    ]

    for dest, sources in mapping:
        if os.getenv(dest):
            continue
        for src in sources:
            val = os.getenv(src)
            if val:
                os.environ[dest] = val
                break


class FrontendCore:
    """
    Shared context for PyRIT operations.

    This object holds all the registries and configuration needed to run
    scenarios. It can be created once (for shell) or per-command (for CLI).
    """

    def __init__(
        self,
        *,
        database: str = SQLITE,
        initialization_scripts: Optional[list[Path]] = None,
        initializer_names: Optional[list[str]] = None,
        env_files: Optional[list[Path]] = None,
        log_level: str = "WARNING",
        locale: str = DEFAULT_CLI_LOCALE,
    ):
        """
        Initialize PyRIT context.

        Args:
            database: Database type (InMemory, SQLite, or AzureSQL).
            initialization_scripts: Optional list of initialization script paths.
            initializer_names: Optional list of built-in initializer names to run.
            env_files: Optional list of environment file paths to load in order.
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Defaults to WARNING.
            locale: CLI display locale ("en" or "ko"). Defaults to "en".

        Raises:
            ValueError: If database or log_level are invalid.
        """
        # Validate inputs
        self._database = validate_database(database=database)
        self._initialization_scripts = initialization_scripts
        self._initializer_names = initializer_names
        self._env_files = env_files
        self._log_level = validate_log_level(log_level=log_level)
        self._locale = locale if locale in ("en", "ko") else DEFAULT_CLI_LOCALE

        # Lazy-loaded registries
        self._scenario_registry: Optional[ScenarioRegistry] = None
        self._initializer_registry: Optional[InitializerRegistry] = None
        self._initialized = False

        # Configure logging
        logging.basicConfig(level=getattr(logging, self._log_level))

    async def initialize_async(self) -> None:
        """Initialize PyRIT and load registries (heavy operation)."""
        if self._initialized:
            return

        from pyrit.registry import InitializerRegistry, ScenarioRegistry
        from pyrit.setup import initialize_pyrit_async

        _apply_openai_frontend_env_fallbacks()

        # Initialize PyRIT without initializers (they run per-scenario)
        await initialize_pyrit_async(
            memory_db_type=self._database,
            initialization_scripts=None,
            initializers=None,
            env_files=self._env_files,
        )

        # Load registries (use singleton pattern for shared access)
        self._scenario_registry = ScenarioRegistry.get_registry_singleton()
        if self._initialization_scripts:
            print(_cli_label("discovering_scenarios", self._locale))
            sys.stdout.flush()
            self._scenario_registry.discover_user_scenarios()

        self._initializer_registry = InitializerRegistry()

        self._initialized = True

    @property
    def scenario_registry(self) -> "ScenarioRegistry":
        """
        Get the scenario registry. Must call await initialize_async() first.

        Raises:
            RuntimeError: If initialize_async() has not been called.
        """
        if not self._initialized:
            raise RuntimeError(
                "FrontendCore not initialized. Call 'await context.initialize_async()' before accessing registries."
            )
        assert self._scenario_registry is not None
        return self._scenario_registry

    @property
    def initializer_registry(self) -> "InitializerRegistry":
        """
        Get the initializer registry. Must call await initialize_async() first.

        Raises:
            RuntimeError: If initialize_async() has not been called.
        """
        if not self._initialized:
            raise RuntimeError(
                "FrontendCore not initialized. Call 'await context.initialize_async()' before accessing registries."
            )
        assert self._initializer_registry is not None
        return self._initializer_registry


async def list_scenarios_async(*, context: FrontendCore) -> list[ScenarioMetadata]:
    """
    List metadata for all available scenarios.

    Args:
        context: PyRIT context with loaded registries.

    Returns:
        List of scenario metadata dictionaries describing each scenario class.
    """
    if not context._initialized:
        await context.initialize_async()
    return context.scenario_registry.list_metadata()


async def list_initializers_async(
    *, context: FrontendCore, discovery_path: Optional[Path] = None
) -> "Sequence[InitializerMetadata]":
    """
    List metadata for all available initializers.

    Args:
        context: PyRIT context with loaded registries.
        discovery_path: Optional path to discover initializers from.

    Returns:
        Sequence of initializer metadata dictionaries describing each initializer class.
    """
    if discovery_path:
        from pyrit.registry import InitializerRegistry

        registry = InitializerRegistry(discovery_path=discovery_path)
        return registry.list_metadata()

    if not context._initialized:
        await context.initialize_async()
    return context.initializer_registry.list_metadata()


async def run_scenario_async(
    *,
    scenario_name: str,
    context: FrontendCore,
    scenario_strategies: Optional[list[str]] = None,
    target_lang: str = "en",
    max_concurrency: Optional[int] = None,
    max_retries: Optional[int] = None,
    memory_labels: Optional[dict[str, str]] = None,
    dataset_names: Optional[list[str]] = None,
    max_dataset_size: Optional[int] = None,
    print_summary: bool = True,
) -> "ScenarioResult":
    """
    Run a scenario by name.

    Args:
        scenario_name: Name of the scenario to run.
        context: PyRIT context with loaded registries.
        scenario_strategies: Optional list of strategy names.
        target_lang: Target language for the run (en|ko). Propagated to memory labels as locale.
        max_concurrency: Max concurrent operations.
        max_retries: Max retry attempts.
        memory_labels: Labels to attach to memory entries.
        dataset_names: Optional list of dataset names to use instead of scenario defaults.
            If provided, creates a new dataset configuration (fetches all items unless
            max_dataset_size is also specified).
        max_dataset_size: Optional maximum number of items to use from the dataset.
            If dataset_names is provided, limits items from the new datasets.
            If only max_dataset_size is provided, overrides the scenario's default limit.
        print_summary: Whether to print the summary after execution. Defaults to True.

    Returns:
        ScenarioResult: The result of the scenario execution.

    Raises:
        ValueError: If scenario not found or fails to run.

    Note:
        Initializers from PyRITContext will be run before the scenario executes.
    """
    from pyrit.scenario.printer.console_printer import ConsoleScenarioResultPrinter
    from pyrit.setup import initialize_pyrit_async

    # Ensure context is initialized first (loads registries)
    # This must happen BEFORE we run initializers to avoid double-initialization
    if not context._initialized:
        await context.initialize_async()

    # Run initializers before scenario
    locale = context._locale
    initializer_instances = None
    if context._initializer_names:
        print(_cli_label("running_initializers", locale, count=len(context._initializer_names)))
        sys.stdout.flush()

        initializer_instances = []

        for name in context._initializer_names:
            initializer_class = context.initializer_registry.get_class(name)
            initializer_instances.append(initializer_class())

    _apply_openai_frontend_env_fallbacks()

    # Re-initialize PyRIT with the scenario-specific initializers
    # This resets memory and applies initializer defaults
    await initialize_pyrit_async(
        memory_db_type=context._database,
        initialization_scripts=context._initialization_scripts,
        initializers=initializer_instances,
        env_files=context._env_files,
    )

    # Get scenario class
    scenario_class = context.scenario_registry.get_class(scenario_name)

    if scenario_class is None:
        available = ", ".join(context.scenario_registry.get_names())
        raise ValueError(_cli_label("scenario_not_found", locale, name=scenario_name, available=available))

    # Build initialization kwargs (these go to initialize_async, not __init__)
    init_kwargs: dict[str, Any] = {}

    if scenario_strategies:
        strategy_class = scenario_class.get_strategy_class()
        strategy_enums = []
        for name in scenario_strategies:
            try:
                strategy_enums.append(strategy_class(name))
            except ValueError:
                available_strategies = [s.value for s in strategy_class]
                raise ValueError(
                    _cli_label(
                        "strategy_not_found", locale,
                        name=name, scenario=scenario_name,
                        available=", ".join(available_strategies),
                    )
                ) from None
        init_kwargs["scenario_strategies"] = strategy_enums

    if max_concurrency is not None:
        init_kwargs["max_concurrency"] = max_concurrency
    if max_retries is not None:
        init_kwargs["max_retries"] = max_retries

    # Some scenarios define objective_target as a required keyword-only argument
    # without using @apply_defaults on initialize_async.
    # Inject a globally registered default (from initializers) when available.
    init_sig = inspect.signature(scenario_class.initialize_async)
    objective_target_param = init_sig.parameters.get("objective_target")
    if objective_target_param and "objective_target" not in init_kwargs:
        from pyrit.common.apply_defaults import get_global_default_values

        found_default, default_objective_target = get_global_default_values().get_default_value(
            class_type=scenario_class,
            parameter_name="objective_target",
        )
        if found_default:
            init_kwargs["objective_target"] = default_objective_target
        elif objective_target_param.default is inspect.Parameter.empty:
            raise ValueError(_cli_label("objective_target_missing", locale, name=scenario_name))

    # Merge/inject memory labels.
    # - Preserve user-provided labels
    # - Force locale to the selected target language (reserved key)
    labels: dict[str, str] = dict(memory_labels or {})
    if target_lang not in ("en", "ko"):
        raise ValueError(_cli_label("target_lang_invalid", locale, value=target_lang))
    labels["locale"] = target_lang
    init_kwargs["memory_labels"] = labels

    # Build dataset_config based on CLI args:
    # - No args: scenario uses its default_dataset_config()
    # - dataset_names only: new config with those datasets, fetches all items
    # - dataset_names + max_dataset_size: new config with limited items
    # - max_dataset_size only: default datasets with overridden limit
    if dataset_names:
        # User specified dataset names - create new config (fetches all unless max_dataset_size set)
        from pyrit.scenario import DatasetConfiguration

        init_kwargs["dataset_config"] = DatasetConfiguration(
            dataset_names=dataset_names,
            max_dataset_size=max_dataset_size,
        )
    elif max_dataset_size is not None:
        # User only specified max_dataset_size - override default config's limit
        default_config = scenario_class.default_dataset_config()
        default_config.max_dataset_size = max_dataset_size
        init_kwargs["dataset_config"] = default_config

    # Instantiate and run
    print(_cli_label("running_scenario", locale, name=scenario_name))
    sys.stdout.flush()

    # Scenarios here are a concrete subclass
    # Runtime parameters are passed to initialize_async()
    scenario = scenario_class()  # type: ignore[call-arg]
    await scenario.initialize_async(**init_kwargs)
    result = await scenario.run_async()

    # Print results if requested
    if print_summary:
        printer = ConsoleScenarioResultPrinter(locale=locale)
        await printer.print_summary_async(result)

    return result


def _format_wrapped_text(*, text: str, indent: str, width: int = 78) -> str:
    """
    Format text with word wrapping.

    Args:
        text: Text to wrap.
        indent: Indentation string for wrapped lines.
        width: Maximum line width. Defaults to 78.

    Returns:
        Formatted text with line breaks.
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        if not current_line:
            current_line = word
        elif len(current_line) + len(word) + 1 + len(indent) <= width:
            current_line += " " + word
        else:
            lines.append(indent + current_line)
            current_line = word

    if current_line:
        lines.append(indent + current_line)

    return "\n".join(lines)


def _print_header(*, text: str) -> None:
    """
    Print a colored header if termcolor is available.

    Args:
        text: Header text to print.
    """
    if HAS_TERMCOLOR:
        termcolor.cprint(f"\n  {text}", "cyan", attrs=["bold"])
    else:
        print(f"\n  {text}")


def format_scenario_metadata(*, scenario_metadata: "ScenarioMetadata", locale: str = DEFAULT_CLI_LOCALE) -> None:
    """
    Print formatted information about a scenario class.

    Args:
        scenario_metadata: Dataclass containing scenario metadata.
        locale: Display locale ("en" or "ko").
    """
    _print_header(text=scenario_metadata.snake_class_name)
    print(_cli_label("class_label", locale, name=scenario_metadata.class_name))

    description = scenario_metadata.class_description
    if description:
        print(_cli_label("description_label", locale))
        print(_format_wrapped_text(text=description, indent="      "))

    if scenario_metadata.aggregate_strategies:
        agg_strategies = scenario_metadata.aggregate_strategies
        print(_cli_label("aggregate_strategies", locale))
        formatted = _format_wrapped_text(text=", ".join(agg_strategies), indent="      - ")
        print(formatted)

    if scenario_metadata.all_strategies:
        strategies = scenario_metadata.all_strategies
        print(_cli_label("available_strategies", locale, count=len(strategies)))
        formatted = _format_wrapped_text(text=", ".join(strategies), indent="      ")
        print(formatted)

    if scenario_metadata.default_strategy:
        print(_cli_label("default_strategy", locale, name=scenario_metadata.default_strategy))

    if scenario_metadata.default_datasets:
        datasets = scenario_metadata.default_datasets
        max_size = scenario_metadata.max_dataset_size
        if datasets:
            size_suffix = _cli_label("datasets_size_suffix", locale, size=max_size) if max_size else ""
            print(_cli_label("default_datasets", locale, count=len(datasets), suffix=size_suffix))
            formatted = _format_wrapped_text(text=", ".join(datasets), indent="      ")
            print(formatted)
        else:
            print(_cli_label("default_datasets_none", locale))


def format_initializer_metadata(
    *, initializer_metadata: "InitializerMetadata", locale: str = DEFAULT_CLI_LOCALE
) -> None:
    """
    Print formatted information about an initializer class.

    Args:
        initializer_metadata: Dataclass containing initializer metadata.
        locale: Display locale ("en" or "ko").
    """
    _print_header(text=initializer_metadata.snake_class_name)
    print(_cli_label("init_class", locale, name=initializer_metadata.class_name))
    print(_cli_label("init_name", locale, name=initializer_metadata.display_name))
    print(_cli_label("init_order", locale, order=initializer_metadata.execution_order))

    if initializer_metadata.required_env_vars:
        print(_cli_label("init_env_vars", locale))
        for env_var in initializer_metadata.required_env_vars:
            print(f"      - {env_var}")
    else:
        print(_cli_label("init_env_vars_none", locale))

    if initializer_metadata.class_description:
        print(_cli_label("init_description", locale))
        print(_format_wrapped_text(text=initializer_metadata.class_description, indent="      "))


def validate_database(*, database: str) -> str:
    """
    Validate database type.

    Args:
        database: Database type string.

    Returns:
        Validated database type.

    Raises:
        ValueError: If database type is invalid.
    """
    valid_databases = [IN_MEMORY, SQLITE, AZURE_SQL]
    if database not in valid_databases:
        raise ValueError(_cli_label("invalid_db", db=database, valid=", ".join(valid_databases)))
    return database


def validate_log_level(*, log_level: str) -> str:
    """
    Validate log level.

    Args:
        log_level: Log level string (case-insensitive).

    Returns:
        Validated log level in uppercase.

    Raises:
        ValueError: If log level is invalid.
    """
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    level_upper = log_level.upper()
    if level_upper not in valid_levels:
        raise ValueError(_cli_label("invalid_log_level", level=log_level, valid=", ".join(valid_levels)))
    return level_upper


def validate_integer(value: str, *, name: str = "value", min_value: Optional[int] = None) -> int:
    """
    Validate and parse an integer value.

    Note: The 'value' parameter is positional (not keyword-only) to allow use with
    argparse lambdas like: lambda v: validate_integer(v, min_value=1).
    This is an exception to the PyRIT style guide for argparse compatibility.

    Args:
        value: String value to parse.
        name: Parameter name for error messages. Defaults to "value".
        min_value: Optional minimum value constraint.

    Returns:
        Parsed integer.

    Raises:
        ValueError: If value is not a valid integer or violates constraints.
    """
    # Reject boolean types explicitly (int(True) == 1, int(False) == 0)
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer string, got boolean: {value}")

    # Ensure value is a string
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string, got {type(value).__name__}: {value}")

    # Strip whitespace and validate it looks like an integer
    value = value.strip()
    if not value:
        raise ValueError(f"{name} cannot be empty")

    try:
        int_value = int(value)
    except (ValueError, TypeError) as e:
        raise ValueError(f"{name} must be an integer, got: {value}") from e

    if min_value is not None and int_value < min_value:
        raise ValueError(f"{name} must be at least {min_value}, got: {int_value}")

    return int_value


def _argparse_validator(validator_func: Callable[..., Any]) -> Callable[[Any], Any]:
    """
    Adapt a validator to argparse by converting ValueError to ArgumentTypeError.

    This decorator adapts our keyword-only validators for use with argparse's type= parameter.
    It handles two challenges:

    1. Exception Translation: argparse expects ArgumentTypeError, but our validators raise
       ValueError. This decorator catches ValueError and re-raises as ArgumentTypeError.

    2. Keyword-Only Parameters: PyRIT validators use keyword-only parameters (e.g.,
       validate_database(*, database: str)), but argparse's type= passes a positional argument.
       This decorator inspects the function signature and calls the validator with the correct
       keyword argument name.

    This pattern allows us to:
    - Keep validators as pure functions with proper type hints
    - Follow PyRIT style guide (keyword-only parameters)
    - Reuse the same validation logic in both argparse and non-argparse contexts

    Args:
        validator_func: Function that raises ValueError on invalid input.
            Must have at least one parameter (can be keyword-only).

    Returns:
        Wrapped function that:
        - Accepts a single positional argument (for argparse compatibility)
        - Calls validator_func with the correct keyword argument
        - Raises ArgumentTypeError instead of ValueError

    Raises:
        ValueError: If validator_func has no parameters.
    """
    import inspect

    # Get the first parameter name from the function signature
    sig = inspect.signature(validator_func)
    params = list(sig.parameters.keys())
    if not params:
        raise ValueError(f"Validator function {validator_func.__name__} must have at least one parameter")
    first_param = params[0]

    def wrapper(value: Any) -> Any:
        import argparse as ap

        try:
            # Call with keyword argument to support keyword-only parameters
            return validator_func(**{first_param: value})
        except ValueError as e:
            raise ap.ArgumentTypeError(str(e)) from e

    # Preserve function metadata for better debugging
    wrapper.__name__ = getattr(validator_func, "__name__", "argparse_validator")
    wrapper.__doc__ = getattr(validator_func, "__doc__", None)
    return wrapper


def resolve_initialization_scripts(script_paths: list[str]) -> list[Path]:
    """
    Resolve initialization script paths.

    Args:
        script_paths: List of script path strings.

    Returns:
        List of resolved Path objects.

    Raises:
        FileNotFoundError: If a script path does not exist.
    """
    from pyrit.registry import InitializerRegistry

    return InitializerRegistry.resolve_script_paths(script_paths=script_paths)


def resolve_env_files(*, env_file_paths: list[str]) -> list[Path]:
    """
    Resolve environment file paths to absolute Path objects.

    Args:
        env_file_paths: List of environment file path strings.

    Returns:
        List of resolved Path objects.

    Raises:
        ValueError: If any path does not exist.
    """
    resolved_paths = []
    for path_str in env_file_paths:
        path = Path(path_str).resolve()
        if not path.exists():
            raise ValueError(_cli_label("env_file_not_found", path=path))
        resolved_paths.append(path)
    return resolved_paths


# Argparse-compatible validators
#
# These wrappers adapt our core validators (which use keyword-only parameters and raise
# ValueError) for use with argparse's type= parameter (which passes positional arguments
# and expects ArgumentTypeError).
#
# Pattern:
#   - Use core validators (validate_database, validate_log_level, etc.) in regular code
#   - Use these _argparse versions ONLY in parser.add_argument(..., type=...)
#
# The lambda wrappers for validate_integer are necessary because we need to partially
# apply the min_value parameter while still allowing the decorator to work correctly.
validate_database_argparse = _argparse_validator(validate_database)
validate_log_level_argparse = _argparse_validator(validate_log_level)
positive_int = _argparse_validator(lambda v: validate_integer(v, min_value=1))
non_negative_int = _argparse_validator(lambda v: validate_integer(v, min_value=0))
resolve_env_files_argparse = _argparse_validator(resolve_env_files)


def parse_memory_labels(json_string: str) -> dict[str, str]:
    """
    Parse memory labels from a JSON string.

    Args:
        json_string: JSON string containing label key-value pairs.

    Returns:
        Dictionary of labels.

    Raises:
        ValueError: If JSON is invalid or contains non-string values.
    """
    try:
        labels = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(_cli_label("invalid_json", error=e)) from e

    if not isinstance(labels, dict):
        raise ValueError(_cli_label("labels_must_be_dict"))

    # Validate all keys and values are strings
    for key, value in labels.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError(_cli_label("labels_must_be_strings", k=key, v=value))

    return labels


def get_default_initializer_discovery_path() -> Path:
    """
    Get the default path for discovering initializers.

    Returns:
        Path to the scenarios initializers directory.
    """
    PYRIT_PATH = Path(__file__).parent.parent.resolve()
    return PYRIT_PATH / "setup" / "initializers" / "scenarios"


async def print_scenarios_list_async(*, context: FrontendCore) -> int:
    """
    Print a formatted list of all available scenarios.

    Args:
        context: PyRIT context with loaded registries.

    Returns:
        Exit code (0 for success).
    """
    locale = context._locale
    scenarios = await list_scenarios_async(context=context)

    if not scenarios:
        print(_cli_label("no_scenarios", locale))
        return 0

    print(_cli_label("available_scenarios", locale))
    print("=" * 80)
    for scenario_metadata in scenarios:
        format_scenario_metadata(scenario_metadata=scenario_metadata, locale=locale)
    print("\n" + "=" * 80)
    print(_cli_label("total_scenarios", locale, count=len(scenarios)))
    return 0


async def print_initializers_list_async(*, context: FrontendCore, discovery_path: Optional[Path] = None) -> int:
    """
    Print a formatted list of all available initializers.

    Args:
        context: PyRIT context with loaded registries.
        discovery_path: Optional path to discover initializers from.

    Returns:
        Exit code (0 for success).
    """
    locale = context._locale
    initializers = await list_initializers_async(context=context, discovery_path=discovery_path)

    if not initializers:
        print(_cli_label("no_initializers", locale))
        return 0

    print(_cli_label("available_initializers", locale))
    print("=" * 80)
    for initializer_metadata in initializers:
        format_initializer_metadata(initializer_metadata=initializer_metadata, locale=locale)
    print("\n" + "=" * 80)
    print(_cli_label("total_initializers", locale, count=len(initializers)))
    return 0


# Shared argument help text
ARG_HELP: dict[str, dict[str, str]] = {
    "en": {
        "initializers": "Built-in initializer names to run before the scenario (e.g., openai_objective_target)",
        "initialization_scripts": "Paths to custom Python initialization scripts to run before the scenario",
        "env_files": "Paths to environment files to load in order (e.g., .env.production .env.local). Later files "
        "override earlier ones.",
        "scenario_strategies": "List of strategy names to run (e.g., base64 rot13)",
        "max_concurrency": "Maximum number of concurrent attack executions (must be >= 1)",
        "max_retries": "Maximum number of automatic retries on exception (must be >= 0)",
        "memory_labels": 'Additional labels as JSON string (e.g., \'{"experiment": "test1"}\')',
        "database": "Database type to use for memory storage",
        "log_level": "Logging level",
        "dataset_names": "List of dataset names to use instead of scenario defaults (e.g., harmbench advbench). "
        "Creates a new dataset config; fetches all items unless --max-dataset-size is also specified",
        "max_dataset_size": "Maximum number of items to use from the dataset (must be >= 1). "
        "Limits new datasets if --dataset-names provided, otherwise overrides scenario's default limit",
        "target_lang": "Target language for the run (en|ko). Use --target-lang. Propagated to memory labels as locale.",
    },
    "ko": {
        "initializers": "시나리오 실행 전 실행할 내장 초기화기 이름 (예: openai_objective_target)",
        "initialization_scripts": "시나리오 실행 전 실행할 사용자 정의 Python 초기화 스크립트 경로",
        "env_files": "순서대로 로드할 환경 파일 경로 (예: .env.production .env.local). 뒤의 파일이 앞의 파일을 덮어씁니다.",
        "scenario_strategies": "실행할 전략 이름 목록 (예: base64 rot13)",
        "max_concurrency": "최대 동시 공격 실행 수 (1 이상)",
        "max_retries": "예외 발생 시 최대 자동 재시도 횟수 (0 이상)",
        "memory_labels": 'JSON 문자열로 된 추가 레이블 (예: \'{"experiment": "test1"}\')',
        "database": "메모리 저장소에 사용할 데이터베이스 유형",
        "log_level": "로깅 수준",
        "dataset_names": "시나리오 기본값 대신 사용할 데이터셋 이름 목록 (예: harmbench advbench). "
        "새 데이터셋 설정을 생성하며, --max-dataset-size를 지정하지 않으면 모든 항목을 가져옵니다",
        "max_dataset_size": "데이터셋에서 사용할 최대 항목 수 (1 이상). "
        "--dataset-names가 지정된 경우 새 데이터셋을 제한하고, 그렇지 않으면 시나리오 기본 제한을 덮어씁니다",
        "target_lang": "실행 대상 언어 (en|ko). --target-lang 사용. 메모리 레이블에 locale로 전파됩니다.",
    },
}


def _arg_help(key: str, locale: str = DEFAULT_CLI_LOCALE) -> str:
    """Get help text for an argument key by locale."""
    return ARG_HELP.get(locale, ARG_HELP["en"]).get(key, ARG_HELP["en"].get(key, key))


def parse_run_arguments(*, args_string: str) -> dict[str, Any]:
    """
    Parse run command arguments from a string (for shell mode).

    Args:
        args_string: Space-separated argument string (e.g., "scenario_name --initializers foo --strategies bar").

    Returns:
        Dictionary with parsed arguments:
            - scenario_name: str
            - initializers: Optional[list[str]]
            - initialization_scripts: Optional[list[str]]
            - scenario_strategies: Optional[list[str]]
            - target_lang: str
            - max_concurrency: Optional[int]
            - max_retries: Optional[int]
            - memory_labels: Optional[dict[str, str]]
            - database: Optional[str]
            - log_level: Optional[str]
            - dataset_names: Optional[list[str]]
            - max_dataset_size: Optional[int]

    Raises:
        ValueError: If parsing or validation fails.
    """
    parts = args_string.split()

    if not parts:
        raise ValueError(_cli_label("no_scenario_name"))

    result: dict[str, Any] = {
        "scenario_name": parts[0],
        "initializers": None,
        "initialization_scripts": None,
        "env_files": None,
        "scenario_strategies": None,
        "target_lang": "en",
        "max_concurrency": None,
        "max_retries": None,
        "memory_labels": None,
        "database": None,
        "log_level": None,
        "dataset_names": None,
        "max_dataset_size": None,
    }

    i = 1
    while i < len(parts):
        if parts[i] == "--initializers":
            # Collect initializers until next flag
            result["initializers"] = []
            i += 1
            while i < len(parts) and not parts[i].startswith("--"):
                result["initializers"].append(parts[i])
                i += 1
        elif parts[i] == "--initialization-scripts":
            # Collect script paths until next flag
            result["initialization_scripts"] = []
            i += 1
            while i < len(parts) and not parts[i].startswith("--"):
                result["initialization_scripts"].append(parts[i])
                i += 1
        elif parts[i] == "--env-files":
            # Collect env file paths until next flag
            result["env_files"] = []
            i += 1
            while i < len(parts) and not parts[i].startswith("--"):
                result["env_files"].append(parts[i])
                i += 1
        elif parts[i] in ("--strategies", "-s"):
            # Collect strategies until next flag
            result["scenario_strategies"] = []
            i += 1
            while i < len(parts) and not parts[i].startswith("--") and parts[i] != "-s":
                result["scenario_strategies"].append(parts[i])
                i += 1
        elif parts[i] == "--max-concurrency":
            i += 1
            if i >= len(parts):
                raise ValueError(_cli_label("requires_value", flag="--max-concurrency"))
            result["max_concurrency"] = validate_integer(parts[i], name="--max-concurrency", min_value=1)
            i += 1
        elif parts[i] == "--max-retries":
            i += 1
            if i >= len(parts):
                raise ValueError(_cli_label("requires_value", flag="--max-retries"))
            result["max_retries"] = validate_integer(parts[i], name="--max-retries", min_value=0)
            i += 1
        elif parts[i] == "--memory-labels":
            i += 1
            if i >= len(parts):
                raise ValueError(_cli_label("requires_value", flag="--memory-labels"))
            result["memory_labels"] = parse_memory_labels(parts[i])
            i += 1
        elif parts[i] == "--target-lang":
            i += 1
            if i >= len(parts):
                raise ValueError(_cli_label("requires_value", flag="--target-lang"))
            if parts[i] not in ("en", "ko"):
                raise ValueError(_cli_label("target_lang_choices"))
            result["target_lang"] = parts[i]
            i += 1
        elif parts[i] == "--database":
            i += 1
            if i >= len(parts):
                raise ValueError(_cli_label("requires_value", flag="--database"))
            result["database"] = validate_database(database=parts[i])
            i += 1
        elif parts[i] == "--log-level":
            i += 1
            if i >= len(parts):
                raise ValueError(_cli_label("requires_value", flag="--log-level"))
            result["log_level"] = validate_log_level(log_level=parts[i])
            i += 1
        elif parts[i] == "--dataset-names":
            # Collect dataset names until next flag
            result["dataset_names"] = []
            i += 1
            while i < len(parts) and not parts[i].startswith("--"):
                result["dataset_names"].append(parts[i])
                i += 1
        elif parts[i] == "--max-dataset-size":
            i += 1
            if i >= len(parts):
                raise ValueError(_cli_label("requires_value", flag="--max-dataset-size"))
            result["max_dataset_size"] = validate_integer(parts[i], name="--max-dataset-size", min_value=1)
            i += 1
        else:
            logger.warning(f"Unknown argument: {parts[i]}")
            i += 1

    return result
