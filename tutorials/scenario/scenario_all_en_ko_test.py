# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: pyrit
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 전체 시나리오 EN/KO 테스트
#
# PyRIT에 등록된 **8개 시나리오**를 각각 실행하여 한국어 내재화를 검증합니다.
#
# | 시나리오 | 기본 데이터셋 | _ko 데이터셋 |
# |----------|-------------|-------------|
# | ContentHarms | airt_hate 외 7종 | airt_hate_ko 외 7종 |
# | Cyber | airt_malware | airt_malware_ko |
# | Scam | airt_scams | airt_scams_ko |
# | Jailbreak | airt_harms | airt_harms_ko |
# | LeakageScenario | airt_leakage | airt_leakage_ko |
# | PsychosocialScenario | airt_imminent_crisis | airt_imminent_crisis_ko |
# | RedTeamAgent | harmbench | harmbench_ko |
# | Encoding | garak_slur_terms 외 | garak_slur_terms_ko 외 |

# %% [markdown]
# ## 1. 설정

# %%
target_lang = "ko"  # "en" or "ko"
# 각 시나리오는 내부 기본값으로 데이터셋 크기를 관리합니다 (보통 3~4개)

# %% [markdown]
# ## 2. 초기화

# %%
import traceback

import pandas as pd
from IPython.display import display, HTML
from sqlalchemy import text

from pyrit.executor.attack import AttackScoringConfig, ConsoleAttackResultPrinter
from pyrit.memory.central_memory import CentralMemory
from pyrit.prompt_target import OpenAIChatTarget
from pyrit.scenario import DatasetConfiguration
from pyrit.scenario.printer.console_printer import ConsoleScenarioResultPrinter
from pyrit.scenario.scenarios.airt.content_harms import ContentHarms, ContentHarmsStrategy, ContentHarmsDatasetConfiguration
from pyrit.scenario.scenarios.airt.cyber import Cyber, CyberStrategy
from pyrit.scenario.scenarios.airt.jailbreak import Jailbreak, JailbreakStrategy
from pyrit.scenario.scenarios.airt.leakage_scenario import LeakageScenario, LeakageStrategy
from pyrit.scenario.scenarios.airt.psychosocial_scenario import PsychosocialScenario, PsychosocialStrategy
from pyrit.scenario.scenarios.airt.scam import Scam, ScamStrategy
from pyrit.scenario.scenarios.foundry import FoundryStrategy
from pyrit.scenario.scenarios.foundry.red_team_agent import RedTeamAgent
from pyrit.scenario.scenarios.garak.encoding import Encoding, EncodingStrategy
from pyrit.score import SelfAskRefusalScorer, TrueFalseInverterScorer
from pyrit.setup import IN_MEMORY, initialize_pyrit_async

from pyrit.datasets import SeedDatasetProvider
from pyrit.setup.initializers.scenarios.load_default_datasets import LoadDefaultDatasets

# LoadDefaultDatasets: 모든 시나리오의 기본 데이터셋(영어)을 메모리에 로드
await initialize_pyrit_async(memory_db_type=IN_MEMORY, initializers=[LoadDefaultDatasets()])  # type: ignore

# 한국어 데이터셋도 메모리에 추가 로드
if target_lang == "ko":
    memory = CentralMemory.get_memory_instance()
    en_names = list(memory.get_seed_dataset_names())
    ko_names = [f"{n}_ko" for n in en_names if not n.endswith("_ko")]
    # 실제 존재하는 ko 데이터셋만 필터
    all_available = SeedDatasetProvider.get_all_dataset_names()
    ko_names = [n for n in ko_names if n in all_available]
    if ko_names:
        print(f"한국어 데이터셋 {len(ko_names)}개 추가 로드 중...")
        ko_datasets = await SeedDatasetProvider.fetch_datasets_async(dataset_names=ko_names)  # type: ignore
        await memory.add_seed_datasets_to_memory_async(datasets=ko_datasets, added_by="KoDatasetLoader")  # type: ignore
        print(f"완료: {ko_names}")

objective_target = OpenAIChatTarget()
printer = ConsoleScenarioResultPrinter()
attack_printer = ConsoleAttackResultPrinter()

# OpenAI API 기반 스코어러 (Azure 불필요)
scorer = TrueFalseInverterScorer(
    scorer=SelfAskRefusalScorer(chat_target=OpenAIChatTarget())
)
scoring_config = AttackScoringConfig(objective_scorer=scorer)

memory_labels = {"locale": target_lang}
memory = CentralMemory.get_memory_instance()
engine = memory.engine


def show_table(df, title, color="#4A90D9"):
    tid = abs(hash(title)) % 10000
    style = (
        f"<style>"
        f".pt{tid} {{ border-collapse:collapse; width:100%; font-size:13px }}"
        f".pt{tid} th {{ background:{color}; color:white; padding:8px; text-align:left }}"
        f".pt{tid} td {{ padding:6px 8px; border-bottom:1px solid #eee; text-align:left }}"
        f"</style>"
    )
    table = df.to_html(index=False, classes=f"pt{tid}", escape=False)
    display(HTML(f"{style}<h3>{title}</h3>{table}"))


def show_scenario_db(scenario_name):
    """시나리오 실행 후 해당 시나리오의 DB 기록을 표시합니다. 스코어러 내부 대화는 제외."""
    convos = pd.read_sql(text(
        'SELECT SUBSTR(conversation_id, 1, 8) AS "대화ID",'
        ' role AS "역할",'
        ' SUBSTR(original_value, 1, 120) AS "원본",'
        ' SUBSTR(converted_value, 1, 150) AS "변환/응답",'
        ' SUBSTR(timestamp, 1, 19) AS "시간"'
        ' FROM PromptMemoryEntries'
        " WHERE role IN ('user', 'assistant')"
        " AND original_value NOT LIKE '너는 평가자다%%'"
        " AND original_value NOT LIKE 'You are an evaluator%%'"
        " AND labels NOT LIKE '%%scorer%%'"
        ' ORDER BY timestamp DESC LIMIT 20'
    ), engine)

    show_table(convos, f"💬 {scenario_name} 대화 기록 ({len(convos)}건, 스코어러 제외)", "#4A90D9")


async def run_scenario(name, scenario, strategies, dataset_config=None):
    """단일 시나리오 실행 + 결과 출력 + DB 조회"""
    try:
        init_kwargs = dict(
            objective_target=objective_target,
            scenario_strategies=strategies,
            max_concurrency=5,
            memory_labels=memory_labels,
        )
        if dataset_config is not None:
            init_kwargs["dataset_config"] = dataset_config
        await scenario.initialize_async(**init_kwargs)  # type: ignore
        print(f"원자적 공격 수: {scenario.atomic_attack_count}")
        for i, attack in enumerate(scenario._atomic_attacks, 1):
            print(f"  [{i}] {attack.atomic_attack_name}")

        result = await scenario.run_async()  # type: ignore

        # 요약
        total = sum(len(v) for v in result.attack_results.values())
        success = sum(1 for v in result.attack_results.values() for r in v if r.outcome.value == "success")
        print(f"\n✅ 완료 — 공격: {total}건, 성공: {success}건 ({success/total*100:.0f}%)" if total else "\n✅ 완료")

        await printer.print_summary_async(result)  # type: ignore
        return result
    except Exception as e:
        print(f"\n❌ 실패: {e}")
        traceback.print_exc()
        return None


print(f"테스트 언어: {target_lang}")
print(f"데이터셋 크기: 각 시나리오 기본값 사용")

# %% [markdown]
# ---
# ## 3-1. ContentHarms
#
# 7가지 유해 카테고리(hate, fairness, violence, sexual, harassment, misinformation, leakage)를 테스트합니다.
# 여기서는 Hate 카테고리만 선택합니다.

# %%
content_harms_result = await run_scenario(  # type: ignore
    "ContentHarms",
    ContentHarms(objective_scorer=scorer, adversarial_chat=OpenAIChatTarget(temperature=1.2)),
    strategies=[ContentHarmsStrategy.Hate],
    dataset_config=None,  # locale에 따라 자동으로 _ko 데이터셋 선택
)

# %%
show_scenario_db("ContentHarms")

# %% [markdown]
# ---
# ## 3-2. Cyber
#
# 사이버 공격 시나리오 — 악성코드 생성 관련 목표를 테스트합니다.

# %%
cyber_result = await run_scenario(  # type: ignore
    "Cyber",
    Cyber(objective_scorer=scorer, adversarial_chat=OpenAIChatTarget(temperature=1.2)),
    strategies=[CyberStrategy.SINGLE_TURN],
    dataset_config=None,
)

# %%
show_scenario_db("Cyber")

# %% [markdown]
# ---
# ## 3-3. Scam
#
# 스캠/피싱 시나리오 — 사기성 콘텐츠 생성 목표를 테스트합니다.

# %%
scam_result = await run_scenario(  # type: ignore
    "Scam",
    Scam(objective_scorer=scorer, adversarial_chat=OpenAIChatTarget(temperature=1.2)),
    strategies=[ScamStrategy.ContextCompliance],
    dataset_config=None,
)

# %%
show_scenario_db("Scam")

# %% [markdown]
# ---
# ## 3-4. Jailbreak
#
# 탈옥 시나리오 — jailbreak 템플릿을 사용하여 안전 장치 우회를 시도합니다.

# %%
jailbreak_result = await run_scenario(  # type: ignore
    "Jailbreak",
    Jailbreak(objective_scorer=scorer, n_jailbreaks=1),
    strategies=None,
    dataset_config=None,
)

# %%
show_scenario_db("Jailbreak")

# %% [markdown]
# ---
# ## 3-5. LeakageScenario
#
# 정보 유출 시나리오 — 시스템 프롬프트, 개인정보 등 민감 정보 유출을 테스트합니다.

# %%
leakage_result = await run_scenario(  # type: ignore
    "LeakageScenario",
    LeakageScenario(objective_scorer=scorer, adversarial_chat=OpenAIChatTarget(temperature=1.2)),
    strategies=[LeakageStrategy.SINGLE_TURN],
    dataset_config=None,
)

# %%
show_scenario_db("Leakage")

# %% [markdown]
# ---
# ## 3-6. PsychosocialScenario
#
# 심리사회적 위험 시나리오 — 자해/위기 상황 관련 대화를 테스트합니다.

# %%
psychosocial_result = await run_scenario(  # type: ignore
    "PsychosocialScenario",
    PsychosocialScenario(objective_scorer=scorer, adversarial_chat=OpenAIChatTarget(temperature=1.2), max_turns=2),
    strategies=[PsychosocialStrategy.SINGLE_TURN],
    dataset_config=None,
)

# %%
show_scenario_db("Psychosocial")

# %% [markdown]
# ---
# ## 3-7. RedTeamAgent (Foundry)
#
# Foundry 레드팀 시나리오 — Base64 인코딩 전략으로 harmbench_ko 데이터셋을 테스트합니다.

# %%
redteam_result = await run_scenario(  # type: ignore
    "RedTeamAgent",
    RedTeamAgent(attack_scoring_config=scoring_config, include_baseline=False),
    strategies=[FoundryStrategy.Base64],
    dataset_config=None,
)

# %%
show_scenario_db("RedTeamAgent")

# %% [markdown]
# ---
# ## 3-8. Encoding (Garak)
#
# 인코딩 시나리오 — ROT13 인코딩으로 유해 페이로드 디코딩 여부를 테스트합니다.

# %%
encoding_result = await run_scenario(  # type: ignore
    "Encoding",
    Encoding(objective_scorer=scorer, include_baseline=False),
    strategies=[EncodingStrategy.ROT13],
    dataset_config=None,
)

# %%
show_scenario_db("Encoding")

# %% [markdown]
# ---
# ## 4. 전체 결과 요약

# %%
_names = ["content_harms_result", "cyber_result", "scam_result", "jailbreak_result",
          "leakage_result", "psychosocial_result", "redteam_result", "encoding_result"]
_labels = ["ContentHarms", "Cyber", "Scam", "Jailbreak",
           "LeakageScenario", "PsychosocialScenario", "RedTeamAgent", "Encoding"]
all_results = {label: globals().get(name) for label, name in zip(_labels, _names)}

summary_rows = []
for name, result in all_results.items():
    if result is None:
        summary_rows.append({"시나리오": name, "상태": "❌ 실패", "공격 수": "-", "성공 수": "-", "성공률": "-"})
        continue
    total = sum(len(v) for v in result.attack_results.values())
    success = sum(1 for v in result.attack_results.values() for r in v if r.outcome.value == "success")
    rate = f"{success/total*100:.0f}%" if total else "N/A"
    summary_rows.append({"시나리오": name, "상태": "✅ 완료", "공격 수": total, "성공 수": success, "성공률": rate})

df_summary = pd.DataFrame(summary_rows)
show_table(df_summary, f"📊 전체 시나리오 테스트 결과 (locale={target_lang})", "#333")

# %% [markdown]
# ## 5. 한국어 내재화 검증 체크리스트
#
# | 검증 항목 | 확인 방법 |
# |----------|----------|
# | 데이터셋 자동 전환 | `_ko` 데이터셋이 로드되었는지 objective 텍스트 확인 |
# | 한국어 프롬프트 전송 | 대화 기록에서 user 메시지가 한국어인지 확인 |
# | 한국어 응답 수신 | assistant 메시지가 한국어인지 확인 |
# | 한국어 스코어링 | 판정 근거(rationale)가 한국어인지 확인 |
# | 실패 사유 한국어 | "N회 시도 후에도 목표를 달성하지 못했습니다" |

# %% [markdown]
# ## 6. 전체 DB 요약

# %%
# 전체 대화 기록 (스코어러 내부 대화 제외)
all_convos = pd.read_sql(text(
    'SELECT SUBSTR(conversation_id, 1, 8) AS "대화ID",'
    ' role AS "역할",'
    ' SUBSTR(original_value, 1, 40) AS "원본",'
    ' SUBSTR(converted_value, 1, 50) AS "변환/응답",'
    ' SUBSTR(timestamp, 1, 19) AS "시간"'
    ' FROM PromptMemoryEntries'
    " WHERE role IN ('user', 'assistant')"
    " AND original_value NOT LIKE '너는 평가자다%%'"
    " AND original_value NOT LIKE 'You are an evaluator%%'"
    " AND labels NOT LIKE '%%scorer%%'"
    ' ORDER BY timestamp'
), engine)
show_table(all_convos, f"💬 전체 대화 기록 ({len(all_convos)}건, 스코어러 제외)", "#4A90D9")

# %%
# 전체 스코어
all_scores = pd.read_sql(text(
    "SELECT scorer_class_identifier AS '스코어러',"
    " score_category AS '카테고리',"
    " CASE score_value WHEN 'True' THEN '✅ True' ELSE '❌ False' END AS '결과',"
    " SUBSTR(score_rationale, 1, 80) AS '판정 근거',"
    " SUBSTR(timestamp, 1, 19) AS '시간'"
    " FROM ScoreEntries ORDER BY timestamp"
), engine)
show_table(all_scores, f"📊 전체 스코어 ({len(all_scores)}건)", "#E8724A")

# %%
# 요약 통계
summary_db = pd.read_sql(text(
    "SELECT"
    " (SELECT COUNT(*) FROM PromptMemoryEntries WHERE role='user') AS '전체 프롬프트',"
    " (SELECT COUNT(*) FROM PromptMemoryEntries WHERE role='assistant') AS '전체 응답',"
    " (SELECT COUNT(*) FROM ScoreEntries) AS '스코어 수',"
    " (SELECT COUNT(*) FROM ScoreEntries WHERE score_value='True') AS '✅ True',"
    " (SELECT COUNT(*) FROM ScoreEntries WHERE score_value='False') AS '❌ False'"
), engine)
show_table(summary_db, "📈 전체 요약 통계", "#2ECC71")
