"""Remote Settings Instance."""

from acere.instances import GlobalInstance
from acere.services.remote_settings import RemoteSettingsFetcher

_remote_settings_fetcher: GlobalInstance[RemoteSettingsFetcher] = GlobalInstance("RemoteSettingsFetcher")
set_remote_settings_fetcher = _remote_settings_fetcher.set
get_remote_settings_fetcher = _remote_settings_fetcher.get
