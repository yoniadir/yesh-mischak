from datetime import datetime

from conftest import events_of, vcal, vevent
from refresh.config import TZ
from refresh.transform import Payloads, build

NOW = datetime(2026, 10, 1, 12, 0, tzinfo=TZ)


def dates_for(*vevents: str) -> list[str]:
    payloads = Payloads(venue={"11": vcal(*vevents)}, fixtures={})
    return [e["date"] for e in events_of(build(payloads, NOW))]


def test_residency_spanning_several_nights_appears_on_each_day():
    assert dates_for(vevent("run", "20261012T210000", "20261014T233000")) == [
        "2026-10-12", "2026-10-13", "2026-10-14",
    ]


def test_each_expanded_day_keeps_the_start_time_and_a_distinct_id():
    payloads = Payloads(venue={"11": vcal(vevent("run", "20261012T210000", "20261013T233000"))}, fixtures={})
    events = events_of(build(payloads, NOW))
    assert [e["time"] for e in events] == ["21:00", "21:00"]
    assert len({e["id"] for e in events}) == 2


def test_event_ending_after_midnight_counts_only_on_its_start_day():
    assert dates_for(vevent("late", "20261012T233000", "20261013T020000")) == ["2026-10-12"]


def test_all_day_event_uses_exclusive_end_date():
    assert dates_for(vevent("fest", "20261012", "20261015")) == [
        "2026-10-12", "2026-10-13", "2026-10-14",
    ]


def test_all_day_event_has_no_time():
    payloads = Payloads(venue={"11": vcal(vevent("fest", "20261012", "20261013"))}, fixtures={})
    assert [e["time"] for e in events_of(build(payloads, NOW))] == [None]
