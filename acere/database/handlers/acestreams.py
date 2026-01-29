"""Handler for content_id to xc_id mapping."""

from typing import TYPE_CHECKING

from pydantic import HttpUrl
from sqlmodel import select

from acere.database.models import AceStreamDBEntry
from acere.instances.config import settings
from acere.instances.xc_category import get_xc_category_db_handler
from acere.services.xc.models import XCCategory, XCStream
from acere.utils.logger import get_logger
from acere.utils.m3u8 import create_extinf_line

from .base import BaseDatabaseHandler

if TYPE_CHECKING:
    from acere.services.scraper.models import FoundAceStream
else:
    FoundAceStream = object

logger = get_logger(__name__)


class AceStreamDBHandler(BaseDatabaseHandler):
    """Handler for content_id to xc_id mapping."""

    _get_streams_cache: list[AceStreamDBEntry] | None = None

    def update_stream(self, stream: FoundAceStream) -> None:
        self._get_streams_cache = None  # Invalidate cache
        with self._get_session() as session:
            statement = select(AceStreamDBEntry).where(AceStreamDBEntry.content_id == stream.content_id)
            result = session.exec(statement).first()
            if result:
                # Update existing entry
                result.title = stream.title
                result.tvg_id = stream.tvg_id
                result.infohash = stream.infohash
                result.tvg_logo = stream.tvg_logo
                result.group_title = stream.group_title
                result.last_scraped_time = stream.last_scraped_time
                session.add(result)
                session.commit()
                logger.trace(
                    "Updated AceStreamDBEntry for content_id/infohash: %s/%s", stream.content_id, stream.infohash
                )
                self._get_streams_cache = None  # Invalidate cache
            else:
                # Create new entry
                new_entry = AceStreamDBEntry(**stream.model_dump())
                session.add(new_entry)
                session.commit()
                logger.debug(
                    "Created new AceStreamDBEntry for content_id/infohash: %s/%s", stream.content_id, stream.infohash
                )

    # region DELETE API
    def delete_by_content_id(self, content_id: str) -> bool:
        """Delete AceStreamDBEntry by content_id."""
        with self._get_session() as session:
            statement = select(AceStreamDBEntry).where(AceStreamDBEntry.content_id == content_id)
            result = session.exec(statement).first()
            if result:
                session.delete(result)
                session.commit()
                logger.info("Deleted AceStreamDBEntry for content_id: %s", content_id)
                self._get_streams_cache = None  # Invalidate cache
                return True
            return False

    # region GET API
    def get_by_content_id(self, content_id: str) -> AceStreamDBEntry | None:
        """Get AceStreamDBEntry by content_id."""
        with self._get_session() as session:
            statement = select(AceStreamDBEntry).where(AceStreamDBEntry.content_id == content_id)
            return session.exec(statement).first()

    def get_content_id_from_infohash(self, infohash: str) -> str | None:
        """Get content_id by infohash."""
        with self._get_session() as session:
            statement = select(AceStreamDBEntry).where(AceStreamDBEntry.infohash == infohash)
            result = session.exec(statement).first()
            if result:
                return result.content_id
            return None

    def get_streams(self) -> list[AceStreamDBEntry]:
        with self._get_session() as session:
            statement = select(AceStreamDBEntry)
            return list(session.exec(statement).all())

    def get_streams_cached(self) -> list[AceStreamDBEntry]:
        """Get streams for IPTV generation, with caching, and title deduplication."""
        if self._get_streams_cache is None:
            self._get_streams_cache = self.get_streams().copy()
            self._mark_alternate_streams(self._get_streams_cache)

        return self._get_streams_cache

    def get_content_id_by_tvg_id(self, tvg_id: str) -> str | None:
        """Get the content ID by TVG ID."""
        with self._get_session() as session:
            statement = select(AceStreamDBEntry).where(AceStreamDBEntry.tvg_id == tvg_id)
            result = session.exec(statement).first()
            if result:
                return result.content_id
            return None

    # region Get API XC
    def get_content_id_by_xc_id(self, xc_id: int) -> str | None:
        """Get content_id by xc_id."""
        with self._get_session() as session:
            record = session.get(AceStreamDBEntry, xc_id)
            if record:
                return record.content_id
            return None

    def get_xc_id_by_content_id(self, content_id: str) -> int | None:
        """Get xc_id by content_id."""
        with self._get_session() as session:
            statement = select(AceStreamDBEntry).where(AceStreamDBEntry.content_id == content_id)
            result = session.exec(statement).first()
            if result:
                return result.id
            return None

    # region GET IPTV
    def get_streams_as_iptv(self, token: str) -> str:
        """Get the found streams as an IPTV M3U8 string."""
        external_url = settings.EXTERNAL_URL
        if not external_url:
            logger.error("External URL is not set, cannot generate IPTV streams.")
            return ""

        # There are a few standards for the tag for the tvg url, most to least common x-tvg-url, url-tvg, tvg-url
        epg_url = HttpUrl(f"{external_url}epg")
        m3u8_content = f'#EXTM3U x-tvg-url="{epg_url}" url-tvg="{epg_url}" refresh="3600"\n'

        iptv_set = set()

        # I used to filter this for whether the stream has ever worked,
        # but sometimes sites change the id of their stream often...
        for stream in self.get_streams_cached():
            logger.debug(stream)

            external_url_tvg = HttpUrl(f"{external_url}tvg-logo/")

            line_one = create_extinf_line(
                stream, tvg_url_base=external_url_tvg, token=token, last_found=int(stream.last_scraped_time.timestamp())
            )
            line_two = f"{external_url}hls/{stream.content_id}"
            if token:
                line_two += f"?token={token}"

            iptv_set.add(line_one + line_two)

        return m3u8_content + "\n".join(sorted(iptv_set))

    # region GET IPTV XC
    def get_streams_as_iptv_xc(
        self,
        xc_category_filter: int | None,
        token: str = "",
    ) -> list[XCStream]:
        """Get the found streams as a list of XCStream objects."""
        handler = get_xc_category_db_handler()
        result_streams: list[XCStream] = []

        token_str = "" if token == "" else f"?token={token}"

        streams = self.get_streams_cached()

        current_stream_number = 1
        for stream in streams:
            xc_id = stream.id
            xc_category_id = handler.get_xc_category_id(stream.group_title)
            if xc_category_filter is None or xc_category_id == xc_category_filter:
                result_streams.append(
                    XCStream(
                        num=current_stream_number,
                        name=stream.title,
                        stream_id=xc_id,
                        stream_icon=f"{settings.EXTERNAL_URL}tvg-logo/{stream.tvg_logo}{token_str}"
                        if stream.tvg_logo
                        else "",
                        epg_channel_id=stream.tvg_id,
                        category_id=str(xc_category_id),
                    )
                )
            current_stream_number += 1

        return result_streams

    def get_xc_categories(self) -> list[XCCategory]:
        """Get all XC categories from the database."""
        handler = get_xc_category_db_handler()
        categories_in_use = {stream.category_id for stream in self.get_streams_as_iptv_xc(xc_category_filter=None)}
        categories_in_use_int = {int(cat_id) for cat_id in categories_in_use if cat_id.isdigit()}
        return handler.get_all_categories_api(categories_in_use_int)

    # region Helpers
    def _mark_alternate_streams(self, streams: list[AceStreamDBEntry]) -> None:
        """Iterates through streams and for any identical title, for duplicates mark the titles with a stream number."""
        results: dict[str, list[AceStreamDBEntry]] = {}  # Title, list of streams with that title
        streams_to_return: list[AceStreamDBEntry] = []

        for stream in streams:
            results[stream.title] = [*results.get(stream.title, []), stream]

        for streams_results in results.values():
            if len(streams_results) <= 1:
                streams_to_return.extend(streams_results)
                continue

            # Sort by xc_id, will approximatly be by date discovered
            streams_results.sort(key=lambda s: s.id)

            # Mark all but the first as alternate
            for n, stream in enumerate(streams_results):
                stream.title += f" #{n + 1}"
