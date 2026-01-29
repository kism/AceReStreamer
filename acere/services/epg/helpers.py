import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lxml import etree
else:
    etree = object


# XX | Channel Name
TVG_ID_PRECEEDING_COUNTRY_CODE_REGEX = re.compile(r"^([a-z]{2})\s*\|\s*(.+)$", re.IGNORECASE)
# Channel Name.xx
TVG_ID_COUNTRY_CODE_REGEX = re.compile(r"^(.*)[._-]([a-z]{2})$", re.IGNORECASE)
# Channel Name.xxn
TVG_ID_COUNTRY_CODE_W_NUMBER_REGEX = re.compile(r"^(.*)[._-]([a-z]{2}\d+)$", re.IGNORECASE)

# Remove Trailing Numbers
REMOVE_TRAILING_NUMBERS_REGEX = re.compile(r"(.*?)(\s*\d+)$")


def normalise_epg_tvg_id(tvg_id: str | None, overrides: dict[str, str] | None = None) -> str | None:
    if not tvg_id:
        return None

    if overrides and tvg_id in overrides:
        return overrides[tvg_id]

    if TVG_ID_COUNTRY_CODE_W_NUMBER_REGEX.match(tvg_id):
        tvg_id = REMOVE_TRAILING_NUMBERS_REGEX.sub(r"\1", tvg_id)

    if match := TVG_ID_PRECEEDING_COUNTRY_CODE_REGEX.match(tvg_id):
        country_code = match.group(1)
        channel_name = match.group(2)
    elif match := TVG_ID_COUNTRY_CODE_REGEX.match(tvg_id):
        channel_name = match.group(1)
        country_code = match.group(2)
    else:
        return tvg_id

    # Cleanup
    channel_name = channel_name.replace(".", " ")
    channel_name = channel_name.replace("_", " ")
    channel_name = channel_name.replace("&amp;", "&")
    channel_name = channel_name.strip()

    country_code = country_code.lower()
    country_code = country_code.strip()

    return f"{channel_name}.{country_code}"


def find_current_program_xml(tvg_id: str, epg_data: etree._Element) -> tuple[str, str]:
    """Find the current program title and description for a given TVG ID in the EPG data."""
    # Find the channel with the given TVG ID
    channel = None
    for ch in epg_data.findall("channel"):
        ch_get_result = ch.get("id")
        if not ch_get_result:
            continue

        if ch_get_result.lower() == tvg_id.lower():
            channel = ch
            break

    if channel is None:
        return "", ""

    # Find the current programme for this channel
    now = datetime.now(tz=UTC)
    programmes = epg_data.findall(f"programme[@channel='{tvg_id}']")
    for programme in programmes:
        start_time = programme.get("start")
        end_time = programme.get("stop")
        if start_time is None or end_time is None:
            continue

        start_date_time = datetime.strptime(start_time, "%Y%m%d%H%M%S %z")
        end_date_time = datetime.strptime(end_time, "%Y%m%d%H%M%S %z")

        if start_date_time <= now <= end_date_time:
            title_match = programme.find("title")
            program_title = ""
            if title_match is not None:
                program_title = title_match.text or program_title

            description_match = programme.find("desc")
            program_description = ""
            if description_match is not None:
                program_description = description_match.text or program_description

            return program_title, program_description

    return "", ""
