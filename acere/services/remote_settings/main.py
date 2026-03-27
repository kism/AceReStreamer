import asyncio
import json
import threading
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import aiohttp
from pydantic import HttpUrl, ValidationError

from acere.config import AceReStreamerConf, ConfigExport
from acere.instances.ace_manager import get_ace_manager
from acere.instances.config import settings
from acere.instances.epg import get_epg_handler
from acere.utils.exception_handling import log_aiohttp_exception
from acere.utils.logger import get_logger

from .models import RemoteSettingsGetModel

if TYPE_CHECKING:
    from .models import RemoteSettingsGetModel
else:
    RemoteSettingsGetModel = object

logger = get_logger(__name__)

REMOTE_SETTINGS_FETCH_TIME = timedelta(days=1)


class RemoteSettingsFetcher:
    def __init__(self, instance_id: str) -> None:
        self._threads: list[threading.Thread] = []
        self._stop_event = threading.Event()
        self._instance_id = instance_id
        self._status: str = "Initialized"
        self._last_fetch_time: datetime | None = None
        self.start_fetching()

    # region GET
    def get_remote_settings_url(self) -> RemoteSettingsGetModel:
        """Get the current remote settings URL."""
        return RemoteSettingsGetModel(
            url=settings.remote_settings.url,
            enable_epg=settings.remote_settings.enable_epg,
            enable_ace=settings.remote_settings.enable_ace,
            status=self._status,
            last_fetched=self._last_fetch_time,
        )

    def get_export_config(self) -> ConfigExport:
        return ConfigExport(
            scraper=settings.ace.scraper,
            epgs=settings.epgs,
        )

    # region POST
    def set_remote_settings_url(
        self,
        url: HttpUrl | None,
        *,
        enable_epg: bool = True,
        enable_ace: bool = True,
    ) -> None:
        settings.remote_settings.url = url
        settings.remote_settings.enable_epg = enable_epg
        settings.remote_settings.enable_ace = enable_ace
        settings.write_backup_config(
            config_path=None,
            existing_data=json.loads(settings.model_dump_json()),
            reason="Remote settings URL and flags updated via API",
        )
        settings.write_config()
        self._status = "URL Updated..."
        self.start_fetching()

    def update_config_with_export(self, config: ConfigExport) -> ConfigExport:
        current_config = self.get_export_config()

        if current_config.model_dump_json() == config.model_dump_json():
            logger.info("Remote settings are identical to current settings; no update needed.")
            return current_config

        settings.ace.scraper = config.scraper
        settings.epgs = config.epgs
        settings.write_backup_config(
            config_path=None,
            existing_data=json.loads(settings.model_dump_json()),
            reason="Configuration updated via API",
        )
        self.reload_config()

        return ConfigExport(
            scraper=settings.ace.scraper,
            epgs=settings.epgs,
        )

    def reload_config(self) -> None:
        """Reload the current configuration."""
        settings.write_config()
        get_ace_manager().start_scrape_thread()
        get_epg_handler().update_epgs(settings.epgs)

    # region Fetch http
    async def fetch_settings(self) -> None:
        if settings.remote_settings.url is None:
            logger.trace("Remote settings URL is not set; skipping fetch. id: %s", self._instance_id)
            return

        logger.info("Fetching remote settings from %s", settings.remote_settings.url.encoded_string())
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(settings.remote_settings.url.encoded_string()) as resp:
                    resp.raise_for_status()
                    data = await resp.text()
            except (aiohttp.ClientError, TimeoutError) as e:
                log_aiohttp_exception(logger, settings.remote_settings.url, e, "Failed to fetch remote settings")
                return
            except Exception as e:
                self._status = e.__class__.__name__
                logger.exception("Unexpected error while fetching remote settings")
                return

        try:
            data_json = json.loads(data)
            new_settings = AceReStreamerConf(**data_json)
        except json.JSONDecodeError as e:
            self._status = e.__class__.__name__
            logger.error("Failed to decode remote settings JSON: %s", e)
            return
        except ValidationError as e:
            self._status = e.__class__.__name__
            logger.error("Valid json, but invalid remote settings format: %s", e)
            return

        self._status = "fetched"
        self._last_fetch_time = datetime.now(tz=UTC)

        # Build ConfigExport based on enabled flags, falling back to current config if disabled
        scraper = new_settings.ace.scraper if settings.remote_settings.enable_ace else settings.ace.scraper
        epgs = new_settings.epgs if settings.remote_settings.enable_epg else settings.epgs

        self.update_config_with_export(
            ConfigExport(
                scraper=scraper,
                epgs=epgs,
            )
        )

    # region Thread
    def fetch_settings_thread(self) -> None:
        logger.info("Starting remote settings fetch thread. [%s]", self._instance_id)
        while not self._stop_event.is_set():
            asyncio.run(self.fetch_settings())
            # Use wait instead of sleep so we can be interrupted
            if self._stop_event.wait(REMOTE_SETTINGS_FETCH_TIME.total_seconds()):
                break

    def start_fetching(self) -> None:
        self.stop_all_threads()
        thread = threading.Thread(
            target=self.fetch_settings_thread, name="RemoteSettingsFetcher: fetch_settings", daemon=True
        )
        self._threads.append(thread)
        thread.start()

    def stop_all_threads(self) -> None:
        """Stop all threads in the RemoteSettingsFetcher."""
        if len(self._threads) == 0:
            return

        logger.info("Stopping all %s threads [%s]", self.__class__.__name__, self._instance_id)
        self._stop_event.set()
        for thread in self._threads.copy():
            if thread.is_alive():
                thread.join(timeout=60)
                if not thread.is_alive():
                    self._threads.remove(thread)
                else:
                    logger.warning("Thread %s did not stop in time.", thread.name)

        self._stop_event.clear()
