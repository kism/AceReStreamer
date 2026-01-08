"""Handler for content_id to xc_id mapping."""

from sqlmodel import select

from acere.database.models import AceQualityCache
from acere.services.ace_quality import Quality
from acere.utils.helpers import check_valid_content_id_or_infohash
from acere.utils.logger import get_logger

from .base import BaseDatabaseHandler

logger = get_logger(__name__)


class AceQualityCacheHandler(BaseDatabaseHandler):
    """Database handler for the Ace Quality Cache."""

    default_quality = Quality().quality

    def get_all(self) -> dict[str, Quality]:
        """Get all entries as a dict."""
        with self._get_session() as session:
            result = session.exec(select(AceQualityCache)).all()
            return {
                entry.content_id: Quality(
                    quality=entry.quality,
                    has_ever_worked=entry.has_ever_worked,
                    m3u_failures=entry.m3u_failures,
                )
                for entry in result
            }

    def get_quality(self, content_id: str) -> Quality:
        """Get the quality for a given content_id."""
        with self._get_session() as session:
            result = session.exec(select(AceQualityCache).where(AceQualityCache.content_id == content_id)).first()
            if result:
                return Quality(
                    quality=result.quality,
                    has_ever_worked=result.has_ever_worked,
                    m3u_failures=result.m3u_failures,
                )

            new_quality = Quality()
            self.set_quality(content_id=content_id, quality=new_quality)
            return new_quality

    def set_quality(self, content_id: str, quality: Quality) -> None:
        """Set the quality for a given content_id."""
        with self._get_session() as session:
            result = session.exec(select(AceQualityCache).where(AceQualityCache.content_id == content_id)).first()
            if not result:
                result = AceQualityCache(content_id=content_id)
                session.add(result)

            result.quality = quality.quality
            result.has_ever_worked = quality.has_ever_worked
            result.m3u_failures = quality.m3u_failures
            session.commit()

    def clean_table(self) -> None:
        """Clean the quality cache table."""
        with self._get_session() as session:
            all_entries = session.exec(select(AceQualityCache)).all()
            for entry in all_entries:
                if not check_valid_content_id_or_infohash(entry.content_id):
                    logger.error(
                        "Found invalid content_id in quality cache: %s",
                        entry.content_id,
                    )
                    session.delete(entry)
            session.commit()

    def increment_quality(self, content_id: str, m3u_playlist: str) -> None:
        """Increment the quality of a stream by content_id."""
        if not check_valid_content_id_or_infohash(content_id):
            return

        if "#EXT-X-STREAM-INF" in m3u_playlist:
            logger.debug(
                "Skipping quality update for Ace ID %s, multistream detected",
                content_id,
            )
            return

        entry = self.get_quality(content_id)
        entry.update_quality(m3u_playlist)

        logger.debug("Updated quality for Ace ID %s: %s", content_id, entry.quality)

        self.set_quality(content_id, entry)
