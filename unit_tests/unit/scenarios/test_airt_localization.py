# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pyrit.scenario.scenarios.airt.localization import get_localized_dataset_names


def test_get_localized_dataset_names_returns_ko_when_available() -> None:
    result = get_localized_dataset_names(
        dataset_names=["airt_malware", "airt_scams"],
        labels={"locale": "ko"},
        available_dataset_names={"airt_malware_ko", "airt_scams_ko"},
    )

    assert result == ["airt_malware_ko", "airt_scams_ko"]


def test_get_localized_dataset_names_falls_back_per_dataset_when_missing() -> None:
    result = get_localized_dataset_names(
        dataset_names=["airt_malware", "airt_scams"],
        labels={"target_lang": "ko"},
        available_dataset_names={"airt_malware_ko"},
    )

    assert result == ["airt_malware_ko", "airt_scams"]


def test_get_localized_dataset_names_keeps_english_for_non_korean_locale() -> None:
    result = get_localized_dataset_names(
        dataset_names=["airt_malware", "airt_scams"],
        labels={"locale": "en-US"},
        available_dataset_names={"airt_malware_ko", "airt_scams_ko"},
    )

    assert result == ["airt_malware", "airt_scams"]
