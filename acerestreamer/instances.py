"""Instances of various objects used throughout the application."""

from acerestreamer.services.ace_pool import AcePool
from acerestreamer.services.authentication import AllowList
from acerestreamer.services.scraper import AceScraper

ace_pool = AcePool()
ace_scraper = AceScraper()
ip_allow_list = AllowList()
