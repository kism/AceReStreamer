"""Handler for IPTV proxy streams."""

from typing import TYPE_CHECKING

from pydantic import HttpUrl
from sqlmodel import select

from acere.database.models.iptv_stream import IPTVStreamDBEntry
from acere.instances.config import settings
from acere.utils.logger import get_logger

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

    def get_streams_as_iptv(self, token: str) -> str:
        """Get the IPTV proxy streams as an M3U8 string."""
        external_url = settings.EXTERNAL_URL

        epg_url_str = f"{external_url}/epg.xml"
        if token:
            epg_url_str += f"?token={token}"
        epg_url = HttpUrl(epg_url_str)
        m3u8_content = f'#EXTM3U x-tvg-url="{epg_url}" url-tvg="{epg_url}" refresh="3600"\n'

        iptv_lines: list[str] = []

        for stream in self.get_streams_cached():
            extinf_parts = [
                "#EXTINF:-1",
            ]
            if stream.tvg_logo:
                logo_url = f"{external_url}/tvg-logo/{stream.tvg_logo}"
                if token:
                    logo_url += f"?token={token}"
                extinf_parts.append(f'tvg-logo="{logo_url}"')
            if stream.tvg_id:
                extinf_parts.append(f'tvg-id="{stream.tvg_id}"')
            if stream.group_title:
                extinf_parts.append(f'group-title="{stream.group_title}"')

            extinf_line = f"{' '.join(extinf_parts)},{stream.title}\n"
            stream_url = f"{external_url}/hls/web/{stream.slug}"
            if token:
                stream_url += f"?token={token}"

            iptv_lines.append(extinf_line + stream_url)

        return m3u8_content + "\n".join(sorted(iptv_lines))
