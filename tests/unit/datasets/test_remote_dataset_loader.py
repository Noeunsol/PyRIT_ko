# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from pyrit.datasets.seed_datasets.remote.remote_dataset_loader import (
    _RemoteDatasetLoader,
)
from pyrit.models import SeedDataset


class ConcreteRemoteLoader(_RemoteDatasetLoader):
    @property
    def dataset_name(self):
        return "test_remote"

    async def fetch_dataset(self):
        return SeedDataset(seeds=[{"value": "test"}])


class TestRemoteDatasetLoader:
    def test_get_cache_file_name(self):
        loader = ConcreteRemoteLoader()
        name = loader._get_cache_file_name(source="http://example.com", file_type="json")
        assert name.endswith(".json")
        # MD5 of "http://example.com"
        assert name.startswith("a9b9f04336ce0181a08e774e01113b31")

    def test_get_cache_file_name_deterministic(self):
        """Test that same source produces same cache name."""
        loader = ConcreteRemoteLoader()
        source = "https://example.com/data.csv"

        name1 = loader._get_cache_file_name(source=source, file_type="csv")
        name2 = loader._get_cache_file_name(source=source, file_type="csv")

        assert name1 == name2

    def test_read_cache_json(self):
        loader = ConcreteRemoteLoader()
        mock_file = mock_open(read_data='[{"key": "value"}]')
        with patch("pathlib.Path.open", mock_file):
            data = loader._read_cache(cache_file=Path("test.json"), file_type="json")
            assert data == [{"key": "value"}]

    def test_read_cache_invalid_type(self):
        loader = ConcreteRemoteLoader()
        with patch("pathlib.Path.open", mock_open()):
            with pytest.raises(ValueError, match="Invalid file_type"):
                loader._read_cache(cache_file=Path("test.xyz"), file_type="xyz")

    def test_write_cache_json(self, tmp_path):
        loader = ConcreteRemoteLoader()
        cache_file = tmp_path / "test.json"
        data = [{"key": "value"}]

        loader._write_cache(cache_file=cache_file, examples=data, file_type="json")

        assert cache_file.exists()
        with open(cache_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_write_cache_creates_directories(self, tmp_path):
        loader = ConcreteRemoteLoader()
        cache_file = tmp_path / "subdir" / "test.json"
        data = [{"key": "value"}]

        loader._write_cache(cache_file=cache_file, examples=data, file_type="json")

        assert cache_file.exists()

    def test_fetch_from_url_file_source_uses_cache_when_cache_is_fresh(self, tmp_path):
        loader = ConcreteRemoteLoader()
        source_file = tmp_path / "source.csv"
        source_file.write_text("a,b\n1,2\n", encoding="utf-8")

        with patch("pyrit.datasets.seed_datasets.remote.remote_dataset_loader.DB_DATA_PATH", tmp_path):
            cache_file = tmp_path / "seed-prompt-entries" / loader._get_cache_file_name(
                source=str(source_file), file_type="csv"
            )
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text("a,b\n3,4\n", encoding="utf-8")

            # Ensure cache mtime is newer than source mtime.
            source_mtime = source_file.stat().st_mtime
            os.utime(cache_file, (source_mtime + 5, source_mtime + 5))

            cached_data = [{"a": "3", "b": "4"}]
            with (
                patch.object(loader, "_read_cache", return_value=cached_data) as mock_read_cache,
                patch.object(loader, "_fetch_from_file") as mock_fetch_from_file,
            ):
                result = loader._fetch_from_url(source=str(source_file), source_type="file", cache=True)

            assert result == cached_data
            mock_read_cache.assert_called_once()
            mock_fetch_from_file.assert_not_called()

    def test_fetch_from_url_file_source_invalidates_cache_when_source_is_newer(self, tmp_path):
        loader = ConcreteRemoteLoader()
        source_file = tmp_path / "source.csv"
        source_file.write_text("a,b\n1,2\n", encoding="utf-8")

        with patch("pyrit.datasets.seed_datasets.remote.remote_dataset_loader.DB_DATA_PATH", tmp_path):
            cache_file = tmp_path / "seed-prompt-entries" / loader._get_cache_file_name(
                source=str(source_file), file_type="csv"
            )
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text("a,b\n3,4\n", encoding="utf-8")

            # Ensure source mtime is newer than cache mtime.
            cache_mtime = cache_file.stat().st_mtime
            os.utime(source_file, (cache_mtime + 5, cache_mtime + 5))

            fresh_data = [{"a": "1", "b": "2"}]
            with (
                patch.object(loader, "_read_cache") as mock_read_cache,
                patch.object(loader, "_fetch_from_file", return_value=fresh_data) as mock_fetch_from_file,
                patch.object(loader, "_write_cache") as mock_write_cache,
            ):
                result = loader._fetch_from_url(source=str(source_file), source_type="file", cache=True)

            assert result == fresh_data
            mock_read_cache.assert_not_called()
            mock_fetch_from_file.assert_called_once()
            mock_write_cache.assert_called_once()
