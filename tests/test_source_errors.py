import json

import pytest

from conftest import NOW, all_payloads, events_of, read_fixture, vcal, vevent
from refresh.model import SourceError
from refresh.transform import Payloads, build


def with_venue(sport: str) -> Payloads:
    p = all_payloads()
    return Payloads(venue={**p.venue, "10": sport}, fixtures=p.fixtures)


def with_fixtures(feed: str) -> Payloads:
    p = all_payloads()
    return Payloads(venue=p.venue, fixtures={**p.fixtures, 566: feed})


@pytest.mark.parametrize("bad", [
    read_fixture("venue-sport.ics")[:20000],  # truncated mid-stream
    "<!DOCTYPE html><html><body>maintenance</body></html>",
    "",
])
def test_bad_venue_payload_raises(bad):
    with pytest.raises(SourceError):
        build(with_venue(bad), NOW)


@pytest.mark.parametrize("bad", [
    read_fixture("fixtures-566.json")[:5000],  # truncated JSON
    "<html>blocked</html>",
    json.dumps({"error": "rate limited"}),
    json.dumps({"games": "nope"}),
    json.dumps({"games": [{"id": 1}]}),
])
def test_bad_fixtures_payload_raises(bad):
    with pytest.raises(SourceError):
        build(with_fixtures(bad), NOW)


def test_venue_feed_without_bloomfield_events_is_a_valid_empty_result():
    other_hall = vcal(vevent("x", "20261012T200000", "20261012T220000", venue="היכל מנורה מבטחים"))
    empty = Payloads(venue={"10": other_hall, "11": vcal()}, fixtures={566: json.dumps({"games": []})})
    artifacts = build(empty, NOW)
    assert events_of(artifacts) == []
    assert json.loads(artifacts.events_json)["version"] == 1
