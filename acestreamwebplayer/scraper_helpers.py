"""Helper functions and functions for searching in beautiful soup tags."""

import re

from bs4 import Tag


def check_candidate(target_html_class: str, html_tag: Tag | None) -> list[str]:
    """Check if the tag has the target class."""
    if not html_tag or not isinstance(html_tag, Tag):
        return []
    html_classes = html_tag.get("class", [""])
    # if not html_classes:
    #     return []

    candidate_titles: list[str] = []
    for html_class in html_classes:
        if html_class == target_html_class:
            candidate_title = cleanup_candidate_title(html_tag.get_text())
            candidate_titles.append(candidate_title)

    return candidate_titles


def search_for_candidate(
    candidate_titles: list[str], target_html_class: str = "", html_tag: Tag | None = None
) -> list[str]:
    """Search the parent of the given tag for a title."""
    if not html_tag or not isinstance(html_tag, Tag):
        return candidate_titles

    html_classes = html_tag.get("class", None)
    if not html_classes:
        return candidate_titles

    # Search children could go here with html_tag.child but I think it will do nothing

    # Search Parents
    more = search_for_candidate(
        candidate_titles=candidate_titles,
        target_html_class=target_html_class,
        html_tag=html_tag.parent,
    )
    candidate_titles.extend(more)

    # Search Self
    candidates = check_candidate(target_html_class, html_tag)
    candidate_titles.extend(candidates)

    return candidate_titles


def search_sibling_for_candidate(
    candidate_titles: list[str], target_html_class: str = "", html_tag: Tag | None = None
) -> list[str]:
    """Search the previous sibling of the given tag for a title."""
    if not html_tag or not isinstance(html_tag, Tag):
        return candidate_titles

    # Recurse through the parent tags
    more = search_sibling_for_candidate(
        candidate_titles=candidate_titles.copy(),
        target_html_class=target_html_class,
        html_tag=html_tag.parent,
    )
    candidate_titles.extend(more)

    # Find and search previous sibling
    previous_sibling = html_tag.find_previous_sibling()
    if previous_sibling and isinstance(previous_sibling, Tag):
        more = check_candidate(target_html_class, previous_sibling)
        candidate_titles.extend(more)

    return candidate_titles


def cleanup_candidate_title(title: str) -> str:
    """Cleanup the candidate title."""
    title = title.strip()
    title = title.split("acestream://")[-1].strip()
    title = title.split("\n")[0].strip()  # Remove any newlines
    # Remove any ace 40 digit hex ids from the title
    return re.sub(r"\b[0-9a-fA-F]{40}\b", "", title).strip()
