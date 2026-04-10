# ---
# jupyter:
#   jupytext:
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
# # 시나리오 (Scenarios)
#
# `Scenario`는 여러 공격 구성(Attack Configuration)을 하나로 묶는 상위 수준의 구조입니다. 이를 통해 여러 공격 방법을 순차적으로 실행하는 종합적인 테스트 캠페인을 수행할 수 있습니다. 시나리오는 특정 워크플로우를 테스트하기 위해 구성되고 작성되도록 설계되었습니다. 따라서 일부 값을 하드코딩해도 괜찮습니다.
#
# ## 시나리오란?
#
# `Scenario`는 여러 원자적 공격 테스트(atomic attack test)로 구성된 종합 테스트 캠페인을 나타냅니다. 여러 `AtomicAttack` 인스턴스를 순차적으로 실행하고, 결과를 하나의 `ScenarioResult`로 집계합니다.
#
# ### 주요 구성 요소
#
# - **Scenario**: 여러 원자적 공격을 그룹화하고 실행하는 최상위 오케스트레이터
# - **AtomicAttack**: 공격 전략, 목표, 실행 파라미터를 결합한 원자적 테스트 단위
# - **ScenarioResult**: 모든 원자적 공격의 집계 결과와 시나리오 메타데이터를 포함
#
# ## 사용 사례
#
# 생성할 수 있는 시나리오 예시:
#
# - **VibeCheckScenario**: HarmBench에서 몇 개의 프롬프트를 무작위로 선택하여 모델 동작을 빠르게 평가
# - **QuickViolence**: 여러 공격 기법을 사용하여 폭력적 목표에 대한 모델의 회복력을 확인
# - **ComprehensiveFoundry**: 사용 가능한 모든 공격 변환기와 전략으로 대상을 테스트
# - **CustomCompliance**: 큐레이션된 데이터셋과 공격으로 특정 규정 준수 요구사항을 테스트
#
# 이러한 시나리오는 테스트 대상을 정교화함에 따라 업데이트하고 추가할 수 있습니다.
#
# ## 시나리오 실행 방법
#
# 시나리오는 기본값만으로도 거의 노력 없이 실행할 수 있습니다. [pyrit_scan](../front_end/1_pyrit_scan.ipynb)과 [pyrit_shell](../front_end/2_pyrit_shell.md) 모두 시나리오를 사용하여 실행합니다.
#
# ## 작동 방식
#
# 각 `Scenario`는 `AtomicAttack` 객체의 컬렉션을 포함합니다. 실행 시:
#
# 1. 각 `AtomicAttack`이 순차적으로 실행됩니다
# 2. 모든 `AtomicAttack`은 지정된 모든 목표와 데이터셋에 대해 구성된 공격을 테스트합니다
# 3. 결과는 모든 공격 결과를 포함하는 단일 `ScenarioResult`로 집계됩니다
# 4. 선택적 메모리 라벨이 시나리오 실행을 추적하고 분류하는 데 도움을 줍니다
#
# ## 커스텀 시나리오 생성
#
# 커스텀 시나리오를 생성하려면 `Scenario` 기본 클래스를 확장하고 필수 추상 메서드를 구현합니다.
#
# ### 필수 구성 요소
#
# 1. **Strategy Enum**: 시나리오에 사용할 수 있는 전략을 정의하는 `ScenarioStrategy` 열거형을 생성합니다.
#    - 각 열거형 멤버는 `(value, tags)`로 정의되며, value는 문자열이고 tags는 문자열 집합입니다
#    - 모든 사용 가능한 전략으로 확장되는 `ALL` 집계 전략을 포함합니다
#    - 선택적으로 전략 조합 규칙을 위한 `supports_composition()`과 `validate_composition()`을 구현합니다
#
# 2. **Scenario 클래스**: `Scenario`를 확장하고 다음 추상 메서드를 구현합니다:
#    - `get_strategy_class()`: 전략 열거형 클래스를 반환
#    - `get_default_strategy()`: 기본 전략을 반환 (일반적으로 `YourStrategy.ALL`)
#    - `_get_atomic_attacks_async()`: `AtomicAttack` 인스턴스 목록을 생성하고 반환
#
# 3. **생성자**: `@apply_defaults` 데코레이터를 사용하고 시나리오 메타데이터와 함께 `super().__init__()`을 호출합니다:
#    - `name`: 시나리오의 설명적 이름
#    - `version`: 정수 버전 번호
#    - `strategy_class`: 이 시나리오의 전략 열거형 클래스
#    - `objective_scorer_identifier`: 점수 매기기 메커니즘의 식별자 딕셔너리 (선택사항)
#    - `include_default_baseline`: 기준선 공격 포함 여부 (기본값: True)
#    - `scenario_result_id`: 기존 시나리오를 재개하기 위한 선택적 ID (선택사항)
#
# 4. **초기화**: `await scenario.initialize_async()`를 호출하여 원자적 공격을 구성합니다:
#    - `objective_target`: 테스트 대상 시스템 (필수)
#    - `scenario_strategies`: 실행할 전략 목록 (선택사항, 기본값은 ALL)
#    - `max_concurrency`: 동시 작업 수 (기본값: 1)
#    - `max_retries`: 실패 시 재시도 횟수 (기본값: 0)
#    - `memory_labels`: 추적을 위한 선택적 라벨 (선택사항)
#
# ### 예제 구조
# %%
from typing import List, Optional, Type

from pyrit.common import apply_defaults
from pyrit.executor.attack import AttackScoringConfig, PromptSendingAttack
from pyrit.scenario import (
    AtomicAttack,
    DatasetConfiguration,
    Scenario,
    ScenarioStrategy,
)
from pyrit.scenario.core.scenario_strategy import ScenarioCompositeStrategy
from pyrit.prompt_target import OpenAIChatTarget
from pyrit.score import SelfAskRefusalScorer, TrueFalseInverterScorer
from pyrit.score.true_false.true_false_scorer import TrueFalseScorer
from pyrit.setup import initialize_pyrit_async

await initialize_pyrit_async(memory_db_type="InMemory")  # type: ignore [top-level-await]


class MyStrategy(ScenarioStrategy):
    ALL = ("all", {"all"})
    StrategyA = ("strategy_a", {"tag1", "tag2"})
    StrategyB = ("strategy_b", {"tag1"})


class MyScenario(Scenario):
    version: int = 1

    # 전략 정의는 호출자가 시나리오를 실행하는 방법을 정의하는 데 도움을 줍니다 (예: front_end에서)
    @classmethod
    def get_strategy_class(cls) -> Type[ScenarioStrategy]:
        return MyStrategy

    @classmethod
    def get_default_strategy(cls) -> ScenarioStrategy:
        return MyStrategy.ALL

    # 이 시나리오의 기본 데이터셋 구성입니다 (예: 전송할 프롬프트)
    @classmethod
    def default_dataset_config(cls) -> DatasetConfiguration:
        return DatasetConfiguration(dataset_names=["dataset_name"])

    @apply_defaults
    def __init__(
        self,
        *,
        objective_scorer: Optional[TrueFalseScorer] = None,
        scenario_result_id: Optional[str] = None,
    ):
        # objective_scorer가 제공되지 않으면 기본 스코어러를 생성합니다
        if objective_scorer is None:
            objective_scorer = TrueFalseInverterScorer(
                scorer=SelfAskRefusalScorer(chat_target=OpenAIChatTarget())
            )

        self._objective_scorer = objective_scorer
        self._scorer_config = AttackScoringConfig(objective_scorer=objective_scorer)

        # 부모 생성자 호출 - 참고: objective_target은 여기서 전달되지 않습니다
        super().__init__(
            name="My Custom Scenario",
            version=self.version,
            strategy_class=MyStrategy,
            objective_scorer=objective_scorer,
            scenario_result_id=scenario_result_id,
        )

    async def _get_atomic_attacks_async(self) -> List[AtomicAttack]:
        """
        선택된 전략에 기반하여 원자적 공격을 구성합니다.

        이 메서드는 전략이 준비된 후 initialize_async()에 의해 호출됩니다.
        self._scenario_composites를 사용하여 선택된 전략에 접근합니다.
        """
        atomic_attacks = []

        # 부모 클래스 검증에 의해 objective_target은 None이 아님이 보장됩니다
        assert self._objective_target is not None

        # 복합 전략에서 개별 전략 값을 추출합니다
        selected_strategies = ScenarioCompositeStrategy.extract_single_strategy_values(
            self._scenario_composites, strategy_type=MyStrategy
        )

        for strategy in selected_strategies:
            # self._dataset_config은 부모 클래스에 의해 설정됩니다
            seed_groups = self._dataset_config.get_all_seed_groups()

            # 전략에 기반한 공격 인스턴스를 생성합니다
            attack = PromptSendingAttack(
                objective_target=self._objective_target,
                attack_scoring_config=self._scorer_config,
            )
            atomic_attacks.append(
                AtomicAttack(
                    atomic_attack_name=strategy,
                    attack=attack,
                    seed_groups=seed_groups,  # type: ignore[arg-type]
                    memory_labels=self._memory_labels,
                )
            )
        return atomic_attacks


scenario = MyScenario()

# %% [markdown]
#
# ## 기존 시나리오

# %%
from pyrit.cli.frontend_core import FrontendCore, print_scenarios_list_async

await print_scenarios_list_async(context=FrontendCore())  # type: ignore

# %% [markdown]
#
# ## 복원력 (Resiliency)
#
# 시나리오는 오랜 시간 동안 실행될 수 있으며, 그로 인해 문제가 발생할 수 있습니다. 네트워크 문제, 속도 제한, 또는 기타 일시적 장애가 실행을 중단시킬 수 있습니다. PyRIT는 이러한 상황을 원활하게 처리하기 위한 내장 복원력 기능을 제공합니다.
#
# ### 자동 재개
#
# `scenario`를 다시 실행하면 중단된 지점부터 자동으로 이어서 시작합니다. 프레임워크가 메모리에서 완료된 공격과 목표를 추적하므로, 시나리오 실행이 중단되더라도 진행 상황을 잃지 않습니다. 이는 작업을 중복하지 않고 안전하게 시나리오를 중지하고 재시작할 수 있음을 의미합니다.
#
# ### 재시도 메커니즘
#
# `max_retries` 파라미터를 활용하여 일시적 장애를 처리할 수 있습니다. 실행 중 알 수 없는 예외가 발생하면 PyRIT가 지정된 횟수만큼 자동으로 실패한 작업을 재시도합니다(중단된 지점부터 시작). 이를 통해 일시적인 문제가 있더라도 시나리오가 성공적으로 완료될 수 있도록 합니다.
#
# ### 동적 구성
#
# 장기 실행 시나리오 중에 리소스 사용을 관리하기 위해 `max_concurrency`와 같은 파라미터를 조정하거나, 스코어러가 다른 대상을 사용하도록 전환할 수 있습니다. PyRIT의 복원력 기능은 시나리오를 안전하게 중지하고, 재구성하고, 필요에 따라 계속할 수 있게 합니다.
#
# 자세한 내용은 [복원력](../setup/2_resiliency.ipynb)을 참조하세요.
