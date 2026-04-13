"""Handler for persistent content_id to xc_id mapping."""

from sqlmodel import select

from acere.database.models.content_id_xc_id import ContentIdXcId
from acere.utils.logger import get_logger

from .base import BaseDatabaseHandler

logger = get_logger(__name__)


class ContentIdXcIdDatabaseHandler(BaseDatabaseHandler):
    """Handler for persistent content_id to xc_id mapping."""

    def get_or_create_xc_id(self, content_id: str) -> int:
        """Get existing xc_id for content_id, or create a new permanent mapping."""
        with self._get_session() as session:
            result = session.exec(select(ContentIdXcId).where(ContentIdXcId.content_id == content_id)).first()
            if isinstance(result, ContentIdXcId):
                return result.xc_id

            new_mapping = ContentIdXcId(content_id=content_id)
            session.add(new_mapping)
            session.commit()
            session.refresh(new_mapping)
            logger.trace("Created new XC stream ID mapping: %s -> %d", content_id, new_mapping.xc_id)
            return new_mapping.xc_id

    def get_content_id_by_xc_id(self, xc_id: int) -> str | None:
        """Get content_id by xc_id."""
        with self._get_session() as session:
            result = session.get(ContentIdXcId, xc_id)
            if result:
                return result.content_id
            return None
