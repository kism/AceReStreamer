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
    output_dir.mkdir(exist_ok=True, parents=True)
    output_file = output_dir / "acestream_url_prefixes.txt"
    output_file.write_text(content + "\n", encoding="utf-8")


def setup(app: Sphinx) -> dict[str, object]:
    """Set up the Sphinx extension."""
    app.connect("builder-inited", generate_txt_examples)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
