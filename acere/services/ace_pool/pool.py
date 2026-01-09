"""AceStream pool management module."""

import contextlib
import threading
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import requests
from pydantic import HttpUrl, TypeAdapter

from acere.instances.config import settings
from acere.utils.constants import OUR_TIMEZONE
from acere.utils.helpers import check_valid_content_id_or_infohash
from acere.utils.logger import get_logger

from .constants import ACESTREAM_API_TIMEOUT
from .entry import AcePoolEntry
from .models import AcePoolAllStatsApi, AcePoolEntryForAPI, AcePoolForApi, AcePoolStat

logger = get_logger(__name__)

if TYPE_CHECKING:
    from acere.core.config import AppConf
else:
    AppConf = object


class AcePool:
    """A pool of AceStream instances to distribute requests across."""

    def __init__(self, instance_id: str = "") -> None:
        """Initialize the AcePool."""
        self._instance_id = instance_id
        logger.debug("Initializing AcePool (%s)", self._instance_id)
        self.ace_address = settings.app.ace_address
        self.max_size = settings.app.ace_max_streams
        self.transcode_audio = settings.app.transcode_audio
        self.ace_instances: dict[str, AcePoolEntry] = {}
        self.healthy = False
        self.ace_version = "unknown"
        self._ace_poolboy_running = False
        self.ace_poolboy()

    # region Health
    def check_ace_running(self) -> bool:
        """Use the AceStream API to check if the instance is running."""
        logger.trace("AcePool check_ace_running (%s)", self._instance_id)
        healthy = False
        if not self.ace_address:
            return healthy

        url = f"{self.ace_address}/webui/api/service?method=get_version"
        version_data = {}

        try:
            response = requests.get(url, timeout=ACESTREAM_API_TIMEOUT)
            response.raise_for_status()
            version_data = response.json()
            if not self.healthy:
                logger.info("Ace Instance %s is healthy", self.ace_address)
            healthy = True
        except requests.RequestException as e:
            error_short = type(e).__name__
            logger.error("Ace Instance %s is not healthy: %s", self.ace_address, error_short)
            healthy = False
        except Exception as e:  # noqa: BLE001 Last resort
            error_short = type(e).__name__
            logger.error(
                "Ace Instance %s is not healthy for a weird reason: %s",
                self.ace_address,
                e,
            )
            healthy = False

        self.ace_version = version_data.get("result", {}).get("version", "unknown")
        self.healthy = healthy

        return self.healthy

    # region Delete
    def remove_instance_by_content_id(self, content_id: str, caller: str = "") -> bool:
        """Remove an AceStream instance from the pool by content_id."""
        if caller != "":
            caller = f"{caller}: "
        if content_id in self.ace_instances:
            logger.info("%sRemoving AceStream instance with content_id %s", caller, content_id)
            with contextlib.suppress(KeyError):
                self.ace_instances[content_id].stop()
                del self.ace_instances[content_id]
            return True

        return False

    # region Getters
    def get_available_instance_number(self) -> int | None:
        """Get the next available AceStream instance URL."""
        instance_numbers = [instance.ace_pid for instance in self.ace_instances.values()]

        for n in range(1, self.max_size + 1):  # Minimum instance number is 1, per the API
            if n not in instance_numbers:
                return n

        shortlist_instances_to_reclaim = [  # We will try to reclaim a non-locked-in instance
            instance for instance in self.ace_instances.values() if not instance.check_locked_in()
        ]

        if shortlist_instances_to_reclaim:
            best_instance = min(shortlist_instances_to_reclaim, key=lambda x: x.last_used)

            logger.info(
                "Found available AceStream instance: %s, reclaiming it.",
                best_instance.ace_pid,
            )
            ace_pid = best_instance.ace_pid
            self.remove_instance_by_content_id(best_instance.content_id, caller="get_available_instance_number")
            return ace_pid

        logger.error("Ace pool is full, could not get available instance.")
        return None

    def get_instance_hls_url_by_content_id(self, content_id: str) -> HttpUrl | None:
        """Find the AceStream instance URL for a given content_id, create a new instance if it doesn't exist."""
        if not self.ace_address:
            logger.error("Ace address is not set, cannot get instance URL.")
            return None

        if not check_valid_content_id_or_infohash(content_id):
            logger.error("Invalid AceStream content ID: %s", content_id)
            return None

        if self.ace_instances.get(content_id):
            instance = self.ace_instances[content_id]
            instance.update_last_used()
            return instance.get_m3u8_url()

        new_instance_number = self.get_available_instance_number()
        if new_instance_number is None:
            logger.error("No available AceStream instance number found.")
            return None

        new_instance = AcePoolEntry(
            ace_pid=new_instance_number,
            content_id=content_id,
            ace_address=self.ace_address,
            transcode_audio=self.transcode_audio,
        )

        self.ace_instances[content_id] = new_instance

        return new_instance.get_m3u8_url()

    def get_instance_by_multistream_path(self, ace_multistream_path: str) -> str:
        """Find the AceStream instance content_id for a given multistream path."""
        ace_multistream_path = ace_multistream_path.split("/")[0]
        if not ace_multistream_path:
            logger.warning("No multistream path provided, cannot get AceStream instance.")
            return ""

        for instance in self.ace_instances.values():
            # We could use .path here but this avoids dealing with None
            m3u8_url = instance.get_m3u8_url()

            if m3u8_url and ace_multistream_path in m3u8_url.encoded_string():
                instance.update_last_used()
                return instance.content_id

        return ""

    def get_instance_by_pid(self, pid: int) -> AcePoolEntry | None:
        """Get the AcePoolEntry instance by its process ID."""
        for entry in self.ace_instances.values():
            if entry.ace_pid == pid:
                return entry

        logger.error("No AceStream instance found with pid %s", pid)
        return None

    # region GET API
    def get_instance_by_content_id_api(self, content_id: str) -> AcePoolEntryForAPI | None:
        """Get the AcePoolEntry instance by its content ID."""
        instance = self.ace_instances.get(content_id)
        if instance:
            return self._make_api_response_from_instance(instance)

        logger.error("No AceStream instance found with content ID %s", content_id)
        return None

    def get_instance_by_pid_api(self, ace_pid: int) -> AcePoolEntryForAPI | None:
        """Get the AcePoolEntry instance by its process ID."""
        for entry in self.ace_instances.values():
            if entry.ace_pid == ace_pid:
                return self._make_api_response_from_instance(entry)

        logger.error("No AceStream instance found with pid %s", ace_pid)
        return None

    def get_instances_api(self) -> AcePoolForApi:
        """Get a list of AcePoolEntryForAPI instances for the API."""
        if self.ace_address:
            instances = [self._make_api_response_from_instance(instance) for instance in self.ace_instances.values()]
        else:
            logger.error("get_instances_api called, Ace address is not set, cannot get instances.")
            instances = []

        return AcePoolForApi(
            ace_address=self.ace_address,
            max_size=self.max_size,
            ace_instances=instances,
            healthy=self.healthy,
            ace_version=self.ace_version,
            transcode_audio=self.transcode_audio,
            external_url=settings.EXTERNAL_URL,
        )

    # region GET API Stats
    def get_all_stats(self) -> AcePoolAllStatsApi:
        """Get all AcePool statistics for each instance, for the API only."""
        # I had to use typing.Any, sad day but it's fine since its from pydantic
        result: dict[int, dict[str, Any] | None] = {}
        for n in range(self.max_size):
            ace_pool_stat = self.get_stats_by_pid(n)
            if ace_pool_stat is None:
                result[n] = None
            else:
                result[n] = ace_pool_stat.model_dump()

        ta = TypeAdapter(AcePoolAllStatsApi)

        return ta.validate_python(result)

    def get_stats_by_pid(self, pid: int) -> AcePoolStat | None:
        """Get the AcePool statistics for a specific index."""
        if not self.healthy:
            logger.error("Ace pool is not healthy, cannot get stats.")
            return None

        for entry in self.ace_instances.values():
            if entry.ace_pid == pid:
                ace_stat = entry.get_ace_stat()
                if ace_stat is not None:
                    return ace_stat

        return None

    def get_stats_by_content_id(self, content_id: str) -> AcePoolStat | None:
        """Get the AcePool statistics for a specific content ID."""
        if not self.healthy:
            logger.error("Ace pool is not healthy, cannot get stats.")
            return None

        instance = self.ace_instances.get(content_id)
        if instance:
            ace_stat = instance.get_ace_stat()
            if ace_stat is not None:
                return ace_stat

        logger.error("No AceStream instance found with content ID %s", content_id)
        return None

    # region Helpers
    def _make_api_response_from_instance(self, instance: AcePoolEntry) -> AcePoolEntryForAPI:
        """Create an AcePoolEntryForAPI instance from an AcePoolEntry instance."""
        locked_in = instance.check_locked_in()
        time_until_unlock = timedelta(seconds=0)
        if locked_in:
            time_until_unlock = instance.get_time_until_unlock()

        total_time_running = timedelta(seconds=0)
        if instance.content_id != "":
            total_time_running = datetime.now(tz=OUR_TIMEZONE) - instance.date_started

        return AcePoolEntryForAPI(
            ace_pid=instance.ace_pid,
            content_id=instance.content_id,
            date_started=instance.date_started,
            last_used=instance.last_used,
            locked_in=locked_in,
            time_until_unlock=time_until_unlock,
            time_running=total_time_running,
            ace_hls_m3u8_url=instance.get_m3u8_url(),
        )

    # region Poolboy
    def ace_poolboy(self) -> None:
        """Run the AcePoolboy to clean up instances."""

        def ace_poolboy_thread() -> None:
            """Thread to clean up instances."""
            while True:
                self.check_ace_running()
                time.sleep(10)

                instances_to_remove: list[str] = []

                for instance in self.ace_instances.copy().values():  # copy to avoid runtime error
                    # If the instance is stale, remove it
                    if instance.check_if_stale():
                        instances_to_remove.append(instance.content_id)
                    else:  # Otherwise, try keep it alive
                        instance.keep_alive()

                for content_id in instances_to_remove:  # Separate loop to avoid modifying the dict while iterating
                    self.remove_instance_by_content_id(content_id, caller="ace_poolboy")

        if not self._ace_poolboy_running:
            self._ace_poolboy_running = True
            logger.info("Starting ace_poolboy_thread (%s)", self._instance_id)
        threading.Thread(target=ace_poolboy_thread, name="AcePool: ace_poolboy", daemon=True).start()
