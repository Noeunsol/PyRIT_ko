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
# # 1. 내장 데이터셋 불러오기
#
# PyRIT에는 AI 레드팀 시작에 바로 사용할 수 있는 내장 데이터셋이 다수 포함되어 있습니다.
# PyRIT는 무엇이 유해한지 강하게 강제하지 않지만, 내장/커뮤니티/사용자 정의 데이터셋을 쉽게 사용할 수 있는 구조를 제공합니다.
#
# **중요**: 데이터셋은 [PyRIT 메모리](../memory/8_seed_database.ipynb)에서 관리할 때 가장 효율적입니다.
# 메모리 기반으로 정규화/조회가 쉬워지기 때문입니다.
# 이 문서는 출발점으로서 "직접 로드" 방법을 보여주며, 이후 메모리로 손쉽게 적재할 수 있습니다.
#
# 아래 코드는 PyRIT에서 사용 가능한 내장 데이터셋 이름 목록을 보여줍니다.
# 일부는 로컬에 있고, 일부는 HuggingFace 같은 원격 소스에서 가져옵니다.

# %%
import sys

# 노트북에서 로컬 PyRIT 소스를 우선 참조
if "/Users/selectstar/PyRIT_ko/src" not in sys.path:
    sys.path.insert(0, "/Users/selectstar/PyRIT_ko/src")

from pyrit.common.locale_utils import NotebookLocale
from pyrit.datasets import SeedDatasetProvider

# 언어 스위치: "ko" 또는 "en"
L = NotebookLocale("ko")

all_dataset_names = SeedDatasetProvider.get_all_dataset_names()
print(L.pick(en="Built-in dataset names:", ko="내장 데이터셋 이름:"))
print(all_dataset_names)


def localized_dataset_name(base_name: str) -> str:
    ko_name = f"{base_name}_ko"
    if L.locale == "ko" and ko_name in all_dataset_names:
        return ko_name
    return base_name

# %% [markdown]
# ## 특정 데이터셋만 로드하기
#
# `SeedDatasetProvider.fetch_datasets_async()`를 사용하면 전체 또는 일부 데이터셋만 선택해 로드할 수 있습니다.
# 반환 타입은 `SeedDataset` 리스트이며, 내부에 Seed 정보가 포함됩니다.

# %%
requested_base_names = ["airt_illegal", "airt_malware"]
selected_dataset_names = [localized_dataset_name(name) for name in requested_base_names]
print(L.pick(en="Selected datasets:", ko="선택된 데이터셋:"), selected_dataset_names)

datasets = await SeedDatasetProvider.fetch_datasets_async(dataset_names=selected_dataset_names)  # type: ignore

for dataset in datasets:
    print(f"\n{L.pick(en='Dataset', ko='데이터셋')}: {dataset.dataset_name}")
    for seed in dataset.seeds:
        print(seed.value)

# %% [markdown]
# ## 데이터셋을 메모리에 적재하기
#
# 직접 로드는 빠른 탐색에 유용하지만, 장기 운영에서는 메모리에 넣는 것이 유리합니다.
# 메모리 사용 시 다음 장점이 있습니다.
# - 유해 카테고리, 데이터 타입, 사용자 메타데이터 기준 조회
# - 출처/버전 추적
# - 팀 단위 공유(예: Azure SQL 사용 시)
# - 중복 적재 방지
#
# 자세한 내용은 [메모리 문서](../memory/0_memory.md), [seed database 가이드](../memory/8_seed_database.ipynb)를 참고하세요.

# %%
from pyrit.memory import CentralMemory
from pyrit.setup.initialization import IN_MEMORY, initialize_pyrit_async

await initialize_pyrit_async(memory_db_type=IN_MEMORY)  # type: ignore

memory = CentralMemory().get_memory_instance()
await memory.add_seed_datasets_to_memory_async(datasets=datasets, added_by="pyrit")  # type: ignore

# 메모리 조회 예시
query_result = memory.get_seeds(harm_categories=["illegal"], is_objective=True)
print(L.pick(en="Query result count:", ko="조회 결과 개수:"), len(query_result))
