"""Mapping between content IDs and infohashes."""

import csv
from pathlib import Path

import requests
from bidict import bidict

from acerestreamer.utils import check_valid_content_id_or_infohash
from acerestreamer.utils.logger import get_logger

logger = get_logger(__name__)


class ContentIDInfohashMapping:
    """A class to manage the mapping between content IDs and infohashes."""

    def __init__(self) -> None:
        """Initialize the mapping."""
        self.content_id_infohash_mapping: bidict[str, str] = bidict()
        self.config_path: Path | None = None
        self.ace_url: str | None = None

    def load_config(self, instance_path: str | Path, ace_url: str) -> None:
        """Load the content ID to infohash mapping from a JSON file."""
        if isinstance(instance_path, str):
            instance_path = Path(instance_path)
        self.config_path = instance_path / "content_id_infohash_map.csv"

        self.ace_url = ace_url

        if not self.config_path.exists():
            return

        with self.config_path.open("r", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:  # noqa: PLR2004
                    content_id, infohash = row
                    if check_valid_content_id_or_infohash(content_id) and check_valid_content_id_or_infohash(infohash):
                        self.content_id_infohash_mapping[content_id] = infohash
                    else:
                        logger.warning(
                            "Invalid content ID or infohash in mapping: %s, %s",
                            content_id,
                            infohash,
                        )

    def _save_config(self) -> None:
        """Save the content ID to infohash mapping to a JSON file."""
        if self.config_path is None:
            logger.error("Instance path is not set. Cannot save configuration.")
            return

        with self.config_path.open("w", encoding="utf-8") as file:
            writer = csv.writer(file)
            for content_id, infohash in self.content_id_infohash_mapping.items():
                writer.writerow([content_id, infohash])

    def add_mapping(self, content_id: str, infohash: str) -> None:
        """Add a mapping between content ID and infohash."""
        self.content_id_infohash_mapping[content_id] = infohash
        self._save_config()

    def get_infohash(self, content_id: str) -> str:
        """Get the infohash for a given content ID."""
        return self.content_id_infohash_mapping.get(content_id, "")

    def get_content_id(self, infohash: str) -> str:
        """Get the content ID for a given infohash."""
        return self.content_id_infohash_mapping.inverse.get(infohash, "")

    def populate_from_api(self, infohash: str) -> str:
        """Populate the mapping from th Ace API from infohash, returning the content ID."""
        logger.info("Populating missing content ID for infohash %s", infohash)
        content_id = ""
        url = f"{self.ace_url}/server/api?api_version=3&method=get_content_id&infohash="

        try:
            resp = requests.get(
                f"{url}{infohash}",
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            error_short = type(e).__name__
            logger.error(  # noqa: TRY400 Short error for requests
                "%s Failed to fetch content ID for infohash %s",
                error_short,
                infohash,
            )
            return content_id

        if data.get("result", {}).get("content_id"):
            content_id = data.get("result", {}).get("content_id", "")
            logger.info(
                "Populated missing content ID for stream %s -> %s",
                infohash,
                content_id,
            )
            self.add_mapping(
                content_id=content_id,
                infohash=infohash,
            )

        return content_id
