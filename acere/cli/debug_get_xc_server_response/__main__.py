"""CLI to fetch all standard XC (Xtream Codes) API endpoints and save responses to disk."""

import argparse
import asyncio
from pathlib import Path

import aiohttp
import anyio

from acere.constants import DEFAULT_INSTANCE_PATH
from acere.utils.cli import console
from acere.utils.helpers import slugify

XC_ACTIONS = [
    "get_live_categories",
    "get_live_streams",
    "get_vod_categories",
    "get_vod_streams",
    "get_series_categories",
    "get_series",
]

_CHUNK_SIZE = 65536


async def _stream_to_file(response: aiohttp.ClientResponse, out_file: Path) -> None:
    async with await anyio.Path(out_file).open("wb") as f:
        async for chunk in response.content.iter_chunked(_CHUNK_SIZE):
            await f.write(chunk)


async def fetch_all_endpoints(base_url: str, username: str, password: str, output_dir: Path) -> None:
    """Fetch all standard XC endpoints, streaming each response directly to disk."""
    base = base_url.rstrip("/")
    player_api_url = base + "/player_api.php"
    get_url = base + "/get.php"
    auth_params = {"username": username, "password": password}

    async with aiohttp.ClientSession() as session:
        # player_api.php — base info and action endpoints
        for label, filename, params in [
            ("base info", "player_api.json", auth_params),
            *[(a, f"{slugify(a)}.json", {**auth_params, "action": a}) for a in XC_ACTIONS],
        ]:
            console.print(f"Fetching {label}...")
            out_file = output_dir / filename
            try:
                async with session.get(player_api_url, params=params) as response:
                    response.raise_for_status()
                    await _stream_to_file(response, out_file)
                console.print(f"  [green]Saved[/green] {out_file}")
            except Exception as e:  # noqa: BLE001
                console.print(f"  [red]Failed: {e}[/red]")

        # get.php — m3u_plus
        console.print("Fetching get.php?type=m3u_plus...")
        out_file = output_dir / "get-m3u-plus.m3u"
        try:
            async with session.get(get_url, params={**auth_params, "type": "m3u_plus", "output": "m3u8"}) as response:
                response.raise_for_status()
                await _stream_to_file(response, out_file)
            console.print(f"  [green]Saved[/green] {out_file}")
        except Exception as e:  # noqa: BLE001
            console.print(f"  [red]Failed: {e}[/red]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch all standard XC API endpoints and save responses to disk.")
    parser.add_argument("url", type=str, help="Base URL of the XC server (e.g. http://myserver.com:8080)")
    parser.add_argument("username", type=str, help="XC server username")
    parser.add_argument("password", type=str, help="XC server password")
    parser.add_argument(
        "--instance-dir",
        type=Path,
        default=DEFAULT_INSTANCE_PATH,
        help="Instance directory root (default: %(default)s)",
    )
    args = parser.parse_args()

    server_slug = slugify(args.url)
    output_dir: Path = args.instance_dir / "cli_xc_response" / server_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"Server: [cyan]{args.url}[/cyan]")
    console.print(f"Output: [cyan]{output_dir}[/cyan]\n")

    asyncio.run(fetch_all_endpoints(args.url, args.username, args.password, output_dir))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt, EOFError:
        console.print("\nExiting...")
