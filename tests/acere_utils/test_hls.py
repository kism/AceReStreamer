from pydantic import HttpUrl

from acere.utils.hls import replace_hls_m3u_sources

_LOCAL_ACE_ADDRESS: HttpUrl = HttpUrl("http://localhost:6878/")
_EXTERNAL_ADDRESS: HttpUrl = HttpUrl("http://ace.pytest.internal/")

_SAMPLE_INPUT_M3U = f"""#EXTM3U
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:7
#EXT-X-MEDIA-SEQUENCE:9
#EXTINF:5.238567,
{_LOCAL_ACE_ADDRESS}ace/c/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/1.ts
"""


def test_replace_hls_m3u_sources() -> None:
    output_m3u = replace_hls_m3u_sources(
        m3u_content=_SAMPLE_INPUT_M3U,
        ace_address=_LOCAL_ACE_ADDRESS,
        server_name=_EXTERNAL_ADDRESS,
        token="",
    )

    assert _LOCAL_ACE_ADDRESS.encoded_string() not in output_m3u
    assert _EXTERNAL_ADDRESS.encoded_string() in output_m3u

    output_m3u_with_token = replace_hls_m3u_sources(
        m3u_content=_SAMPLE_INPUT_M3U,
        ace_address=_LOCAL_ACE_ADDRESS,
        server_name=_EXTERNAL_ADDRESS,
        token="sometoken",
    )

    assert _LOCAL_ACE_ADDRESS.encoded_string() not in output_m3u_with_token
    assert _EXTERNAL_ADDRESS.encoded_string() in output_m3u
    assert "?token=sometoken" in output_m3u_with_token
