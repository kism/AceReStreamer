# -- Project information -----------------------------------------------------

project = "AceReStreamer"
copyright = "2026, Kieran Gee"
author = "Kieran Gee"


# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
]


# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "sphinx_rtd_theme"
