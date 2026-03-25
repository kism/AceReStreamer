"""Scraper service."""

from acere.services.scraper.ace import (
    AceAPIStreamScraper,
    AceHTMLStreamScraper,
    AceIPTVStreamScraper,
    AceScraperSourceApi,
    AceScraperSourcesApi,
    CandidateAceStream,
    FoundAceStream,
    FoundAceStreamAPI,
    ManuallyAddedAceStream,
    ace_create_unique_stream_list,
)
from acere.services.scraper.cache import ScraperCache
from acere.services.scraper.models import (
    CombinedStreamAPI,
    FoundIPTVStream,
    FoundIPTVStreamAPI,
    IPTVSourceApi,
)

__all__ = [
    "AceAPIStreamScraper",
    "AceHTMLStreamScraper",
    "AceIPTVStreamScraper",
    "AceScraperSourceApi",
    "AceScraperSourcesApi",
    "CandidateAceStream",
    "CombinedStreamAPI",
    "FoundAceStream",
    "FoundAceStreamAPI",
    "FoundIPTVStream",
    "FoundIPTVStreamAPI",
    "IPTVSourceApi",
    "ManuallyAddedAceStream",
    "ScraperCache",
    "ace_create_unique_stream_list",
]
