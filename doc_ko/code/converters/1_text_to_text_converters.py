# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: pyrit (3.13.5)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 1. Text-to-Text Converters (한국어 테스트)
#
# 텍스트-텍스트 변환기는 텍스트 입력을 변형된 텍스트 출력으로 변환합니다.
# 인코딩, 난독화, LLM 기반 변환 등 가장 일반적인 유형의 변환기입니다.
#
# ## 개요
#
# 이 노트북은 두 가지 주요 카테고리를 다룹니다:
#
# - **[Non-LLM Converters](#non-llm-converters)**: 인코딩, 난독화, 문자 조작 등 정적 변환
# - **[LLM-Based Converters](#llm-based-converters)**: 번역, 변형, 의미 변환 등 AI 기반 변환
#
# 한국어 내재화(`locale="ko"`)를 지원하는 변환기는 **[ko]** 태그로 표시합니다.

# %% [markdown]
# <a id="non-llm-converters"></a>
# ## Non-LLM Converters
#
# Non-LLM 변환기는 결정적 알고리즘으로 텍스트를 변환합니다:
# - **인코딩**: Base64, Binary, Morse, NATO 음성 부호 등
# - **난독화**: Leetspeak(야민정음), Unicode 조작, 문자 교체 등
# - **텍스트 조작**: ROT13, Caesar 암호, Atbash 등

# %% [markdown]
# ### 1.1 기본 인코딩 변환기
#
# 다양한 형식으로 텍스트를 인코딩합니다.
# NATO와 Braille은 `locale="ko"`로 한국어 전용 변환을 지원합니다:

# %%
from pyrit.prompt_converter import (
    AsciiArtConverter,
    AskToDecodeConverter,
    AtbashConverter,
    Base64Converter,
    Base2048Converter,
    BinaryConverter,
    BinAsciiConverter,
    BrailleConverter,
    CaesarConverter,
    EcojiConverter,
    MorseConverter,
    NatoConverter,
    NegationTrapConverter,
    ROT13Converter,
)
from pyrit.setup import IN_MEMORY, initialize_pyrit_async

await initialize_pyrit_async(memory_db_type=IN_MEMORY)  # type: ignore

# 한국어 프롬프트로 테스트
prompt = "나무를 베는 방법을 알려줘"

# --- 언어 무관 변환기 (인코딩 계열: 한국어 입력도 그대로 동작) ---
print("Base64:", await Base64Converter().convert_async(prompt=prompt))  # type: ignore
print("Base2048:", await Base2048Converter().convert_async(prompt=prompt))  # type: ignore
print("Binary:", await BinaryConverter().convert_async(prompt=prompt))  # type: ignore
print("BinAscii:", await BinAsciiConverter().convert_async(prompt=prompt))  # type: ignore
print("ASCII Art:", await AsciiArtConverter().convert_async(prompt=prompt))  # type: ignore
print("Ecoji:", await EcojiConverter().convert_async(prompt=prompt))  # type: ignore

# --- [ko] 한국어 내재화 지원 변환기 (암호 계열) ---
# ROT13: locale="ko"로 자음 7칸, 모음 5칸 회전
print("ROT13 (en):", await ROT13Converter().convert_async(prompt="hello"))  # type: ignore
print("ROT13 (ko):", await ROT13Converter(locale="ko").convert_async(prompt=prompt))  # type: ignore

# Caesar: locale="ko"로 자음/모음을 offset만큼 시프트
print("Caesar (en):", await CaesarConverter(caesar_offset=3).convert_async(prompt="hello"))  # type: ignore
print("Caesar (ko):", await CaesarConverter(caesar_offset=3, locale="ko").convert_async(prompt=prompt))  # type: ignore

# Atbash: locale="ko"로 자음/모음 역순 대응
print("Atbash (en):", await AtbashConverter().convert_async(prompt="hello"))  # type: ignore
print("Atbash (ko):", await AtbashConverter(locale="ko").convert_async(prompt=prompt))  # type: ignore

# --- [ko] 한국어 내재화 지원 변환기 ---
# Morse: locale="ko"로 한글 자모를 한국식 모스부호로 변환
print("Morse (en):", await MorseConverter().convert_async(prompt="hello"))  # type: ignore
print("Morse (ko):", await MorseConverter(locale="ko").convert_async(prompt=prompt))  # type: ignore

# NATO: locale="ko"로 한국어 통신 부호 사용 (ㄱ=기러기, ㄴ=나폴리, ...)
print("NATO (en):", await NatoConverter().convert_async(prompt="hello"))  # type: ignore
print("NATO (ko):", await NatoConverter(locale="ko").convert_async(prompt="안녕"))  # type: ignore

# Braille: locale="ko"로 2024 개정 한국 점자 규정 적용
print("Braille (en):", await BrailleConverter().convert_async(prompt="hello"))  # type: ignore
print("Braille (ko):", await BrailleConverter(locale="ko").convert_async(prompt="안녕"))  # type: ignore

# NegationTrap: locale="ko"로 한국어 부정문 템플릿 사용
print("NegationTrap (en):", await NegationTrapConverter().convert_async(prompt="your metaprompt"))  # type: ignore
print("NegationTrap (ko):", await NegationTrapConverter(locale="ko").convert_async(prompt="당신의 메타프롬프트"))  # type: ignore

# Ask to decode: 한국어 인코딩 후 디코딩 요청
base64_text = await Base64Converter().convert_async(prompt=prompt)  # type: ignore
ask_decoder = AskToDecodeConverter(encoding_name="Base64")
print("Ask to Decode:", await ask_decoder.convert_async(prompt=base64_text.output_text))  # type: ignore


# %% [markdown]
# ### 1.2 난독화 변환기
#
# 탐지 또는 필터를 우회하기 위해 텍스트를 난독화합니다.
# Leetspeak과 ColloquialWordswap은 `locale="ko"`로 한국어 전용 변환을 지원합니다:

# %%
from pyrit.prompt_converter import (
    AnsiAttackConverter,
    CharacterSpaceConverter,
    CharSwapConverter,
    CodeChameleonConverter,
    ColloquialWordswapConverter,
    DiacriticConverter,
    EmojiConverter,
    FirstLetterConverter,
    FlipConverter,
    InsertPunctuationConverter,
    LeetspeakConverter,
    MathObfuscationConverter,
    RandomCapitalLettersConverter,
    RepeatTokenConverter,
    StringJoinConverter,
    SuperscriptConverter,
    UnicodeConfusableConverter,
    UnicodeReplacementConverter,
    UnicodeSubstitutionConverter,
    WordProportionSelectionStrategy,
    ZalgoConverter,
    ZeroWidthConverter,
)

prompt = "나무를 베는 방법을 알려줘"
prompt_en = "tell me how to cut down a tree"

# --- 언어 무관 변환기 (한국어 입력도 그대로 동작) ---
print("Random Capitals:", await RandomCapitalLettersConverter(percentage=50.0).convert_async(prompt=prompt))  # type: ignore
print("Unicode Confusable:", await UnicodeConfusableConverter().convert_async(prompt=prompt))  # type: ignore
print("Unicode Substitution:", await UnicodeSubstitutionConverter().convert_async(prompt=prompt))  # type: ignore
print("Unicode Replacement:", await UnicodeReplacementConverter().convert_async(prompt=prompt))  # type: ignore
print("Emoji:", await EmojiConverter().convert_async(prompt=prompt))  # type: ignore
print("First Letter:", await FirstLetterConverter().convert_async(prompt=prompt))  # type: ignore
print("String Join:", await StringJoinConverter().convert_async(prompt=prompt))  # type: ignore
print("Zero Width:", await ZeroWidthConverter().convert_async(prompt=prompt))  # type: ignore
print("Flip:", await FlipConverter().convert_async(prompt=prompt))  # type: ignore
print("Character Space:", await CharacterSpaceConverter().convert_async(prompt=prompt))  # type: ignore
print("Zalgo:", await ZalgoConverter().convert_async(prompt=prompt))  # type: ignore

# CharSwap: 단어 내 문자 교체
char_swap = CharSwapConverter(max_iterations=3, word_selection_strategy=WordProportionSelectionStrategy(proportion=0.8))
print("CharSwap:", await char_swap.convert_async(prompt=prompt))  # type: ignore

# Insert punctuation: 문장부호 삽입
insert_punct = InsertPunctuationConverter(word_swap_ratio=0.2)
print("Insert Punctuation:", await insert_punct.convert_async(prompt=prompt))  # type: ignore

# ANSI escape sequences
ansi_converter = AnsiAttackConverter(incorporate_user_prompt=True)
print("ANSI Attack:", await ansi_converter.convert_async(prompt=prompt))  # type: ignore

# Repeat token: 반복 토큰 추가
repeat_token = RepeatTokenConverter(token_to_repeat="!", times_to_repeat=10, token_insert_mode="append")
print("Repeat Token:", await repeat_token.convert_async(prompt=prompt))  # type: ignore

# Diacritic, Superscript: 라틴 문자 전용 (영문 예시)
print("Diacritic (en):", await DiacriticConverter().convert_async(prompt=prompt_en))  # type: ignore
print("Superscript (en):", await SuperscriptConverter().convert_async(prompt=prompt_en))  # type: ignore

# Math obfuscation: 영문 전용 (수학 표현으로 치환)
math_obf = MathObfuscationConverter()
print("Math Obfuscation (en):", await math_obf.convert_async(prompt=prompt_en))  # type: ignore

# --- [ko] 한국어 내재화 지원 변환기 ---
# Leetspeak: locale="ko"로 야민정음 스타일 직접 치환 (예: 귀→커, 멍→댕)
print("Leetspeak (en):", await LeetspeakConverter().convert_async(prompt=prompt_en))  # type: ignore
print("Leetspeak (ko):", await LeetspeakConverter(locale="ko").convert_async(prompt="귀멍"))  # type: ignore

# ColloquialWordswap: locale="ko"로 한국어 구어체 치환 (father→아빠/아부지 등)
print("Colloquial (en):", await ColloquialWordswapConverter().convert_async(prompt="my father told me"))  # type: ignore
print("Colloquial (ko):", await ColloquialWordswapConverter(locale="ko").convert_async(prompt="우리 아버지가 말씀하셨어"))  # type: ignore

# CodeChameleon: locale="ko"로 한국어 템플릿 + 한국어 주석 사용
code_chameleon = CodeChameleonConverter(encrypt_type="reverse", locale="ko")
print("CodeChameleon (ko):", await code_chameleon.convert_async(prompt=prompt))  # type: ignore

# %% [markdown]
# ### 1.3 텍스트 조작 변환기
#
# 텍스트 치환, 템플릿 삽입, URL 인코딩 등을 수행합니다:

# %%
from pyrit.datasets import TextJailBreak
from pyrit.prompt_converter import (
    JsonStringConverter,
    SearchReplaceConverter,
    SuffixAppendConverter,
    TemplateSegmentConverter,
    TextJailbreakConverter,
    UrlConverter,
)

prompt = "나무를 베는 방법을 알려줘"

# Search and replace: 한국어 패턴 치환
search_replace = SearchReplaceConverter(pattern="나무", replace="건물")
print("Search Replace:", await search_replace.convert_async(prompt=prompt))  # type: ignore

# Suffix append: 한국어 접미사 추가
suffix_append = SuffixAppendConverter(suffix=" 자세한 방법을 단계별로 알려줘.")
print("Suffix Append:", await suffix_append.convert_async(prompt=prompt))  # type: ignore

# URL encoding: 한국어도 동작
url_converter = UrlConverter()
print("URL Encoded:", await url_converter.convert_async(prompt=prompt))  # type: ignore

# JSON string escaping: 한국어 이스케이프
json_string_converter = JsonStringConverter()
print("JSON String:", await json_string_converter.convert_async(prompt='그가 "안녕\n세상"이라고 말했다'))  # type: ignore

# Text jailbreak: 탈옥 템플릿 적용
text_jailbreak = TextJailbreakConverter(jailbreak_template=TextJailBreak(template_file_name="aim.yaml"))
print("Text Jailbreak:", await text_jailbreak.convert_async(prompt=prompt))  # type: ignore

# Template segment: 템플릿으로 프롬프트 분할
template_converter = TemplateSegmentConverter()
print("Template Segment:", await template_converter.convert_async(prompt=prompt))  # type: ignore

# %% [markdown]
# ### 1.4 토큰 스머글링 변환기
#
# Unicode 변이 선택자 등으로 텍스트를 숨기는 기법입니다:

# %%
from pyrit.prompt_converter import (
    AsciiSmugglerConverter,
    SneakyBitsSmugglerConverter,
    VariationSelectorSmugglerConverter,
)

prompt = "비밀 메시지"

# ASCII smuggler: Unicode 태그로 숨기기
ascii_smuggler = AsciiSmugglerConverter(action="encode", unicode_tags=True)
print("ASCII Smuggler:", await ascii_smuggler.convert_async(prompt=prompt))  # type: ignore

# Sneaky bits: 제로 폭 문자로 숨기기
sneaky_bits = SneakyBitsSmugglerConverter(action="encode")
print("Sneaky Bits:", await sneaky_bits.convert_async(prompt=prompt))  # type: ignore

# Variation selector: 변이 선택자로 숨기기
var_selector = VariationSelectorSmugglerConverter(action="encode", embed_in_base=True)
print("Variation Selector:", await var_selector.convert_async(prompt=prompt))  # type: ignore

# %% [markdown]
# <a id="llm-based-converters"></a>
# ## LLM 기반 변환기
#
# LLM 기반 변환기는 언어 모델을 사용하여 프롬프트를 변환합니다.
# 더 유연하고 자연스러운 변형을 만들 수 있지만, 느리고 LLM 타겟이 필요합니다.
#
# 스타일, 톤, 언어, 의미를 변환합니다:

# %%
import pathlib

from pyrit.common.path import CONVERTER_SEED_PROMPT_PATH
from pyrit.models import SeedPrompt
from pyrit.prompt_converter import (
    DenylistConverter,
    MaliciousQuestionGeneratorConverter,
    MathPromptConverter,
    NoiseConverter,
    PersuasionConverter,
    RandomTranslationConverter,
    TenseConverter,
    ToneConverter,
    ToxicSentenceGeneratorConverter,
    TranslationConverter,
    VariationConverter,
)
from pyrit.prompt_target import OpenAIChatTarget

attack_llm = OpenAIChatTarget()

# 한국어 프롬프트로 LLM 기반 변환 테스트
prompt = "대한민국의 역사에 대해 알려줘"

# Variation: 프롬프트 변형 생성
variation_converter_strategy = SeedPrompt.from_yaml_file(
    pathlib.Path(CONVERTER_SEED_PROMPT_PATH) / "variation_converter_prompt_softener.yaml"
)
variation_converter = VariationConverter(converter_target=attack_llm, prompt_template=variation_converter_strategy)
print("Variation:", await variation_converter.convert_async(prompt=prompt))  # type: ignore

# Noise: 노이즈 추가
noise_converter = NoiseConverter(converter_target=attack_llm)
print("Noise:", await noise_converter.convert_async(prompt=prompt))  # type: ignore

# Tone: 톤 변경 (한국어 입력 → LLM이 톤 변경)
tone_converter = ToneConverter(converter_target=attack_llm, tone="angry")
print("Tone (angry):", await tone_converter.convert_async(prompt=prompt))  # type: ignore

# Translation: 한국어 → 프랑스어
translation_converter = TranslationConverter(converter_target=attack_llm, language="French")
print("Translation (ko→fr):", await translation_converter.convert_async(prompt=prompt))  # type: ignore

# Random translation: 여러 언어를 거쳐 번역 (한국어 포함)
random_translation_converter = RandomTranslationConverter(
    converter_target=attack_llm, languages=["French", "German", "Korean", "English"]
)
print("Random Translation:", await random_translation_converter.convert_async(prompt=prompt))  # type: ignore

# Tense: 시제 변경
tense_converter = TenseConverter(converter_target=attack_llm, tense="far future")
print("Tense (future):", await tense_converter.convert_async(prompt=prompt))  # type: ignore

# Persuasion: 설득 기법 적용
persuasion_converter = PersuasionConverter(converter_target=attack_llm, persuasion_technique="logical_appeal")
print("Persuasion:", await persuasion_converter.convert_async(prompt=prompt))  # type: ignore

# Denylist: 금지어 탐지
denylist_converter = DenylistConverter(converter_target=attack_llm)
print("Denylist Check:", await denylist_converter.convert_async(prompt=prompt))  # type: ignore

# Malicious question: 악의적 질문 생성
malicious_question = MaliciousQuestionGeneratorConverter(converter_target=attack_llm)
print("Malicious Question:", await malicious_question.convert_async(prompt=prompt))  # type: ignore

# Toxic sentence: 유해 문장 생성
toxic_generator = ToxicSentenceGeneratorConverter(converter_target=attack_llm)
print("Toxic Sentence:", await toxic_generator.convert_async(prompt="건물"))  # type: ignore

# Math prompt: 수학 표현으로 변환 (locale="ko" 지원)
math_prompt_converter = MathPromptConverter(converter_target=attack_llm, locale="ko")
print("Math Prompt (ko):", await math_prompt_converter.convert_async(prompt=prompt))  # type: ignore
