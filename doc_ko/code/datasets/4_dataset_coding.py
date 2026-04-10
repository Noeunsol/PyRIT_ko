# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
# ---

# %% [markdown]
# # 4. PyRIT에 데이터셋 기여하기
#
# PyRIT는 무엇을 테스트해야 하는지 강제하지 않고, 필요한 테스트를 유연하게 수행하도록 설계된 프레임워크입니다.
# 가장 흔한 기여 방식 중 하나가 새로운 데이터셋 추가입니다.
#
# 이 문서는 아래와 같은 데이터셋을 PyRIT 소스에 기여하는 방법을 설명합니다.
# - **Jailbreak 템플릿**: 안전장치 우회를 유도하는 패턴
# - **유해성 벤치마크**: 모델 안전성 평가용 케이스(`SeedObjective`/`SeedPrompt`)
# - **시스템 프롬프트**: adversarial model/scorer/converter 템플릿
#
# PyRIT에 데이터셋을 포함하는 대표 방식은 3가지입니다.
#
# ## 방법 1: YAML 파일
#
# 라이선스가 호환되고 PyRIT 커뮤니티에 널리 재사용될 수 있는 데이터셋은 YAML로 포함하는 것이 좋습니다.
# 장점:
# - 버전 관리와 코드 리뷰 용이
# - 수정/확장 간단
# - 내장 provider를 통한 자동 로딩
#
# ### YAML 파일 주요 위치
#
# **Jailbreak 템플릿**
# - 위치: `pyrit/datasets/jailbreak/templates/`
# - 사용처: `TextJailBreak` 계열 및 `TextJailBreakConverter`
#
# **유해성 데이터셋**
# - 위치: `pyrit/datasets/seed_datasets/local/`
# - 사용처: `SeedDatasetProvider`를 통한 자동 로드
#
# YAML 형식 상세는 [Seed Programming](./2_seed_programming.ipynb)을 참고하세요.
#
# ## 방법 2: 원격 데이터셋 로더
#
# 아래 조건에서는 원격 로더가 적합합니다.
# - 라이선스상 재배포 제약이 있는 경우
# - 원본 데이터셋이 자주 업데이트되는 경우
# - 데이터셋 규모가 커서 외부 호스팅이 더 적합한 경우
#
# 보통 URL/HuggingFace에서 가져오며, `_RemoteDatasetLoader` 서브클래스를 구현해
# 파싱/캐시/다운로드 로직을 넣습니다. 해당 로더는 `SeedDatasetProvider`가 자동 발견합니다.
#
# ### 예시: DarkBench 원격 로더
#
# 아래 코드는 [`DarkBenchDataset`](../../../pyrit/datasets/seed_datasets/remote/darkbench_dataset.py)의 단순화 버전입니다.

# %%
import sys

# 노트북에서 로컬 PyRIT 소스를 우선 참조
if "/Users/selectstar/PyRIT_ko/src" not in sys.path:
    sys.path.insert(0, "/Users/selectstar/PyRIT_ko/src")

from pyrit.common.locale_utils import NotebookLocale
from pyrit.datasets.seed_datasets.remote.remote_dataset_loader import (
    _RemoteDatasetLoader,
)
from pyrit.models import SeedDataset, SeedPrompt

# 언어 스위치: "ko" 또는 "en"
L = NotebookLocale("ko")


class SimpleDarkBench(_RemoteDatasetLoader):
    @property
    def dataset_name(self) -> str:
        return "dark_bench"

    async def fetch_dataset(self, *, cache: bool = True) -> SeedDataset:
        # HuggingFace에서 원격 데이터셋 로드
        data = await self._fetch_from_huggingface(
            dataset_name="apart/darkbench",
            config="default",
            split="train",
            cache=cache,
            data_files="darkbench.tsv",
        )

        # 로케일별로 사용 컬럼 선택 (ko 컬럼이 없으면 en 컬럼으로 fallback)
        def select_value(item: dict, en_key: str, ko_key: str) -> str:
            if L.locale == "ko":
                return str(item.get(ko_key) or item.get(en_key) or "")
            return str(item.get(en_key) or "")

        seed_prompts = [
            SeedPrompt(
                value=select_value(item, "Example", "Example_ko"),
                data_type="text",
                dataset_name=self.dataset_name,
                harm_categories=[select_value(item, "Deceptive Pattern", "Deceptive Pattern_ko")],
            )
            for item in data
        ]

        return SeedDataset(seeds=seed_prompts, dataset_name=self.dataset_name)
