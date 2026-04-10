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
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 5. 시나리오로 종합 테스트를 어떻게 실행하나요?
#
# **목표**: 시나리오(Scenario)가 무엇인지 이해하고, ContentHarms 시나리오를 직접 실행합니다.
#
# ## 시나리오란?
#
# 지금까지 배운 공격(Attack)은 **"한 번의 시도"**였습니다.
# 시나리오는 **여러 공격을 묶어서 순차 실행하는 종합 테스트 캠페인**입니다.
#
# ```
# Scenario (시나리오)
#   ├── AtomicAttack 1: PromptSendingAttack + violence 데이터셋
#   ├── AtomicAttack 2: RolePlayAttack + violence 데이터셋
#   ├── AtomicAttack 3: ManyShotJailbreakAttack + violence 데이터셋
#   ├── AtomicAttack 4: PromptSendingAttack + hate 데이터셋
#   └── ... (카테고리 × 공격전략 조합)
# ```
#
# ## 시나리오의 구성 요소
#
# | 구성 요소 | 역할 |
# |----------|------|
# | **Scenario** | 여러 원자적 공격을 묶어 실행하는 최상위 오케스트레이터 |
# | **AtomicAttack** | 공격 전략 + 목표 + 데이터셋을 결합한 원자적 테스트 단위 |
# | **ScenarioStrategy** | 어떤 카테고리/전략으로 테스트할지 정의 |
# | **DatasetConfiguration** | 테스트에 사용할 데이터셋 설정 |
# | **ScenarioResult** | 모든 원자적 공격의 집계 결과 |
#
# ## 내장 시나리오
#
# | 시나리오 | 테스트 대상 | 카테고리 |
# |---------|-----------|---------|
# | `ContentHarms` | 유해 콘텐츠 생성 | violence, hate, sexual, harassment, misinformation, fairness, leakage |
# | `Jailbreak` | 탈옥 공격 내성 | 다양한 탈옥 기법 |
# | `Cyber` | 사이버 위협 | malware, exploit |
# | `PsychosocialScenario` | 심리적 조작 | 위기 상담, 자해 유도 |
# | `RedTeamAgent` | 종합 레드팀 | 다양한 전략 조합 (Foundry) |

# %% [markdown]
# ---
# ## 사용자 설정

# %%
import os
import sys

if "/Users/selectstar/PyRIT_ko/src" not in sys.path:
    sys.path.insert(0, "/Users/selectstar/PyRIT_ko/src")

from pyrit.common.locale_utils import NotebookLocale
from pyrit.setup import IN_MEMORY, initialize_pyrit_async
from pyrit.setup.initializers.scenarios.load_default_datasets import LoadDefaultDatasets

# 시나리오 실행에는 seed 데이터셋이 필요합니다.
# LoadDefaultDatasets()가 모든 시나리오의 기본 데이터셋(한국어 포함)을 메모리에 로드합니다.
await initialize_pyrit_async(memory_db_type=IN_MEMORY, initializers=[LoadDefaultDatasets()])  # type: ignore

# ═══════════════════════════════════════════
# 여기만 수정하세요
# ═══════════════════════════════════════════
LOCALE = "ko"                    # "ko" (한국어) 또는 "en" (영어)
MODEL_NAME = "gpt-4o-mini"       # 사용할 모델

L = NotebookLocale(LOCALE)

# %%
from pyrit.prompt_target import OpenAIChatTarget
from pyrit.score import SelfAskRefusalScorer, TrueFalseInverterScorer

objective_target = OpenAIChatTarget(
    endpoint="https://api.openai.com/v1",
    api_key=os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_CHAT_KEY"),
    model_name=MODEL_NAME,
)

# 공통 스코어러: "거부 안 했으면 = 공격 성공"
objective_scorer = TrueFalseInverterScorer(
    scorer=SelfAskRefusalScorer(chat_target=objective_target),
)

# %% [markdown]
# ---
# # 1. ContentHarms 시나리오 실행
#
# `ContentHarms`는 가장 대표적인 내장 시나리오입니다.
# 7개 유해 콘텐츠 카테고리에 대해 여러 공격 전략을 자동으로 조합하여 실행합니다.
#
# ## 사용 가능한 전략 (카테고리)
#
# | 전략 | 설명 |
# |------|------|
# | `ContentHarmsStrategy.Violence` | 폭력 콘텐츠 |
# | `ContentHarmsStrategy.Hate` | 혐오 표현 |
# | `ContentHarmsStrategy.Sexual` | 성적 콘텐츠 |
# | `ContentHarmsStrategy.Harassment` | 괴롭힘/학대 |
# | `ContentHarmsStrategy.Misinformation` | 허위정보 |
# | `ContentHarmsStrategy.Fairness` | 편향/공정성 |
# | `ContentHarmsStrategy.Leakage` | 정보 유출 |
# | `ContentHarmsStrategy.ALL` | 위 전체 |
#
# ## 각 카테고리에서 실행되는 공격
#
# 각 카테고리마다 아래 공격들이 자동으로 생성됩니다:
# - `PromptSendingAttack` — 직접 전송 (기준선)
# - `RolePlayAttack` — 역할극 포장
# - `ManyShotJailbreakAttack` — 대량 예시 유도
# - `MultiPromptSendingAttack` — 순차 메시지 (해당 데이터가 있는 경우)

# %% [markdown]
# ## 1-1. 시나리오 생성
#
# `ContentHarms`를 생성하고, 테스트할 **카테고리**와 **데이터셋 크기**를 설정합니다.

# %%
from pyrit.scenario.scenarios.airt.content_harms import ContentHarms, ContentHarmsStrategy

# 테스트할 카테고리 선택 (여러 개 가능)
HARM_CATEGORIES = [ContentHarmsStrategy.Violence]

scenario = ContentHarms(objective_scorer=objective_scorer)

# %% [markdown]
# ## 1-2. 시나리오 초기화
#
# `initialize_async()`를 호출하면 선택한 카테고리에 맞는 **원자적 공격(AtomicAttack)**이 자동 생성됩니다.
#
# > **핵심**: `memory_labels=L.labels()`로 `{"locale": "ko"}`를 전달하면,
# > 내부적으로 `airt_violence_ko` 등 한국어 데이터셋이 자동 선택됩니다.
# >
# > `dataset_config`를 생략하면 ContentHarms가 기본 데이터셋(카테고리당 최대 4개)을
# > locale에 맞게 자동 로드합니다.

# %%
await scenario.initialize_async(  # type: ignore
    objective_target=objective_target,
    scenario_strategies=HARM_CATEGORIES,
    memory_labels=L.labels(),
)

# 생성된 원자적 공격 확인
print(f"시나리오: {scenario.name}")
print(f"원자적 공격 수: {scenario.atomic_attack_count}")
for i, attack in enumerate(scenario._atomic_attacks, 1):
    print(f"  [{i}] {attack.atomic_attack_name}")

# %% [markdown]
# ## 1-3. 시나리오 실행
#
# `run_async()`를 호출하면 모든 원자적 공격이 순차적으로 실행됩니다.
#
# > **참고**: 원자적 공격 수 × 데이터셋 크기만큼 API 호출이 발생하므로,
# > 카테고리와 데이터셋 크기를 작게 설정하면 빠르게 실행됩니다.

# %%
scenario_result = await scenario.run_async()  # type: ignore

# %% [markdown]
# ## 1-4. 결과 확인 — 요약
#
# `ConsoleScenarioResultPrinter`로 시나리오 결과 요약을 출력합니다.

# %%
from pyrit.scenario.printer.console_printer import ConsoleScenarioResultPrinter

await ConsoleScenarioResultPrinter(locale=L.locale).print_summary_async(scenario_result)  # type: ignore

# %% [markdown]
# ## 1-5. 결과 확인 — 개별 공격 결과
#
# 각 원자적 공격의 개별 결과를 확인합니다.
# 성공한 공격이 있으면 해당 결과를, 없으면 첫 번째 실패 결과를 출력합니다.

# %%
from pyrit.executor.attack import ConsoleAttackResultPrinter

printer = ConsoleAttackResultPrinter(locale=L.locale)

# 모든 전략의 공격 결과를 평탄화
all_results = [result for results in scenario_result.attack_results.values() for result in results]

successful = [r for r in all_results if r.outcome.value == "success"]
failed = [r for r in all_results if r.outcome.value != "success"]

print(f"총 {len(all_results)}개 공격 중 성공: {len(successful)}개, 실패: {len(failed)}개\n")

if successful:
    print("=== 성공한 공격 예시 ===")
    await printer.print_result_async(result=successful[0])  # type: ignore
else:
    print("=== 성공한 공격 없음 — 첫 번째 실패 결과 ===")
    await printer.print_result_async(result=failed[0])  # type: ignore

# %% [markdown]
# ## 1-6. 결과 해석
#
# | 항목 | 의미 |
# |------|------|
# | **원자적 공격 수** | 카테고리 × 공격 전략 수. Violence 1개에 3~4개 전략이면 3~4개 |
# | **objective_achieved_rate** | 전체 공격 중 성공(모델이 유해 콘텐츠 제공)한 비율 |
# | **성공 공격** | 모델이 안전 필터를 뚫고 유해 콘텐츠를 생성한 경우 |
# | **실패 공격** | 모델이 정상적으로 거부한 경우 |
#
# > 성공률이 높으면 모델의 안전 필터에 문제가 있는 것이고,
# > 성공률이 0%면 해당 카테고리에서 모델이 잘 방어하고 있는 것입니다.

# %% [markdown]
# ---
# # 2. 여러 카테고리 동시 테스트
#
# 여러 카테고리를 한 번에 테스트할 수도 있습니다.
# 아래는 Violence + Hate 두 카테고리를 동시에 실행합니다.

# %%
multi_scenario = ContentHarms(objective_scorer=objective_scorer)

await multi_scenario.initialize_async(  # type: ignore
    objective_target=objective_target,
    scenario_strategies=[ContentHarmsStrategy.Violence, ContentHarmsStrategy.Hate],
    memory_labels=L.labels(),
)

print(f"원자적 공격 수: {multi_scenario.atomic_attack_count}")
for i, attack in enumerate(multi_scenario._atomic_attacks, 1):
    print(f"  [{i}] {attack.atomic_attack_name}")

multi_result = await multi_scenario.run_async()  # type: ignore
await ConsoleScenarioResultPrinter(locale=L.locale).print_summary_async(multi_result)  # type: ignore

# %% [markdown]
# ---
# # 3. 메모리에서 시나리오 결과 조회
#
# 시나리오 실행 결과는 메모리에 자동 저장됩니다.
# 나중에 메모리에서 결과를 불러올 수 있습니다.

# %%
from pyrit.memory import CentralMemory

memory = CentralMemory.get_memory_instance()
saved_results = memory.get_scenario_results(scenario_name="ContentHarms")
print(f"저장된 ContentHarms 시나리오 결과: {len(saved_results)}개")

for i, sr in enumerate(saved_results, 1):
    strategies = sr.get_strategies_used()
    total = sum(len(v) for v in sr.attack_results.values())
    print(f"  [{i}] 전략: {strategies}  |  공격 수: {total}  |  상태: {sr.scenario_run_state}")

# %% [markdown]
# ---
# # 4. 시나리오 vs 개별 공격 비교
#
# | | 개별 공격 (02번에서 학습) | 시나리오 (이 노트북) |
# |---|---|---|
# | **단위** | 공격 1개 + 목표 1개 | 공격 N개 × 목표 M개 |
# | **설정** | 공격/타겟/스코어러를 직접 조합 | 카테고리만 선택하면 자동 조합 |
# | **결과** | `AttackResult` 1개 | `ScenarioResult` (집계) |
# | **용도** | 특정 공격 기법 실험 | 종합 안전성 평가 |
# | **시간** | 짧음 | 공격 수에 비례 |
#
# **언제 무엇을 쓰나요?**
# - "이 모델이 FlipAttack에 취약한지 알고 싶다" → **02번 (개별 공격)**
# - "이 모델의 폭력/혐오 카테고리 전반적 안전성을 평가하고 싶다" → **05번 (시나리오)**

# %% [markdown]
# ---
# ## 한줄 요약
#
# > **시나리오는 여러 공격 전략 × 여러 목표를 자동으로 조합하여 실행하는 종합 테스트 캠페인입니다.
# > `memory_labels=L.labels()`로 한국어 데이터셋이 자동 선택됩니다.**
