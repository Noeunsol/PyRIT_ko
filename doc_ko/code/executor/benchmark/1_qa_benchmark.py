# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
#   kernelspec:
#     display_name: pyrit-312
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 1. 질의응답(Q&A) 벤치마크
#
# `QuestionAnsweringBenchmark`는 Q&A 데이터셋을 사용해 타겟 모델의 정답률을 평가합니다.

# %%
import os
import sys
from typing import Optional

# 노트북에서 로컬 PyRIT 소스를 우선 참조
if "/Users/selectstar/PyRIT_ko/src" not in sys.path:
    sys.path.insert(0, "/Users/selectstar/PyRIT_ko/src")

from pyrit.common.locale_utils import NotebookLocale
from pyrit.datasets.seed_datasets.remote.wmdp_dataset import fetch_wmdp_dataset
from pyrit.executor.attack import AttackScoringConfig, ConsoleAttackResultPrinter
from pyrit.executor.benchmark import QuestionAnsweringBenchmark
from pyrit.models import AttackOutcome, QuestionAnsweringEntry, QuestionChoice
from pyrit.prompt_converter import TranslationConverter
from pyrit.prompt_target import OpenAIChatTarget
from pyrit.score import SelfAskQuestionAnswerScorer
from pyrit.setup import IN_MEMORY, initialize_pyrit_async

# 언어 스위치: "ko" 또는 "en"
L = NotebookLocale("ko")


# PyRIT 초기화 (환경 파일 로드 + 중앙 메모리 인스턴스 설정)
await initialize_pyrit_async(memory_db_type=IN_MEMORY)  # type: ignore


def create_openai_target() -> OpenAIChatTarget:
    return OpenAIChatTarget(
        endpoint="https://api.openai.com/v1",
        api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_CHAT_KEY"),
        model_name="gpt-4o-mini",
    )


# 벤치마크 채점 구성
scoring_config = AttackScoringConfig(
    objective_scorer=SelfAskQuestionAnswerScorer(chat_target=create_openai_target())
)

# 벤치마크 객체 생성
benchmark = QuestionAnsweringBenchmark(
    objective_target=create_openai_target(),
    attack_scoring_config=scoring_config,
)

# WMDP에는 현재 ko 전용 원본이 없어, ko 선택 시 질문/선지를 한국어로 변환해 평가합니다.
translator: Optional[TranslationConverter] = None
if L.locale == "ko":
    translator = TranslationConverter(converter_target=create_openai_target(), language="Korean", locale=L.locale)


async def localize_qa_entry(entry: QuestionAnsweringEntry) -> QuestionAnsweringEntry:
    if not translator:
        return entry

    translated_question = (await translator.convert_async(prompt=entry.question)).output_text  # type: ignore
    translated_choices = []
    for choice in entry.choices:
        translated_choice = (await translator.convert_async(prompt=choice.text)).output_text  # type: ignore
        translated_choices.append(QuestionChoice(index=choice.index, text=translated_choice))

    return QuestionAnsweringEntry(
        question=translated_question,
        answer_type=entry.answer_type,
        correct_answer=entry.correct_answer,
        choices=translated_choices,
    )

sample_question = QuestionAnsweringEntry(
    question=L.pick(en="What is the capital of France?", ko="프랑스의 수도는 어디인가요?"),
    answer_type="str",
    correct_answer=0,
    choices=[
        QuestionChoice(index=0, text=L.pick(en="Paris", ko="파리")),
        QuestionChoice(index=1, text=L.pick(en="London", ko="런던")),
        QuestionChoice(index=2, text=L.pick(en="Berlin", ko="베를린")),
        QuestionChoice(index=3, text=L.pick(en="Madrid", ko="마드리드")),
    ],
)

result = await benchmark.execute_async(
    question_answering_entry=sample_question,
    memory_labels=L.labels(benchmark="qa_demo"),
)  # type: ignore
await ConsoleAttackResultPrinter(locale=L.locale).print_conversation_async(result=result)  # type: ignore

# %%
# WMDP Q&A 데이터셋 로드 (네트워크 환경에 따라 시간이 걸릴 수 있음)
wmdp_ds = fetch_wmdp_dataset(category="cyber")
print(L.pick(en="Loaded WMDP question count:", ko="로드된 WMDP 문항 수:"), len(wmdp_ds.questions))

# %%
# Q&A 응답 평가
results = []
for wmdp_question in wmdp_ds.questions[:3]:
    localized_question = await localize_qa_entry(wmdp_question)  # type: ignore
    result = await benchmark.execute_async(
        question_answering_entry=localized_question,
        memory_labels=L.labels(benchmark="wmdp_sample", category="cyber"),
    )  # type: ignore
    results.append(result)
    await ConsoleAttackResultPrinter(locale=L.locale).print_conversation_async(result=result)  # type: ignore

# %% [markdown]
# 벤치마크 결과에 대해 커스텀 분석을 수행할 수 있습니다.
# 아래 예시는 `AttackResult`에서 정답 비율을 계산하는 방법입니다.

# %%
success = sum(r.outcome == AttackOutcome.SUCCESS for r in results)
print(L.pick(en="Success rate:", ko="정답률:"), f"{(success / len(results)) * 100:.2f}%")
