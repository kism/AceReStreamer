from pathlib import Path
from typing import TYPE_CHECKING

from acere.services.scraper.name_processor import ACE_URL_PREFIXES_CONTENT_ID, ACE_URL_PREFIXES_INFOHASH

if TYPE_CHECKING:
    from sphinx.application import Sphinx
else:
    Sphinx = object


def generate_txt_examples(app: Sphinx) -> None:
    """Generate TXT examples for AceStream URLs."""
    content = "\n".join(ACE_URL_PREFIXES_CONTENT_ID + ACE_URL_PREFIXES_INFOHASH)
    output_dir = Path(app.srcdir) / "generated"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "acestream_url_prefixes.txt"
    output_file.write_text(content)
