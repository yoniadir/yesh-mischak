# יש משחק (yesh-mischak) v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A static page answering "is there an event at Bloomfield today?", fed by a daily CI job that builds `events.json` and `bloomfield.ics` from the venue iCal feed (confirmed) and 365scores fixtures (tentative).

**Architecture:** A Python package `refresh/` exposes one pure function `build(payloads, now) -> Artifacts`; a thin CLI wraps it with HTTP fetching and file writing. A static `site/` folder holds a vanilla-JS page whose reader-facing logic is one pure function `viewModel(data, now)` in `site/view.js`. GitHub Actions runs tests, refreshes daily, commits the artifacts and deploys `site/` to GitHub Pages.

**Tech Stack:** Python ≥3.12 managed by `uv`, `httpx==0.28.1`, `icalendar==7.3.0`, `pytest`; vanilla ES modules, `node --test` (Node 22); GitHub Actions + GitHub Pages.

## Global Constraints

- All date reasoning uses **Asia/Jerusalem**, regardless of device timezone or CI runner timezone.
- "Today" = calendar day in Asia/Jerusalem, whole-day resolution; a finished event still makes the day an event day.
- Today / next-event determination happens **in the browser at page-open time**, never at build time.
- Banner and next-event line use **confirmed events only**; tentative events appear only in the calendar, distinguished visually **and in words**.
- Merge rule is exactly: (1) venue event whose venue is Bloomfield → `confirmed`; (2) fixture whose **home** competitor is one of the two Tel Aviv clubs → `tentative` (all competitions); (3) a day with ≥1 confirmed event drops that day's tentative events. No aliasing, fuzzy matching, or cross-source time reconciliation.
- Venue-feed oddities (implausible late-night times, duplicates) pass through **unmodified**.
- `events.json` window: all future events + trailing **7** days. Sorted by date then time. Multi-day source events expand to one entry per day.
- `bloomfield.ics`: **confirmed only**, stable UIDs, times in Asia/Jerusalem.
- Failure policy: non-200, unparseable feed, or transport error → run fails, nothing written or committed. Zero events is **not** a failure.
- Web client: single static HTML page, vanilla JS, no framework, no build step. Fetches `events.json` by **relative path**. Hebrew default (RTL), English toggle, choice persisted locally. Mobile-first, dark mode. Staleness warning when `generated_at` is more than **two days** old.
- Source URLs, club ids, calendar ids and stadium name are constants in `refresh/config.py` only.
- Tests: pure functions, injected time, real captured fixtures; no network mocking, no clock patching, no filesystem writes. Tests assert on consumer-visible output (`events.json` content, `.ics` content, view-model result).
- `events.json` is a versioned public contract (`"version": 1`): fields may be added, never renamed or repurposed.
- Repository is public: no personal address/location/account info anywhere.

## Facts discovered while planning (verified 2026-09-26)

- Venue iCal: `https://www.sportpalace.co.il/index.php?option=com_dpcalendar&task=ical.download&id={10|11}` (301 → 200, `text/calendar`). Calendar **10** = sport, **11** = culture. Venue is in `X-LOCATION-DISPLAYNAME`; Bloomfield values are `אצטדיון בלומפילד`, sometimes with a room suffix like `אצטדיון בלומפילד [האצטדיון המרכזי]` → match with **startswith**.
- Fixtures: `https://webws.365scores.com/web/games/fixtures/?appTypeId=5&langId=2&timezoneName=Asia/Jerusalem&competitors={id}` (langId=2 → Hebrew names). Maccabi Tel Aviv = **566**, Hapoel Tel Aviv = **567**. One page covers ~5 months (22 games); only future games. Games have no public URL field. A derby appears in **both** club feeds with the same game `id`.
- Real fixtures captured into `tests/fixtures/` (`venue-sport.ics`, `venue-culture.ics`, `fixtures-566.json`, `fixtures-567.json`). With `now = 2026-09-26 06:00 Asia/Jerusalem` they yield: **5 confirmed** (2026-09-19, 10-10, 10-17, 10-24, 10-29; the 09-19 one is Beitar Jerusalem), 22 unique home fixtures of which 4 fall on confirmed days → **18 tentative**. The 2026-09-18 Bloomfield event is exactly outside the 7-day window. With `now = 2026-06-10 12:00` the culture calendar yields 6 Eyal Golan concerts (06-11 … 06-20).

## Decisions this plan makes that the spec left open (review these)

1. **Midnight crossing vs. multi-day.** Many venue events end after midnight (e.g. 23:30→00:30). An event is counted on a later day only if it is still running at **06:00** of that day. All-day (`VALUE=DATE`) events use the exclusive DTEND. Each expanded day carries the source start time.
2. **Kind** comes from the source calendar: sport calendar → `football`, culture calendar → `concert`, fixtures → `football`. `other` stays in the contract but v1 never emits it.
3. **Tentative de-duplication by 365scores game id** (the derby is in both club feeds). This is same-source identity, not cross-source matching.
4. **Tentative events have `url: null`** — 365scores exposes no stable per-game URL.
5. **ICS event duration** is a fixed 2 hours (source DTENDs are unreliable 1h stubs).
6. **Next event** = first confirmed event that has not started yet (`date > today`, or today with `time > now`). Relative description: `today`, `tomorrow`, `weekday` (2–6 days out), `date` (≥7 days out, where a weekday name would be ambiguous).
7. **Cron** is `0 3 * * *` UTC — 06:00 in summer (IDT), 05:00 in winter (IST). GitHub cron has no timezone support.
8. **"Commit only if changed"** effectively commits daily, because `generated_at` changes every run — this is required for the staleness warning to mean anything.
9. Hosting is **GitHub Pages** via Actions, publishing the `site/` folder.

## File Structure

```
yesh-mischak/
  pyproject.toml, uv.lock, .python-version, .gitignore, package.json, README.md
  refresh/
    __init__.py
    config.py      # all constants (URLs, ids, stadium name, TZ, window)
    model.py       # Event dataclass, SourceError
    venue.py       # venue iCal text -> confirmed Events (Bloomfield filter, day expansion)
    fixtures.py    # 365scores JSON text -> tentative Events  (the swappable fixtures adapter)
    ics.py         # confirmed Events -> bloomfield.ics text
    transform.py   # Payloads, Artifacts, build()  <- Seam 1
    __main__.py    # fetch + build + write (untested wrapper)
  tests/
    fixtures/      # real captured responses (already present)
    conftest.py    # payload loaders, NOW, synthetic iCal helpers
    test_venue_events.py, test_multiday.py, test_merge.py, test_source_errors.py, test_ics.py
  site/
    index.html, styles.css, app.js
    view.js        # viewModel()  <- Seam 2
    view.test.js
    events.json, bloomfield.ics   # generated, committed
  .github/workflows/publish.yml
```

---

### Task 1: Scaffold + confirmed events from the venue feed

**Files:**
- Create: `.gitignore`, `.python-version`, `pyproject.toml`, `refresh/__init__.py`, `refresh/config.py`, `refresh/model.py`, `refresh/venue.py`, `refresh/transform.py`, `tests/conftest.py`, `tests/test_venue_events.py`
- Existing: `tests/fixtures/*` (already captured)

**Interfaces:**
- Produces:
  - `refresh.model.Event` (frozen dataclass): `id: str, date: datetime.date, time: str | None ("HH:MM"), title: str, kind: str, status: str, source: str, url: str | None`, method `to_json() -> dict`
  - `refresh.model.SourceError(Exception)`
  - `refresh.venue.parse_venue(ics_text: str, kind: str) -> list[Event]`
  - `refresh.transform.Payloads(venue: dict[str, str], fixtures: dict[int, str])`
  - `refresh.transform.Artifacts(events_json: str)` (Task 5 adds `ics: str`)
  - `refresh.transform.build(payloads: Payloads, now: datetime) -> Artifacts`
  - `tests/conftest.py`: `NOW`, `read_fixture(name)`, `venue_payloads()`, `all_payloads()`, `events_of(artifacts)`, `vcal(*vevents)`, `vevent(...)`

- [ ] **Step 1: Initialise repo and tooling**

```bash
cd ~/Documents/Projects/yesh-mischak
git init -b main
printf '3.12\n' > .python-version
printf '.venv/\n__pycache__/\n.pytest_cache/\nnode_modules/\n.DS_Store\n' > .gitignore
```

Create `pyproject.toml`:

```toml
[project]
name = "yesh-mischak"
version = "1.0.0"
description = "Is there an event at Bloomfield today?"
requires-python = ">=3.12"
dependencies = []

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

```bash
uv add httpx==0.28.1 icalendar==7.3.0
uv add --dev pytest
```

Expected: `uv.lock` created, `pyproject.toml` lists both pinned deps and a `dev` group with pytest.

- [ ] **Step 2: Write config and model**

`refresh/__init__.py`: empty file.

`refresh/config.py`:

```python
from datetime import timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Jerusalem")

STADIUM_NAME = "אצטדיון בלומפילד"

VENUE_ICAL_URL = (
    "https://www.sportpalace.co.il/index.php"
    "?option=com_dpcalendar&task=ical.download&id={calendar_id}"
)
# DPCalendar calendar id -> event kind
VENUE_CALENDARS = {"10": "football", "11": "concert"}

FIXTURES_URL = (
    "https://webws.365scores.com/web/games/fixtures/"
    "?appTypeId=5&langId=2&timezoneName=Asia/Jerusalem&competitors={club_id}"
)
TEL_AVIV_CLUBS = {566: "מכבי תל אביב", 567: "הפועל תל אביב"}

PAST_DAYS = 7
# A night event only counts on the following day if still running at this hour.
DAY_ROLLOVER = timedelta(hours=6)

USER_AGENT = "yesh-mischak/1.0 (+https://github.com/)"

SOURCES = [
    {
        "id": "sportpalace",
        "name": "היכלי הספורט תל אביב",
        "url": "https://www.sportpalace.co.il/tlv-faclities/sport-halls/new-blumfield/blumfield-events",
    },
    {"id": "365scores", "name": "365Scores", "url": "https://www.365scores.com/he"},
]
```

`refresh/model.py`:

```python
from dataclasses import dataclass
from datetime import date


class SourceError(Exception):
    """A source responded with something we cannot trust."""


@dataclass(frozen=True)
class Event:
    id: str
    date: date
    time: str | None
    title: str
    kind: str  # football | concert | other
    status: str  # confirmed | tentative
    source: str  # sportpalace | 365scores
    url: str | None

    def to_json(self) -> dict:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "time": self.time,
            "title": self.title,
            "kind": self.kind,
            "status": self.status,
            "source": self.source,
            "url": self.url,
        }
```

- [ ] **Step 3: Write test helpers**

`tests/conftest.py`:

```python
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
```

- [ ] **Step 4: Write the failing tests**

`tests/test_venue_events.py`:

```python
from datetime import datetime

from conftest import NOW, events_of, venue_payloads
from refresh.config import TZ
from refresh.transform import build


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


def test_document_header():
    import json
    doc = json.loads(build(venue_payloads(), NOW).events_json)
    assert doc["version"] == 1
    assert doc["generated_at"] == "2026-09-26T06:00:00+03:00"
    assert doc["timezone"] == "Asia/Jerusalem"
    assert [s["id"] for s in doc["sources"]] == ["sportpalace", "365scores"]
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `uv run pytest -q`
Expected: collection error `ModuleNotFoundError: No module named 'refresh.transform'` (or `refresh.venue`).

- [ ] **Step 6: Implement venue parsing (single-day for now) and build()**

`refresh/venue.py`:

```python
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
```

`refresh/transform.py`:

```python
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from refresh.config import PAST_DAYS, SOURCES, TZ, VENUE_CALENDARS
from refresh.venue import parse_venue


@dataclass(frozen=True)
class Payloads:
    venue: dict[str, str]  # calendar id -> iCal text
    fixtures: dict[int, str]  # club id -> JSON text


@dataclass(frozen=True)
class Artifacts:
    events_json: str


def build(payloads: Payloads, now: datetime) -> Artifacts:
    confirmed = [
        event
        for calendar_id, text in payloads.venue.items()
        for event in parse_venue(text, VENUE_CALENDARS[calendar_id])
    ]
    cutoff = now.astimezone(TZ).date() - timedelta(days=PAST_DAYS)
    kept = sorted(
        (e for e in confirmed if e.date >= cutoff),
        key=lambda e: (e.date, e.time or "", e.title, e.id),
    )
    document = {
        "version": 1,
        "generated_at": now.astimezone(TZ).isoformat(timespec="seconds"),
        "timezone": "Asia/Jerusalem",
        "sources": SOURCES,
        "events": [e.to_json() for e in kept],
    }
    return Artifacts(events_json=json.dumps(document, ensure_ascii=False, indent=2) + "\n")
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `uv run pytest -q`
Expected: `7 passed`. If `test_events_are_sorted_by_date_then_time` disagrees on the 2026-01-25 times, print them (`uv run python -c ...`) and correct the literal list to what the fixture actually contains — it must still include the 17:00 and 22:00 entries in ascending order.

- [ ] **Step 8: Commit**

```bash
git add .gitignore .python-version pyproject.toml uv.lock refresh tests SPEC.md docs
git commit -m "feat: confirmed Bloomfield events from venue feed into events.json"
```

---

### Task 2: Multi-day expansion with the 06:00 rollover rule

**Files:**
- Modify: `refresh/venue.py`
- Test: `tests/test_multiday.py`

**Interfaces:**
- Consumes: `parse_venue`, `build`, `Payloads`, conftest `vcal`, `vevent`, `events_of`
- Produces: no new names; `parse_venue` now returns one `Event` per affected day.

- [ ] **Step 1: Write the failing tests**

`tests/test_multiday.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_multiday.py -q`
Expected: residency and all-day-range tests FAIL (only the first day is emitted); the midnight and no-time tests pass already.

- [ ] **Step 3: Implement day expansion**

Replace `refresh/venue.py` with:

```python
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
```

- [ ] **Step 4: Run all tests**

Run: `uv run pytest -q`
Expected: `12 passed` (Task 1's real-fixture assertions are unchanged because every real Bloomfield event ends before 06:00 next day).

- [ ] **Step 5: Commit**

```bash
git add refresh/venue.py tests/test_multiday.py
git commit -m "feat: expand multi-day venue events to one entry per day"
```

---

### Task 3: Tentative events from fixtures + merge rule

**Files:**
- Create: `refresh/fixtures.py`
- Modify: `refresh/transform.py`
- Test: `tests/test_merge.py`

**Interfaces:**
- Consumes: `Event`, `SourceError`, `TEL_AVIV_CLUBS`, `TZ`, conftest `all_payloads`, `NOW`, `events_of`
- Produces: `refresh.fixtures.parse_fixtures(json_text: str) -> list[Event]` — the only module to replace when switching to the IFA PDF fallback.

- [ ] **Step 1: Write the failing tests**

`tests/test_merge.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_merge.py -q`
Expected: FAIL — no tentative events are produced (fixtures payloads are ignored).

- [ ] **Step 3: Implement the fixtures adapter**

`refresh/fixtures.py`:

```python
"""365scores fixtures adapter.

Designated replacement if this endpoint breaks: the Israel Football
Association's official fixture PDF. Swapping sources means replacing this
module only; it must keep returning tentative football Events.
"""

import json
from datetime import datetime

from refresh.config import TEL_AVIV_CLUBS, TZ
from refresh.model import Event, SourceError


def parse_fixtures(json_text: str) -> list[Event]:
    try:
        games = json.loads(json_text)["games"]
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise SourceError(f"fixtures feed is not the expected JSON: {e}") from e
    if not isinstance(games, list):
        raise SourceError("fixtures feed 'games' is not a list")

    events = []
    for game in games:
        try:
            home, away = game["homeCompetitor"], game["awayCompetitor"]
            if home["id"] not in TEL_AVIV_CLUBS:
                continue
            start = datetime.fromisoformat(game["startTime"]).astimezone(TZ)
            game_id = game["id"]
        except (KeyError, TypeError, ValueError) as e:
            raise SourceError(f"fixtures feed game is malformed: {e}") from e
        events.append(
            Event(
                id=f"365scores:{game_id}",
                date=start.date(),
                time=start.strftime("%H:%M"),
                title=f"{home['name']} – {away['name']}",
                kind="football",
                status="tentative",
                source="365scores",
                url=None,
            )
        )
    return events
```

- [ ] **Step 4: Apply the merge rule in build()**

In `refresh/transform.py`, add `from refresh.fixtures import parse_fixtures` and replace the body of `build` up to the `cutoff` line:

```python
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
```

(the `document = {...}` and `return` lines stay as they are).

- [ ] **Step 5: Run all tests**

Run: `uv run pytest -q`
Expected: `19 passed`.

- [ ] **Step 6: Commit**

```bash
git add refresh/fixtures.py refresh/transform.py tests/test_merge.py
git commit -m "feat: tentative home fixtures for Tel Aviv clubs, suppressed on confirmed days"
```

---

### Task 4: Fail loudly on bad payloads, succeed on empty ones

**Files:**
- Test: `tests/test_source_errors.py`
- Modify (only if a test fails): `refresh/venue.py`, `refresh/fixtures.py`

**Interfaces:**
- Consumes: `build`, `Payloads`, `SourceError`, conftest helpers
- Produces: guarantee that `build()` raises `SourceError` before returning anything if any payload is bad.

- [ ] **Step 1: Write the tests**

`tests/test_source_errors.py`:

```python
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
```

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test_source_errors.py -q`
Expected: all PASS with the code from Tasks 1–3 (icalendar raises `ValueError` on truncated/non-iCal input; `parse_fixtures` validates shape). If any case fails, add the missing check to the adapter it concerns — e.g. for a venue payload that parses but is not a calendar, add after `Calendar.from_ical`:

```python
    if calendar.name != "VCALENDAR":
        raise SourceError("venue feed is not a VCALENDAR")
```

and re-run until green.

- [ ] **Step 3: Run the whole suite and commit**

Run: `uv run pytest -q` → Expected: `28 passed`.

```bash
git add tests/test_source_errors.py refresh
git commit -m "test: bad source payloads raise, empty ones produce empty artifacts"
```

---

### Task 5: `bloomfield.ics` calendar feed

**Files:**
- Create: `refresh/ics.py`
- Modify: `refresh/transform.py`
- Test: `tests/test_ics.py`

**Interfaces:**
- Consumes: `Event`, `TZ`
- Produces: `refresh.ics.render_ics(events: list[Event], now: datetime) -> str`; `Artifacts` gains `ics: str`.

- [ ] **Step 1: Write the failing tests**

`tests/test_ics.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_ics.py -q`
Expected: FAIL with `AttributeError: 'Artifacts' object has no attribute 'ics'`.

- [ ] **Step 3: Implement rendering**

`refresh/ics.py`:

```python
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
```

In `refresh/transform.py`: add `from refresh.ics import render_ics`, add the field `ics: str` to `Artifacts`, and change the return to:

```python
    return Artifacts(
        events_json=json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        ics=render_ics([e for e in kept if e.status == "confirmed"], now),
    )
```

- [ ] **Step 4: Run all tests**

Run: `uv run pytest -q` → Expected: `32 passed`.

- [ ] **Step 5: Commit**

```bash
git add refresh/ics.py refresh/transform.py tests/test_ics.py
git commit -m "feat: bloomfield.ics feed of confirmed events with stable UIDs"
```

---

### Task 6: Refresh CLI (fetch → build → write)

**Files:**
- Create: `refresh/__main__.py`
- Create (generated): `site/events.json`, `site/bloomfield.ics`

**Interfaces:**
- Consumes: `build`, `Payloads`, `SourceError`, config URLs/ids, `USER_AGENT`
- Produces: `uv run python -m refresh [out_dir]` — exits non-zero and writes nothing on any failure; writes both artifacts to `site/` by default.

This wrapper is deliberately outside the tested seam (spec: HTTP and file writing are not unit-tested). Verification is a live run.

- [ ] **Step 1: Implement**

`refresh/__main__.py`:

```python
import sys
from datetime import datetime
from pathlib import Path

import httpx

from refresh.config import FIXTURES_URL, TEL_AVIV_CLUBS, TZ, USER_AGENT, VENUE_CALENDARS, VENUE_ICAL_URL
from refresh.model import SourceError
from refresh.transform import Payloads, build


def fetch(client: httpx.Client, url: str) -> str:
    response = client.get(url)
    if response.status_code != 200:
        raise SourceError(f"{url} answered HTTP {response.status_code}")
    return response.text


def main(out_dir: Path) -> None:
    with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        payloads = Payloads(
            venue={cid: fetch(client, VENUE_ICAL_URL.format(calendar_id=cid)) for cid in VENUE_CALENDARS},
            fixtures={club: fetch(client, FIXTURES_URL.format(club_id=club)) for club in TEL_AVIV_CLUBS},
        )
    artifacts = build(payloads, datetime.now(TZ))

    # Both artifacts exist in memory before either file is touched.
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in (("events.json", artifacts.events_json), ("bloomfield.ics", artifacts.ics)):
        tmp = out_dir / f".{name}.tmp"
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(out_dir / name)
    print(f"wrote {out_dir}/events.json and {out_dir}/bloomfield.ics")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("site"))
```

- [ ] **Step 2: Live run**

Run: `uv run python -m refresh`
Expected: `wrote site/events.json and site/bloomfield.ics`; `site/events.json` has `"version": 1` and at least the confirmed Bloomfield events after today−7.

- [ ] **Step 3: Verify failure leaves files untouched**

```bash
cp site/events.json /tmp/before.json
uv run python -c "import refresh.config as c; c.VENUE_ICAL_URL='https://www.sportpalace.co.il/definitely-missing-{calendar_id}'; import refresh.__main__ as m; from pathlib import Path; m.VENUE_ICAL_URL=c.VENUE_ICAL_URL; m.main(Path('site'))"; echo "exit=$?"
cmp site/events.json /tmp/before.json && echo unchanged
```

Expected: a `SourceError ... HTTP 404` traceback, `exit=1`, then `unchanged`.

- [ ] **Step 4: Commit**

```bash
git add refresh/__main__.py site/events.json site/bloomfield.ics
git commit -m "feat: refresh CLI fetching sources and writing artifacts atomically"
```

---

### Task 7: View model (Seam 2)

**Files:**
- Create: `package.json`, `site/view.js`, `site/view.test.js`

**Interfaces:**
- Consumes: the `events.json` contract from Tasks 1–5.
- Produces (ES module `site/view.js`):
  - `viewModel(data, now: Date) -> { today: { busy: boolean, isGame: boolean, events: Event[] }, next: { event: Event, relative: { type: 'today'|'tomorrow'|'weekday'|'date', weekday?: 0-6, date?: 'YYYY-MM-DD' } } | null, stale: boolean, generatedAt: string }`
  - `jerusalemDate(now: Date) -> 'YYYY-MM-DD'`, `jerusalemTime(now: Date) -> 'HH:MM'`

- [ ] **Step 1: Add the test runner config**

`package.json`:

```json
{
  "private": true,
  "type": "module",
  "scripts": {
    "test": "TZ=Pacific/Honolulu node --test site/"
  }
}
```

(Honolulu, UTC−10, makes any accidental use of device-local time fail the day-boundary tests.)

- [ ] **Step 2: Write the failing tests**

`site/view.test.js`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { viewModel } from './view.js';

const ev = (date, time, extra = {}) => ({
  id: `t:${date}:${time}`, date, time, title: `event ${date} ${time}`,
  kind: 'football', status: 'confirmed', source: 'sportpalace', url: null, ...extra,
});
const doc = (events, generated_at = '2026-10-09T06:00:00+03:00') =>
  ({ version: 1, generated_at, timezone: 'Asia/Jerusalem', sources: [], events });
const at = (iso) => new Date(iso);

test('confirmed event today answers yes', () => {
  const vm = viewModel(doc([ev('2026-10-10', '19:30')]), at('2026-10-10T10:00:00+03:00'));
  assert.equal(vm.today.busy, true);
  assert.equal(vm.today.isGame, true);
});

test('tentative event today does not answer yes', () => {
  const vm = viewModel(doc([ev('2026-10-10', '19:30', { status: 'tentative' })]), at('2026-10-10T10:00:00+03:00'));
  assert.equal(vm.today.busy, false);
});

test('concert today is an event, not a game', () => {
  const vm = viewModel(doc([ev('2026-10-10', '21:00', { kind: 'concert' })]), at('2026-10-10T10:00:00+03:00'));
  assert.equal(vm.today.busy, true);
  assert.equal(vm.today.isGame, false);
});

test('earlier event still answers yes late in the evening', () => {
  const vm = viewModel(doc([ev('2026-10-10', '15:45')]), at('2026-10-10T23:30:00+03:00'));
  assert.equal(vm.today.busy, true);
});

test('next event tomorrow is described as tomorrow', () => {
  const vm = viewModel(doc([ev('2026-10-10', '15:45')]), at('2026-10-09T23:00:00+03:00'));
  assert.equal(vm.today.busy, false);
  assert.equal(vm.next.event.date, '2026-10-10');
  assert.deepEqual(vm.next.relative, { type: 'tomorrow' });
});

test('next event 2-6 days out is described by weekday', () => {
  // Tue 2026-10-06 -> Sat 2026-10-10
  const vm = viewModel(doc([ev('2026-10-10', '19:30')]), at('2026-10-06T12:00:00+03:00'));
  assert.deepEqual(vm.next.relative, { type: 'weekday', weekday: 6 });
});

test('next event a week or more out is described by date', () => {
  const vm = viewModel(doc([ev('2026-10-17', '18:45')]), at('2026-10-10T12:00:00+03:00'));
  assert.deepEqual(vm.next.relative, { type: 'date', date: '2026-10-17' });
});

test('next event is shown even when there is an event today', () => {
  const data = doc([ev('2026-10-10', '19:30'), ev('2026-10-17', '18:45')]);
  const before = viewModel(data, at('2026-10-10T10:00:00+03:00'));
  assert.equal(before.next.event.date, '2026-10-10');
  assert.deepEqual(before.next.relative, { type: 'today' });
  const after = viewModel(data, at('2026-10-10T21:00:00+03:00'));
  assert.equal(after.today.busy, true);
  assert.equal(after.next.event.date, '2026-10-17');
});

test('tentative events are never the next event', () => {
  const data = doc([ev('2026-10-11', '19:00', { status: 'tentative' }), ev('2026-10-17', '18:45')]);
  const vm = viewModel(data, at('2026-10-10T12:00:00+03:00'));
  assert.equal(vm.next.event.date, '2026-10-17');
});

test('data older than two days is stale, recent data is not', () => {
  const now = at('2026-09-26T07:00:00+03:00');
  assert.equal(viewModel(doc([], '2026-09-24T06:00:00+03:00'), now).stale, true);
  assert.equal(viewModel(doc([], '2026-09-25T06:00:00+03:00'), now).stale, false);
});

test('today is the Jerusalem day, not the device day', () => {
  // 21:30Z on Oct 9 = 00:30 Oct 10 in Jerusalem = 11:30 Oct 9 in Honolulu
  const now = at('2026-10-09T21:30:00Z');
  assert.equal(viewModel(doc([ev('2026-10-10', '19:30')]), now).today.busy, true);
  assert.equal(viewModel(doc([ev('2026-10-09', '18:00')]), now).today.busy, false);
});

test('empty event list is coherent', () => {
  const vm = viewModel(doc([]), at('2026-10-10T12:00:00+03:00'));
  assert.deepEqual(vm.today, { busy: false, isGame: false, events: [] });
  assert.equal(vm.next, null);
  assert.equal(vm.stale, false);
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `npm test`
Expected: FAIL — `Cannot find module '.../site/view.js'`.

- [ ] **Step 4: Implement**

`site/view.js`:

```js
export const TIMEZONE = 'Asia/Jerusalem';
const STALE_AFTER_MS = 2 * 24 * 60 * 60 * 1000;

const dateFormat = new Intl.DateTimeFormat('en-CA', {
  timeZone: TIMEZONE, year: 'numeric', month: '2-digit', day: '2-digit',
});
const timeFormat = new Intl.DateTimeFormat('en-GB', {
  timeZone: TIMEZONE, hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
});

export const jerusalemDate = (now) => dateFormat.format(now);
export const jerusalemTime = (now) => timeFormat.format(now);

const dayNumber = (isoDate) => Date.parse(`${isoDate}T00:00:00Z`) / 86_400_000;

function relativeDay(today, date) {
  const days = dayNumber(date) - dayNumber(today);
  if (days === 0) return { type: 'today' };
  if (days === 1) return { type: 'tomorrow' };
  if (days < 7) return { type: 'weekday', weekday: new Date(`${date}T12:00:00Z`).getUTCDay() };
  return { type: 'date', date };
}

export function viewModel(data, now) {
  const today = jerusalemDate(now);
  const clock = jerusalemTime(now);
  const confirmed = data.events.filter((e) => e.status === 'confirmed');
  const todays = confirmed.filter((e) => e.date === today);
  const next = confirmed.find(
    (e) => e.date > today || (e.date === today && e.time !== null && e.time > clock),
  ) ?? null;
  return {
    today: { busy: todays.length > 0, isGame: todays.some((e) => e.kind === 'football'), events: todays },
    next: next && { event: next, relative: relativeDay(today, next.date) },
    stale: now.getTime() - Date.parse(data.generated_at) > STALE_AFTER_MS,
    generatedAt: data.generated_at,
  };
}
```

- [ ] **Step 5: Run tests**

Run: `npm test` → Expected: `# pass 12`, `# fail 0`.

- [ ] **Step 6: Commit**

```bash
git add package.json site/view.js site/view.test.js
git commit -m "feat: view model for today answer, next event and staleness"
```

---

### Task 8: Page shell — banner, next event, freshness, sources, language

**Files:**
- Create: `site/index.html`, `site/styles.css`, `site/app.js`

**Interfaces:**
- Consumes: `viewModel`, `jerusalemDate`, `TIMEZONE` from `./view.js`; `./events.json`
- Produces (in `app.js`, used by Task 9): `STRINGS` (per-language dictionary), `state = { lang, data, month }`, `render()`, `t(key)`; element `<section id="calendar">` left empty for Task 9.

Verification is by opening the page (DOM rendering is outside the tested seam).

- [ ] **Step 1: Write `site/index.html`**

```html
<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>יש משחק?</title>
  <link rel="stylesheet" href="styles.css">
  <link rel="alternate" type="text/calendar" href="bloomfield.ics">
</head>
<body>
  <header class="bar">
    <span class="brand" data-i18n="brand"></span>
    <button id="lang" type="button"></button>
  </header>
  <main>
    <p id="stale" class="warning" hidden></p>
    <section id="today" class="today" aria-live="polite"></section>
    <section id="next" class="next"></section>
    <section id="calendar" class="calendar"></section>
  </main>
  <footer>
    <p id="updated"></p>
    <p id="sources"></p>
    <p><a href="bloomfield.ics" data-i18n="subscribe"></a></p>
  </footer>
  <script type="module" src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write `site/styles.css`**

```css
:root {
  --bg: #f7f7f5; --fg: #1b1b1b; --muted: #666; --card: #fff; --line: #ddd;
  --yes: #c62828; --no: #2e7d32; --warn-bg: #fff3cd; --warn-fg: #664d03;
  --confirmed: #1565c0; --tentative: #8d6e63;
  font-family: system-ui, -apple-system, "Segoe UI", Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #121212; --fg: #eee; --muted: #aaa; --card: #1e1e1e; --line: #333;
    --yes: #ef5350; --no: #66bb6a; --warn-bg: #3d3200; --warn-fg: #ffe08a;
    --confirmed: #64b5f6; --tentative: #bcaaa4;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); line-height: 1.4; }
main, .bar, footer { max-width: 40rem; margin: 0 auto; padding: 0 16px; }
.bar { display: flex; justify-content: space-between; align-items: center; padding-block: 12px; }
.brand { font-weight: 700; }
button { font: inherit; background: var(--card); color: var(--fg); border: 1px solid var(--line); border-radius: 8px; padding: 6px 12px; min-height: 40px; cursor: pointer; }
.warning { background: var(--warn-bg); color: var(--warn-fg); padding: 10px 12px; border-radius: 8px; }
.today { text-align: center; padding: 28px 0 12px; }
.today .answer { font-size: clamp(2.5rem, 12vw, 4rem); font-weight: 800; margin: 0; }
.today.yes .answer { color: var(--yes); }
.today.no .answer { color: var(--no); }
.today ul { list-style: none; padding: 0; margin: 8px 0 0; }
.next { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 12px 16px; }
.next .label { color: var(--muted); font-size: .9rem; }
.next .what { font-weight: 600; }
footer { color: var(--muted); font-size: .85rem; padding-block: 24px; }
footer a { color: inherit; }
```

- [ ] **Step 3: Write `site/app.js`**

```js
import { viewModel, jerusalemDate, TIMEZONE } from './view.js';

export const STRINGS = {
  he: {
    dir: 'rtl', locale: 'he-IL', toggle: 'English', brand: 'יש משחק? · בלומפילד',
    yesGame: 'יש משחק', yesEvent: 'יש אירוע', no: 'אין משחק',
    next: 'האירוע הבא', noNext: 'אין אירועים מאושרים בקרוב',
    today: 'היום', tomorrow: 'מחר',
    stale: 'שימו לב: הנתונים לא עודכנו יותר מיומיים — ייתכן שהם לא מעודכנים.',
    updated: 'עודכן', sources: 'מקורות', subscribe: 'הוספה ליומן (iCal)',
    loadError: 'לא ניתן לטעון את הנתונים.',
    tentative: 'משוער', prevMonth: 'החודש הקודם', nextMonth: 'החודש הבא',
    football: '⚽', concert: '🎵', other: '•',
  },
  en: {
    dir: 'ltr', locale: 'en-GB', toggle: 'עברית', brand: 'Game on? · Bloomfield',
    yesGame: "There's a game", yesEvent: "There's an event", no: 'No game',
    next: 'Next event', noNext: 'No confirmed events coming up',
    today: 'Today', tomorrow: 'Tomorrow',
    stale: 'Heads up: data has not been refreshed for over two days and may be out of date.',
    updated: 'Updated', sources: 'Sources', subscribe: 'Add to calendar (iCal)',
    loadError: 'Could not load the data.',
    tentative: 'Tentative', prevMonth: 'Previous month', nextMonth: 'Next month',
    football: '⚽', concert: '🎵', other: '•',
  },
};

const LANG_KEY = 'yesh-mischak.lang';
const $ = (id) => document.getElementById(id);

function loadLang() {
  try { return localStorage.getItem(LANG_KEY) === 'en' ? 'en' : 'he'; } catch { return 'he'; }
}
function saveLang(lang) {
  try { localStorage.setItem(LANG_KEY, lang); } catch { /* private mode: not remembered */ }
}

export const state = { lang: loadLang(), data: null, month: jerusalemDate(new Date()).slice(0, 7) };
export const t = (key) => STRINGS[state.lang][key];

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => (k === 'class' ? (node.className = v) : node.setAttribute(k, v)));
  node.append(...children.filter((c) => c !== null && c !== undefined));
  return node;
}

export const eventLine = (e) => `${e.time ? e.time + ' · ' : ''}${e.title}`;

function relativeText({ type, weekday, date }) {
  const locale = t('locale');
  if (type === 'today') return t('today');
  if (type === 'tomorrow') return t('tomorrow');
  if (type === 'weekday') {
    // 2026-10-04 is a Sunday; offset gives the requested weekday.
    return new Date(Date.UTC(2026, 9, 4 + weekday, 12)).toLocaleDateString(locale, { weekday: 'long', timeZone: 'UTC' });
  }
  return new Date(`${date}T12:00:00Z`).toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC' });
}

function renderChrome() {
  document.documentElement.lang = state.lang;
  document.documentElement.dir = t('dir');
  document.title = t('brand');
  $('lang').textContent = t('toggle');
  document.querySelectorAll('[data-i18n]').forEach((n) => (n.textContent = t(n.dataset.i18n)));
}

function renderAnswer(vm) {
  const today = $('today');
  today.className = `today ${vm.today.busy ? 'yes' : 'no'}`;
  const answer = vm.today.busy ? (vm.today.isGame ? t('yesGame') : t('yesEvent')) : t('no');
  today.replaceChildren(
    el('p', { class: 'answer' }, answer),
    vm.today.busy ? el('ul', {}, ...vm.today.events.map((e) => el('li', {}, eventLine(e)))) : null,
  );

  const next = $('next');
  next.replaceChildren(
    el('div', { class: 'label' }, t('next')),
    vm.next
      ? el('div', { class: 'what' }, `${t(vm.next.event.kind)} ${relativeText(vm.next.relative)} · ${eventLine(vm.next.event)}`)
      : el('div', { class: 'what' }, t('noNext')),
  );

  $('stale').hidden = !vm.stale;
  $('stale').textContent = t('stale');
}

function renderFooter(data) {
  const when = new Date(data.generated_at).toLocaleString(t('locale'), {
    timeZone: TIMEZONE, dateStyle: 'medium', timeStyle: 'short',
  });
  $('updated').textContent = `${t('updated')}: ${when}`;
  $('sources').replaceChildren(
    `${t('sources')}: `,
    ...data.sources.flatMap((s, i) => [i ? ' · ' : '', el('a', { href: s.url, rel: 'noopener' }, s.name)]),
  );
}

// Task 9 replaces this with the month calendar.
export function renderCalendar() {}

export function render() {
  renderChrome();
  if (!state.data) return;
  renderAnswer(viewModel(state.data, new Date()));
  renderFooter(state.data);
  renderCalendar();
}

$('lang').addEventListener('click', () => {
  state.lang = state.lang === 'he' ? 'en' : 'he';
  saveLang(state.lang);
  render();
});

render();
try {
  const response = await fetch('events.json', { cache: 'no-cache' });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  state.data = await response.json();
  render();
} catch (error) {
  $('today').replaceChildren(el('p', { class: 'warning' }, t('loadError')));
  console.error(error);
}
```

- [ ] **Step 4: Verify in the browser**

Run: `python3 -m http.server 8000 -d site` (background), open `http://localhost:8000/`.
Check, at 375px width and at desktop width, in light and dark scheme:
- Hebrew, RTL, answer `אין משחק` or `יש משחק` matching today's confirmed events in `site/events.json`.
- Next-event card shows emoji + `מחר`/weekday/date + time + title.
- Footer shows update time in Jerusalem time and both source links.
- Toggle switches to English/LTR; reload keeps English.
- Temporarily edit `generated_at` in `site/events.json` to 3 days ago → warning shows; revert with `git checkout site/events.json`.
- No console errors.

- [ ] **Step 5: Commit**

```bash
git add site/index.html site/styles.css site/app.js
git commit -m "feat: page with today answer, next event, freshness and language toggle"
```

---

### Task 9: Month calendar

**Files:**
- Modify: `site/app.js` (replace the `renderCalendar` stub), `site/styles.css` (append)

**Interfaces:**
- Consumes: `state`, `t`, `el`, `eventLine`, `jerusalemDate` from Task 8.
- Produces: rendered `#calendar` with prev/next month navigation.

- [ ] **Step 1: Replace the stub in `site/app.js`**

Replace the two lines `// Task 9 replaces this with the month calendar.` / `export function renderCalendar() {}` with:

```js
function shiftMonth(month, delta) {
  const [y, m] = month.split('-').map(Number);
  const d = new Date(Date.UTC(y, m - 1 + delta, 1));
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
}

function monthDays(month) {
  const [y, m] = month.split('-').map(Number);
  const first = new Date(Date.UTC(y, m - 1, 1));
  const count = new Date(Date.UTC(y, m, 0)).getUTCDate();
  const blanks = first.getUTCDay(); // weeks start on Sunday
  const days = Array.from({ length: count }, (_, i) => `${month}-${String(i + 1).padStart(2, '0')}`);
  return { blanks, days };
}

export function renderCalendar() {
  const locale = t('locale');
  const [y, m] = state.month.split('-').map(Number);
  const title = new Date(Date.UTC(y, m - 1, 15)).toLocaleDateString(locale, { month: 'long', year: 'numeric', timeZone: 'UTC' });
  const today = jerusalemDate(new Date());
  const byDay = Map.groupBy(state.data.events, (e) => e.date);

  const nav = el('div', { class: 'cal-nav' },
    el('button', { type: 'button', 'aria-label': t('prevMonth'), 'data-shift': '-1' }, state.lang === 'he' ? '→' : '←'),
    el('h2', {}, title),
    el('button', { type: 'button', 'aria-label': t('nextMonth'), 'data-shift': '1' }, state.lang === 'he' ? '←' : '→'),
  );

  const weekdayNames = Array.from({ length: 7 }, (_, i) =>
    new Date(Date.UTC(2026, 9, 4 + i, 12)).toLocaleDateString(locale, { weekday: 'short', timeZone: 'UTC' }));
  const { blanks, days } = monthDays(state.month);

  const grid = el('ol', { class: 'cal-grid' },
    ...weekdayNames.map((n) => el('li', { class: 'cal-head', 'aria-hidden': 'true' }, n)),
    ...Array.from({ length: blanks }, () => el('li', { class: 'cal-blank', 'aria-hidden': 'true' })),
    ...days.map((date) => {
      const events = byDay.get(date) ?? [];
      const classes = ['cal-day'];
      if (date === today) classes.push('is-today');
      if (date < today) classes.push('is-past');
      if (events.some((e) => e.status === 'confirmed')) classes.push('has-confirmed');
      else if (events.length) classes.push('has-tentative');
      return el('li', { class: classes.join(' ') },
        el('span', { class: 'cal-num' }, String(Number(date.slice(8)))),
        ...events.map((e) => el('div', { class: `cal-event ${e.status}` },
          `${t(e.kind)} ${eventLine(e)}`,
          e.status === 'tentative' ? el('span', { class: 'cal-tag' }, t('tentative')) : null)),
      );
    }),
  );

  const section = document.getElementById('calendar');
  section.replaceChildren(nav, grid);
  section.querySelectorAll('[data-shift]').forEach((b) =>
    b.addEventListener('click', () => {
      state.month = shiftMonth(state.month, Number(b.dataset.shift));
      renderCalendar();
    }));
}
```

(`Map.groupBy` is available in all current evergreen browsers — Safari 17.4+, Chrome 117+.)

- [ ] **Step 2: Append calendar styles to `site/styles.css`**

```css
.calendar { margin-top: 20px; }
.cal-nav { display: flex; justify-content: space-between; align-items: center; }
.cal-nav h2 { font-size: 1.1rem; margin: 0; }
.cal-grid { list-style: none; padding: 0; margin: 8px 0 0; display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 3px; }
.cal-head { text-align: center; font-size: .75rem; color: var(--muted); }
.cal-day { background: var(--card); border: 1px solid var(--line); border-radius: 6px; min-height: 3.2rem; padding: 2px 3px; font-size: .68rem; overflow-wrap: anywhere; }
.cal-day.is-past { opacity: .6; }
.cal-day.is-today { outline: 2px solid var(--fg); }
.cal-day.has-confirmed { border-color: var(--confirmed); border-width: 2px; }
.cal-day.has-tentative { border-style: dashed; border-color: var(--tentative); }
.cal-num { font-weight: 700; font-size: .8rem; }
.cal-event { margin-top: 2px; }
.cal-event.confirmed { color: var(--confirmed); font-weight: 600; }
.cal-event.tentative { color: var(--tentative); font-style: italic; }
.cal-tag { display: inline-block; margin-inline-start: 3px; padding: 0 4px; border: 1px dashed var(--tentative); border-radius: 4px; font-style: normal; }
```

- [ ] **Step 3: Verify in the browser**

With the server from Task 8 running, reload `http://localhost:8000/`:
- Current month grid, week starting Sunday, today outlined, past days dimmed but visible.
- Confirmed days: solid blue border, bold entries. Tentative days: dashed border + word `משוער` / `Tentative`.
- Next-month button reaches November 2026 and shows tentative Maccabi/Hapoel home games; days with two events list both.
- Arrow direction feels right in both RTL and LTR; no horizontal scroll at 375px.
- In English the weekday headers and month title switch language; event titles stay Hebrew.

- [ ] **Step 4: Commit**

```bash
git add site/app.js site/styles.css
git commit -m "feat: month calendar distinguishing confirmed and tentative days"
```

---

### Task 10: CI — tests, daily refresh, Pages deploy, README

**Files:**
- Create: `.github/workflows/publish.yml`, `README.md`

**Interfaces:**
- Consumes: `uv run pytest`, `npm test`, `uv run python -m refresh`, `site/`.
- Produces: daily-refreshed public `…/events.json` and `…/bloomfield.ics` URLs.

- [ ] **Step 1: Write the workflow**

`.github/workflows/publish.yml`:

```yaml
name: publish

on:
  schedule:
    - cron: "0 3 * * *" # 06:00 Asia/Jerusalem in summer (IDT), 05:00 in winter
  workflow_dispatch:
  push:
    branches: [main]

permissions:
  contents: write
  pages: write
  id-token: write

concurrency:
  group: publish
  cancel-in-progress: false

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv run pytest -q
      - uses: actions/setup-node@v4
        with:
          node-version: 22
      - run: npm test

  refresh:
    needs: test
    if: github.event_name != 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv run python -m refresh
      - name: Commit artifacts if changed
        run: |
          git config user.name "yesh-mischak bot"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add site/events.json site/bloomfield.ics
          git diff --cached --quiet || { git commit -m "data: refresh $(TZ=Asia/Jerusalem date +%F)"; git push; }

  deploy:
    needs: [test, refresh]
    if: always() && needs.test.result == 'success' && needs.refresh.result != 'failure' && needs.refresh.result != 'cancelled'
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: main
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - id: deployment
        uses: actions/deploy-pages@v4
```

A failed `refresh` fails the run (GitHub emails the maintainer about failed scheduled runs by default) and skips `deploy`, so the last good artifacts stay live.

- [ ] **Step 2: Write `README.md`**

```markdown
# יש משחק

Is there an event at Bloomfield Stadium today? One static page, refreshed daily.

- Page: `https://<user>.github.io/yesh-mischak/`
- Data contract: `…/events.json` (version 1 — fields may be added, never renamed)
- Calendar feed (confirmed events only): `…/bloomfield.ics`
  Google Calendar → Other calendars → **From URL** → paste the feed URL. Set a reminder on that calendar for a day-ahead notification.

## How it works

`refresh/` fetches two sources once a day (GitHub Actions, 03:00 UTC), builds
`site/events.json` and `site/bloomfield.ics`, commits them and deploys `site/` to GitHub Pages.

| Source | Role | Horizon |
|---|---|---|
| sportpalace.co.il DPCalendar iCal (calendars 10 sport, 11 culture) | **confirmed**: venue says Bloomfield | 1–2 weeks |
| 365scores fixtures JSON, per club (Maccabi TA 566, Hapoel TA 567) | **tentative**: Tel Aviv home fixture | months |

Merge: venue events at Bloomfield are confirmed; home fixtures of the two clubs are tentative;
a day with a confirmed event drops its tentative ones. Nothing else.

Known, accepted quirks: European "home" ties played abroad and neutral-venue finals show as
tentative false positives; the venue feed's odd late-night times and duplicates are passed through.

## Fallback source

If the 365scores endpoint changes, breaks or becomes undesirable, replace it with the
Israel Football Association's official fixture PDF. Only `refresh/fixtures.py` changes.

## Develop

    uv run pytest          # build transform (offline, real captured fixtures)
    npm test               # view model
    uv run python -m refresh   # live refresh into site/
    python3 -m http.server 8000 -d site

Failure policy: any non-200, unparseable feed or transport error fails the run and commits
nothing; a successful run with zero events (off-season) is not a failure.

## Attribution

Event data: היכלי הספורט תל אביב (sportpalace.co.il) and 365Scores. Only bare facts
(date, time, participants) are stored. Non-commercial.
```

- [ ] **Step 3: Verify workflow syntax locally**

Run: `uv run --with pyyaml python -c "import yaml; d=yaml.safe_load(open('.github/workflows/publish.yml')); print(sorted(d['jobs']))"`
Expected: `['deploy', 'refresh', 'test']`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/publish.yml README.md
git commit -m "ci: daily refresh, tests and GitHub Pages deploy"
```

- [ ] **Step 5: Publish (needs the owner — outward-facing)**

Ask the owner before doing any of this:
1. `gh repo create yesh-mischak --public --source . --push`
2. Repo Settings → Pages → Source: **GitHub Actions**.
3. Actions → publish → **Run workflow**; confirm `test`, `refresh`, `deploy` all green and the page loads at the Pages URL.
4. Replace `<user>` in `README.md` and `USER_AGENT` in `refresh/config.py` with the real repo URL; commit.
5. Subscribe to `…/bloomfield.ics` in Google Calendar and confirm events appear.
```
