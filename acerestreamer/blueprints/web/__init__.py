"""Web blueprints."""

from .auth import bp as auth_bp
from .epg import bp as epg_bp
from .home import bp as home_bp
from .info import bp as info_bp
from .iptv import bp as iptv_bp
from .streams import bp as streams_bp

__all__ = [
    "auth_bp",
    "epg_bp",
    "home_bp",
    "info_bp",
    "iptv_bp",
    "streams_bp",
]
