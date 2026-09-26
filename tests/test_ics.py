from datetime import datetime, timedelta

from icalendar import Calendar

from conftest import NOW, all_payloads, events_of
from refresh.config import TZ
from refresh.transform import build


def vevents(artifacts):
    return list(Calendar.from_ical(artifacts.ics).walk("VEVENT"))


def test_contains_every_confirmed_event_and_no_tentative_one():
    artifacts = build(all_payloads(), NOW)
    confirmed = [e for e in events_of(artifacts) if e["status"] == "confirmed"]
    entries = vevents(artifacts)
    assert len(entries) == len(confirmed) == 5
    assert sorted(str(v["SUMMARY"]) for v in entries) == sorted(e["title"] for e in confirmed)
    assert not any("365scores" in str(v["UID"]) for v in entries)


def test_times_are_asia_jerusalem_with_real_start():
    entry = next(v for v in vevents(build(all_payloads(), NOW)) if str(v["SUMMARY"]) == 'מכבי ת"א- בני סכנין')
    start = entry.decoded("DTSTART")
    assert start == datetime(2026, 10, 10, 19, 30, tzinfo=TZ)
    assert str(start.tzinfo) == "Asia/Jerusalem"
    assert entry["DTSTART"].params["TZID"] == "Asia/Jerusalem"
    assert entry.decoded("DTEND") - start == timedelta(hours=2)


def test_uids_are_stable_across_refreshes():
    first = {str(v["UID"]) for v in vevents(build(all_payloads(), NOW))}
    later = {str(v["UID"]) for v in vevents(build(all_payloads(), NOW + timedelta(hours=1)))}
    assert first == later
    assert len(first) == 5


def test_calendar_is_named_and_carries_source_links():
    cal = Calendar.from_ical(build(all_payloads(), NOW).ics)
    assert str(cal["X-WR-CALNAME"]) == "בלומפילד · יש משחק"
    assert all(str(v["URL"]).startswith("https://") for v in cal.walk("VEVENT"))
