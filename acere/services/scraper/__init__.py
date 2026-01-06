"""Scraper service."""

from acere.services.scraper.api import APIStreamScraper
from acere.services.scraper.cache import ScraperCache
from acere.services.scraper.helpers import create_unique_stream_list
from acere.services.scraper.html import HTMLStreamScraper
from acere.services.scraper.iptv import IPTVStreamScraper
from acere.services.scraper.main import AceScraper
from acere.services.scraper.models import (
    CandidateAceStream,
    FoundAceStream,
    FoundAceStreamAPI,
)
from acere.services.scraper.name_processor import StreamNameProcessor

__all__ = [
    "APIStreamScraper",
    "AceScraper",
    "CandidateAceStream",
    "FoundAceStream",
    "FoundAceStreamAPI",
    "HTMLStreamScraper",
    "IPTVStreamScraper",
    "Quality",
    "ScraperCache",
    "StreamNameProcessor",
    "create_unique_stream_list",
]
