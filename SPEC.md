# יש משחק (yesh-mischak) — v1 Spec

## Problem Statement

I live next to Bloomfield Stadium in Tel Aviv. When there is a football match or
a concert there, my evening is disrupted — noise, crowds, traffic and no parking.
I find out by walking outside and discovering the street has filled up.

I want to know in advance — at least a week ahead — whether the stadium has an
event, so I can plan around it: move the car, schedule things elsewhere, or
simply not be surprised.

Today there is no single place that answers this. The venue's own site lists
events but is awkward to read and only covers the near term. League schedules
list matches but not where they are played. Concerts are announced separately
again. Nobody publishes "is Bloomfield busy this week" as one answer.

## Solution

A tiny web page that answers one question at a glance: **יש משחק / אין משחק**
— is there an event at Bloomfield today?

Underneath the answer, it always shows the next event, described in human terms
(today / tomorrow / a weekday name). Below that, a month calendar shows the full
picture, marking days that are **confirmed** (a source explicitly says the event
is at Bloomfield) distinctly from days that are **tentative** (a Tel Aviv club
has a home fixture, so an event is likely but the venue is not yet published).

A calendar feed (`bloomfield.ics`) carries the confirmed events only, so I can
subscribe to it from Google Calendar once and get the events — and reminders —
inside the calendar I already use. That subscription is the notification system
for v1; the app itself does not push.

The data is refreshed once a day by an automated job and published as static
files. There is no server to run and no account to create. If the refresh
breaks, the page keeps showing the last good data and says how old it is.

## User Stories

### Core question

1. As a neighbour of the stadium, I want to open one page and immediately see whether there is an event at Bloomfield today, so that I know whether tonight will be disrupted.
2. As a neighbour, I want the today answer to be based only on confirmed data, so that I never rearrange my evening because of a guess.
3. As a neighbour, I want the answer to stay "yes" for the whole calendar day even after the final whistle, so that I am not misled into thinking the streets have cleared while the crowds are still leaving.
4. As a neighbour, I want the next upcoming event shown at all times — not only when today is empty — so that at 23:00 I can already see tomorrow's 15:45 kickoff.
5. As a neighbour, I want the next event expressed as היום / מחר / a weekday name rather than a raw date, so that I can read it without doing mental arithmetic.
6. As a neighbour, I want to see the event's start time, so that I can judge when to move my car.
7. As a neighbour, I want to see what the event actually is — which teams, or which artist — so that I can gauge how big the crowd will be.
8. As a neighbour, I want to know at least a week ahead, so that I have time to act on the information.

### Calendar view

9. As a neighbour, I want a month calendar of stadium events, so that I can plan further ahead than just the next event.
10. As a neighbour, I want to move between months, so that I can check a date I care about that is further out.
11. As a neighbour, I want confirmed and tentative days to look clearly different, so that I know which entries I can rely on.
12. As a neighbour, I want tentative entries labelled in words (not only by colour), so that the distinction survives a glance on a phone in sunlight.
13. As a neighbour, I want a day with several events (an evening double-header, or consecutive concert nights) to show all of them, so that nothing is hidden.
14. As a neighbour, I want multi-day events such as a concert residency to appear on each affected day, so that a six-night run shows as six busy evenings rather than one.
15. As a neighbour, I want concerts and football distinguished, so that I can tell a league match from a music night.
16. As a neighbour, I want recent past days to still be visible, so that I can confirm whether last night's disruption was the stadium.

### Trust and freshness

17. As a neighbour, I want to see when the data was last refreshed, so that I know how much to trust it.
18. As a neighbour, I want a visible warning when the data is more than two days old, so that I do not read a stale "no event today" as reassurance.
19. As a neighbour, I want the page to keep showing the last good data when a source is broken, so that a failed refresh does not leave me with a blank page.
20. As a neighbour, I want to see which sources the answer came from, so that I can check the original myself when something looks wrong.
21. As the maintainer, I want to be emailed automatically when the daily refresh fails, so that I find out before the data goes stale.
22. As the maintainer, I want an off-season with no events not to count as a failure, so that I am not alerted about a correct empty result.

### Calendar integration

23. As a Google Calendar user, I want to subscribe to a stable calendar feed URL once, so that stadium events appear alongside the rest of my life without any further action.
24. As a Google Calendar user, I want only confirmed events in the feed, so that my calendar is never polluted with events that turn out to be elsewhere.
25. As a Google Calendar user, I want each calendar entry to carry the real event title and start time, so that the entry is meaningful without opening the app.
26. As a Google Calendar user, I want to set my own reminder on the subscribed calendar, so that I get notified a day ahead without the app needing push notifications.
27. As an Apple Calendar user, I want the same feed to work in my calendar app, so that I am not tied to Google.

### Language and device

28. As a Hebrew speaker, I want the interface in Hebrew with right-to-left layout, so that it reads naturally alongside the Hebrew event titles.
29. As an English speaker, I want to switch the interface to English, so that I can share the page with someone who does not read Hebrew.
30. As a returning visitor, I want my language choice remembered, so that I do not re-pick it on every visit.
31. As a phone user, I want the page to be legible and usable at phone width, so that I can check it on the way home.
32. As a phone user, I want the page to load fast on a mobile connection, so that checking it is quicker than asking someone.
33. As a user, I want the page to work in dark mode, so that it is not blinding at night.

### Data correctness

34. As a neighbour, I want events at Bloomfield to be included regardless of which club is playing, so that a Beitar Jerusalem match relocated to Bloomfield still warns me.
35. As a neighbour, I want tentative guesses restricted to the two clubs whose home ground this actually is, so that the calendar is not filled with speculative matches for visiting clubs.
36. As a neighbour, I want a confirmed event on a day to suppress that day's tentative entries, so that the same match is not listed twice.
37. As a neighbour, I want non-football events at the stadium included, so that a concert night warns me as clearly as a derby.
38. As a neighbour, I want cup ties and European nights included in the tentative view, so that the biggest crowds are not the ones I find out about last.

### Future platforms

39. As a future iOS app, I want a single stable JSON URL as my only dependency, so that I can be built without duplicating any ingestion logic.
40. As a future home-screen widget, I want the today answer derivable from that same file, so that the widget and the web page can never disagree.

## Implementation Decisions

### Sources

- **Venue feed (authoritative).** The sportpalace.co.il DPCalendar iCal export, two calendars: sport events and culture events. Each event carries an explicit venue display name, so Bloomfield events are selected by matching that field against the stadium's Hebrew name. This feed is the only source of truth for *confirmed* events. Its horizon is roughly one to two weeks.
- **Fixtures feed (supplementary).** The 365scores web JSON fixtures endpoint, queried **by competitor** rather than by competition — one request per Tel Aviv club. A per-club query returns every competition the club is in (league, Toto Cup, State Cup, European competitions) without maintaining a list of competition ids, and new competitions appear automatically. Its horizon is several months, but it publishes a venue only for the current round.
- **Fallback, not implemented in v1.** The Israel Football Association publishes the official fixture list as a PDF. It is recorded in the README as the designated replacement should the 365scores endpoint change, break, or become undesirable to use. Switching sources must not require changes outside the fixtures-feed adapter.
- Source URLs, the two club identifiers, the two calendar identifiers and the stadium name are configuration constants, not scattered literals.

### Merge rule

Deliberately minimal — three rules, applied at **day** resolution:

1. A venue-feed event whose venue is Bloomfield becomes a `confirmed` event, taken as-is.
2. A fixtures-feed game whose **home** competitor is one of the two Tel Aviv clubs becomes a `tentative` event. All competitions qualify, including European ties.
3. If a day already has at least one confirmed event, that day's tentative events are discarded.

No team-name aliasing between sources, no cross-source time reconciliation, no
fuzzy matching, no deduplication beyond rule 3. This was chosen over a more
accurate merge explicitly for simplicity: the confirmed layer is correct by
construction, and the tentative layer is labelled as a guess.

Accepted consequences, recorded so they are not later mistaken for bugs:

- European "home" ties may be played abroad for security reasons, and neutral-venue cup finals may be played elsewhere. These appear as tentative false positives beyond the confirmed window. Accepted in exchange for a single uniform rule.
- The venue feed contains some implausible kickoff times (late-night and midnight values, apparently a timezone handling error at the source) and occasional duplicate entries. These are passed through unmodified.

### Output artifacts

Two files, regenerated wholesale on each run and published as static assets:

- **`events.json`** — the single contract for every client, present and future. Contains a generation timestamp and a list of events. Each event carries: date, start time, title, kind (football / concert / other), status (confirmed / tentative), originating source, and a link to the source page where one exists. Events are sorted by date and time. Multi-day source events are expanded into one entry per affected day. The window is all future events plus a trailing seven days of past events, which keeps the file small.
- **`bloomfield.ics`** — an iCalendar feed containing **confirmed events only**, intended for subscribe-by-URL in Google Calendar or Apple Calendar. Each event uses a stable identifier so that repeated refreshes update rather than duplicate entries in subscribers' calendars. Times are emitted in the Asia/Jerusalem timezone.

Both files are committed to the repository and served as static files from the
project's published site, so the "file retrieved from the server" is a plain URL
with no backend.

### Timezone and the meaning of "today"

- All date reasoning uses **Asia/Jerusalem**, regardless of the viewer's device timezone or where the refresh job runs.
- "Today" means the calendar day in that timezone, at whole-day resolution. An event that has already finished still makes the day count as an event day.
- The today / next-event determination happens **in the browser at page-open time**, not at build time. A flag precomputed during the 06:00 refresh would be wrong for anyone opening the page after midnight.

### Refresh job

- Runs on the repository's own CI on a daily schedule at 06:00 Asia/Jerusalem, and can also be triggered manually.
- Written in Python, managed with `uv`, with pinned dependencies for HTTP and iCalendar handling. Python was chosen over alternatives for the smallest amount of tooling to maintain: no build step, no package manifest ceremony, and terse HTTP/iCal/JSON handling. The choice is independent of the future native app, which shares no code with the job.
- The job fetches, transforms, writes both artifacts, and commits them only if they changed.
- **Failure policy.** A non-200 response, an unparseable feed, or a transport error fails the run loudly; CI emails the maintainer on failure. A run that fails commits nothing, leaving the previous good artifacts in place. A successful run that yields zero events is **not** a failure — that is the correct answer during the off-season.

### Web client

- A single static HTML page with vanilla JavaScript and no framework and no build step. A framework was rejected because the eventual native client will be SwiftUI reading the same JSON, so shared JavaScript abstractions would buy nothing.
- Three regions, top to bottom: the today banner, the next confirmed event, and a month calendar.
- The banner and the next-event line are derived from **confirmed events only**. Tentative events appear exclusively in the calendar, visually and textually distinguished.
- Bilingual Hebrew / English with a toggle, Hebrew being the default and driving right-to-left layout. Event titles come from the sources and remain in their original language in both modes. The chosen language persists locally per browser.
- Mobile-first layout; the page is expected to be opened on a phone.
- A staleness warning is shown when the generation timestamp is more than two days old.
- The page fetches `events.json` from a relative path, so the same page works locally and when published.

### Client contract

`events.json` is a versioned, public contract. Fields may be added; existing
field names and meanings may not change without a deliberate version bump,
because the future iOS app and widget will read the same file.

## Testing Decisions

### What makes a good test here

A good test in this project asserts on **the artifacts a consumer sees** —
the contents of `events.json`, the contents of `bloomfield.ics`, and the answer
shown to the reader — given a known set of source payloads and a known current
time. It does not reach inside the transform to assert on intermediate parsing
steps, helper functions or data structures, because those are the parts most
likely to be rewritten while the behaviour stays the same.

Both seams are pure functions with time injected as a parameter. No test mocks
the network, patches the clock, or touches the filesystem.

### Seam 1 — the build transform (Python)

The entire ingestion pipeline is expressed as one pure function taking the raw
source payloads and the current time, and returning the two output artifacts.
HTTP fetching, file writing and the CI wrapper sit outside this seam and are not
tested.

Test inputs are the **real captured responses** from all four source requests
(two venue-feed calendars, two per-club fixture feeds), saved as fixture files,
together with a frozen timestamp. Covered behaviour:

- Only Bloomfield events are selected from the venue feed; events at the other venues in the same calendars are excluded.
- Both venue calendars contribute, so concerts appear alongside football.
- A home fixture for either Tel Aviv club becomes tentative; an away fixture for those clubs does not; a fixture between two other clubs does not.
- A confirmed event on a day suppresses that day's tentative events, while tentative events on other days survive.
- A confirmed event for a club other than the two Tel Aviv clubs is still included when the venue feed says Bloomfield.
- Multi-day source events expand to one entry per day.
- The output window includes future events and the trailing seven days, and excludes older ones.
- Events are ordered by date and time.
- The generated iCalendar contains every confirmed event, no tentative event, stable identifiers, and Asia/Jerusalem times.
- A malformed or truncated source payload raises rather than silently producing a partial artifact.
- A source payload containing no Bloomfield events produces a valid, empty result rather than an error.

### Seam 2 — the view model (JavaScript)

The reader-facing determination is a pure function taking the parsed
`events.json` and the current time, and returning what the page should say:
the today answer, the next event with its relative-day description, and whether
the data is stale. The DOM rendering that consumes it is outside the seam and is
verified by opening the page.

This seam exists despite the preference for a single seam, because this is the
logic behind the product's central promise — that the today answer is never
wrong — and it cannot live in the Python seam: it must be evaluated when the
page is opened, not when the file is built.

Covered behaviour:

- A confirmed event today yields the affirmative answer; a tentative event today does not.
- An event earlier today still yields the affirmative answer late in the evening.
- With no event today, the next confirmed event is reported, described as tomorrow when it falls on the following day and by weekday name beyond that.
- The next-event line is present even when there is an event today.
- Tentative events are never chosen as the next event.
- A generation timestamp older than two days is reported as stale; a recent one is not.
- Times are interpreted in Asia/Jerusalem irrespective of the simulated device timezone, including across a day boundary.
- An empty event list produces a coherent result rather than an error.

### Prior art

None — this is a greenfield repository with no existing tests to imitate. These
two seams establish the pattern: pure function, real captured fixtures, injected
time, assertions on consumer-visible output.

### Live sources

The sources are deliberately **not** contacted from the test suite, which keeps
it fast, offline and deterministic. The daily refresh job serves as the live
contract check: if a source changes shape, the run fails and the maintainer is
emailed.

## Out of Scope

- **Native iOS application and home-screen widget.** Planned as the next phase. Their only dependency will be the published `events.json` URL; no ingestion logic will be duplicated into them.
- **Push notifications of any kind.** The calendar subscription provides reminders for v1.
- **Any server-side component, database, user accounts, or per-user preferences** beyond the locally remembered language choice.
- **Writing events directly into a Google Calendar via its API.** Subscribe-by-URL achieves the same outcome without OAuth, credentials or a stored token.
- **A long-term historical archive** of past events. Only a trailing seven days is retained.
- **Correcting the venue feed's implausible kickoff times or duplicate entries.**
- **Cross-source reconciliation of kickoff times**, team-name alias tables, or fuzzy matching between sources.
- **Other venues**, including the other halls in the same venue-feed calendars.
- **Crowd-size estimation, traffic or parking prediction**, or any modelling of how disruptive a given event will be.
- **Implementing the Israel Football Association PDF fallback.** Documented as the designated replacement, not built.
- **Internationalisation beyond Hebrew and English**, and translation of event titles.

## Further Notes

**Naming.** The project is named יש משחק ("there's a game") — the sentence the
app exists to say. The name is narrower than the product, which also covers
concerts; when the event is not football the interface says יש אירוע ("there's
an event"). This was a deliberate choice: the name reflects the common case and
how the answer is said out loud.

**Legal posture.** The venue feed is an iCalendar export the venue's operator
publishes deliberately; polling it once a day is its intended use. The fixtures
feed is the undocumented JSON endpoint the 365scores website calls for itself,
and automated use is very likely contrary to its terms. The project accepts this
with mitigations: one request per club per day, storage of bare facts only
(date, time, participants, venue) rather than any editorial content, visible
attribution of both sources on the page, no monetisation, and the IFA fallback
documented should the situation change. This was raised with and accepted by the
project owner.

**Repository is public**, which is required for free static hosting. Nothing
personal is published — the artifacts contain only public stadium events, and no
address, location or account information appears anywhere in the repository.

**Cost.** Everything runs on free tiers: CI minutes are unlimited for public
repositories and the job takes about a minute a day; static hosting for public
repositories is free. There is no paid dependency anywhere in the design.

**Why the confirmed / tentative split exists at all.** The venue feed alone
answers "today?" and "next event?" correctly but goes blank beyond one to two
weeks, which fails the stated requirement of at least a week of warning with no
margin. The fixtures feed alone knows months ahead but not where the match is
played. Neither source answers the question; the split is what lets one page be
both reliable in the near term and useful further out, without ever presenting a
guess as a fact.
