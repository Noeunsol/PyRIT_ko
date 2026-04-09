# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pathlib import Path
from typing import Literal

from pyrit.datasets.seed_datasets.remote.harmbench_dataset import _HarmBenchDataset


class _HarmBenchKoDataset(_HarmBenchDataset):
    """
    HarmBench 데이터셋의 한국어 번역 로더.

    원본 _HarmBenchDataset과 동일한 CSV 파싱 로직을 상속하며,
    로컬 한국어 CSV 파일을 소스로 사용합니다.

    원본: https://github.com/centerforaisafety/HarmBench
    """

    def __init__(
        self,
        *,
        source: str = str(Path(__file__).parent.parent / "local" / "harmbench_ko.csv"),
        source_type: Literal["public_url", "file"] = "file",
    ):
        super().__init__(source=source, source_type=source_type)

    @property
    def dataset_name(self) -> str:
        return "harmbench_ko"
