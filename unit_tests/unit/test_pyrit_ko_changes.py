# Copyright (c) SelectStar.
# Tests for PyRIT-KO changes: AnsiAttackConverter locale, scorer YAML ko prompts,
# sentiment_ko.yaml fix, and notebook code patterns.

import pathlib
from textwrap import dedent
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from unit.mocks import get_mock_target_identifier

# ---------------------------------------------------------------------------
# 1. AnsiAttackConverter locale support
# ---------------------------------------------------------------------------


class TestAnsiAttackConverterLocale:
    """Tests for AnsiAttackConverter Korean locale support."""

    @pytest.mark.asyncio
    async def test_locale_ko_uses_korean_asks(self):
        from pyrit.prompt_converter import AnsiAttackConverter

        converter = AnsiAttackConverter(
            include_tasks=True,
            include_repeats=False,
            include_unescape=False,
            incorporate_user_prompt=False,
            locale="ko",
        )
        result = await converter.convert_async(prompt="테스트")
        output = result.output_text
        # Korean asks: "터미널 ANSI 코드로", "VT100 코드로", "OSC 8로"
        korean_patterns = ["터미널", "VT100", "OSC 8"]
        assert any(p in output for p in korean_patterns), f"Expected Korean ask pattern in: {output}"

    @pytest.mark.asyncio
    async def test_locale_ko_uses_korean_user_input_stub(self):
        from pyrit.prompt_converter import AnsiAttackConverter

        converter = AnsiAttackConverter(
            include_tasks=True,
            include_repeats=False,
            include_unescape=False,
            incorporate_user_prompt=True,
            locale="ko",
        )
        result = await converter.convert_async(prompt="나무를 베는 방법")
        assert "사용자 입력을 고려" in result.output_text

    @pytest.mark.asyncio
    async def test_locale_en_uses_english_asks(self):
        from pyrit.prompt_converter import AnsiAttackConverter

        converter = AnsiAttackConverter(
            include_tasks=True,
            include_repeats=False,
            include_unescape=False,
            incorporate_user_prompt=False,
            locale="en",
        )
        result = await converter.convert_async(prompt="test")
        output = result.output_text
        english_patterns = ["terminal ANSI", "VT100", "OSC 8"]
        assert any(p in output for p in english_patterns), f"Expected English ask pattern in: {output}"

    @pytest.mark.asyncio
    async def test_locale_ko_repeat_stub_korean(self):
        from pyrit.prompt_converter import AnsiAttackConverter

        converter = AnsiAttackConverter(
            include_tasks=False,
            include_repeats=True,
            include_unescape=False,
            incorporate_user_prompt=False,
            locale="ko",
        )
        result = await converter.convert_async(prompt="테스트")
        korean_stubs = ["반복하세요", "출력하세요", "콜론 뒤"]
        assert any(s in result.output_text for s in korean_stubs), f"Expected Korean repeat stub in: {result.output_text}"

    @pytest.mark.asyncio
    async def test_locale_ko_unescape_stub_korean(self):
        from pyrit.prompt_converter import AnsiAttackConverter

        converter = AnsiAttackConverter(
            include_tasks=False,
            include_repeats=False,
            include_unescape=True,
            include_escaped=True,
            incorporate_user_prompt=False,
            locale="ko",
        )
        result = await converter.convert_async(prompt="테스트")
        korean_stubs = ["디코딩하세요", "언이스케이프하세요"]
        assert any(s in result.output_text for s in korean_stubs), f"Expected Korean unescape stub in: {result.output_text}"

    @pytest.mark.asyncio
    async def test_default_locale_is_english(self):
        from pyrit.prompt_converter import AnsiAttackConverter

        converter = AnsiAttackConverter(
            include_tasks=True,
            include_repeats=False,
            include_unescape=False,
            incorporate_user_prompt=True,
        )
        result = await converter.convert_async(prompt="test")
        assert "Additionally, consider this user input:" in result.output_text


# ---------------------------------------------------------------------------
# 2. Scorer YAML Korean response instruction
# ---------------------------------------------------------------------------


class TestScorerYamlKoreanInstruction:
    """Tests that _ko.yaml scorer prompts include Korean response instruction."""

    SCORER_KO_YAMLS = [
        "prompts/score/insecure_code/system_prompt_ko.yaml",
        "prompts/score/scales/general_system_prompt_ko.yaml",
        "prompts/score/likert/likert_system_prompt_ko.yaml",
        "prompts/score/true_false_question/true_false_system_prompt_ko.yaml",
        "prompts/score/content_classifiers/content_classifier_system_prompt_ko.yaml",
        "prompts/score/refusal/refusal_with_objective_ko.yaml",
        "prompts/score/refusal/refusal_without_objective_ko.yaml",
    ]

    @pytest.mark.parametrize("yaml_path", SCORER_KO_YAMLS)
    def test_ko_yaml_contains_korean_response_instruction(self, yaml_path):
        full_path = pathlib.Path(__file__).resolve().parent.parent.parent / yaml_path
        assert full_path.exists(), f"File not found: {full_path}"
        content = full_path.read_text(encoding="utf-8")
        assert "한국어" in content, f"{yaml_path} should contain Korean response instruction ('한국어')"


# ---------------------------------------------------------------------------
# 3. sentiment_ko.yaml no_category_found fix
# ---------------------------------------------------------------------------


class TestSentimentKoYaml:
    """Tests that sentiment_ko.yaml has consistent no_category_found."""

    def test_no_category_found_matches_category_name(self):
        yaml_path = (
            pathlib.Path(__file__).resolve().parent.parent.parent
            / "prompts/score/content_classifiers/sentiment_ko.yaml"
        )
        assert yaml_path.exists()
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        no_cat = data["no_category_found"]
        category_names = [c["name"] for c in data["categories"]]
        assert no_cat in category_names, (
            f"no_category_found='{no_cat}' not found in category names: {category_names}"
        )

    def test_harm_ko_no_category_found_matches(self):
        yaml_path = (
            pathlib.Path(__file__).resolve().parent.parent.parent
            / "prompts/score/content_classifiers/harm_ko.yaml"
        )
        assert yaml_path.exists()
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        no_cat = data["no_category_found"]
        category_names = [c["name"] for c in data["categories"]]
        assert no_cat in category_names


# ---------------------------------------------------------------------------
# 4. NotebookLocale and locale utilities
# ---------------------------------------------------------------------------


class TestNotebookLocalePatterns:
    """Tests for locale patterns used across all notebooks."""

    def test_pick_returns_korean_for_ko(self):
        from pyrit.common.locale_utils import NotebookLocale

        L = NotebookLocale("ko")
        assert L.pick(en="hello", ko="안녕") == "안녕"

    def test_pick_returns_english_for_en(self):
        from pyrit.common.locale_utils import NotebookLocale

        L = NotebookLocale("en")
        assert L.pick(en="hello", ko="안녕") == "hello"

    def test_labels_includes_locale(self):
        from pyrit.common.locale_utils import NotebookLocale

        L = NotebookLocale("ko")
        labels = L.labels(attack="test")
        assert labels["locale"] == "ko"
        assert labels["attack"] == "test"

    def test_yaml_returns_ko_suffix(self):
        from pyrit.common.locale_utils import NotebookLocale

        L = NotebookLocale("ko")
        assert L.yaml("aim.yaml") == "aim_ko.yaml"
        assert L.yaml("tone_converter.yaml") == "tone_converter_ko.yaml"

    def test_yaml_returns_original_for_en(self):
        from pyrit.common.locale_utils import NotebookLocale

        L = NotebookLocale("en")
        assert L.yaml("aim.yaml") == "aim.yaml"

    def test_prepend_returns_korean_system_prompt(self):
        from pyrit.common.locale_utils import NotebookLocale

        L = NotebookLocale("ko")
        prepend = L.prepend
        assert len(prepend) == 1
        assert "한국어" in prepend[0].message_pieces[0].original_value

    def test_prepend_returns_empty_for_en(self):
        from pyrit.common.locale_utils import NotebookLocale

        L = NotebookLocale("en")
        assert L.prepend == []

    def test_kr_alias_normalizes_to_ko(self):
        from pyrit.common.locale_utils import NotebookLocale

        L = NotebookLocale("kr")
        assert L.locale == "ko"


# ---------------------------------------------------------------------------
# 5. Converter locale parameter consistency
# ---------------------------------------------------------------------------


class TestConverterLocaleParam:
    """Tests that converters with locale param work with 'ko'."""

    @pytest.mark.asyncio
    async def test_rot13_ko_produces_different_output(self):
        from pyrit.prompt_converter import ROT13Converter

        en_result = await ROT13Converter(locale="en").convert_async(prompt="hello")
        ko_result = await ROT13Converter(locale="ko").convert_async(prompt="안녕")
        # Both should produce output, but different from input
        assert en_result.output_text != "hello"
        assert ko_result.output_text != "안녕"
        assert ko_result.output_text  # non-empty

    @pytest.mark.asyncio
    async def test_morse_ko_produces_output(self):
        from pyrit.prompt_converter import MorseConverter

        result = await MorseConverter(locale="ko").convert_async(prompt="안녕")
        assert result.output_text
        assert result.output_text != "안녕"

    @pytest.mark.asyncio
    async def test_nato_ko_produces_korean_phonetic(self):
        from pyrit.prompt_converter import NatoConverter

        result = await NatoConverter(locale="ko").convert_async(prompt="안녕")
        assert result.output_text
        # Korean NATO uses Korean words like 잉어, 나폴리 etc.
        assert any(ord(c) >= 0xAC00 for c in result.output_text)  # Contains Hangul

    @pytest.mark.asyncio
    async def test_leetspeak_ko_produces_output(self):
        from pyrit.prompt_converter import LeetspeakConverter

        result = await LeetspeakConverter(locale="ko").convert_async(prompt="사이트")
        assert result.output_text
        assert result.output_text != "사이트"

    @pytest.mark.asyncio
    async def test_caesar_ko_produces_different_output(self):
        from pyrit.prompt_converter import CaesarConverter

        result = await CaesarConverter(locale="ko", caesar_offset=3).convert_async(prompt="안녕")
        assert result.output_text != "안녕"

    @pytest.mark.asyncio
    async def test_atbash_ko_produces_different_output(self):
        from pyrit.prompt_converter import AtbashConverter

        result = await AtbashConverter(locale="ko").convert_async(prompt="안녕")
        assert result.output_text != "안녕"

    @pytest.mark.asyncio
    async def test_braille_ko_produces_output(self):
        from pyrit.prompt_converter import BrailleConverter

        result = await BrailleConverter(locale="ko").convert_async(prompt="안녕")
        assert result.output_text
        assert result.output_text != "안녕"


# ---------------------------------------------------------------------------
# 6. Scorer locale resolution via labels
# ---------------------------------------------------------------------------


class TestScorerLocaleResolution:
    """Tests that scorers resolve locale from MessagePiece labels."""

    def test_refusal_scorer_resolves_ko_locale(self):
        from pyrit.models import MessagePiece
        from pyrit.score import SelfAskRefusalScorer

        mock_target = MagicMock()
        mock_target.get_identifier.return_value = get_mock_target_identifier("MockTarget")
        scorer = SelfAskRefusalScorer(chat_target=mock_target)

        mp = MessagePiece(role="user", original_value="test", labels={"locale": "ko"})
        locale = scorer._resolve_locale(message_piece=mp)
        assert locale == "ko"

    def test_refusal_scorer_defaults_to_en(self):
        from pyrit.models import MessagePiece
        from pyrit.score import SelfAskRefusalScorer

        mock_target = MagicMock()
        mock_target.get_identifier.return_value = get_mock_target_identifier("MockTarget")
        scorer = SelfAskRefusalScorer(chat_target=mock_target)

        mp = MessagePiece(role="user", original_value="test")
        locale = scorer._resolve_locale(message_piece=mp)
        assert locale == "en"

    def test_insecure_code_scorer_resolves_ko_locale(self):
        from pyrit.models import MessagePiece
        from pyrit.score import InsecureCodeScorer

        mock_target = MagicMock()
        mock_target.get_identifier.return_value = get_mock_target_identifier("MockTarget")
        scorer = InsecureCodeScorer(chat_target=mock_target)

        mp = MessagePiece(role="user", original_value="test", labels={"locale": "ko"})
        locale = scorer._resolve_locale(message_piece=mp)
        assert locale == "ko"

    def test_insecure_code_scorer_has_ko_system_prompt(self):
        from pyrit.score import InsecureCodeScorer

        mock_target = MagicMock()
        mock_target.get_identifier.return_value = get_mock_target_identifier("MockTarget")
        scorer = InsecureCodeScorer(chat_target=mock_target)

        assert "ko" in scorer._system_prompts_by_locale
        assert "한국어" in scorer._system_prompts_by_locale["ko"]


# ---------------------------------------------------------------------------
# 7. Jailbreak templates _ko.yaml existence
# ---------------------------------------------------------------------------


class TestJailbreakTemplatesKo:
    """Tests that Korean jailbreak templates exist for key templates."""

    JAILBREAK_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "prompts" / "jailbreak" / "templates"

    def test_jailbreak_templates_dir_exists(self):
        assert self.JAILBREAK_DIR.exists()

    def test_ko_templates_exist(self):
        ko_files = list(self.JAILBREAK_DIR.glob("*_ko.yaml"))
        assert len(ko_files) > 50, f"Expected >50 ko templates, found {len(ko_files)}"

    @pytest.mark.parametrize("template", ["aim", "dan_1", "anti_gpt", "better_dan"])
    def test_specific_ko_template_exists(self, template):
        ko_path = self.JAILBREAK_DIR / f"{template}_ko.yaml"
        assert ko_path.exists(), f"Missing Korean template: {template}_ko.yaml"


# ---------------------------------------------------------------------------
# 8. Attack class import and basic instantiation
# ---------------------------------------------------------------------------


class TestAttackImportsAndInstantiation:
    """Tests that all attack classes used in notebooks can be imported and instantiated."""

    def test_all_single_turn_attacks_importable(self):
        from pyrit.executor.attack import (
            ContextComplianceAttack,
            FlipAttack,
            ManyShotJailbreakAttack,
            PromptSendingAttack,
            RolePlayAttack,
            SkeletonKeyAttack,
        )
        # Just verify import works
        assert PromptSendingAttack is not None
        assert FlipAttack is not None
        assert ContextComplianceAttack is not None
        assert ManyShotJailbreakAttack is not None
        assert RolePlayAttack is not None
        assert SkeletonKeyAttack is not None

    def test_all_multi_turn_attacks_importable(self):
        from pyrit.executor.attack import (
            ChunkedRequestAttack,
            CrescendoAttack,
            MultiPromptSendingAttack,
            RedTeamingAttack,
            TAPAttack,
        )
        assert CrescendoAttack is not None
        assert RedTeamingAttack is not None
        assert TAPAttack is not None
        assert MultiPromptSendingAttack is not None
        assert ChunkedRequestAttack is not None

    def test_all_scorer_classes_importable(self):
        from pyrit.score import (
            ContentClassifierPaths,
            FloatScaleThresholdScorer,
            InsecureCodeScorer,
            LikertScalePaths,
            MarkdownInjectionScorer,
            SelfAskCategoryScorer,
            SelfAskGeneralFloatScaleScorer,
            SelfAskGeneralTrueFalseScorer,
            SelfAskLikertScorer,
            SelfAskRefusalScorer,
            SelfAskScaleScorer,
            SelfAskTrueFalseScorer,
            SubStringScorer,
            TrueFalseCompositeScorer,
            TrueFalseInverterScorer,
            TrueFalseQuestionPaths,
            TrueFalseScoreAggregator,
        )
        assert SelfAskRefusalScorer is not None
        assert TrueFalseScoreAggregator is not None

    def test_scenario_classes_importable(self):
        from pyrit.scenario.scenarios.airt.content_harms import ContentHarms, ContentHarmsStrategy
        from pyrit.scenario.printer.console_printer import ConsoleScenarioResultPrinter

        assert ContentHarms is not None
        assert ContentHarmsStrategy.Violence is not None
        assert ConsoleScenarioResultPrinter is not None
