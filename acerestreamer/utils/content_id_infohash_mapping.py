"""Mapping between content IDs and infohashes."""

import json
from pathlib import Path

from bidict import bidict

from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)


class ContentIDInfohashMapping:
    """A class to manage the mapping between content IDs and infohashes."""

    def __init__(self) -> None:
        """Initialize the mapping."""
        self.content_id_infohash_mapping: bidict[str, str] = bidict()
        self.instance_path: Path | None = None

    def load_config(self, instance_path: str | Path) -> None:
        """Load the content ID to infohash mapping from a JSON file."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)
        self.instance_path = instance_path

        config_path = instance_path / "content_id_infohash_map.json"
        if not config_path.exists():
            return

        with config_path.open("r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                if isinstance(data, dict):
                    self.content_id_infohash_mapping = bidict(data)
            except json.JSONDecodeError:
                logger.exception("Failed to decode JSON from content_id_infohash_map.json")

    def save_config(self) -> None:
        """Save the content ID to infohash mapping to a JSON file."""
        if self.instance_path is None:
            logger.error("Instance path is not set. Cannot save configuration.")
            return

        config_path = self.instance_path / "content_id_infohash_map.json"
        with config_path.open("w", encoding="utf-8") as file:
            json.dump(self.content_id_infohash_mapping, file)

    def add_mapping(self, content_id: str, infohash: str) -> None:
        """Add a mapping between content ID and infohash."""
        self.content_id_infohash_mapping[content_id] = infohash

    def get_infohash(self, content_id: str) -> str:
        """Get the infohash for a given content ID."""
        return self.content_id_infohash_mapping.get(content_id, "")

    def get_content_id(self, infohash: str) -> str:
        """Get the content ID for a given infohash."""
        return self.content_id_infohash_mapping.inverse.get(infohash, "")


content_id_infohash_mapping: ContentIDInfohashMapping = ContentIDInfohashMapping()
