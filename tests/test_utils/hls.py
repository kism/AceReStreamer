def generate_hls_m3u8(n_segments: int) -> str:
    """Generate a simple HLS M3U8 playlist for testing."""
    content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0"""
    for i in range(n_segments):
        content += f"""
#EXTINF:10.0,
http://localhost:5100/ace/c/segment{i}.ts"""
    return content
