import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from refresh.config import PAST_DAYS, SOURCES, TZ, VENUE_CALENDARS
from refresh.fixtures import parse_fixtures
from refresh.ics import render_ics
from refresh.venue import parse_venue


@dataclass(frozen=True)
class Payloads:
    venue: dict[str, str]  # calendar id -> iCal text
    fixtures: dict[int, str]  # club id -> JSON text


@dataclass(frozen=True)
class Artifacts:
    events_json: str
    ics: str


def build(payloads: Payloads, now: datetime) -> Artifacts:
    confirmed = [
        event
        for calendar_id, text in payloads.venue.items()
        for event in parse_venue(text, VENUE_CALENDARS[calendar_id])
    ]
    # The same game appears in both clubs' feeds (derbies): keep one per game id.
    tentative = {
        event.id: event for text in payloads.fixtures.values() for event in parse_fixtures(text)
    }.values()
    confirmed_days = {e.date for e in confirmed}
    merged = confirmed + [e for e in tentative if e.date not in confirmed_days]

    cutoff = now.astimezone(TZ).date() - timedelta(days=PAST_DAYS)
    kept = sorted(
        (e for e in merged if e.date >= cutoff),
        key=lambda e: (e.date, e.time or "", e.title, e.id),
    )
    document = {
        "version": 1,
        "generated_at": now.astimezone(TZ).isoformat(timespec="seconds"),
        "timezone": "Asia/Jerusalem",
        "sources": SOURCES,
        "events": [e.to_json() for e in kept],
    }
    return Artifacts(
        events_json=json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        ics=render_ics([e for e in kept if e.status == "confirmed"], now),
    )
