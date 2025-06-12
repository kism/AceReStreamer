"""Rendering or getting HTML snippets."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates" / "snippets"


def get_header_snippet(page_title: str) -> str:
    """Get the HTML header snippet with the given page title."""
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True)
    template = env.get_template("header.html.j2")
    return template.render(page_title=page_title)
