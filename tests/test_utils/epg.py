from datetime import UTC, datetime, timedelta

from lxml import etree

from acere.utils.helpers import slugify


def generate_future_program_xml(
    channels: int = 2,
    programs: int = 6,
    *,
    good_description: bool = True,
    with_icon: bool = True,
    programs_in_past: int = 0,
) -> etree._Element:
    # Calculate start time:
    # - If programs_in_past > 0, start from (now - programs_in_past hours) so those programs are in the past
    # - Otherwise, start from (now + 2 hours) to have programs in the future by default
    now = datetime.now(tz=UTC)
    start_time_offset = now - timedelta(hours=programs_in_past) if programs_in_past > 0 else now + timedelta(hours=2)

    xml_root = etree.Element("tv")
    for ch in range(1, channels + 1):
        channel_name = f"Channel {ch}"
        channel_tvg_id = f"channel{ch}"
        channel_name_slug = slugify(channel_name)

        channel_elem = etree.SubElement(xml_root, "channel", id=channel_tvg_id)
        display_name = etree.SubElement(channel_elem, "display-name")
        display_name.text = f"Channel {ch}"

        # Generate programs_in_past programs in the past and programs in the future
        total_programs = programs_in_past + programs
        for pr in range(total_programs):
            program_start = start_time_offset + timedelta(hours=pr)
            program_end = start_time_offset + timedelta(hours=pr + 1)
            # Convert to UTC for the XML format
            start_time = program_start.astimezone(tz=UTC).strftime("%Y%m%d%H%M%S +0000")
            end_time = program_end.astimezone(tz=UTC).strftime("%Y%m%d%H%M%S +0000")
            programme_elem = etree.SubElement(
                xml_root,
                "programme",
                start=start_time,
                stop=end_time,
                channel=channel_tvg_id,
            )
            title = etree.SubElement(programme_elem, "title")
            title.text = f"Program {pr + 1} on Channel {ch}"

            desc = etree.SubElement(programme_elem, "desc")
            if good_description:
                desc.text = "This is a good description."
            else:
                desc.text = "Short"

            if with_icon:
                etree.SubElement(programme_elem, "icon", src=f"http://pytest.internal/{channel_name_slug}.png")

    return xml_root
