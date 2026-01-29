from typing import TYPE_CHECKING

from pydantic import (
    BaseModel,
    ConfigDict,
    HttpUrl,
    field_validator,
)

from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object
logger = get_logger(__name__)


class AppConf(BaseModel):
    """Application configuration definition."""

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    ace_address: HttpUrl = HttpUrl("http://localhost:6878")
    transcode_audio: bool = True
    ace_max_streams: int = 4

    @field_validator("ace_max_streams", mode="after")
    @classmethod
    def validate_max_streams(cls, value: int) -> int:
        """Validate the max streams."""
        n_min_streams = 1
        n_default_streams = 4
        n_high_streams = 10
        n_very_high_streams = 20

        if value < n_min_streams:
            msg = (
                f"ace_max_streams '{value}' must be at least {n_min_streams}, setting to default of {n_default_streams}"
            )
            logger.warning(msg)
            value = n_default_streams

        if value > n_high_streams and value <= n_very_high_streams:
            logger.warning(
                "You have set ace_max_streams to a high value (%d), this may cause performance issues.",
                value,
            )
        elif value > n_very_high_streams:
            logger.warning(
                "You have set ace_max_streams to a VERY high value (%d), this will likely cause performance issues.",
                value,
            )

        return value
