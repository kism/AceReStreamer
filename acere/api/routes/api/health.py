"""Health API Blueprint."""

import threading

from fastapi import APIRouter
from psutil import Process

from acere.constants import OUR_TIMEZONE
from acere.utils.health import HealthResponseModel, ThreadHealthModel
from acere.utils.logger import get_logger
from acere.version import VERSION_FULL, __version__

logger = get_logger(__name__)

# No auth for health?
router = APIRouter(prefix="/health", tags=["Health"])

PROCESS = Process()


@router.get("/")
def health() -> HealthResponseModel:
    """API endpoint to check the health of the service."""
    threads_enumerated = threading.enumerate()
    thread_list = [ThreadHealthModel(name=thread.name, is_alive=thread.is_alive()) for thread in threads_enumerated]
    memory = str(PROCESS.memory_info().rss / (1024 * 1024))

    return HealthResponseModel(
        version=__version__,
        version_full=VERSION_FULL,
        time_zone=str(OUR_TIMEZONE.tzname(None)),
        threads=thread_list,
        memory_usage_mb=memory,
    )
