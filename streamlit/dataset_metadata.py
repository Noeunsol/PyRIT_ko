# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
"""Dynamic dataset metadata for the Streamlit demo.

Used by ``app.py`` to resolve the useful upper bound for the
"max items per dataset" slider per selected scenario. The index is built
once per process by scanning the local seed dataset files; new datasets
are picked up on the next Streamlit app restart.
"""

from __future__ import annotations

import csv
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

_DATASETS_ROOT = (
    Path(__file__).resolve().parent.parent
    / "src"
    / "pyrit"
    / "datasets"
    / "seed_datasets"
    / "local"
)


@lru_cache(maxsize=1)
def build_seed_count_index() -> dict[str, int]:
    """Scan local seed files to build ``{dataset_name: item_count}``.

    Handles two on-disk formats:
    - ``*.prompt`` YAML files with a ``dataset_name`` key and a ``seeds`` list
    - ``*.csv`` files whose stem matches the dataset name (e.g. ``harmbench_ko``)
    """
    index: dict[str, int] = {}

    if not _DATASETS_ROOT.exists():
        return index

    for path in _DATASETS_ROOT.rglob("*.prompt"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            logger.debug("Failed to parse YAML: %s", path, exc_info=True)
            continue
        if not isinstance(data, dict):
            continue
        name = data.get("dataset_name")
        seeds = data.get("seeds")
        if name and isinstance(seeds, list):
            index[str(name)] = len(seeds)

    for path in _DATASETS_ROOT.rglob("*.csv"):
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                # subtract 1 for the header row
                row_count = sum(1 for _ in csv.reader(f)) - 1
        except Exception:
            logger.debug("Failed to count CSV rows: %s", path, exc_info=True)
            continue
        if row_count > 0:
            index[path.stem] = row_count

    return index


@lru_cache(maxsize=None)
def get_scenario_dataset_max(scenario_name: str, locale: str = "ko") -> Optional[int]:
    """Return the useful upper bound for ``max_dataset_size`` for a scenario.

    ``DatasetConfiguration.max_dataset_size`` is applied **per dataset**, so
    the meaningful ceiling is the largest individual dataset the scenario
    uses. If the scenario uses multiple datasets, returns the maximum size
    among them. Returns ``None`` if the scenario or its datasets cannot be
    resolved (caller should fall back to a static default).
    """
    try:
        from pyrit.registry import ScenarioRegistry

        registry = ScenarioRegistry.get_registry_singleton()
        scenario_cls = registry.get_class(scenario_name)
        if scenario_cls is None:
            return None
        dataset_names = scenario_cls.default_dataset_config().get_default_dataset_names()
    except Exception:
        logger.debug("Failed to resolve scenario %s", scenario_name, exc_info=True)
        return None

    if not dataset_names:
        return None

    index = build_seed_count_index()
    sizes: list[int] = []
    for base in dataset_names:
        if locale == "ko" and not base.endswith("_ko"):
            localized = f"{base}_ko"
            size = index.get(localized) or index.get(base)
        else:
            size = index.get(base)
        if size:
            sizes.append(size)

    return max(sizes) if sizes else None
