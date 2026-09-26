from datetime import datetime

import pytest

from conftest import NOW, events_of, vcal, vevent, venue_payloads
from refresh.config import STADIUM_NAME, TZ
from refresh.model import SourceError
from refresh.transform import Payloads, build


def test_only_bloomfield_events_in_window_are_confirmed():
    events = events_of(build(venue_payloads(), NOW))
    assert [(e["date"], e["time"]) for e in events] == [
        ("2026-09-19", "20:30"),
        ("2026-10-10", "19:30"),
        ("2026-10-17", "18:45"),
        ("2026-10-24", "19:30"),
        ("2026-10-29", "20:30"),
    ]
    assert {e["status"] for e in events} == {"confirmed"}
    assert {e["source"] for e in events} == {"sportpalace"}


def test_event_for_non_tel_aviv_club_is_included():
    events = events_of(build(venue_payloads(), NOW))
    assert events[0]["title"] == 'בית"ר ירושלים- הפועל חיפה'


def test_events_carry_title_kind_and_source_link():
    event = events_of(build(venue_payloads(), NOW))[1]
    assert event["title"] == 'מכבי ת"א- בני סכנין'
    assert event["kind"] == "football"
    assert event["url"].startswith("https://www.sportpalace.co.il/")


def test_window_keeps_trailing_seven_days_only():
    dates = [e["date"] for e in events_of(build(venue_payloads(), NOW))]
    assert "2026-09-19" in dates  # 7 days back
    assert "2026-09-18" not in dates  # 8 days back
    assert min(dates) == "2026-09-19"


def test_culture_calendar_contributes_concerts():
    june = datetime(2026, 6, 10, 12, 0, tzinfo=TZ)
    concerts = [e for e in events_of(build(venue_payloads(), june)) if e["kind"] == "concert"]
    assert [e["date"] for e in concerts] == [
        "2026-06-11", "2026-06-13", "2026-06-14", "2026-06-16", "2026-06-18", "2026-06-20",
    ]
    assert {e["title"] for e in concerts} == {"אייל גולן"}


def test_events_are_sorted_by_date_then_time():
    events = events_of(build(venue_payloads(), datetime(2026, 1, 20, tzinfo=TZ)))
    keys = [(e["date"], e["time"] or "") for e in events]
    assert keys == sorted(keys)
    # 2026-01-25 has four Bloomfield events in the real feed
    assert [e["time"] for e in events if e["date"] == "2026-01-25"] == ["17:00", "21:00", "21:00", "22:00"]


def test_venue_name_with_leading_whitespace_is_still_matched():
    padded = vcal(vevent("pad", "20261012T193000", "20261012T220000", venue=f"  {STADIUM_NAME}  "))
    payloads = Payloads(venue={"10": padded}, fixtures={})
    events = events_of(build(payloads, NOW))
    assert [e["date"] for e in events] == ["2026-10-12"]


def test_vevent_without_dtstart_raises_source_error():
    raw = (
        "BEGIN:VEVENT\r\nUID:no-start\r\n"
        f"SUMMARY:x\r\nX-LOCATION-DISPLAYNAME:{STADIUM_NAME}\r\nEND:VEVENT\r\n"
    )
    payloads = Payloads(venue={"10": vcal(raw)}, fixtures={})
    with pytest.raises(SourceError):
        build(payloads, NOW)


def test_document_header():
    import json
    doc = json.loads(build(venue_payloads(), NOW).events_json)
    assert doc["version"] == 1
    assert doc["generated_at"] == "2026-09-26T06:00:00+03:00"
    assert doc["timezone"] == "Asia/Jerusalem"
    assert [s["id"] for s in doc["sources"]] == ["sportpalace", "365scores"]
