from acere.services.epg.helpers import normalise_epg_tvg_id


def test_normalise_epg_tvg_id() -> None:
    assert normalise_epg_tvg_id("AU | Test Channel 1") == "Test Channel 1.au"
    assert normalise_epg_tvg_id("au | Test Channel 2") == "Test Channel 2.au"
    assert normalise_epg_tvg_id("au | Test Channel 3") == "Test Channel 3.au"

    assert normalise_epg_tvg_id("Test.Channel.1.uk") == "Test Channel 1.uk"
    assert normalise_epg_tvg_id("Test_Channel_2.uk") == "Test Channel 2.uk"
    assert normalise_epg_tvg_id("Test Channel 3.uk") == "Test Channel 3.uk"
    assert normalise_epg_tvg_id("Test Channel 4.UK") == "Test Channel 4.uk"
    assert normalise_epg_tvg_id("Test Channel 5.uk2") == "Test Channel 5.uk"
