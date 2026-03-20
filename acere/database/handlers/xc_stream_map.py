"""Handler for the xc_stream_map table."""

from sqlmodel import select

from acere.database.models.xc_stream_map import XCStreamMap
from acere.utils.logger import get_logger

from .base import BaseDatabaseHandler

logger = get_logger(__name__)


class XCStreamMapHandler(BaseDatabaseHandler):
    """Handler for the unified XC stream mapping table."""

    def get_or_create_xc_id(self, stream_type: str, stream_key: str) -> int:
        """Return the xc_id for the given (stream_type, stream_key). Creates a new row if absent."""
        with self._get_session() as session:
            statement = select(XCStreamMap).where(
                XCStreamMap.stream_type == stream_type,
                XCStreamMap.stream_key == stream_key,
            )
            row = session.exec(statement).first()
            if row is not None and row.xc_id is not None:
                return row.xc_id

            new_row = XCStreamMap(stream_type=stream_type, stream_key=stream_key)
            session.add(new_row)
            session.commit()
            session.refresh(new_row)
            if new_row.xc_id is None:  # pragma: no cover
                msg = "Failed to assign xc_id after insert"
                raise RuntimeError(msg)
            logger.debug(
                "Created xc_stream_map entry: type=%s key=%s -> xc_id=%d",
                stream_type,
                stream_key,
                new_row.xc_id,
            )
            return new_row.xc_id

    def get_xc_id(self, stream_type: str, stream_key: str) -> int | None:
        """Return the xc_id for the given (stream_type, stream_key), or None."""
        with self._get_session() as session:
            statement = select(XCStreamMap).where(
                XCStreamMap.stream_type == stream_type,
                XCStreamMap.stream_key == stream_key,
            )
            row = session.exec(statement).first()
            return row.xc_id if row is not None else None

    def get_stream_info_by_xc_id(self, xc_id: int) -> tuple[str, str] | None:
        """Return (stream_type, stream_key) for the given xc_id, or None."""
        with self._get_session() as session:
            row = session.get(XCStreamMap, xc_id)
            if row is not None:
                return (row.stream_type, row.stream_key)
            return None

    def delete_by_type_and_keys(self, stream_type: str, keys_to_keep: set[str]) -> int:
        """Delete xc_stream_map rows of the given stream_type whose stream_key is NOT in keys_to_keep."""
        with self._get_session() as session:
            statement = select(XCStreamMap).where(XCStreamMap.stream_type == stream_type)
            rows = list(session.exec(statement).all())
            deleted = 0
            for row in rows:
                if row.stream_key not in keys_to_keep:
                    session.delete(row)
                    deleted += 1
            if deleted:
                session.commit()
                logger.info("Deleted %d stale xc_stream_map entries for type=%s", deleted, stream_type)
            return deleted

    def register_keys(self, stream_type: str, stream_keys: set[str]) -> None:
        """Ensure every key in stream_keys has a mapping row. Idempotent."""
        for key in stream_keys:
            self.get_or_create_xc_id(stream_type, key)
