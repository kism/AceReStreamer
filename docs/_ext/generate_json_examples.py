"""Sphinx extension to generate JSON examples from Pydantic models."""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import HttpUrl

from acere.core.config.scraper import HTMLScraperFilter, ScrapeSiteAPI, ScrapeSiteHTML, ScrapeSiteIPTV, TitleFilter
from acere.services.scraper.api import APISiteResponseItem

if TYPE_CHECKING:
    from sphinx.application import Sphinx
else:
    Sphinx = object


def generate_json_examples(app: Sphinx) -> None:
    """Generate JSON examples from Pydantic models."""
    # Import here to avoid issues with module loading

    output_dir = Path(app.srcdir) / "generated"
    output_dir.mkdir(exist_ok=True)

    # Generate IPTV example
    iptv_example = ScrapeSiteIPTV(
        type="iptv",
        name="english-iptv",
        url=HttpUrl("https://example.com/playlist.m3u8"),
        title_filter=TitleFilter(
            always_exclude_words=[],
            always_include_words=[],
            exclude_words=[],
            include_words=["[AU]", "[IE]", "[UK]", "[US]", "[EN]", "[CA]"],
            regex_postprocessing=[],
        ),
    )

    iptv_example_titlefilter = ScrapeSiteIPTV(
        type="iptv",
        name="english-iptv",
        url=HttpUrl("https://example.com/playlist.m3u8"),
        title_filter=TitleFilter(
            always_exclude_words=["Adult"],
            always_include_words=[],
            exclude_words=[],
            include_words=["[AU]", "[IE]", "[UK]", "[US]", "[EN]", "[CA]"],
            regex_postprocessing=[],
        ),
    )

    # Generate HTML example
    html_example = ScrapeSiteHTML(
        type="html",
        name="example-site",
        url=HttpUrl("https://example.com/acestreams"),
        title_filter=TitleFilter(
            always_exclude_words=[],
            always_include_words=[],
            exclude_words=[],
            include_words=["[AU]", "[IE]", "[UK]", "[US]", "[EN]", "[CA]"],
            regex_postprocessing=["Mirror \\d+: "],
        ),
        html_filter=HTMLScraperFilter(target_class="stream-title", check_sibling=True),
    )

    example_api_site_response = [
        APISiteResponseItem(
            infohash="1000000000000000000000000000000000000001",
            name="Channel 1 [AU]",
            availability=1,
            availability_updated_at=1769756822,
            categories=["general"],
        ),
        APISiteResponseItem(
            infohash="1000000000000000000000000000000000000002",
            name="Channel 5 [AU]",
            availability=1,
            availability_updated_at=1769756822,
            categories=["general"],
        ),
    ]

    # Generate API example
    api_example = ScrapeSiteAPI(
        type="api",
        name="my-cool-api-site",
        url=HttpUrl("https://api.example.com/all_ace_streams"),
        title_filter=TitleFilter(
            always_exclude_words=[],
            always_include_words=[],
            exclude_words=[],
            include_words=["[AU]", "[IE]", "[UK]", "[US]", "[EN]", "[CA]"],
            regex_postprocessing=[],
        ),
    )

    # Write examples to files
    examples: dict[str, ScrapeSiteIPTV | ScrapeSiteHTML | ScrapeSiteAPI] = {
        "iptv_example.json": iptv_example,
        "iptv_example_titlefilter.json": iptv_example_titlefilter,
        "html_example.json": html_example,
        "api_example.json": api_example,
    }

    examples_list: dict[str, list[APISiteResponseItem]] = {
        "api_site_response_example.json": example_api_site_response,
    }

    for filename, example in examples.items():
        output_file = output_dir / filename
        with output_file.open("w") as f:
            json.dump(example.model_dump(mode="json"), f, indent=2)

    for filename, example_list in examples_list.items():
        output_file = output_dir / filename
        data_to_dump = [item.model_dump(mode="json") for item in example_list]

        with output_file.open("w") as f:
            json.dump(data_to_dump, f, indent=2)

    app.config.html_context["json_examples_generated"] = True


def setup(app: Sphinx) -> dict[str, object]:
    """Set up the Sphinx extension."""
    app.connect("builder-inited", generate_json_examples)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
