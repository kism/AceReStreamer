"""Misc file generation for file mode."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
else:
    Path = object

GIT_ATTRIBUTES = """*.woff2 filter=lfs diff=lfs merge=lfs -text
*.ico filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.webp filter=lfs diff=lfs merge=lfs -text
"""

GIT_IGNORE = """core
*.log
scraper_cache
.DS_Store
__pycache__
config_backups
"""


def generate_misc(instance_path: Path) -> None:
    """Generate misc files for the repo."""
    (instance_path / ".gitattributes").write_text(GIT_ATTRIBUTES, encoding="utf-8")
    (instance_path / ".gitignore").write_text(GIT_IGNORE, encoding="utf-8")
