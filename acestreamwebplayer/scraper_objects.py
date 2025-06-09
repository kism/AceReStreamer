"""Custom Pydantic models (objects) for scraping."""

from pydantic import BaseModel


class FoundAceStream(BaseModel):
    """Model for a found AceStream."""

    title: str
    ace_id: str


class FoundAceStreams(BaseModel):
    """Model for a list of found AceStreams."""

    site_name: str
    stream_list: list[FoundAceStream]


class CandidateAceStream(BaseModel):
    """Model for a candidate AceStream."""

    ace_id: str
    title_candidates: list[str] = []
