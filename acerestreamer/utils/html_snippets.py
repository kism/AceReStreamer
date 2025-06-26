"""Rendering or getting HTML snippets."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from acerestreamer.utils.flask_helpers import TEMPLATES_DIRECTORY
from acerestreamer.utils.logger import get_logger

SNIPPETS_DIRECTORY = TEMPLATES_DIRECTORY / "snippets"

logger = get_logger(__name__)  # Create a logger: acerestreamer.html_snippets, inherit config from root logger


def get_header_snippet(page_title: str) -> str:
    """Get the HTML header snippet with the given page title."""
    from acerestreamer import __version__  # noqa: PLC0415,RUF100 # Avoid circular import by importing here

    git_head_log = Path.cwd() / ".git" / "logs" / "HEAD"
    git_head = Path.cwd() / ".git" / "HEAD"
    last_commit = ""
    current_branch = ""

    if git_head_log.is_file():
        with git_head_log.open("r") as f:
            last_commit = f.readlines()[-1].strip().split(" ")[0][:7]  # Get the last commit hash, first 7 characters

    if git_head.is_file():
        with git_head.open("r") as f:
            current_branch = f.read().strip().split("/")[-1]

    version_info = (
        f"Version: {__version__}"
        f"{(', ' + current_branch + ' ') if current_branch else ''}"
        f"{(' (' + last_commit + ')') if last_commit else ''}"
    )

    env = Environment(loader=FileSystemLoader(SNIPPETS_DIRECTORY), autoescape=True)
    template = env.get_template("header.html.j2")
    return template.render(page_title=page_title, version_info=version_info)
