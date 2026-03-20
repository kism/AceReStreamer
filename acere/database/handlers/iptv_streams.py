"""Handler for IPTV proxy streams."""

from typing import TYPE_CHECKING

from pydantic import HttpUrl
from sqlmodel import select

from acere.database.models.iptv_stream import IPTVStreamDBEntry
from acere.instances.config import settings
from acere.instances.xc_category import get_xc_category_db_handler
from acere.services.xc.models import XCCategory, XCStream
from acere.utils.logger import get_logger
from acere.utils.m3u8 import create_extinf_line

from .base import BaseDatabaseHandler

if TYPE_CHECKING:
    from acere.services.scraper.models import FoundIPTVStream
else:
    FoundIPTVStream = object

logger = get_logger(__name__)


class IPTVStreamDBHandler(BaseDatabaseHandler):
    """Handler for IPTV proxy stream database operations."""

    _get_streams_cache: list[IPTVStreamDBEntry] | None = None

    def update_stream(self, stream: FoundIPTVStream, slug: str) -> None:
        """Update or create an IPTV stream entry."""
        self._get_streams_cache = None
        with self._get_session() as session:
            statement = select(IPTVStreamDBEntry).where(IPTVStreamDBEntry.slug == slug)
            result = session.exec(statement).first()
            if result:
                result.title = stream.title
                result.upstream_url = stream.upstream_url
                result.source_name = stream.source_name
                result.tvg_id = stream.tvg_id
                result.tvg_logo = stream.tvg_logo
                result.group_title = stream.group_title
                result.last_scraped_time = stream.last_scraped_time
                session.add(result)
                session.commit()
                logger.trace("Updated IPTVStreamDBEntry for slug: %s", slug)
            else:
                new_entry = IPTVStreamDBEntry(
                    title=stream.title,
                    upstream_url=stream.upstream_url,
                    slug=slug,
                    source_name=stream.source_name,
                    tvg_id=stream.tvg_id,
                    tvg_logo=stream.tvg_logo,
                    group_title=stream.group_title,
                    last_scraped_time=stream.last_scraped_time,
                )
                session.add(new_entry)
                session.commit()
                logger.debug("Created new IPTVStreamDBEntry for slug: %s", slug)

    def get_by_slug(self, slug: str) -> IPTVStreamDBEntry | None:
        """Get an IPTV stream by its slug."""
        with self._get_session() as session:
            statement = select(IPTVStreamDBEntry).where(IPTVStreamDBEntry.slug == slug)
            return session.exec(statement).first()

    def delete_by_slug(self, slug: str) -> bool:
        """Delete an IPTV stream by its slug."""
        with self._get_session() as session:
            statement = select(IPTVStreamDBEntry).where(IPTVStreamDBEntry.slug == slug)
            result = session.exec(statement).first()
            if result:
                session.delete(result)
                session.commit()
                logger.info("Deleted IPTVStreamDBEntry for slug: %s", slug)
                self._get_streams_cache = None
                return True
            return False

    def get_streams(self) -> list[IPTVStreamDBEntry]:
        """Get all IPTV streams."""
        with self._get_session() as session:
            statement = select(IPTVStreamDBEntry)
            return list(session.exec(statement).all())

    def get_streams_cached(self) -> list[IPTVStreamDBEntry]:
        """Get streams with caching."""
        if self._get_streams_cache is None:
            self._get_streams_cache = self.get_streams().copy()
        return self._get_streams_cache

    def delete_streams_by_source(self, source_name: str) -> int:
        """Delete all streams from a given source. Returns count of deleted rows."""
        self._get_streams_cache = None
        with self._get_session() as session:
            statement = select(IPTVStreamDBEntry).where(IPTVStreamDBEntry.source_name == source_name)
            streams = list(session.exec(statement).all())
            count = len(streams)
            for stream in streams:
                session.delete(stream)
            session.commit()
            logger.info("Deleted %d IPTV streams from source '%s'", count, source_name)
            return count

    def get_iptv_lines(self, token: str) -> list[str]:
        """Return IPTV EXTINF+URL pairs for all IPTV proxy streams, without M3U header."""
        external_url = settings.EXTERNAL_URL
        iptv_entries: list[str] = []

        for stream in self.get_streams_cached():
            external_url_tvg = HttpUrl(f"{external_url}/tvg-logo/")
            line_one = create_extinf_line(
                stream, tvg_url_base=external_url_tvg, token=token, last_found=int(stream.last_scraped_time.timestamp())
            )
            stream_url = f"{external_url}/hls/web/{stream.slug}"
            if token:
                stream_url += f"?token={token}"
            iptv_entries.append(line_one + stream_url)

        return sorted(iptv_entries)

    def get_streams_as_iptv(self, token: str) -> str:
        """Get the IPTV proxy streams as an M3U8 string."""
        external_url = settings.EXTERNAL_URL

        epg_url_str = f"{external_url}/epg.xml"
        if token:
            epg_url_str += f"?token={token}"
        epg_url = HttpUrl(epg_url_str)
        m3u8_content = f'#EXTM3U x-tvg-url="{epg_url}" url-tvg="{epg_url}" refresh="3600"\n'

        return m3u8_content + "\n".join(self.get_iptv_lines(token))

    # region GET IPTV XC
    def get_streams_as_iptv_xc(
        self,
        xc_category_filter: int | None,
        token: str = "",
    ) -> list[XCStream]:
        """Get IPTV proxy streams as XCStream objects."""
        from acere.instances.xc_stream_map import get_xc_stream_map_handler  # noqa: PLC0415

        cat_handler = get_xc_category_db_handler()
        xc_map = get_xc_stream_map_handler()
        result_streams: list[XCStream] = []
        token_str = "" if token == "" else f"?token={token}"
        streams = self.get_streams_cached()

        current_stream_number = 1
        for stream in streams:
            xc_id = xc_map.get_or_create_xc_id("iptv", stream.slug)
            xc_category_id = cat_handler.get_xc_category_id(stream.group_title)
            if xc_category_filter is None or xc_category_id == xc_category_filter:
                result_streams.append(
                    XCStream(
                        num=current_stream_number,
                        name=stream.title,
                        stream_id=xc_id,
                        stream_icon=f"{settings.EXTERNAL_URL}/tvg-logo/{stream.tvg_logo}{token_str}"
                        if stream.tvg_logo
                        else "",
                        epg_channel_id=stream.tvg_id,
                        category_id=str(xc_category_id),
                    )
                )
            current_stream_number += 1

        return result_streams

    def get_xc_categories(self) -> list[XCCategory]:
        """Get XC categories in use by IPTV proxy streams."""
        cat_handler = get_xc_category_db_handler()
        categories_in_use = {stream.category_id for stream in self.get_streams_as_iptv_xc(xc_category_filter=None)}
        categories_in_use_int = {int(cat_id) for cat_id in categories_in_use if cat_id.isdigit()}
        return cat_handler.get_all_categories_api(categories_in_use_int)
