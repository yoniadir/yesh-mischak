# Apple HIG redesign — design

Restyle the page to follow Apple's Human Interface Guidelines (system colours, type styles,
grouped inset lists, 44pt targets, materials, safe areas) and replace the cramped month grid
with an Apple-Calendar-style view: dots in the cells, detail list for the selected day.
The pixel-art stadium stays as the hero.

## Decisions

- Full redesign, not polish only: the calendar cells (event titles wrapping one word per line
  in 7 narrow columns) cannot be fixed with styling alone.
- No new dependencies, no web fonts, no build step. System font stack only, so Apple devices
  get SF / SF Hebrew and others fall back gracefully.
- `events.json` contract, `bloomfield.ics`, `refresh/` and `tools/stadium.py` are untouched.
- Semantic meaning of colours is unchanged: red = game today, green = no game,
  blue = confirmed, orange = likely (tentative).

## Visual system (`site/styles.css`)

**Colour tokens** — Apple system colours, light and dark, defined on `:root` and overridden in
`@media (prefers-color-scheme: dark)`. Names mirror Apple's semantic colours:

| Token | Light | Dark |
|---|---|---|
| `--bg` (grouped background) | `#f2f2f7` | `#000000` |
| `--surface` (secondary grouped) | `#ffffff` | `#1c1c1e` |
| `--label` | `#000000` | `#ffffff` |
| `--label-2` | `rgb(60 60 67 / .6)` | `rgb(235 235 245 / .6)` |
| `--label-3` | `rgb(60 60 67 / .3)` | `rgb(235 235 245 / .3)` |
| `--separator` | `rgb(60 60 67 / .29)` | `rgb(84 84 88 / .6)` |
| `--fill` (tertiary fill) | `rgb(118 118 128 / .12)` | `rgb(118 118 128 / .24)` |
| `--red` | `#ff3b30` | `#ff453a` |
| `--green` | `#34c759` | `#30d158` |
| `--blue` | `#007aff` | `#0a84ff` |
| `--orange` | `#ff9500` | `#ff9f0a` |
| `--yellow-bg` / `--yellow-fg` | tinted from system yellow | tinted from system yellow |

Text colours used for body copy must meet WCAG AA (4.5:1) on their surface; the large answer
text and non-text indicators (dots) meet 3:1. Where a system colour is too light for small
text on white (green, orange), text uses a darker variant and the system colour is kept for
fills, dots and the large answer.

**Type** — `font-family: -apple-system, system-ui, "SF Pro Text", "Segoe UI", sans-serif`.
Sizes in `rem` so browser text scaling works (the web analogue of Dynamic Type):

| Style | Size / weight | Use |
|---|---|---|
| Large Title | `clamp(2.125rem, 10vw, 3rem)` / 700 | the answer |
| Title 2 | 1.375rem / 700 | month title |
| Headline | 1.0625rem / 600 | event title |
| Body | 1.0625rem / 400 | rows |
| Subheadline | .9375rem / 400 | secondary labels |
| Footnote | .8125rem / 400 | footer |
| Caption | .75rem / 500 | weekday heads |

Line-height ≈ 1.3, `-webkit-font-smoothing: antialiased`, `text-size-adjust: 100%`.

**Surfaces** — inset grouped cards: `--surface` background, 12px radius (16px for the hero
group), no border, rows separated by 0.5px `--separator` hairlines inset from the leading edge.
No drop shadows except the existing stadium art shadow.

**Header** — sticky, translucent navigation bar: `background: color-mix(in srgb, var(--bg) 72%, transparent)`,
`backdrop-filter: saturate(180%) blur(20px)` (with an opaque fallback under
`@supports not (backdrop-filter…)`), hairline bottom separator. Title left/leading, language
control trailing.

**Language control** — a two-segment control (`עברית | English`) instead of a one-button toggle:
`role="group"`, two buttons with `aria-pressed`, selected segment on a raised `--surface` pill
over a `--fill` track. Height 32px visual, 44px hit area via padding/`::before`.

**Interaction** — every control has a ≥44×44px hit area. `:active` dims to 60% (Apple's
highlight behaviour), `:focus-visible` shows a 2px `--blue` ring with offset, hover only under
`@media (hover: hover)`. Transitions ≤200ms, removed under `prefers-reduced-motion: reduce`.

**Viewport / safe areas** — `viewport-fit=cover`; `theme-color` meta pair for light/dark;
`padding-inline` and header/footer padding use `max(16px, env(safe-area-inset-*))`;
`color-scheme: light dark` retained. Content column stays centred, max about 40rem.

**Stale warning** — inline banner in a yellow-tinted grouped row with a warning glyph (CSS/inline
SVG, `aria-hidden`), text in `--yellow-fg`. `role="status"`.

## Structure and components

Markup (`site/index.html`) keeps the same landmarks and ids where possible
(`#stale`, `#stadium`, `#today`, `#next`, `#calendar`, `#updated`, `#sources`) so the stadium
generator markers and tests stay valid.

1. **Hero** — stadium figure, then the answer in Large Title, centred. Below it, today's
   events (when busy) as a grouped list: time (secondary, tabular numerals) and title per row.
2. **Next event** — grouped list section with a small section header ("האירוע הבא" /
   "Next event", Footnote, `--label-2`), one row: kind glyph in a rounded 30px tile,
   Headline title, Subheadline "relative day · time". No border box.
3. **Calendar** — one grouped card.
   - Header row: Title 2 month name, chevron buttons trailing (44×44, no border, `--blue`
     tinted, glyph mirrored in RTL so "previous" always points at the start edge), plus a
     "Today" text button shown when the visible month or selection differs from today.
   - Weekday row: Caption, `--label-2`, `aria-hidden`.
   - Day cells: `<button type="button">`, square, day number centred (tabular numerals).
     Below the number, up to two dots: solid `--blue` for a confirmed event, hollow
     `--orange` ring for likely. Today: number in a filled `--red` circle with white text.
     Selected day: `--fill` circle (or `--label` circle when it is not today). Past days at
     40% opacity but still selectable. No event text in cells.
   - Weeks start on Sunday (unchanged).
4. **Selected-day detail** — directly under the grid, in the same card after a hairline: date
   as Headline ("Saturday, 10 October"), then one row per event (kind glyph, title,
   time, and a "Likely" pill for tentative events, orange text on orange 15% fill). When the day
   has no events: "No events" in `--label-2`. Default selection: today if the visible month is
   the current month, else the first event day of that month, else nothing selected (detail row
   shows the month's summary line, "No events this month"). Changing month re-applies the default.
   Container is `aria-live="polite"`.
5. **Footer** — grouped list: a tappable row "Add to calendar (iCal)" with a trailing chevron
   (44px min height), then Footnote lines for updated time and sources.

Event rows are plain text; no new outbound links are added.

## Logic (`site/view.js`, `site/app.js`)

Pure, testable additions to `view.js`:

- `defaultSelection(events, month, today)` → ISO date string or `null`, implementing the rule
  above for a given visible month.
- `dayIndicators(events)` → `{ confirmed: boolean, tentative: boolean }` for a day's events
  (tentative dots only appear when the day has no confirmed event, matching the merge rule
  already in `refresh/`; the view does not re-merge, it just reads the data).

`app.js` keeps rendering: `state` gains `selected` (ISO date or null). Clicking a day sets
`state.selected` and re-renders only the calendar section. Month change calls
`defaultSelection`. Language switch keeps the selection. `renderAnswer` is unchanged apart from
class names and markup for the new hero/next components.

RTL: use logical properties (`margin-inline`, `padding-inline`, `inset-inline`, `text-align: start`)
throughout; chevron direction chosen in JS as today (`state.lang`), not by CSS transform.

## Accessibility

- Day buttons carry a full `aria-label`: "Saturday 10 October, today, 1 confirmed event" (in
  the active language), `aria-pressed` for selection, `aria-current="date"` for today.
- Grid remains a list of buttons in DOM order; arrow-key roving focus is a stretch goal, not
  required (Tab works through days).
- Colour is never the only carrier: confirmed = solid dot, likely = hollow ring, plus text
  labels in the detail list.
- Contrast targets above; `forced-colors` gets outlines on selected/today.
- Language segments and controls are real `<button>`s with names.
- Stadium art stays `aria-hidden`; the text answer remains the source of truth.

## Files touched

- `site/index.html` — meta (viewport-fit, theme-color), header markup, footer markup.
- `site/styles.css` — rewritten (the generated `stadium:start/end` block is preserved
  byte-for-byte).
- `site/app.js` — new render functions for hero rows, next row, calendar cells, detail list,
  language control; new strings (`noEventsDay`, `noEventsMonth`, `todayButton`, aria-label
  parts) in both languages.
- `site/view.js`, `site/view.test.js` — `defaultSelection`, `dayIndicators` + tests.
- Not touched: `refresh/`, `tools/`, `tests/`, `site/events.json`, `site/bloomfield.ics`,
  `site/stadium.svg`.

## Testing

- `npm test` (node --test): new unit tests for `defaultSelection` (current month with/without
  today events, other month with events, empty month, tentative-only days) and `dayIndicators`.
- `uv run pytest` must still pass unchanged (`test_stadium_art.py` checks the stadium markers
  in `index.html` / `styles.css` are unmodified).
- Manual visual pass with the local server (`python3 -m http.server 8000 -d site`) in:
  light/dark, Hebrew/English (RTL/LTR), 375px / 768px / 1280px widths, game day / no game /
  stale / load error states (by editing a copy of `events.json` and the system clock via
  devtools).

## Out of scope

- Changing the data model, refresh pipeline, ICS feed or stadium art.
- PWA manifest / installability, push notifications.
- Animations beyond simple state transitions.
- Arrow-key grid navigation and swipe-to-change-month (possible follow-ups).
