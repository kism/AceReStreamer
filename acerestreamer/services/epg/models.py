"""EPG API Models."""

from pydantic import BaseModel


class EPGApiResponse(BaseModel):
    """Model for EPG API response."""

    url: str
    region_code: str
    seconds_since_last_updated: int
