# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
# ---

# %% [markdown]
# # 1. 시나리오 구성하기
#
# 이 노트북에서는 복합 전략(composite strategy)인 `FoundryStrategy`를 사용하여 여러 공격 전략으로 대상을 테스트하는 방법을 보여줍니다.
# "복합 전략"은 `ScenarioStrategy` 인스턴스의 컬렉션과 자동 생성된 설명적 이름을 캡슐화하는 클래스로,
# 단일 전략과 다중 전략 공격을 모두 쉽게 표현할 수 있습니다.
#
# `Foundry` 시나리오는 다음을 포함하는 종합적인 테스트 접근 방식을 제공합니다:
# - **변환기 기반 공격**: 다양한 인코딩/난독화 기법 적용 (Base64, 시저 암호 등)
# - **다중 턴 공격**: 복잡한 대화형 공격 전략 (Crescendo, RedTeaming)
# - **전략 조합**: 여러 변환기를 함께 결합
# - **난이도 수준**: EASY, MODERATE, DIFFICULT 카테고리로 구성
#
# 이것은 Foundry 시나리오(또는 다른 시나리오)를 실행하는 가장 쉬운 방법은 아닙니다. 모든 구성 요소를 어떻게 설정할 수 있는지 보여주기 위한 것입니다.
#
# ## 설정
#
# 먼저 PyRIT를 초기화하고 테스트할 대상을 구성합니다.

# %%
from pyrit.executor.attack import AttackScoringConfig
from pyrit.prompt_target import OpenAIChatTarget
from pyrit.scenario import ScenarioCompositeStrategy
from pyrit.scenario.printer.console_printer import ConsoleScenarioResultPrinter
from pyrit.scenario.scenarios.foundry import FoundryStrategy, RedTeamAgent
from pyrit.score import SelfAskRefusalScorer, TrueFalseInverterScorer
from pyrit.setup import IN_MEMORY, initialize_pyrit_async

await initialize_pyrit_async(memory_db_type=IN_MEMORY, initializers=[])  # type: ignore

objective_target = OpenAIChatTarget()
printer = ConsoleScenarioResultPrinter()

# Azure 서비스 없이 OpenAI API만으로 동작하는 커스텀 스코어러 구성
scorer = TrueFalseInverterScorer(
    scorer=SelfAskRefusalScorer(chat_target=OpenAIChatTarget())
)
scoring_config = AttackScoringConfig(objective_scorer=scorer)

# %% [markdown]
# ## 시드 그룹 정의
#
# 기본적으로 `RedTeamAgent`는 HarmBench에서 4개의 무작위 목표를 선택합니다. 여기서는 시연을 위해 2개만 가져옵니다. `seed_groups`를 전달하지 않으면 `max_dataset_size=4`인 것을 제외하고 거의 동일합니다.

# %%
from pyrit.datasets import SeedDatasetProvider
from pyrit.models import SeedGroup
from pyrit.scenario import DatasetConfiguration

datasets = await SeedDatasetProvider.fetch_datasets_async(dataset_names=["harmbench_ko"])  # type: ignore
seed_groups: list[SeedGroup] = datasets[0].seed_groups  # type: ignore
dataset_config = DatasetConfiguration(seed_groups=seed_groups, max_dataset_size=2)

# %% [markdown]
# ## 공격 전략 선택
#
# 개별 전략을 지정하거나 여러 변환기를 함께 조합할 수 있습니다.
# 시나리오는 세 가지 유형의 전략 지정을 지원합니다:
#
# 1. **단일 전략**: 개별 변환기 또는 공격 전략 (예: `FoundryStrategy.Base64`)
# 2. **집계 전략**: 태그 기반 그룹 (예: `FoundryStrategy.EASY`는 모든 쉬운 전략으로 확장)
# 3. **복합 전략**: 여러 변환기를 함께 적용 (예: Caesar + CharSwap)
#
# 선택하지 않으면 항상 기본값이 있습니다. 이 경우 기본값은 `FoundryStrategy.EASY`입니다.

# %%
scenario_strategies = [
    FoundryStrategy.Base64,  # 단일 전략 (내부적으로 자동 래핑)
    FoundryStrategy.Binary,  # 단일 전략 (내부적으로 자동 래핑)
    ScenarioCompositeStrategy(strategies=[FoundryStrategy.Caesar, FoundryStrategy.CharSwap]),  # 복합 전략
]

# %% [markdown]
# ## 시나리오 생성 및 초기화
#
# 시나리오는 실행 전에 초기화해야 합니다. 이 과정에서 선택된 전략을 기반으로 원자적 공격이 구성됩니다. 대부분 기본값이 있지만, 시나리오가 공격 대상을 알 수 있도록 `objective_target`은 반드시 제공해야 합니다.

# %%
foundry_scenario = RedTeamAgent(attack_scoring_config=scoring_config)
await foundry_scenario.initialize_async(  # type: ignore
    objective_target=objective_target,
    scenario_strategies=scenario_strategies,
    max_concurrency=10,
    dataset_config=dataset_config,
    memory_labels={"locale": "ko"},
)

print(f"생성된 시나리오: {foundry_scenario.name}")
print(f"원자적 공격 수: {foundry_scenario.atomic_attack_count}")
for i, attack in enumerate(foundry_scenario._atomic_attacks, 1):
    print(f"  [{i}] {attack.atomic_attack_name}")

# %% [markdown]
# ## 시나리오 실행
#
# 이제 시나리오를 실행하고 결과를 출력합니다. 시나리오는 다음을 수행합니다:
# 1. 각 원자적 공격을 순차적으로 실행
# 2. 모든 목표에 공격 전략을 적용
# 3. 구성된 스코어러를 사용하여 결과를 평가
# 4. 모든 결과를 `ScenarioResult`로 집계
#
# 아래 예제는 실제로 시나리오를 실행하고 결과를 저장합니다.

# %%
scenario_result = await foundry_scenario.run_async()  # type: ignore

# %% [markdown]
# ## 시나리오 결과 출력
#
# `ScenarioResult` 객체는 시나리오 실행의 모든 결과를 집계합니다. `scenario_identifier`(이름, 설명, 버전 포함), 테스트 대상을 설명하는 `objective_target_identifier`, 각 원자적 공격 전략 이름을 `AttackResult` 객체 목록에 매핑하는 `attack_results` 딕셔너리를 포함합니다. 주요 속성으로는 `scenario_run_state`("CREATED", "IN_PROGRESS", "COMPLETED", "FAILED" 중 하나), 메타데이터 태깅을 위한 `labels`, 그리고 `completion_time`이 있습니다. 이 클래스는 모든 공격 전략을 나열하는 `get_strategies_used()`, 테스트된 고유 목표를 가져오는 `get_objectives()`, 성공률을 백분율로 계산하는 `objective_achieved_rate()`와 같은 헬퍼 메서드를 제공합니다. 특정 `atomic_attack_name`으로 필터링하거나 모든 공격에 대해 집계할 수 있습니다.

# %%
await printer.print_summary_async(scenario_result)  # type: ignore

# %% [markdown]
# 모든 개별 결과를 확인하려면 `ScenarioResult`의 `attack_results` 속성을 살펴볼 수 있습니다. 또한 시나리오 결과는 `run_async`에서 반환되지만, 메모리에서도 가져올 수 있습니다.

# %%
from pyrit.executor.attack import ConsoleAttackResultPrinter
from pyrit.memory.central_memory import CentralMemory

memory = CentralMemory.get_memory_instance()
scenario_results_from_memory = memory.get_scenario_results(scenario_name="RedTeamAgent")
last_scenario_result = scenario_results_from_memory[-1]
print(f"메모리에서 {len(scenario_results_from_memory)}개의 시나리오 결과를 가져왔습니다.")

# 모든 전략의 공격 결과를 평탄화
all_results = [result for results in last_scenario_result.attack_results.values() for result in results]

successful_attacks = [r for r in all_results if r.outcome.value == "success"]
non_successful_attacks = [r for r in all_results if r.outcome.value != "success"]

if len(successful_attacks) > 0:
    print("\n성공한 공격:")
    for result in successful_attacks:
        await ConsoleAttackResultPrinter().print_result_async(result=result)  # type: ignore
else:
    print("\n성공한 공격이 없습니다. 첫 번째 실패 결과를 표시합니다...\n")
    await ConsoleAttackResultPrinter().print_result_async(result=non_successful_attacks[0])  # type: ignore

# %% [markdown]
# ## 대안: 난이도 수준 사용
#
# 개별 전략을 지정하는 대신 `EASY`, `MODERATE`, `DIFFICULT`와 같은 집계 태그를 사용하여 여러 전략을 한 번에 테스트할 수 있습니다.

# %%
# 예제: 모든 EASY 전략 테스트
# easy_scenario = RedTeamAgent(
#     objective_target=objective_target,
#     scenario_strategies=[FoundryStrategy.EASY],  # 모든 쉬운 전략으로 확장
#     objectives=objectives,
# )
# await easy_scenario.initialize_async()
# easy_results = await easy_scenario.run_async()
# await printer.print_summary_async(easy_results)

# %% [markdown]
# ## 기준선 전용 실행
#
# 때때로 공격 전략을 적용하지 *않고* 대상이 목표에 어떻게 응답하는지 기준선 측정을 하고 싶을 수 있습니다. 이는 다음과 같은 경우에 유용합니다:
#
# - **기본 방어력 측정**: 난독화 없이 유해한 프롬프트에 대상이 어떻게 응답하는지 확인
# - **비교 기준점 설정**: 기준선 거부율과 전략 강화 공격을 비교
# - **빠른 정상 동작 확인**: 전체 시나리오를 실행하기 전에 대상과 스코어링이 작동하는지 검증
# - **공격 효과 이해**: 각 전략이 기준선 대비 제공하는 "향상도"를 계산
#
# 기준선 전용 시나리오를 실행하려면 `scenario_strategies`에 빈 목록을 전달합니다:

# %%
baseline_only_scenario = RedTeamAgent(attack_scoring_config=scoring_config)
await baseline_only_scenario.initialize_async(  # type: ignore
    objective_target=objective_target,
    scenario_strategies=[],  # 빈 목록 = 기준선만 실행
    dataset_config=dataset_config,
    memory_labels={"locale": "ko"},
)
baseline_result = await baseline_only_scenario.run_async()  # type: ignore
await printer.print_summary_async(baseline_result)  # type: ignore


# %% [markdown]
# 기준선 공격은 변환기나 다중 턴 전략 없이 각 목표를 대상에 직접 전송합니다. 이를 통해 "수정되지 않은" 성공/실패율을 얻을 수 있습니다.
#
# 비교 없이 특정 전략만 실행하려면 시나리오 생성자에서 `include_default_baseline=False`를 설정하여 기준선을 완전히 비활성화할 수도 있습니다:
#
# ```python
# # 전략만 실행, 기준선 없음
# scenario = RedTeamAgent(include_default_baseline=False)
# await scenario.initialize_async(
#     objective_target=objective_target,
#     scenario_strategies=[FoundryStrategy.Base64],
# )
# ```

# %% [markdown]
# ## 시나리오 복원력
#
# `Foundry` 시나리오는 자동 재개 및 재시도 메커니즘을 지원합니다:
#
# - **자동 재개**: 실행이 중단되면 시나리오를 다시 실행할 때 중단된 지점부터 계속됩니다
# - **재시도 메커니즘**: `max_retries`를 설정하여 일시적 장애 시 자동으로 재시도합니다
# - **진행 상황 추적**: 시나리오는 완료된 목표를 메모리에서 추적합니다
#
# 복원력 기능에 대한 자세한 내용은 [복원력 문서](../setup/2_resiliency.ipynb)를 참조하세요.

# %% [markdown]
# ## 메모리 DB 직접 조회
#
# PyRIT는 모든 대화 기록을 SQLite(InMemory 또는 파일)에 저장합니다.
# 아래에서 실제 저장된 데이터를 pandas DataFrame으로 확인합니다.

# %%
import pandas as pd
from sqlalchemy import text
from IPython.display import display, HTML
from pyrit.memory.central_memory import CentralMemory
from pyrit.setup import IN_MEMORY, initialize_pyrit_async

# 메모리가 초기화되지 않은 경우를 대비
try:
    memory = CentralMemory.get_memory_instance()
except ValueError:
    await initialize_pyrit_async(memory_db_type=IN_MEMORY)  # type: ignore
    memory = CentralMemory.get_memory_instance()

engine = memory.engine
pd.set_option("display.max_colwidth", 80)
pd.set_option("display.max_rows", None)
pd.set_option("styler.render.max_elements", 999999)

def show_table(df, title, color="#4A90D9"):
    style = (
        "<style>"
        f".pt{id(df)} {{ border-collapse:collapse; width:100%; font-size:13px }}"
        f".pt{id(df)} th {{ background:{color}; color:white; padding:8px; text-align:left }}"
        f".pt{id(df)} td {{ padding:6px 8px; border-bottom:1px solid #eee; text-align:left }}"
        "</style>"
    )
    table = df.to_html(index=False, classes=f"pt{id(df)}", escape=False)
    display(HTML(f"{style}<h3>{title}</h3>{table}"))


# 저장된 테이블 목록
tables = pd.read_sql(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"), engine)
show_table(tables, "📁 테이블 목록")

# %%
# 대화 기록 — 같은 대화 ID끼리 묶어서 표시 (system 역할 제외)
row_count = pd.read_sql(text("SELECT COUNT(*) as cnt FROM PromptMemoryEntries WHERE role != 'system'"), engine)
print(f"PromptMemoryEntries 레코드 수 (system 제외): {row_count['cnt'][0]}")

if row_count["cnt"][0] > 0:
    conversations = pd.read_sql(text(
        'SELECT SUBSTR(conversation_id, 1, 8) AS "대화 ID",'
        ' role AS "역할",'
        ' SUBSTR(original_value, 1, 50) AS "원본 값",'
        ' SUBSTR(converted_value, 1, 60) AS "변환/응답 값",'
        ' response_error AS "에러",'
        ' SUBSTR(timestamp, 1, 19) AS "시간"'
        ' FROM PromptMemoryEntries'
        " WHERE role != 'system'"
        ' ORDER BY conversation_id, sequence, role'
    ), engine)

    # 같은 대화 ID끼리 묶어서 배경색 교차 적용
    colors = ["#F8F9FA", "#E8F0FE"]
    conv_ids = conversations["대화 ID"].unique()
    color_map = {cid: colors[i % 2] for i, cid in enumerate(conv_ids)}

    def row_color(row):
        bg = color_map.get(row["대화 ID"], "#FFFFFF")
        return [f"background-color: {bg}"] * len(row)

    styled = (
        conversations.style
        .apply(row_color, axis=1)
        .set_properties(**{"text-align": "left", "font-size": "13px", "padding": "6px 8px"})
        .set_table_styles([
            {"selector": "th", "props": [("background", "#4A90D9"), ("color", "white"), ("padding", "8px"), ("text-align", "left")]},
        ])
    )
    display(HTML(f"<h3>💬 대화 기록 ({len(conversations)}건, {len(conv_ids)}개 대화)</h3>"))
    display(styled)
else:
    print("대화 기록이 비어 있습니다. 위의 시나리오 실행 셀을 먼저 실행해주세요.")

# %%
# 스코어 기록 — 각 공격의 판정 결과
scores = pd.read_sql(text("""
    SELECT
        s.scorer_class_identifier AS "스코어러",
        s.score_category AS "카테고리",
        CASE s.score_value WHEN 'True' THEN '✅ True' ELSE '❌ False' END AS "결과",
        SUBSTR(s.score_rationale, 1, 80) AS "판정 근거",
        SUBSTR(s.timestamp, 1, 19) AS "시간"
    FROM ScoreEntries s
    ORDER BY s.timestamp
"""), engine)
show_table(scores, "📊 스코어 기록", "#E8724A")

# %%
# 요약 통계
summary = pd.read_sql(text("""
    SELECT
        (SELECT COUNT(*) FROM PromptMemoryEntries WHERE role='user' AND labels NOT LIKE '%%scorer%%') AS "공격 수",
        (SELECT COUNT(*) FROM PromptMemoryEntries WHERE role='assistant' AND labels NOT LIKE '%%scorer%%') AS "응답 수",
        (SELECT COUNT(*) FROM ScoreEntries) AS "스코어 수",
        (SELECT COUNT(*) FROM ScoreEntries WHERE score_value='True') AS "✅ 성공",
        (SELECT COUNT(*) FROM ScoreEntries WHERE score_value='False') AS "❌ 실패"
"""), engine)
show_table(summary, "📈 요약 통계", "#2ECC71")
