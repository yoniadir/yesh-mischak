from datetime import datetime, time, timedelta, timezone

from icalendar import Calendar
from icalendar import Event as VEvent

from refresh.config import TZ
from refresh.model import Event

# Source end times are unreliable one-hour stubs; use a fixed block instead.
EVENT_DURATION = timedelta(hours=2)


def render_ics(events: list[Event], now: datetime) -> str:
    calendar = Calendar()
    calendar.add("prodid", "-//yesh-mischak//bloomfield//HE")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("x-wr-calname", "בלומפילד · יש משחק")
    calendar.add("x-wr-timezone", "Asia/Jerusalem")
    stamp = now.astimezone(timezone.utc)
    for event in events:
        entry = VEvent()
        entry.add("uid", f"{event.id}@yesh-mischak")
        entry.add("dtstamp", stamp)
        entry.add("summary", event.title)
        if event.time:
            hour, minute = map(int, event.time.split(":"))
            start = datetime.combine(event.date, time(hour, minute), tzinfo=TZ)
            entry.add("dtstart", start)
            entry.add("dtend", start + EVENT_DURATION)
        else:
            entry.add("dtstart", event.date)
            entry.add("dtend", event.date + timedelta(days=1))
        if event.url:
            entry.add("url", event.url)
        calendar.add_component(entry)
    calendar.add_missing_timezones()
    return calendar.to_ical().decode("utf-8")
