"""AceStream pool management module."""

import contextlib
import threading
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

import requests

from acerestreamer.utils import check_valid_ace_content_id_or_infohash
from acerestreamer.utils.constants import OUR_TIMEZONE
from acerestreamer.utils.logger import get_logger

from .constants import ACESTREAM_API_TIMEOUT
from .entry import AcePoolEntry
from .models import AcePoolEntryForAPI, AcePoolForApi, AcePoolStat

logger = get_logger(__name__)

if TYPE_CHECKING:
    from acerestreamer.config.models import AppConf
else:
    AppConf = object


class AcePool:
    """A pool of AceStream instances to distribute requests across."""

    def __init__(self) -> None:
        """Initialize the AcePool."""
        self.ace_address = ""
        self.max_size = 0
        self.transcode_audio = False
        self.ace_instances: dict[str, AcePoolEntry] = {}
        self.healthy = False
        self.ace_version = "unknown"
        self._ace_poolboy_running = False

    def load_config(self, app_config: AppConf) -> None:
        """Load the configuration for the AcePool."""
        self.ace_address = app_config.ace_address
        self.max_size = app_config.ace_max_streams
        self.transcode_audio = app_config.transcode_audio
        self.ace_poolboy()

    def check_ace_running(self) -> bool:
        """Use the AceStream API to check if the instance is running."""
        healthy = False
        if not self.ace_address:
            return healthy

        url = f"{self.ace_address}/webui/api/service?method=get_version"
        version_data = {}

        try:
            response = requests.get(url, timeout=ACESTREAM_API_TIMEOUT)
            response.raise_for_status()
            version_data = response.json()
            healthy = True
        except requests.RequestException as e:
            error_short = type(e).__name__
            logger.error("Ace Instance %s is not healthy: %s", self.ace_address, error_short)  # noqa: TRY400 Short error for requests
            healthy = False
        except Exception as e:  # noqa: BLE001 Last resort
            error_short = type(e).__name__
            logger.error("Ace Instance %s is not healthy for a weird reason: %s", self.ace_address, e)  # noqa: TRY400 Short error for requests
            healthy = False

        self.ace_version = version_data.get("result", {}).get("version", "unknown")
        self.healthy = healthy

        return self.healthy

    def remove_instance_by_ace_content_id(self, ace_content_id: str, caller: str = "") -> bool:
        """Remove an AceStream instance from the pool by ace_content_id."""
        if caller != "":
            caller = f"{caller}: "
        if ace_content_id in self.ace_instances:
            logger.info("%sRemoving AceStream instance with ace_content_id %s", caller, ace_content_id)
            with contextlib.suppress(KeyError):
                self.ace_instances[ace_content_id].stop()
                del self.ace_instances[ace_content_id]
            return True

        return False

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

            logger.info("Found available AceStream instance: %s, reclaiming it.", best_instance.ace_pid)
            ace_pid = best_instance.ace_pid
            self.remove_instance_by_ace_content_id(best_instance.ace_content_id, caller="get_available_instance_number")
            return ace_pid

        logger.error("Ace pool is full, could not get available instance.")
        return None

    def get_instance_by_content_id(self, ace_content_id: str) -> str | None:
        """Find the AceStream instance URL for a given ace_content_id."""
        if not check_valid_ace_content_id_or_infohash(ace_content_id):
            logger.error("Invalid AceStream content ID: %s", ace_content_id)
            return None

        if self.ace_instances.get(ace_content_id):
            instance = self.ace_instances[ace_content_id]
            instance.update_last_used()
            return instance.ace_hls_m3u8_url

        new_instance_number = self.get_available_instance_number()
        if new_instance_number is None:
            logger.error("No available AceStream instance number found.")
            return None

        new_instance = AcePoolEntry(
            ace_pid=new_instance_number,
            ace_content_id=ace_content_id,
            ace_address=self.ace_address,
            transcode_audio=self.transcode_audio,
        )

        self.ace_instances[ace_content_id] = new_instance

        return new_instance.ace_hls_m3u8_url

    def get_instance_by_infohash(self, ace_infohash: str) -> str | None:
        """Find the AceStream instance URL for a given infohash."""
        if not ace_infohash:
            logger.error("No infohash provided, cannot get AceStream instance.")
            return None

        for instance in self.ace_instances.values():
            if instance.ace_infohash == ace_infohash:
                instance.update_last_used()
                return instance.ace_hls_m3u8_url

        return None

    def get_instance_by_multistream_path(self, ace_multistream_path: str) -> str:
        """Find the AceStream instance URL for a given multistream path."""
        ace_multistream_path = ace_multistream_path.split("/")[0]
        if not ace_multistream_path:
            logger.warning("No multistream path provided, cannot get AceStream instance.")
            return ""

        for instance in self.ace_instances.values():
            if ace_multistream_path in instance.ace_hls_m3u8_url:
                instance.update_last_used()
                return instance.ace_content_id

        return ""

    def get_instances_nice(self) -> AcePoolForApi:
        """Get a list of AcePoolEntryForAPI instances for the API."""
        instances = []

        for instance in self.ace_instances.values():
            locked_in = instance.check_locked_in()
            time_until_unlock = timedelta(seconds=0)
            if locked_in:
                time_until_unlock = instance.get_time_until_unlock()

            total_time_running = timedelta(seconds=0)
            if instance.ace_content_id != "":
                total_time_running = datetime.now(tz=OUR_TIMEZONE) - instance.date_started

            instances.append(
                AcePoolEntryForAPI(
                    ace_pid=instance.ace_pid,
                    ace_content_id=instance.ace_content_id,
                    date_started=instance.date_started,
                    last_used=instance.last_used,
                    locked_in=locked_in,
                    time_until_unlock=time_until_unlock,
                    time_running=total_time_running,
                    ace_hls_m3u8_url=instance.ace_hls_m3u8_url,
                )
            )

        return AcePoolForApi(
            ace_address=self.ace_address,
            max_size=self.max_size,
            ace_instances=instances,
            healthy=self.healthy,
            ace_version=self.ace_version,
            transcode_audio=self.transcode_audio,
        )

    def get_instance_by_pid(self, pid: int) -> AcePoolEntry | None:
        """Get the AcePoolEntry instance by its process ID."""
        for entry in self.ace_instances.values():
            if entry.ace_pid == pid:
                return entry

        logger.error("No AceStream instance found with pid %s", pid)
        return None

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

    def get_all_stats(self) -> dict[int, dict[str, Any] | None]:
        """Get all AcePool statistics for each instance, for the API only."""
        # I had to use typing.Any, sad day but it's fine since its from pydantic
        result: dict[int, dict[str, Any] | None] = {}
        n = 1
        for _ in range(self.max_size):
            ace_pool_stat = self.get_stats_by_pid(n)
            if ace_pool_stat is None:
                result[n] = None
            else:
                result[n] = ace_pool_stat.model_dump()

            n += 1

        return result

    def ace_poolboy(self) -> None:
        """Run the AcePoolboy to clean up instances."""

        def ace_poolboy_thread() -> None:
            """Thread to clean up instances."""
            while True:
                self.check_ace_running()
                time.sleep(10)

                instances_to_remove: list[str] = []

                for instance in self.ace_instances.values():
                    # If the instance is stale, remove it
                    if instance.check_if_stale():
                        instances_to_remove.append(instance.ace_content_id)
                    else:  # Otherwise, try keep it alive
                        instance.keep_alive()

                for ace_content_id in instances_to_remove:  # Separate loop to avoid modifying the dict while iterating
                    self.remove_instance_by_ace_content_id(ace_content_id, caller="ace_poolboy")

        if not self._ace_poolboy_running:
            self._ace_poolboy_running = True
            logger.info("Starting ace_poolboy_thread")
        threading.Thread(target=ace_poolboy_thread, name="AcePool: ace_poolboy", daemon=True).start()
