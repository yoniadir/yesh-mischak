import json

from conftest import NOW, all_payloads, events_of, venue_payloads
from refresh.transform import Payloads, build


def by_status(events, status):
    return [e for e in events if e["status"] == status]


def test_home_fixtures_of_either_club_become_tentative():
    events = events_of(build(all_payloads(), NOW))
    tentative = by_status(events, "tentative")
    assert len(tentative) == 18
    assert {e["source"] for e in tentative} == {"365scores"}
    assert {e["kind"] for e in tentative} == {"football"}
    titles = {e["title"] for e in tentative}
    assert "מכבי תל אביב – מכבי פתח תקוה" in titles  # Maccabi home, 2026-11-06
    assert "הפועל תל אביב – מכבי חיפה" in titles  # Hapoel home, 2026-11-02


def test_tentative_event_shape():
    event = next(e for e in events_of(build(all_payloads(), NOW)) if e["date"] == "2026-11-06")
    assert event == {
        "id": "365scores:4739294",
        "date": "2026-11-06",
        "time": "14:00",
        "title": "מכבי תל אביב – מכבי פתח תקוה",
        "kind": "football",
        "status": "tentative",
        "source": "365scores",
        "url": None,
    }


def test_away_fixture_is_not_included():
    # Maccabi Tel Aviv plays away on 2026-10-19; nothing else happens that day.
    dates = [e["date"] for e in events_of(build(all_payloads(), NOW))]
    assert "2026-10-19" not in dates


def test_fixture_between_two_other_clubs_is_not_included():
    feed = json.dumps({"games": [{
        "id": 1, "startTime": "2026-11-11T20:00:00+02:00",
        "homeCompetitor": {"id": 559, "name": "בית\"ר ירושלים"},
        "awayCompetitor": {"id": 561, "name": "בני סכנין"},
    }]})
    events = events_of(build(Payloads(venue={}, fixtures={566: feed}), NOW))
    assert events == []


def test_confirmed_day_suppresses_tentative_that_day_only():
    events = events_of(build(all_payloads(), NOW))
    for day in ("2026-10-10", "2026-10-17", "2026-10-24", "2026-10-29"):
        assert [e["status"] for e in events if e["date"] == day] == ["confirmed"]
    assert by_status(events, "confirmed") == events_of(build(venue_payloads(), NOW))


def test_derby_listed_in_both_club_feeds_appears_once():
    only_tentative = Payloads(venue={}, fixtures=all_payloads().fixtures)
    events = events_of(build(only_tentative, NOW))
    assert [e["id"] for e in events].count("365scores:4815899") == 1
    assert len(events) == 22


def test_merged_output_is_sorted():
    events = events_of(build(all_payloads(), NOW))
    keys = [(e["date"], e["time"] or "") for e in events]
    assert keys == sorted(keys)
