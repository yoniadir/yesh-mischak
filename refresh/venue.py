from datetime import date, datetime

from icalendar import Calendar

from refresh.config import STADIUM_NAME, TZ
from refresh.model import Event, SourceError


def parse_venue(ics_text: str, kind: str) -> list[Event]:
    try:
        calendar = Calendar.from_ical(ics_text)
    except ValueError as e:
        raise SourceError(f"venue feed is not valid iCalendar: {e}") from e

    events = []
    for vevent in calendar.walk("VEVENT"):
        if not str(vevent.get("X-LOCATION-DISPLAYNAME", "")).startswith(STADIUM_NAME):
            continue
        start = _local(vevent.decoded("DTSTART"))
        uid = str(vevent["UID"])
        day = start.date() if isinstance(start, datetime) else start
        events.append(
            Event(
                id=f"sportpalace:{uid}:{day.isoformat()}",
                date=day,
                time=start.strftime("%H:%M") if isinstance(start, datetime) else None,
                title=str(vevent.get("SUMMARY", "")).strip(),
                kind=kind,
                status="confirmed",
                source="sportpalace",
                url=str(vevent["URL"]) if "URL" in vevent else None,
            )
        )
    return events


def _local(value: date | datetime) -> date | datetime:
    if not isinstance(value, datetime):
        return value
    if value.tzinfo is None:
        return value.replace(tzinfo=TZ)
    return value.astimezone(TZ)
