"""IPTV Proxy Manager instance."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from acere.services.iptv_proxy.manager import IPTVProxyManager
else:
    IPTVProxyManager = object

_iptv_proxy_manager: IPTVProxyManager | None = None


def set_iptv_proxy_manager(manager: IPTVProxyManager) -> None:
    """Set the global IPTVProxyManager instance."""
    global _iptv_proxy_manager
    _iptv_proxy_manager = manager
    _iptv_proxy_manager.start_scrape_thread()


def get_iptv_proxy_manager() -> IPTVProxyManager:
    """Get the global IPTVProxyManager instance."""
    if _iptv_proxy_manager is None:
        msg = "IPTVProxyManager instance is not set."
        raise ValueError(msg)
    return _iptv_proxy_manager
