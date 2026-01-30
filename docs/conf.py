import sys
from pathlib import Path

# -- Project information -----------------------------------------------------

project = "AceReStreamer"
copyright = "2026, Kieran Gee"
author = "Kieran Gee"


# -- General configuration ---------------------------------------------------


# Add the docs/_ext directory to the path so Sphinx can find our custom extension
sys.path.insert(0, str(Path(__file__).parent / "_ext"))

# Add the project root to the path so we can import acere modules
sys.path.insert(0, str(Path(__file__).parent.parent))

extensions = [
    "myst_parser",
    "generate_json_examples",
    "generate_txt_examples",
]


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "_ext"]
html_theme = "sphinx_rtd_theme"
