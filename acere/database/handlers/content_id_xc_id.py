"""Handler for content_id to xc_id mapping."""

from sqlmodel import select

from acere.database.models import ContentIdXCID

from .base import BaseDatabaseHandler


class ContentIdXCIDDatabaseHandler(BaseDatabaseHandler):
    """Handler for content_id to xc_id mapping."""

    def get_xc_id(self, content_id: str) -> int:
        """Get the xc_id for a given content_id."""
        with self._get_session() as session:
            result = session.exec(select(ContentIdXCID).where(ContentIdXCID.content_id == content_id)).first()

            if result:
                return result.xc_id

            new_mapping = ContentIdXCID(content_id=content_id)
            session.add(new_mapping)
            session.commit()
            return new_mapping.xc_id

    def get_content_id(self, xc_id: int) -> str:
        """Get the content_id for a given xc_id."""
        with self._get_session() as session:
            result = session.exec(select(ContentIdXCID).where(ContentIdXCID.xc_id == xc_id)).first()
            return result.content_id if result else ""
