"""Ace-specific scraper service."""

from acere.services.scraper.ace.api import AceAPIStreamScraper
from acere.services.scraper.ace.helpers import ace_create_unique_stream_list
from acere.services.scraper.ace.html import AceHTMLStreamScraper
from acere.services.scraper.ace.iptv import AceIPTVStreamScraper
from acere.services.scraper.ace.models import (
    AceScraperSourceApi,
    AceScraperSourcesApi,
    CandidateAceStream,
    FoundAceStream,
    FoundAceStreamAPI,
    ManuallyAddedAceStream,
)

__all__ = [
    "AceAPIStreamScraper",
    "AceHTMLStreamScraper",
    "AceIPTVStreamScraper",
    "AceScraperSourceApi",
    "AceScraperSourcesApi",
    "CandidateAceStream",
    "FoundAceStream",
    "FoundAceStreamAPI",
    "ManuallyAddedAceStream",
    "ace_create_unique_stream_list",
]
