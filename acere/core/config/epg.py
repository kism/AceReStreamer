import urllib
import urllib.parse
from typing import TYPE_CHECKING, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    HttpUrl,
    computed_field,
)

from acere.utils.helpers import slugify
from acere.utils.logger import get_logger

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object
logger = get_logger(__name__)


class EPGInstanceConf(BaseModel):
    """EPG (Electronic Program Guide) configuration definition.

    tvg_id_overrides is a str:str dict where you can override stream tvg_ids to match those in the EPG.
    """

    model_config = ConfigDict(extra="ignore")  # Ignore extras for config related things

    format: Literal["xml.gz", "xml"] = "xml.gz"
    url: HttpUrl
    tvg_id_overrides: dict[
        str, str
    ] = {}  # The program normanises the tvg_ids pretty well, but sometimes you need to override specific ones.

    @computed_field
    @property
    def slug(self) -> str:
        """Generate a slug from the url."""
        return slugify(urllib.parse.unquote(self.url.encoded_string()))
