"""Version Metadata."""

from pathlib import Path

__author__ = "Kieran Gee"
__version__ = "1.0.3"  # This is the version of the app, used in pyproject.toml, enforced in a test.
PROGRAM_NAME = "AceReStreamer"
URL = "https://github.com/kism/ace-restreamer"


def get_version_str() -> str:
    """Get a string representation of the version, including branch and commit hash."""
    git_head_log = Path.cwd() / ".git" / "logs" / "HEAD"
    git_head = Path.cwd() / ".git" / "HEAD"
    last_commit = "unknown"
    current_branch = "unknown"

    # Last commit
    if git_head_log.is_file():
        with git_head_log.open("r") as f:
            lines = f.readlines()
            if lines:  # pragma: no cover # This doesn't get hit in CI
                last_commit = lines[-1].strip().split(" ")[1]  # Get the current commit hash,

    last_commit_short = last_commit[:7] if last_commit != "unknown" else last_commit

    # Current branch, if the branch is not detached
    if git_head.is_file():
        with git_head.open("r") as f:
            current_branch = f.read().strip().split("/")[-1]

    if last_commit == current_branch:  # We don't have a branch name
        return f"{__version__}-{last_commit_short}"

    return f"{__version__}-{current_branch}/{last_commit_short}"


VERSION_FULL = get_version_str()
