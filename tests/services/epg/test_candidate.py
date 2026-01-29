from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from pydantic import HttpUrl

from acere.services.epg.candidate import EPGCandidate, EPGCandidateHandler
from tests.test_utils.epg import generate_future_program_xml

if TYPE_CHECKING:
    from lxml import etree
else:
    etree = object


def get_epg_url() -> HttpUrl:
    """Generate a unique EPG URL for testing."""
    return HttpUrl(f"http://pytest.internal/epg-{uuid4()}")


@pytest.fixture
def epg_url() -> HttpUrl:
    """Fixture for a sample EPG URL."""
    return get_epg_url()


@pytest.fixture
def xml_good_quality() -> etree._Element:
    """Load test.xml as an etree."""
    return generate_future_program_xml(
        channels=2,
        programs=6,
        good_description=True,
        with_icon=True,
    )


@pytest.fixture
def xml_poor_quality() -> etree._Element:
    """Load test2.xml as an etree."""
    return generate_future_program_xml(
        channels=2,
        programs=6,
        good_description=False,
        with_icon=False,
    )


@pytest.fixture
def xml_past_programs_only() -> etree._Element:
    """Generate XML with only past programs."""
    wip_xml = generate_future_program_xml(
        channels=2,
        programs=0,
        good_description=True,
        with_icon=True,
        programs_in_past=6,
    )

    time_now = datetime.now(tz=UTC)
    for programme in wip_xml.findall("programme"):
        start_str = programme.get("start")
        assert start_str is not None
        start_time = datetime.strptime(start_str, "%Y%m%d%H%M%S %z").astimezone(UTC)
        assert start_time < time_now  # Programs should be in the past

    return wip_xml


# region EPGCandidateHandler
def test_epg_candidate_handler_initialization() -> None:
    """Test EPGCandidateHandler initialization."""
    handler = EPGCandidateHandler()
    assert handler.get_number_of_candidates() == 0


def test_epg_candidate_handler_add(
    xml_good_quality: etree._Element,
    epg_url: HttpUrl,
) -> None:
    """Test adding a program to the handler."""
    handler = EPGCandidateHandler()
    program = xml_good_quality.findall("programme")[0]
    tvg_id = program.get("channel")
    assert tvg_id is not None

    handler.add_program(tvg_id, epg_url, program)
    assert handler.get_number_of_candidates() == 1

    channel = xml_good_quality.findall("channel")[0]
    tvg_id = channel.get("id")
    assert tvg_id is not None

    handler.add_channel(tvg_id, epg_url, channel)
    assert handler.get_number_of_candidates() == 1


def test_epg_candidate_handler_multiple_candidates(
    xml_good_quality: etree._Element,
    xml_poor_quality: etree._Element,
) -> None:
    """Test adding multiple candidates from different EPGs."""
    handler = EPGCandidateHandler()
    epg_url_1 = get_epg_url()
    epg_url_2 = get_epg_url()

    # Add programs from test.xml
    for program in xml_good_quality.findall("programme"):
        tvg_id = program.get("channel")
        assert tvg_id is not None
        handler.add_program(tvg_id, epg_url_1, program)

    # Add channels from test.xml
    for channel in xml_good_quality.findall("channel"):
        tvg_id = channel.get("id")
        assert tvg_id is not None
        handler.add_channel(tvg_id, epg_url_1, channel)

    # Add programs from test2.xml (same tvg_ids, different URL)
    for program in xml_poor_quality.findall("programme"):
        tvg_id = program.get("channel")
        assert tvg_id is not None
        handler.add_program(tvg_id, epg_url_2, program)

    # Should have 4 candidates: 2 tvg_ids * 2 EPG URLs
    assert handler.get_number_of_candidates() == 4


def test_epg_candidate_handler_get_best_candidate_single(
    xml_good_quality: etree._Element,
    epg_url: HttpUrl,
) -> None:
    """Test getting the best candidate when there's only one option."""
    handler = EPGCandidateHandler()
    tvg_id = "channel1"

    # Add all programs and channels for channel1.au
    for program in xml_good_quality.findall("programme"):
        if program.get("channel") == tvg_id:
            handler.add_program(tvg_id, epg_url, program)

    for channel in xml_good_quality.findall("channel"):
        if channel.get("id") == tvg_id:
            handler.add_channel(tvg_id, epg_url, channel)
    best_candidate = handler.get_best_candidate(tvg_id)
    assert best_candidate is not None
    assert best_candidate.tvg_id == tvg_id
    assert best_candidate.epg_url == epg_url


def test_epg_candidate_handler_get_best_candidate_none() -> None:
    """Test getting the best candidate when no candidate exists."""
    handler = EPGCandidateHandler()
    best_candidate = handler.get_best_candidate("nonexistent.channel")
    assert best_candidate is None


def test_epg_candidate_handler_get_best_candidate_multiple(
    xml_good_quality: etree._Element,
    xml_poor_quality: etree._Element,
) -> None:
    """Test getting the best candidate when multiple EPGs have the same tvg_id."""
    handler = EPGCandidateHandler()
    tvg_id = "channel1"

    epg_url_1 = get_epg_url()
    epg_url_2 = get_epg_url()

    # Add programs from test.xml (has more details)
    for program in xml_good_quality.findall("programme"):
        if program.get("channel") == tvg_id:
            handler.add_program(tvg_id, epg_url_1, program)

    for channel in xml_good_quality.findall("channel"):
        if channel.get("id") == tvg_id:
            handler.add_channel(tvg_id, epg_url_1, channel)

    # Add programs from test2.xml (has less details)
    for program in xml_poor_quality.findall("programme"):
        if program.get("channel") == tvg_id:
            handler.add_program(tvg_id, epg_url_2, program)

    for channel in xml_poor_quality.findall("channel"):
        if channel.get("id") == tvg_id:
            handler.add_channel(tvg_id, epg_url_2, channel)
    best_candidate = handler.get_best_candidate(tvg_id)
    assert best_candidate is not None
    assert best_candidate.tvg_id == tvg_id
    # test.xml has more detailed descriptions and icons, so it should win
    assert best_candidate.epg_url == epg_url_1


# region EPGCandidate
def test_epg_candidate_add_program(
    xml_good_quality: etree._Element,
    epg_url: HttpUrl,
) -> None:
    """Test adding a program to EPGCandidate."""
    candidate = EPGCandidate("channel1", epg_url)
    program = xml_good_quality.findall("programme")[0]

    candidate.add_program(program)
    assert len(candidate._programs) == 1


def test_epg_candidate_add_channel(
    xml_good_quality: etree._Element,
    epg_url: HttpUrl,
) -> None:
    """Test adding a channel to EPGCandidate."""
    candidate = EPGCandidate("channel1", epg_url)
    channel = xml_good_quality.findall("channel")[0]

    candidate.add_channel(channel)
    assert len(candidate._channels) == 1


def test_epg_candidate_get_channels_programs(
    xml_good_quality: etree._Element,
    epg_url: HttpUrl,
) -> None:
    """Test getting all channels and programs from EPGCandidate."""
    candidate = EPGCandidate("channel1", epg_url)

    # Add channel
    channel = xml_good_quality.findall("channel")[0]
    candidate.add_channel(channel)

    # Add programs
    programs = [p for p in xml_good_quality.findall("programme") if p.get("channel") == "channel1"]
    for program in programs:
        candidate.add_program(program)

    channels_programs = candidate.get_channels_programs()
    assert len(channels_programs) == 1 + len(programs)  # 1 channel + N programs


def test_epg_candidate_score_no_programs(epg_url: HttpUrl) -> None:
    """Test EPGCandidate scoring with no programs."""
    candidate = EPGCandidate("test.channel", epg_url)
    score = candidate.get_epg_score()
    assert score == 0


def test_epg_candidate_score_caching(
    xml_good_quality: etree._Element,
    epg_url: HttpUrl,
) -> None:
    """Test that EPGCandidate score is cached."""
    candidate = EPGCandidate("channel1", epg_url)

    # Add a program
    program = xml_good_quality.findall("programme")[0]
    candidate.add_program(program)

    # Get score twice
    score1 = candidate.get_epg_score()
    score2 = candidate.get_epg_score()

    assert score1 == score2
    assert candidate._score is not None


def test_epg_candidate_score_invalidation_on_add_program(
    xml_good_quality: etree._Element,
    epg_url: HttpUrl,
) -> None:
    """Test that score cache is invalidated when adding a program."""
    candidate = EPGCandidate("channel1", epg_url)

    # Add a program and get score
    program1 = xml_good_quality.findall("programme")[0]
    candidate.add_program(program1)
    score1 = candidate.get_epg_score()
    assert score1 == 1

    # Add another program
    program2 = xml_good_quality.findall("programme")[1]
    candidate.add_program(program2)

    # Score cache should be invalidated
    assert candidate._score is None

    # New score should be different
    score2 = candidate.get_epg_score()
    # Since the programs are in the past, scores might be 0, but we can check that scoring works
    assert score2 == 2


def test_epg_candidate_score_invalidation_on_add_channel(
    xml_good_quality: etree._Element,
    epg_url: HttpUrl,
) -> None:
    """Test that score cache is invalidated when adding a channel."""
    candidate = EPGCandidate("channel1", epg_url)

    # Add a program and get score
    program = xml_good_quality.findall("programme")[0]
    candidate.add_program(program)
    score1 = candidate.get_epg_score()
    assert score1 == 1

    # Add a channel
    channel = xml_good_quality.findall("channel")[0]
    candidate.add_channel(channel)

    # Score cache should be invalidated
    assert candidate._score is None


def test_epg_candidate_score_with_future_programs(
    xml_good_quality: etree._Element,
    epg_url: HttpUrl,
) -> None:
    """Test EPGCandidate scoring with future programs."""
    candidate = EPGCandidate("channel1", epg_url)

    for program in xml_good_quality.findall("programme"):
        candidate.add_program(program)

    for channel in xml_good_quality.findall("channel"):
        candidate.add_channel(channel)

    score = candidate.get_epg_score()
    assert score > 0


def test_epg_candidate_score_comparison(
    xml_good_quality: etree._Element,
    xml_poor_quality: etree._Element,
    xml_past_programs_only: etree._Element,
) -> None:
    """Test that EPGCandidate with more quality data has higher score."""
    channel_tvg_id = "channel1"

    def create_candidate_from_xml(xml: etree._Element, epg_url: HttpUrl) -> EPGCandidate:
        """Helper to create and populate a candidate from XML."""
        candidate = EPGCandidate(channel_tvg_id, epg_url)
        for program in xml.findall("programme"):
            if program.get("channel") == channel_tvg_id:
                candidate.add_program(program)
        for channel in xml.findall("channel"):
            if channel.get("id") == channel_tvg_id:
                candidate.add_channel(channel)
        return candidate

    # Candidate with good data
    candidate1 = create_candidate_from_xml(xml_good_quality, get_epg_url())
    score1 = candidate1.get_epg_score()

    # Candidate with poor data
    candidate2 = create_candidate_from_xml(xml_poor_quality, get_epg_url())
    score2 = candidate2.get_epg_score()

    # Candidate with only past programs
    candidate3 = create_candidate_from_xml(xml_past_programs_only, get_epg_url())
    score3 = candidate3.get_epg_score()

    assert score1 > score2
    assert score2 > score3
