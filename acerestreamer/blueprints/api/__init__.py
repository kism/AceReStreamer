"""API blueprints."""

from .ace_pool import bp as ace_pool_bp
from .auth import bp as auth_bp
from .epg import bp as epg_bp
from .health import bp as health_bp
from .scraper import bp as scraper_bp
from .streams import bp as streams_bp

__all__ = [
    "ace_pool_bp",
    "auth_bp",
    "epg_bp",
    "health_bp",
    "scraper_bp",
    "streams_bp",
]
