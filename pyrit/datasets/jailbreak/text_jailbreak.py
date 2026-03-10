# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import random
from pathlib import Path
from typing import Any, List, Optional

from pyrit.common.path import JAILBREAK_TEMPLATES_PATH
from pyrit.models import SeedPrompt


class TextJailBreak:
    """
    A class that manages jailbreak datasets (like DAN, etc.).
    """

    def __init__(
        self,
        *,
        template_path: Optional[str] = None,
        template_file_name: Optional[str] = None,
        template_relative_path: Optional[str] = None,
        string_template: Optional[str] = None,
        random_template: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a Jailbreak instance with exactly one template source.

        Args:
            template_path (str, optional): Full path to a YAML template file.
            template_file_name (str, optional): Name of a template file in datasets/jailbreak directory.
            template_relative_path (str, optional): Relative path of a template file under datasets/jailbreak/templates.
            string_template (str, optional): A string template to use directly.
            random_template (bool, optional): Whether to use a random template from datasets/jailbreak.
            **kwargs: Additional parameters to apply to the template. The 'prompt' parameter will be preserved
                     for later use in get_jailbreak().

        Raises:
            ValueError: If more than one template source is provided or if no template source is provided.
        """
        # Track the template source for error reporting
        self.template_source: str = "<unknown>"
        # Count how many template sources are provided
        template_sources = [template_path, template_file_name, template_relative_path, string_template, random_template]
        provided_sources = [source for source in template_sources if source]

        if len(provided_sources) != 1:
            raise ValueError(
                "Exactly one of template_path, template_file_name, template_relative_path, string_template, "
                "or random_template must be provided"
            )

        if template_path:
            self.template = SeedPrompt.from_yaml_file(template_path)
            self.template_source = str(template_path)
        elif string_template:
            self.template = SeedPrompt(value=string_template)
            self.template_source = "<string_template>"
        else:
            # Get all yaml files in the jailbreak directory and its subdirectories
            jailbreak_dir = JAILBREAK_TEMPLATES_PATH
            # Get all yaml files but exclude those in multi_parameter subdirectory
            yaml_files = [f for f in jailbreak_dir.rglob("*.yaml") if "multi_parameter" not in f.parts]
            if not yaml_files:
                raise ValueError(
                    "No YAML templates found in jailbreak directory (excluding multi_parameter subdirectory)"
                )

            if template_relative_path:
                normalized_relative_path = template_relative_path.replace("\\", "/").lstrip("./")
                matching_files = [
                    f for f in yaml_files if f.relative_to(jailbreak_dir).as_posix() == normalized_relative_path
                ]
                if not matching_files:
                    raise ValueError(
                        f"Template relative path '{template_relative_path}' not found in jailbreak directory "
                        "or its subdirectories"
                    )
                self.template = SeedPrompt.from_yaml_file(matching_files[0])
                self.template_source = str(matching_files[0])
            elif template_file_name:
                matching_files = [f for f in yaml_files if f.name == template_file_name]
                if not matching_files:
                    raise ValueError(
                        f"Template file '{template_file_name}' not found in jailbreak directory or its subdirectories"
                    )
                if len(matching_files) > 1:
                    raise ValueError(f"Multiple files named '{template_file_name}' found in jailbreak directory")
                self.template = SeedPrompt.from_yaml_file(matching_files[0])
                self.template_source = str(matching_files[0])
            else:
                while True:
                    random_template_path = random.choice(yaml_files)
                    self.template = SeedPrompt.from_yaml_file(random_template_path)

                    if self.template.parameters == ["prompt"]:
                        self.template_source = str(random_template_path)
                        # Validate template renders correctly by test-rendering with dummy prompt
                        try:
                            self.template.render_template_value(prompt="test")
                            break
                        except ValueError as e:
                            # Template has syntax errors - fail fast with clear error
                            raise ValueError(f"Invalid jailbreak template '{random_template_path}': {str(e)}") from e

        # Validate that all required parameters (except 'prompt') are provided in kwargs
        template_params = self.template.parameters or []
        required_params = [p for p in template_params if p != "prompt"]
        missing_params = [p for p in required_params if p not in kwargs]
        if missing_params:
            raise ValueError(
                f"Template requires parameters that were not provided: {missing_params}. "
                f"Required parameters (excluding 'prompt'): {required_params}"
            )

        # Apply any kwargs to the template, preserving the prompt parameter for later use
        if kwargs:
            kwargs.pop("prompt", None)
            # Apply remaining kwargs to the template while preserving template variables
            self.template.value = self.template.render_template_value_silent(**kwargs)

    @classmethod
    def _normalize_locale(cls, *, locale: Optional[str]) -> Optional[str]:
        """Normalize locale-like values to 'en'/'ko' primary subtags."""
        if not locale:
            return None
        normalized = locale.strip().lower().replace("_", "-")
        if not normalized:
            return None

        primary_subtag = normalized.split("-", maxsplit=1)[0]
        if primary_subtag == "kr":
            return "ko"
        return primary_subtag

    @classmethod
    def _list_jailbreak_template_paths(cls) -> List[Path]:
        """List all supported jailbreak template paths (excluding multi-parameter templates)."""
        return sorted(
            (f for f in JAILBREAK_TEMPLATES_PATH.rglob("*.yaml") if "multi_parameter" not in f.parts),
            key=lambda path: path.relative_to(JAILBREAK_TEMPLATES_PATH).as_posix(),
        )

    @classmethod
    def _filter_jailbreak_template_paths_by_locale(
        cls, *, template_paths: List[Path], locale: Optional[str]
    ) -> List[Path]:
        """
        Filter templates by locale with sibling fallback.

        - locale='en': use `name.yaml`, fallback to `name_ko.yaml` if only Korean exists.
        - locale='ko': use `name_ko.yaml`, fallback to `name.yaml` if Korean is missing.
        - locale unset/unsupported: return input unchanged.
        """
        normalized_locale = cls._normalize_locale(locale=locale)
        if normalized_locale not in {"en", "ko"}:
            return template_paths

        english_by_key: dict[str, Path] = {}
        korean_by_key: dict[str, Path] = {}
        for path in template_paths:
            relative_path = path.relative_to(JAILBREAK_TEMPLATES_PATH)
            if relative_path.stem.endswith("_ko"):
                pairing_key = relative_path.with_name(f"{relative_path.stem[:-3]}{relative_path.suffix}").as_posix()
                korean_by_key[pairing_key] = path
            else:
                pairing_key = relative_path.as_posix()
                english_by_key[pairing_key] = path

        selected_paths: List[Path] = []
        for pairing_key in sorted(set(english_by_key) | set(korean_by_key)):
            if normalized_locale == "ko":
                selected_paths.append(korean_by_key.get(pairing_key) or english_by_key[pairing_key])
            else:
                selected_paths.append(english_by_key.get(pairing_key) or korean_by_key[pairing_key])
        return selected_paths

    @classmethod
    def get_all_jailbreak_templates(
        cls,
        n: Optional[int] = None,
        *,
        locale: Optional[str] = None,
        return_relative_paths: bool = False,
    ) -> List[str]:
        """
        Retrieve all jailbreak template file names from the jailbreak templates directory tree.

        Args:
            n (int, optional): Number of jailbreak templates to return. None to get all.
            locale (str, optional): Locale hint ('en' or 'ko'). When provided, localized sibling templates are
                selected with locale-aware fallback.
            return_relative_paths (bool): Whether to return relative paths under jailbreak/templates.
                If False, return basename file names (legacy behavior).

        Returns:
            List[str]: List of jailbreak template file names.

        Raises:
            ValueError: If no jailbreak templates are found in the jailbreak directory.
            ValueError: If n is larger than the number of templates that exist.
        """
        template_paths = cls._list_jailbreak_template_paths()
        template_paths = cls._filter_jailbreak_template_paths_by_locale(template_paths=template_paths, locale=locale)
        if not template_paths:
            raise ValueError("No jailbreak templates found in the jailbreak directory")

        if n:
            if n > len(template_paths):
                raise ValueError(
                    f"Attempted to pull {n} jailbreaks from a dataset with only {len(template_paths)} jailbreaks!"
                )
            template_paths = random.choices(template_paths, k=n)

        if return_relative_paths:
            return [path.relative_to(JAILBREAK_TEMPLATES_PATH).as_posix() for path in template_paths]
        return [path.name for path in template_paths]

    def get_jailbreak_system_prompt(self) -> str:
        """
        Get the jailbreak template as a system prompt without a specific user prompt.

        Returns:
            str: The rendered jailbreak template with an empty prompt parameter.
        """
        return self.get_jailbreak(prompt="")

    def get_jailbreak(self, prompt: str) -> str:
        """
        Render the jailbreak template with the provided user prompt.

        Args:
            prompt (str): The user prompt to insert into the jailbreak template.

        Returns:
            str: The rendered jailbreak template with the prompt parameter filled in.

        Raises:
            ValueError: If the template fails to render.
        """
        return self.template.render_template_value(prompt=prompt)
