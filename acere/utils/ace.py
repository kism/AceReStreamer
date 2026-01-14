from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import HttpUrl
else:
    HttpUrl = object


def get_middleware_url(ace_url: HttpUrl, content_id: str, ace_pid: int, *, transcode_audio: bool) -> str:
    """Get the middleware URL from the AceStream URL."""
    # https://docs.acestream.net/developers/start-playback/
    return (
        f"{ace_url}ace/manifest.m3u8"
        "?format=json"
        f"&content_id={content_id}"
        f"&transcode_ac3={str(transcode_audio).lower()}"
        f"&pid={ace_pid}"
    )


def ace_id_short(content_id: str) -> str:
    """Get a short version of the AceStream content ID for logging."""
    return f"{content_id[:8]}..."
