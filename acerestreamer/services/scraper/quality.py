"""AceQuality, for tracking quality of Ace URIs."""

import contextlib
import json
import threading
import time
from pathlib import Path

import requests
from pydantic import BaseModel

from acerestreamer.utils.helpers import check_valid_ace_id
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)


# region: Quality
class Quality(BaseModel):
    """Model for tracking quality of a stream."""

    quality: int = -1
    has_ever_worked: bool = False


class AceQuality:
    """For tracking quality of Streams."""

    default_quality: int = -1  # Unknown quality
    quality_on_first_success: int = 20
    min_quality: int = 0
    max_quality: int = 99
    currently_checking_quality = False

    def __init__(self) -> None:
        """Init AceQuality."""
        self.cache_file: Path | None = None
        self.ace_streams: dict[str, Quality] = {}
        self.external_url: str = ""

    def load_config(self, instance_path: Path, external_url: str) -> None:
        """Init AceQuality."""
        self.cache_file = instance_path / "ace_quality_cache.json"
        self.external_url = external_url
        self._load_cache()
        self._clean_cache()

    def _clean_cache(self) -> None:
        """Ensure that the cache only contains valid Ace IDs."""
        logger.debug("Cleaning AceQuality cache")
        if not self.ace_streams:
            return

        cleaned_cache = {}
        for ace_id, quality in self.ace_streams.items():
            if check_valid_ace_id(ace_id):
                cleaned_cache[ace_id] = quality
            else:
                logger.warning("Invalid Ace ID found in cache: %s", ace_id)

        self.ace_streams = cleaned_cache

    def _load_cache(self) -> None:
        if self.cache_file and self.cache_file.exists():
            try:
                with self.cache_file.open("r") as f:
                    cache_json_raw = f.read()

                ace_streams_dict = json.loads(cache_json_raw)
            except (json.JSONDecodeError, OSError):
                logger.exception("Error loading cache file: %s", self.cache_file)
                return

            for ace_id, quality_data in ace_streams_dict.items():
                try:
                    self.ace_streams[ace_id] = Quality(**quality_data)
                except TypeError:
                    error_short = type(quality_data).__name__
                    msg = (
                        f"{error_short} loading quality cache, invalid quality data for Ace ID {ace_id}: {quality_data}"
                    )
                    logger.error(msg)  # noqa: TRY400 Short error is fine
                    continue

    def save_cache(self) -> None:
        """Save the current quality cache to a file."""
        if not self.cache_file:
            return

        cache_as_dict = {ace_id: quality.model_dump() for ace_id, quality in self.ace_streams.items()}

        try:
            with self.cache_file.open("w") as f:
                json.dump(cache_as_dict, f, indent=4)
        except OSError:
            logger.exception("Error saving cache file: %s", self.cache_file)

    def get_quality(self, ace_id: str) -> Quality:
        """Get the quality of a stream by ace_id."""
        if not check_valid_ace_id(ace_id):
            return Quality()

        if ace_id not in self.ace_streams:
            self._ensure_entry(ace_id)
        return self.ace_streams[ace_id]

    def _ensure_entry(self, ace_id: str) -> None:
        """Creates an entry with defaults if it doen't exist."""
        if ace_id not in self.ace_streams:
            self.ace_streams[ace_id] = Quality()

    def increment_quality(self, ace_id: str, rating: int) -> None:
        """Increment the quality of a stream by ace_id."""
        if not check_valid_ace_id(ace_id):
            return

        logger.trace("Setting quality for AceStream %s by %d", ace_id, rating)
        if ace_id not in self.ace_streams:
            self.ace_streams[ace_id] = Quality()

        if rating > 0 and not self.ace_streams[ace_id].has_ever_worked:
            # Only need max if someone edited the json, I might do something with it later
            rating = max(self.quality_on_first_success, self.ace_streams[ace_id].quality)
            self.ace_streams[ace_id].has_ever_worked = True

        self.ace_streams[ace_id].quality += rating
        self.ace_streams[ace_id].quality = max(self.ace_streams[ace_id].quality, self.min_quality)
        self.ace_streams[ace_id].quality = min(self.ace_streams[ace_id].quality, self.max_quality)
        self.save_cache()

    def check_missing_quality(self) -> None:
        """Cycle through all Ace IDs that have never worked and check them."""
        if self.currently_checking_quality:
            return

        def check_missing_quality_thread(base_url: str) -> None:
            self.currently_checking_quality = True

            ace_streams_never_worked = len(
                [  # We also check if the quality is zero, since maybe it started working
                    ace_id
                    for ace_id, quality in self.ace_streams.items()
                    if not quality.has_ever_worked or quality.quality == 0
                ]
            )

            # Don't enumerate here, and don't bother with list comprehension tbh
            n = 0
            for ace_id, quality in self.ace_streams.items():
                if not quality.has_ever_worked or quality.quality == 0:
                    n += 1
                    stream_url = f"{base_url}/{ace_id}"
                    logger.info("Checking Ace Stream %s (%d/%d)", stream_url, n, ace_streams_never_worked)

                    for _ in range(3):
                        try:
                            requests.get(stream_url, timeout=10)
                        except (requests.Timeout, requests.ConnectionError) as e:
                            error_short = type(e).__name__
                            logger.error("Error checking Ace Stream %s: %s", stream_url, error_short)  # noqa: TRY400 Temp
                        time.sleep(1)

                    time.sleep(10)

            self.currently_checking_quality = False

        url = f"{self.external_url}/hls"

        thread = threading.Thread(
            target=check_missing_quality_thread,
            name="AceQuality: check_missing_quality",
            args=(url,),
            daemon=True,
        )
        thread.start()
