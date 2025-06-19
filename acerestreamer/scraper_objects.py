"""Custom Pydantic models (objects) for scraping."""

from pydantic import BaseModel


class FoundAceStream(BaseModel):
    """Model for a found AceStream."""

    title: str
    ace_id: str
    quality: int = -1


class FoundAceStreams(BaseModel):
    """Model for a list of found AceStreams."""

    site_name: str
    site_slug: str
    stream_list: list[FoundAceStream]


class CandidateAceStream(BaseModel):
    """Model for a candidate AceStream."""

    ace_id: str
    title_candidates: list[str] = []


class FlatFoundAceStream(BaseModel):
    """Flat model for a found AceStream."""

    site_name: str
    quality: int
    title: str
    ace_id: str
