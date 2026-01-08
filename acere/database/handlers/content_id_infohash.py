"""Handler for content_id to infohash mapping."""

import requests
from pydantic import HttpUrl
from sqlmodel import select

from acere.database.models import ContentIdInfohash
from acere.utils.logger import get_logger

from .base import BaseDatabaseHandler

logger = get_logger(__name__)


class ContentIdInfohashDatabaseHandler(BaseDatabaseHandler):
    """Database handler for mapping content_id and infohash."""

    def __init__(self) -> None:
        """Initialise the handler."""
        self.ace_url: HttpUrl | None = None
        super().__init__()

    def load(self, ace_url: HttpUrl) -> None:
        """Load the ACE URL."""
        self.ace_url = ace_url

    def add_mapping(self, infohash: str = "", content_id: str = "") -> None:
        """Add a new mapping of infohash to content_id."""
        if not infohash and not content_id:
            return

        if self.get_infohash(content_id) or self.get_content_id(infohash):
            return

        mapping = ContentIdInfohash(infohash=infohash, content_id=content_id)

        with self._get_session() as session:
            session.add(mapping)
            session.commit()

    def get_infohash(self, content_id: str) -> str:
        """Get infohash by content_id."""
        with self._get_session() as session:
            mapping = session.exec(select(ContentIdInfohash).where(ContentIdInfohash.content_id == content_id)).first()
            if isinstance(mapping, ContentIdInfohash):
                return mapping.infohash
        return ""

    def get_content_id(self, infohash: str) -> str:
        """Get content_id by infohash."""
        with self._get_session() as session:
            mapping = session.exec(select(ContentIdInfohash).where(ContentIdInfohash.infohash == infohash)).first()
            if isinstance(mapping, ContentIdInfohash):
                return mapping.content_id
        return ""

    def populate_from_api(self, infohash: str) -> str:
        """Populate the mapping from th Ace API from infohash, returning the content ID."""
        if not self.ace_url:
            logger.warning("ACE URL is not set for ContentIdInfohashDatabaseHandler")
            return ""

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
