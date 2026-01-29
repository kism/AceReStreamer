from typing import TYPE_CHECKING

from acere.database.handlers.quality_cache import AceQualityCacheHandler
from acere.services.ace_quality import Quality
from tests.test_utils.ace import get_random_content_id
from tests.test_utils.hls import generate_hls_m3u8

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    import pytest
    from pytest_mock import MockerFixture
else:
    Path = object
    Generator = object
    MockerFixture = object
    pytest = object


def test_init(quality_cache_handler: AceQualityCacheHandler) -> None:
    """Test initialization of AceQualityCacheHandler."""
    handler = quality_cache_handler
    override_quality = 50

    content_id = get_random_content_id()

    quality = handler.get_quality(content_id)
    assert quality is not None  # Returns a new Quality object
    assert quality.quality == -1

    new_quality = quality.model_copy()
    new_quality.quality = override_quality

    handler.set_quality(content_id, new_quality)
    assert handler.get_quality(content_id).quality == override_quality

    handler.clean_table()

    handler.increment_quality(content_id, generate_hls_m3u8(1))
    handler.increment_quality(content_id, generate_hls_m3u8(2))
    handler.increment_quality(content_id, generate_hls_m3u8(3))
    handler.increment_quality(content_id, generate_hls_m3u8(4))
    assert handler.get_quality(content_id).quality == override_quality + 3

    handler.increment_quality(content_id, generate_hls_m3u8(4))
    handler.increment_quality(content_id, generate_hls_m3u8(4))
    handler.increment_quality(content_id, generate_hls_m3u8(4))
    assert handler.get_quality(content_id).quality == override_quality + 3

    handler.increment_quality(content_id, generate_hls_m3u8(5))
    assert handler.get_quality(content_id).quality == override_quality + 4


def test_clean_table(
    quality_cache_handler: AceQualityCacheHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test cleaning of the quality cache table."""
    handler = quality_cache_handler
    handler.set_quality("too_short", quality=Quality(quality=10))
    with caplog.at_level("ERROR"):
        handler.clean_table()

    assert "Found invalid content_id" in caplog.text


def test_get_quality_no_cache(quality_cache_handler: AceQualityCacheHandler) -> None:
    handler = quality_cache_handler
    handler._cache.clear()
    content_id = get_random_content_id()
    quality_default = Quality()

    quality = handler.get_quality(content_id)
    handler._cache.clear()
    assert quality.quality == quality_default.quality

    handler.set_quality(content_id, Quality(quality=75))
    handler._cache.clear()
    quality = handler.get_quality(content_id)
    assert quality.quality == 75
