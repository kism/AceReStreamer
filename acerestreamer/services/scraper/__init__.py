"""Scraper service."""

from acerestreamer.services.scraper.cache import ScraperCache
from acerestreamer.services.scraper.main import AceScraper
from acerestreamer.services.scraper.objects import (
    CandidateAceStream,
    FlatFoundAceStream,
    FoundAceStream,
    FoundAceStreams,
)

__all__ = [
    "AceScraper",
    "CandidateAceStream",
    "FlatFoundAceStream",
    "FoundAceStream",
    "FoundAceStreams",
    "ScraperCache",
]
