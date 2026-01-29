"""Remote Settings Instance."""

from acere.services.remote_settings import RemoteSettingsFetcher

_remote_settings_fetcher: RemoteSettingsFetcher | None = None


def set_remote_settings_fetcher(fetcher: RemoteSettingsFetcher) -> None:
    """Set the global RemoteSettingsFetcher instance."""
    global _remote_settings_fetcher  # noqa: PLW0603
    _remote_settings_fetcher = fetcher


def get_remote_settings_fetcher() -> RemoteSettingsFetcher:
    """Get the global RemoteSettingsFetcher instance."""
    if _remote_settings_fetcher is None:
        msg = "RemoteSettingsFetcher instance is not set."
        raise ValueError(msg)

    return _remote_settings_fetcher
