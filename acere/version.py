"""Version Metadata."""

from pathlib import Path

__author__ = "Kieran Gee"
__version__ = "1.0.0b2"  # This is the version of the app, used in pyproject.toml, enforced in a test.
PROGRAM_NAME = "AceReStreamer"
URL = "https://github.com/kism/ace-restreamer"


def get_version_str() -> str:
    """Get a string representation of the version, including branch and commit hash."""
    git_head_log = Path.cwd() / ".git" / "logs" / "HEAD"
    git_head = Path.cwd() / ".git" / "HEAD"
    last_commit = ""
    current_branch = ""

    if git_head_log.is_file():
        with git_head_log.open("r") as f:
            lines = f.readlines()
            if lines:  # pragma: no cover # This doesn't get hit in CI
                last_commit = lines[-1].strip().split(" ")[0][:7]  # Get the last commit hash, first 7 characters

    if git_head.is_file():
        with git_head.open("r") as f:
            current_branch = f.read().strip().split("/")[-1]

    return (
        f"{__version__}"
        f"{('-' + current_branch) if current_branch else ''}"
        f"{('/' + last_commit + '') if last_commit else ''}"
    )


VERSION_FULL = get_version_str()
