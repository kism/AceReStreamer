"""Instances of various objects used throughout the application."""

from .ace_pool import AcePool
from .authentication_allow_list import AllowList
from .epg import EPGHandler
from .scraper import AceScraper
from .scraper_cache import ScraperCache
from .scraper_m3u_name_replacer import M3UNameReplacer

scraper_cache = ScraperCache()
m3u_replacer = M3UNameReplacer()
ace_pool = AcePool()
ace_scraper = AceScraper()
ip_allow_list = AllowList()
epg_handler = EPGHandler()
