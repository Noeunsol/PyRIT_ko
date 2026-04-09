# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
# ---

# %% [markdown]
# # 변환기 (Converters)

# %% [markdown]
# 변환기는 프롬프트를 타겟에 전송하기 전에 **변환**하는 데 사용됩니다.
#
# 이는 다양한 이유로 유용합니다. 예를 들어 프롬프트를 다른 형식으로 인코딩하거나, 추가 정보를 붙이는 등의 작업이 가능합니다.
# Base64로 인코딩하거나, 프롬프트 앞에 접두어를 추가하는 것이 대표적인 예입니다.
#
# 변환기는 다음과 같은 방식으로 프롬프트를 변환할 수 있습니다:
# - **텍스트→텍스트**: 인코딩, 난독화, 번역, 의미 변환
# - **멀티모달**: 텍스트, 이미지, 오디오, 비디오, 파일 간 변환
# - **대화형**: 사람이 직접 검토하고 수정하는 방식
#
# ## 변환기 모달리티 참조 테이블
#
# 아래 테이블은 입출력 모달리티별로 사용 가능한 변환기를 보여줍니다:

# %%
import pandas as pd

from pyrit.prompt_converter import get_converter_modalities
from pyrit.setup import IN_MEMORY, initialize_pyrit_async

await initialize_pyrit_async(memory_db_type=IN_MEMORY)  # type: ignore

# 모든 변환기의 모달리티 정보를 가져옵니다
converter_list = get_converter_modalities()

# DataFrame 생성용 행 리스트
rows = []
for name, inputs, outputs in converter_list:
    input_str = ", ".join(inputs) if inputs else "any"
    output_str = ", ".join(outputs) if outputs else "any"
    rows.append({"입력 모달리티": input_str, "출력 모달리티": output_str, "변환기": name})

# DataFrame 생성 및 정렬
df = pd.DataFrame(rows)
df = df.sort_values(by=["입력 모달리티", "출력 모달리티", "변환기"]).reset_index(drop=True)

# 모든 행 표시
pd.set_option("display.max_rows", None)
df

# %% [markdown]
# ## 변환기 카테고리
#
# 변환기는 다음과 같은 카테고리로 구성됩니다:
#
# - **[텍스트→텍스트 변환기](1_text_to_text_converters.ipynb)**: 비LLM(인코딩, 난독화) 및 LLM 기반(번역, 변형, 톤 변환)
# - **[오디오 변환기](2_audio_converters.ipynb)**: 텍스트→오디오, 오디오→텍스트, 오디오→오디오
# - **[이미지 변환기](3_image_converters.ipynb)**: 텍스트→이미지, 이미지→이미지
# - **[비디오 변환기](4_video_converters.ipynb)**: 이미지→비디오
# - **[파일 변환기](5_file_converters.ipynb)**: 텍스트→파일 (PDF, URL)
# - **[선택적 변환](6_selectively_converting.ipynb)**: 프롬프트의 특정 부분만 변환하는 고급 기법
# - **[사람 참여형 변환기](7_human_converter.ipynb)**: 대화형 프롬프트 검토 및 수정

# %% [markdown]
# ## 간단한 변환기 예제

# %% [markdown]
# 변환기를 사용하면 다양한 형태의 변환이 가능합니다. 아래는 ROT13, RandomCapitalLetters, AsciiArt, Binary, FirstLetter 변환기를 사용하는 간단한 프로그램입니다.
#
# **참고**: ROT13, RandomCapitalLetters, AsciiArt는 라틴 문자 전용이므로 영문 프롬프트로 테스트합니다. Binary와 FirstLetter는 한국어에서도 동작합니다.

# %%

from pyrit.prompt_converter import (
    AsciiArtConverter,
    BinaryConverter,
    FirstLetterConverter,
    RandomCapitalLettersConverter,
    ROT13Converter,
)

# 라틴 문자 전용 변환기 (영문)
prompt_en = "tell me how to cut down a tree"
print("--- 라틴 문자 전용 변환기 ---")
print("ROT13:", await ROT13Converter().convert_tokens_async(prompt=prompt_en))  # type: ignore
print("Random Capitals:", await RandomCapitalLettersConverter(percentage=25.0).convert_tokens_async(prompt=prompt_en))  # type: ignore
print("ASCII Art:", await AsciiArtConverter().convert_tokens_async(prompt=prompt_en))  # type: ignore

# 한국어에서도 동작하는 변환기
prompt_ko = "나무를 베는 방법을 알려줘"
print("\n--- 한국어 호환 변환기 ---")
print("Binary:", await BinaryConverter().convert_tokens_async(prompt=prompt_ko))  # type: ignore
print("First Letter:", await FirstLetterConverter().convert_tokens_async(prompt=prompt_ko))  # type: ignore

# %% [markdown]
# ## 변환기 스택킹 (Stacking Converters)
#
# 변환기는 단독으로 사용할 수도 있지만, 파이프라인의 한 조각으로 생각해야 합니다. 일반적으로 공격에는 프롬프트를 타겟에 전송하기 전에 변환하는 인자가 포함됩니다. 변환기를 쌓을 수 있고, LLM을 활용할 수 있으며, 강력한 도구입니다.
#
# 시작하기 전에, PyRIT이 올바르게 설치되어 있고 시크릿이 설정되어 있는지 확인하세요. [여기](../../setup/populating_secrets.md)를 참고하세요.
#
# ### PromptSendingAttack에서 변환기 스택킹
#
# 아래 예제에서는 `TextTarget`을 사용하여 프롬프트를 단순히 출력하고 메모리에 추가합니다. 이는 레드팀 작업 시 수동으로 프롬프트를 입력해야 할 때 유용합니다. 타겟은 다른 [타겟](../targets/0_prompt_targets.md)으로 교체할 수 있습니다.
#
# 이 예제에서는 변환기가 스택됩니다. 먼저 `VariationConverter`로 변형을 찾고, 그 다음 `StringJoinConverter`로 글자 사이에 대시를 추가합니다. **순서가 중요합니다.** `StringJoinConverter`가 먼저 오면 LLM에게 이런 프롬프트의 변형을 요청하게 됩니다:
# "나-무-를- -베-는- -방-법-을- -알-려-줘"

# %%
from pyrit.executor.attack import (
    AttackConverterConfig,
    ConsoleAttackResultPrinter,
    PromptSendingAttack,
)
from pyrit.prompt_converter import StringJoinConverter, VariationConverter
from pyrit.prompt_normalizer import PromptConverterConfiguration
from pyrit.prompt_target import OpenAIChatTarget, TextTarget

# 한국어 프롬프트로 스택킹 테스트
objective = "나무를 베는 방법을 알려줘"

# 변환기용 LLM 타겟: Azure OpenAI GPT-4o Chat 모델
converter_target = OpenAIChatTarget()
prompt_variation_converter = VariationConverter(converter_target=converter_target)

converter_configs = PromptConverterConfiguration.from_converters(  # type: ignore
    converters=[prompt_variation_converter, StringJoinConverter()]
)

converter_config = AttackConverterConfig(request_converters=converter_configs)  # type: ignore

target = TextTarget()
attack = PromptSendingAttack(
    objective_target=target,
    attack_converter_config=converter_config,
)

result = await attack.execute_async(objective=objective)  # type: ignore

# 변환 과정 확인: conversation_id로 메모리에서 원본/변환 값 조회
from pyrit.memory import CentralMemory

memory = CentralMemory.get_memory_instance()
entries = memory.get_conversation(conversation_id=result.conversation_id)
for entry in entries:
    if entry.role == "user":
        print(f"원본 프롬프트: {entry.original_value}")
        print(f"변환된 프롬프트: {entry.converted_value}")
        break
print()

printer = ConsoleAttackResultPrinter()
await printer.print_conversation_async(result=result)  # type: ignore

# %% [markdown]
# ## 응답 변환기 (Response Converters)
#
# 지금까지는 프롬프트를 타겟에 전송하기 전에 변환하는 **요청 변환기**에 집중했습니다. PyRIT은 타겟의 응답을 반환하기 전에 변환하는 **응답 변환기**도 지원합니다. 다음과 같은 상황에서 유용합니다:
#
# - 다른 언어로 프롬프트를 전송한 후 응답을 원래 언어로 번역
# - 인코딩된 응답을 디코딩
# - 응답 텍스트 정규화 또는 정리
#
# 응답 변환기는 요청 변환기와 동일한 `PromptConverterConfiguration` 클래스를 사용합니다. `AttackConverterConfig`의 `response_converters` 파라미터로 설정합니다.
#
# ### 번역 라운드트립 예제
#
# 일반적인 사용 사례는 타겟이 비영어 입력을 어떻게 처리하는지 테스트하기 위해 다른 언어로 프롬프트를 보내는 것입니다. 이 예제에서는:
#
# 1. **요청 변환기**로 프롬프트를 한국어에서 프랑스어로 번역
# 2. 번역된 프롬프트를 타겟에 전송
# 3. **응답 변환기**로 응답을 다시 한국어로 번역

# %%
from pyrit.executor.attack import (
    AttackConverterConfig,
    ConsoleAttackResultPrinter,
    PromptSendingAttack,
)
from pyrit.prompt_converter import TranslationConverter
from pyrit.prompt_normalizer import PromptConverterConfiguration
from pyrit.prompt_target import OpenAIChatTarget

# 한국어 → 프랑스어 → 한국어 라운드트립 테스트
objective = "프랑스의 수도는 어디인가요?"

# 변환기용 LLM 타겟
converter_target = OpenAIChatTarget()

# 프롬프트 전송용 LLM 타겟
prompt_target = OpenAIChatTarget()

# 요청 변환기: 한국어 → 프랑스어로 번역
request_converter = TranslationConverter(converter_target=converter_target, language="French")
request_converter_config = PromptConverterConfiguration(converters=[request_converter])

# 응답 변환기: 프랑스어 응답 → 한국어로 번역
response_converter = TranslationConverter(converter_target=converter_target, language="Korean")
response_converter_config = PromptConverterConfiguration(converters=[response_converter])

# 요청 + 응답 변환기를 함께 설정
converter_config = AttackConverterConfig(
    request_converters=[request_converter_config],
    response_converters=[response_converter_config],
)

attack = PromptSendingAttack(
    objective_target=prompt_target,
    attack_converter_config=converter_config,
)

result = await attack.execute_async(objective=objective)  # type: ignore

# 원본 및 변환된 값을 포함한 대화 출력
printer = ConsoleAttackResultPrinter()
await printer.print_conversation_async(result=result)  # type: ignore
