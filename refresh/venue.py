from datetime import date, datetime, timedelta

from icalendar import Calendar

from refresh.config import DAY_ROLLOVER, STADIUM_NAME, TZ
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
        end = _local(vevent.decoded("DTEND")) if "DTEND" in vevent else start
        uid = str(vevent["UID"])
        for day in _days(start, end):
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


def _days(start: date | datetime, end: date | datetime) -> list[date]:
    """Every calendar day the event occupies.

    A timed event counts on a later day only if it is still running at
    DAY_ROLLOVER that day, so 23:30-00:30 stays on its start day.
    All-day events have an exclusive DTEND.
    """
    if isinstance(start, datetime):
        first = start.date()
        last = max(first, (end - DAY_ROLLOVER).date())
    else:
        first = start
        last = max(first, end - timedelta(days=1))
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def _local(value: date | datetime) -> date | datetime:
    if not isinstance(value, datetime):
        return value
    if value.tzinfo is None:
        return value.replace(tzinfo=TZ)
    return value.astimezone(TZ)
