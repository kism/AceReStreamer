"""AceQuality, for tracking quality of Ace URIs."""

import json
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


class AceQuality:
    """For tracking quality of Streams."""

    default_quality: int = -1
    quality_on_first_success: int = 20
    min_quality: int = 0
    max_quality: int = 99

    def __init__(self, cache_file: Path | None) -> None:
        """Init AceQuality."""
        self.cache_file = cache_file
        self.ace_streams: dict[str, int] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if self.cache_file and self.cache_file.exists():
            try:
                with self.cache_file.open("r") as f:
                    cache_json_raw = f.read()

                self.ace_streams = json.loads(cache_json_raw)
            except (json.JSONDecodeError, OSError):
                logger.exception("Error loading cache file: %s", self.cache_file)
                return

    def save_cache(self) -> None:
        """Save the current quality cache to a file."""
        logger.debug("Saving AceQuality cache to %s", self.cache_file)
        if not self.cache_file:
            return

        try:
            with self.cache_file.open("w") as f:
                json.dump(self.ace_streams, f, indent=4)
        except OSError:
            logger.exception("Error saving cache file: %s", self.cache_file)

    def get_quality(self, ace_id: str) -> int:
        """Get the quality of a stream by ace_id."""
        if ace_id not in self.ace_streams:
            self.ensure_entry(ace_id)
        return self.ace_streams[ace_id]

    def ensure_entry(self, ace_id: str) -> None:
        """Creates an entry with defaults if it doen't exist."""
        if ace_id not in self.ace_streams:
            self.ace_streams[ace_id] = self.default_quality

    def increment_quality(self, ace_id: str, rating: int) -> None:
        """Increment the quality of a stream by ace_id."""
        logger.debug("Setting quality for AceStream %s by %d", ace_id, rating)
        if ace_id not in self.ace_streams:
            self.ace_streams[ace_id] = self.default_quality

        if self.ace_streams[ace_id] == self.default_quality and rating > 0:
            rating = self.quality_on_first_success

        self.ace_streams[ace_id] += rating
        self.ace_streams[ace_id] = max(self.ace_streams[ace_id], self.min_quality)
        self.ace_streams[ace_id] = min(self.ace_streams[ace_id], self.max_quality)
        self.save_cache()
