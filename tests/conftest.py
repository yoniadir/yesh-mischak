import json
from datetime import datetime
from pathlib import Path

from refresh.config import STADIUM_NAME, TZ
from refresh.transform import Payloads

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 9, 26, 6, 0, tzinfo=TZ)


def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def venue_payloads() -> Payloads:
    return Payloads(
        venue={"10": read_fixture("venue-sport.ics"), "11": read_fixture("venue-culture.ics")},
        fixtures={},
    )


def all_payloads() -> Payloads:
    return Payloads(
        venue=venue_payloads().venue,
        fixtures={566: read_fixture("fixtures-566.json"), 567: read_fixture("fixtures-567.json")},
    )


def events_of(artifacts) -> list[dict]:
    return json.loads(artifacts.events_json)["events"]


def vcal(*vevents: str) -> str:
    return "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:test\r\n" + "".join(vevents) + "END:VCALENDAR\r\n"


def vevent(uid: str, start: str, end: str, summary: str = "אירוע", venue: str = STADIUM_NAME) -> str:
    """start/end: '20261010T193000' (Asia/Jerusalem) or '20261010' (all-day)."""
    kind = ";TZID=Asia/Jerusalem" if "T" in start else ";VALUE=DATE"
    return (
        f"BEGIN:VEVENT\r\nUID:{uid}\r\nDTSTART{kind}:{start}\r\nDTEND{kind}:{end}\r\n"
        f"SUMMARY:{summary}\r\nX-LOCATION-DISPLAYNAME:{venue}\r\nEND:VEVENT\r\n"
    )
