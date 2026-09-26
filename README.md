# יש משחק

Is there an event at Bloomfield Stadium today? One static page, refreshed daily.

- Page: `https://yoniadir.github.io/yesh-mischak/`
- Data contract: `…/events.json` (version 1 — fields may be added, never renamed)
- Calendar feed (confirmed events only): `…/bloomfield.ics`
  Google Calendar → Other calendars → **From URL** → paste the feed URL. Set a reminder on that calendar for a day-ahead notification.

## First-time setup

Before the first run, enable Pages on the repo: Settings → Pages → Source = **GitHub Actions**.

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
nothing; a successful run with zero events (off-season) is not a failure. Failure emails
follow the maintainer's own GitHub Actions notification settings — no separate alerting is
configured.

The ICS feed and `events.json` keep only the last 7 days of past events, so older events
drop out of subscribed calendars by design.

## Attribution

Event data: היכלי הספורט תל אביב (sportpalace.co.il) and 365Scores. Only bare facts
(date, time, participants) are stored. Non-commercial.
