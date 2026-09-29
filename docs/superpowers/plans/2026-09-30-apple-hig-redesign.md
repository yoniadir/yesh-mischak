# Apple HIG Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle the page to Apple's Human Interface Guidelines and replace the cramped month grid with dots-plus-selected-day-detail.

**Architecture:** `view.js` gains two pure helpers (`dayIndicators`, `defaultSelection`) tested with `node --test`. `styles.css` is rewritten around Apple semantic colour tokens and grouped inset lists (the generated stadium block is preserved byte-for-byte). `app.js` renders the new hero/next/footer/calendar markup and keeps a `state.selected` date.

**Tech Stack:** Static HTML, CSS custom properties, ES modules, `node --test`. No new dependencies.

Spec: `docs/superpowers/specs/2026-09-30-apple-hig-redesign-design.md`

## Global Constraints

- `events.json` contract, `bloomfield.ics`, `refresh/`, `tools/`, `tests/`, `site/stadium.svg` are not modified.
- The `/* stadium:start … stadium:end */` block in `site/styles.css` and the `<!-- stadium:start -->…<!-- stadium:end -->` block in `site/index.html` stay byte-identical (`python3 tools/stadium.py --check` must pass).
- No web fonts, no build step, no new dependencies.
- Colour meaning: red = game today, green = no game, blue = confirmed, orange = likely.
- Every control has a hit area of at least 44×44px.
- Logical CSS properties (`inline-start/end`) for RTL/LTR.
- Existing ids stay: `#stale #stadium #today #next #calendar #updated #sources #lang`.
- Commit messages end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

---

### Task 1: View helpers `dayIndicators` and `defaultSelection`

**Files:**
- Modify: `site/view.js` (append)
- Test: `site/view.test.js` (append; update import line 3)

**Interfaces:**
- Produces: `dayIndicators(events: Event[]) -> { confirmed: boolean, tentative: boolean }` (tentative is true only if the day has a tentative event and no confirmed event).
- Produces: `defaultSelection(events: Event[], month: 'YYYY-MM', today: 'YYYY-MM-DD') -> 'YYYY-MM-DD' | null` (today if it is in `month`; else the earliest event date in `month`; else `null`).

- [ ] **Step 1: Write the failing tests**

Change line 3 of `site/view.test.js` to:

```js
import { viewModel, dayIndicators, defaultSelection } from './view.js';
```

Append:

```js
test('dayIndicators: confirmed wins over tentative', () => {
  assert.deepEqual(dayIndicators([]), { confirmed: false, tentative: false });
  assert.deepEqual(dayIndicators([ev('2026-10-10', '19:30')]), { confirmed: true, tentative: false });
  assert.deepEqual(dayIndicators([ev('2026-10-10', null, { status: 'tentative' })]), { confirmed: false, tentative: true });
  assert.deepEqual(
    dayIndicators([ev('2026-10-10', null, { status: 'tentative' }), ev('2026-10-10', '19:30')]),
    { confirmed: true, tentative: false },
  );
});

test('defaultSelection: today when the visible month is the current month', () => {
  assert.equal(defaultSelection([], '2026-10', '2026-10-10'), '2026-10-10');
  assert.equal(defaultSelection([ev('2026-10-20', '19:30')], '2026-10', '2026-10-10'), '2026-10-10');
});

test('defaultSelection: first event day of another month, in date order', () => {
  const events = [ev('2026-11-20', '19:30'), ev('2026-11-05', null, { status: 'tentative' }), ev('2026-12-01', '19:30')];
  assert.equal(defaultSelection(events, '2026-11', '2026-10-10'), '2026-11-05');
});

test('defaultSelection: nothing selected in an empty other month', () => {
  assert.equal(defaultSelection([ev('2026-12-01', '19:30')], '2026-11', '2026-10-10'), null);
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test`
Expected: FAIL with `does not provide an export named 'dayIndicators'`.

- [ ] **Step 3: Implement**

Append to `site/view.js`:

```js
export function dayIndicators(events) {
  const confirmed = events.some((e) => e.status === 'confirmed');
  return { confirmed, tentative: !confirmed && events.some((e) => e.status === 'tentative') };
}

export function defaultSelection(events, month, today) {
  if (today.startsWith(month)) return today;
  const dates = events.filter((e) => e.date.startsWith(month)).map((e) => e.date).sort();
  return dates[0] ?? null;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test`
Expected: all tests pass (no failures).

- [ ] **Step 5: Commit**

```bash
git add site/view.js site/view.test.js
git commit -m "feat: view helpers for calendar day indicators and default selection

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Apple visual system, header, hero, next event, footer

**Files:**
- Modify: `site/index.html` (everything outside the stadium markers)
- Modify: `site/styles.css` (rewrite; preserve the generated block)
- Modify: `site/app.js` (strings, `renderChrome`, `renderAnswer`, `renderFooter`, language handler, `load` error banner)

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: CSS classes used by Task 3: `.group`, `.list`, `.row`, `.tile`, `.row-main`, `.row-title`, `.row-sub`, `.pill`, `.chev`, `.pt-start`, `.pt-end`, `.icon-btn`, `.text-btn`. JS helper `eventRow(e, { showStatus, lead })` and `fullDate(date)` in `app.js`. Colour tokens `--surface --label --label-2 --label-3 --separator --fill --red --green --blue --orange` plus `--red-text --green-text --blue-text --orange-text --today-bg`.

- [ ] **Step 1: Save the generated stadium CSS block**

```bash
mkdir -p "$TMPDIR/hig" && awk '/\/\* stadium:start/{p=1} p{print}' site/styles.css > "$TMPDIR/hig/stadium-block.css"
head -c 120 "$TMPDIR/hig/stadium-block.css"; tail -n 1 "$TMPDIR/hig/stadium-block.css"
```
Expected: starts with `/* stadium:start — generated by tools/stadium.py */`, last line `/* stadium:end */`.

- [ ] **Step 2: Rewrite `site/index.html`**

Replace the file with (the two lines between `stadium:start`/`stadium:end` markers must remain exactly as in the current file):

```html
<!doctype html>
<html lang="he" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="color-scheme" content="light dark">
  <meta name="theme-color" content="#f2f2f7" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
  <title>יש משחק?</title>
  <link rel="stylesheet" href="styles.css">
  <link rel="alternate" type="text/calendar" href="bloomfield.ics">
</head>
<body>
  <header class="bar">
    <div class="bar-inner">
      <span class="brand" data-i18n="brand"></span>
      <div id="lang" class="segmented" role="group" aria-label="שפה / Language">
        <button type="button" data-lang="he" lang="he">עברית</button>
        <button type="button" data-lang="en" lang="en">English</button>
      </div>
    </div>
  </header>
  <main>
    <p id="stale" class="banner" role="status" hidden></p>
    <figure id="stadium" class="stadium" aria-hidden="true" hidden>
      <!-- stadium:start -->
      <svg viewBox="0 0 118 106" width="118" height="106" shape-rendering="crispEdges" focusable="false"><use href="stadium.svg#art"/></svg>
      <!-- stadium:end -->
    </figure>
    <section id="today" class="today" aria-live="polite"></section>
    <section id="next" class="next"></section>
    <section id="calendar" class="calendar"></section>
  </main>
  <footer>
    <ul class="group">
      <li><a class="row row-link" href="bloomfield.ics"><span class="row-main" data-i18n="subscribe"></span><span class="chev pt-end" aria-hidden="true"></span></a></li>
    </ul>
    <p id="updated"></p>
    <p id="sources"></p>
  </footer>
  <script type="module" src="app.js"></script>
</body>
</html>
```

Verify the stadium markers are untouched: `python3 tools/stadium.py --check` → exit 0 (it may print nothing).

- [ ] **Step 3: Rewrite `site/styles.css` (head part)**

Write this to `$TMPDIR/hig/head.css`, then `cat "$TMPDIR/hig/head.css" "$TMPDIR/hig/stadium-block.css" > site/styles.css`.

```css
:root {
  color-scheme: light dark;
  --bg: #f2f2f7; --surface: #fff; --seg-selected: #fff;
  --label: #000; --label-2: rgb(60 60 67 / .6); --label-3: rgb(60 60 67 / .3);
  --separator: rgb(60 60 67 / .29); --fill: rgb(118 118 128 / .12);
  --red: #ff3b30; --green: #34c759; --blue: #007aff; --orange: #ff9500;
  --red-text: #d70015; --green-text: #1f7a37; --blue-text: #0062cc; --orange-text: #b35c00;
  --today-bg: #dc1f2e;
  --yellow-bg: rgb(255 204 0 / .2); --yellow-fg: #6b4e00;
  font-family: -apple-system, system-ui, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #000; --surface: #1c1c1e; --seg-selected: #636366;
    --label: #fff; --label-2: rgb(235 235 245 / .6); --label-3: rgb(235 235 245 / .3);
    --separator: rgb(84 84 88 / .6); --fill: rgb(118 118 128 / .24);
    --red: #ff453a; --green: #30d158; --blue: #0a84ff; --orange: #ff9f0a;
    --red-text: #ff453a; --green-text: #30d158; --blue-text: #0a84ff; --orange-text: #ff9f0a;
    --today-bg: #dc1f2e;
    --yellow-bg: rgb(255 214 10 / .18); --yellow-fg: #ffd60a;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }
body { margin: 0; background: var(--bg); color: var(--label); font-size: 1.0625rem; line-height: 1.3; -webkit-font-smoothing: antialiased; }
main, .bar-inner, footer { max-width: 40rem; margin-inline: auto; padding-inline: max(16px, env(safe-area-inset-left), env(safe-area-inset-right)); }
[hidden] { display: none !important; }

button { font: inherit; color: inherit; background: none; border: 0; padding: 0; cursor: pointer; -webkit-tap-highlight-color: transparent; transition: opacity .15s, background-color .15s; }
button:active, a.row:active { opacity: .6; }
:focus-visible { outline: 2px solid var(--blue); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }

/* navigation bar */
.bar { position: sticky; top: 0; z-index: 10; padding-top: env(safe-area-inset-top); background: var(--bg); border-bottom: .5px solid var(--separator); }
@supports ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .bar { background: color-mix(in srgb, var(--bg) 72%, transparent); -webkit-backdrop-filter: saturate(180%) blur(20px); backdrop-filter: saturate(180%) blur(20px); }
}
.bar-inner { display: flex; justify-content: space-between; align-items: center; gap: 12px; min-height: 52px; }
.brand { font-weight: 600; }
.segmented { display: inline-flex; padding: 2px; background: var(--fill); border-radius: 9px; }
.segmented button { position: relative; min-width: 44px; min-height: 32px; padding: 0 12px; border-radius: 7px; font-size: .8125rem; font-weight: 500; }
.segmented button::before { content: ""; position: absolute; inset: -6px 0; }
.segmented button[aria-pressed="true"] { background: var(--seg-selected); font-weight: 600; box-shadow: 0 1px 3px rgb(0 0 0 / .12), 0 0 0 .5px rgb(0 0 0 / .04); }

/* stale banner */
.banner { display: flex; gap: 10px; align-items: flex-start; margin: 12px 0 0; padding: 12px 14px; border-radius: 12px; background: var(--yellow-bg); color: var(--yellow-fg); font-size: .9375rem; }
.banner::before { content: "!"; flex: none; width: 20px; height: 20px; border-radius: 50%; background: var(--yellow-fg); color: var(--surface); font-weight: 700; font-size: .8125rem; line-height: 20px; text-align: center; }

/* hero */
.stadium { width: min(13rem, 42vw, 30vh); margin: 12px auto 0; filter: drop-shadow(0 1px 2px rgb(0 0 0 / .25)); }
.stadium svg { display: block; width: 100%; height: auto; }
.today { text-align: center; padding-top: 8px; }
.answer { margin: 0; font-size: clamp(2.125rem, 10vw, 3rem); font-weight: 700; line-height: 1.1; letter-spacing: -.01em; }
.today.yes .answer { color: var(--red-text); }
.today.no .answer { color: var(--green-text); }
.today .group { margin-top: 16px; text-align: start; }

/* grouped lists */
.list, .group { list-style: none; margin: 0; padding: 0; }
.group { background: var(--surface); border-radius: 12px; overflow: hidden; }
.section-title { margin: 24px 16px 6px; font-size: .8125rem; font-weight: 400; color: var(--label-2); }
.row { position: relative; display: flex; align-items: center; gap: 12px; min-height: 44px; padding: 10px 16px; font-size: 1.0625rem; color: inherit; text-decoration: none; }
.row:has(.tile) { --row-inset: 58px; }
li + li > .row::before, .row + .row::before { content: ""; position: absolute; top: 0; inset-inline: var(--row-inset, 16px) 0; height: .5px; background: var(--separator); }
.row-plain { color: var(--label-2); }
.tile { flex: none; display: grid; place-items: center; width: 30px; height: 30px; border-radius: 7px; background: var(--fill); font-size: 1rem; }
.row-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.row-title { font-weight: 600; overflow-wrap: anywhere; }
.row-sub { font-size: .9375rem; color: var(--label-2); font-variant-numeric: tabular-nums; }
.pill { flex: none; padding: 2px 8px; border-radius: 999px; background: rgb(255 149 0 / .15); color: var(--orange-text); font-size: .75rem; font-weight: 600; }
.row-link .row-main { flex-direction: row; }

/* chevrons: points toward the end edge (pt-end) or the start edge (pt-start) */
.chev { display: block; flex: none; width: 10px; height: 10px; border-top: 2.5px solid currentColor; border-right: 2.5px solid currentColor; }
.row-link .chev { color: var(--label-3); }
.pt-end { transform: rotate(45deg); }
[dir="rtl"] .pt-end { transform: rotate(-135deg); }
.pt-start { transform: rotate(-135deg); }
[dir="rtl"] .pt-start { transform: rotate(45deg); }
.icon-btn { display: grid; place-items: center; min-width: 44px; min-height: 44px; border-radius: 22px; color: var(--blue); }
.text-btn { min-height: 44px; padding: 0 8px; color: var(--blue-text); font-size: 1.0625rem; }

/* footer */
footer { padding-block: 24px max(24px, env(safe-area-inset-bottom)); color: var(--label-2); font-size: .8125rem; }
footer .group { margin-bottom: 12px; }
footer p { margin: 8px 16px 0; }
footer p a { color: var(--blue-text); }

/* legacy calendar (replaced in the calendar task) */
.calendar { margin-top: 20px; }
.cal-nav { display: flex; justify-content: space-between; align-items: center; }
.cal-nav h2 { font-size: 1.1rem; margin: 0; }
.cal-nav button { border: 1px solid var(--separator); border-radius: 8px; padding: 6px 12px; min-height: 44px; }
.cal-grid { list-style: none; padding: 0; margin: 8px 0 0; display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 3px; }
.cal-head { text-align: center; font-size: .75rem; color: var(--label-2); }
.cal-day { background: var(--surface); border: 1px solid var(--separator); border-radius: 6px; min-height: 3.2rem; padding: 2px 3px; font-size: .68rem; overflow-wrap: anywhere; min-width: 0; }
.cal-event.confirmed { color: var(--blue-text); font-weight: 600; }
.cal-event.tentative { color: var(--orange-text); font-style: italic; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }

```

- [ ] **Step 4: Update `site/app.js` strings and chrome**

In `STRINGS`, remove the `toggle` key from both languages. Then apply these changes:

Replace the two-line comment-free `eventLine` export with:

```js
const fullDate = (date) => new Date(`${date}T12:00:00Z`).toLocaleDateString(t('locale'), {
  weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC',
});

export function eventRow(e, { showStatus = false, lead = null } = {}) {
  const sub = [lead, e.time].filter(Boolean).join(' · ');
  return el('li', { class: 'row' },
    el('span', { class: 'tile', 'aria-hidden': 'true' }, t(e.kind)),
    el('span', { class: 'row-main' },
      el('span', { class: 'row-title' }, el('bdi', {}, e.title)),
      sub ? el('span', { class: 'row-sub' }, sub) : null),
    showStatus && e.status === 'tentative' ? el('span', { class: 'pill' }, t('tentative')) : null);
}
```

`renderChrome`: replace the `$('lang').textContent = t('toggle');` line with:

```js
  document.querySelectorAll('#lang [data-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === state.lang)));
```

`renderAnswer`: replace the `today.replaceChildren(…)` and `next.replaceChildren(…)` statements with:

```js
  today.replaceChildren(
    el('p', { class: 'answer' }, answer),
    ...(vm.today.busy ? [el('ul', { class: 'group' }, ...vm.today.events.map((e) => eventRow(e)))] : []),
  );

  const next = $('next');
  next.replaceChildren(
    el('h2', { class: 'section-title' }, t('next')),
    el('ul', { class: 'group' },
      vm.next
        ? eventRow(vm.next.event, { lead: relativeText(vm.next.relative) })
        : el('li', { class: 'row row-plain' }, t('noNext'))),
  );
```
(Delete the old `const next = $('next');` line that preceded the old statement, so it is declared once.)

Language handler: replace `$('lang').addEventListener('click', …)` block with:

```js
document.querySelectorAll('#lang [data-lang]').forEach((b) => b.addEventListener('click', () => {
  if (state.lang === b.dataset.lang) return;
  state.lang = b.dataset.lang;
  saveLang(state.lang);
  render();
}));
```

`load()` error banner: change `el('p', { class: 'warning' }, t('loadError'))` to `el('p', { class: 'banner' }, t('loadError'))`.

The legacy calendar in `renderCalendar` still calls `eventLine`; change that one use to keep the file working until Task 3:
replace `...eventLine(e)` with `e.time ? \`${e.time} · \` : '', el('bdi', {}, e.title)` in the `cal-event` div.

- [ ] **Step 5: Run checks**

Run: `npm test && python3 tools/stadium.py --check && node --check site/app.js 2>&1 | head`
Expected: tests pass, stadium check exits 0 (`node --check` on an ES module may warn; ignore if only about module syntax — the browser check in the next step is authoritative).

- [ ] **Step 6: Visual check**

Run: `python3 -m http.server 8000 -d site` (background), open `http://localhost:8000/` at 375px. Confirm: translucent header with segmented עברית|English control (Hebrew pressed), stale banner (if data older than 2 days), stadium, large green answer, "האירוע הבא" section with one grouped row, footer grouped row with chevron pointing left in RTL. Click "English": layout flips to LTR, chevron points right. Console has no errors.

- [ ] **Step 7: Commit**

```bash
git add site/index.html site/styles.css site/app.js
git commit -m "feat: Apple HIG visual system, header, hero, next-event row and footer

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Calendar with dots and selected-day detail

**Files:**
- Modify: `site/app.js` (strings, `renderCalendar`, click handling, `load`)
- Modify: `site/styles.css` (replace the "legacy calendar" section)
- Modify: `docs/superpowers/specs/2026-09-30-apple-hig-redesign-design.md` (record deviations)

**Interfaces:**
- Consumes: `dayIndicators`, `defaultSelection` (Task 1); `eventRow`, `fullDate` and CSS classes (Task 2).
- Produces: `state.selected: string | null`; `renderCalendar(focusSelector?: string)`.

- [ ] **Step 1: Add strings**

In `STRINGS.he` add:

```js
    noEventsDay: 'אין אירועים ביום זה', noEventsMonth: 'אין אירועים החודש',
    confirmedCount: (n) => (n === 1 ? 'אירוע מאושר אחד' : `${n} אירועים מאושרים`),
    likelyCount: (n) => (n === 1 ? 'אירוע משוער אחד' : `${n} אירועים משוערים`),
```

In `STRINGS.en` add:

```js
    noEventsDay: 'No events', noEventsMonth: 'No events this month',
    confirmedCount: (n) => (n === 1 ? '1 confirmed event' : `${n} confirmed events`),
    likelyCount: (n) => (n === 1 ? '1 likely event' : `${n} likely events`),
```

- [ ] **Step 2: Replace `renderCalendar` and add event handling**

Update the import: `import { viewModel, jerusalemDate, TIMEZONE, dayIndicators, defaultSelection } from './view.js';`
and `export const state = { lang: loadLang(), data: null, month: jerusalemDate(new Date()).slice(0, 7), selected: null };`

Replace the whole `renderCalendar` function with:

```js
export function renderCalendar(focusSelector) {
  const locale = t('locale');
  const [y, m] = state.month.split('-').map(Number);
  const title = new Date(Date.UTC(y, m - 1, 15)).toLocaleDateString(locale, { month: 'long', year: 'numeric', timeZone: 'UTC' });
  const today = jerusalemDate(new Date());
  const byDay = groupByDate(state.data.events);
  const chev = (dir) => el('span', { class: `chev ${dir}`, 'aria-hidden': 'true' });

  const nav = el('div', { class: 'cal-nav' },
    el('h2', {}, title),
    state.month !== today.slice(0, 7) || state.selected !== today
      ? el('button', { type: 'button', class: 'text-btn', 'data-today': '' }, t('today')) : null,
    el('button', { type: 'button', class: 'icon-btn', 'aria-label': t('prevMonth'), 'data-shift': '-1' }, chev('pt-start')),
    el('button', { type: 'button', class: 'icon-btn', 'aria-label': t('nextMonth'), 'data-shift': '1' }, chev('pt-end')),
  );

  const weekdayNames = Array.from({ length: 7 }, (_, i) =>
    new Date(Date.UTC(2026, 9, 4 + i, 12)).toLocaleDateString(locale, { weekday: 'short', timeZone: 'UTC' }));
  const { blanks, days } = monthDays(state.month);

  const grid = el('ol', { class: 'cal-grid', 'aria-label': title },
    ...weekdayNames.map((n) => el('li', { class: 'cal-head', 'aria-hidden': 'true' }, n)),
    ...Array.from({ length: blanks }, () => el('li', { class: 'cal-blank', 'aria-hidden': 'true' })),
    ...days.map((date) => {
      const events = byDay.get(date) ?? [];
      const { confirmed, tentative } = dayIndicators(events);
      const classes = ['cal-day'];
      if (date === today) classes.push('is-today');
      if (date < today) classes.push('is-past');
      const confirmedCount = events.filter((e) => e.status === 'confirmed').length;
      const likelyCount = events.length - confirmedCount;
      const label = [
        fullDate(date),
        date === today ? t('today') : null,
        confirmedCount ? t('confirmedCount')(confirmedCount) : null,
        likelyCount ? t('likelyCount')(likelyCount) : null,
      ].filter(Boolean).join(', ');
      return el('li', {},
        el('button', {
          type: 'button', class: classes.join(' '), 'data-date': date, 'aria-label': label,
          'aria-pressed': String(date === state.selected), ...(date === today ? { 'aria-current': 'date' } : {}),
        },
        el('span', { class: 'cal-num', 'aria-hidden': 'true' }, String(Number(date.slice(8)))),
        el('span', { class: 'cal-dots', 'aria-hidden': 'true' },
          confirmed ? el('i', { class: 'dot confirmed' }) : null,
          tentative ? el('i', { class: 'dot tentative' }) : null)));
    }),
  );

  const selectedEvents = state.selected ? byDay.get(state.selected) ?? [] : [];
  const detail = el('div', { class: 'cal-detail', 'aria-live': 'polite' },
    state.selected ? el('h3', {}, fullDate(state.selected)) : null,
    selectedEvents.length
      ? el('ul', { class: 'list' }, ...selectedEvents.map((e) => eventRow(e, { showStatus: true })))
      : el('p', { class: 'cal-empty' }, state.selected ? t('noEventsDay') : t('noEventsMonth')));

  $('calendar').replaceChildren(el('div', { class: 'group cal-card' }, nav, grid, detail));
  if (focusSelector) $('calendar').querySelector(focusSelector)?.focus();
}

$('calendar').addEventListener('click', (event) => {
  const button = event.target.closest('button');
  if (!button || !state.data) return;
  const today = jerusalemDate(new Date());
  if (button.dataset.date) {
    state.selected = button.dataset.date;
    renderCalendar(`[data-date="${state.selected}"]`);
  } else if (button.dataset.shift) {
    state.month = shiftMonth(state.month, Number(button.dataset.shift));
    state.selected = defaultSelection(state.data.events, state.month, today);
    renderCalendar(`[data-shift="${button.dataset.shift}"]`);
  } else if (button.hasAttribute('data-today')) {
    state.month = today.slice(0, 7);
    state.selected = today;
    renderCalendar(`[data-date="${today}"]`);
  }
});
```

In `load()`, right after `state.data = await response.json();` add:

```js
    if (state.selected === null) state.selected = defaultSelection(state.data.events, state.month, jerusalemDate(new Date()));
```

- [ ] **Step 3: Replace the legacy calendar CSS**

In `site/styles.css`, delete everything from `/* legacy calendar` up to (not including) `/* stadium:start`, and insert:

```css
/* calendar */
.calendar { margin-top: 24px; }
.cal-card { border-radius: 16px; padding-bottom: 0; }
.cal-nav { display: flex; align-items: center; padding: 4px 8px 0 16px; }
.cal-nav h2 { flex: 1; margin: 0; font-size: 1.375rem; font-weight: 700; }
.cal-grid { list-style: none; margin: 0; padding: 0 8px 8px; display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); row-gap: 2px; }
.cal-head { padding: 6px 0; text-align: center; font-size: .75rem; font-weight: 500; color: var(--label-2); }
.cal-day { width: 100%; min-height: 48px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; border-radius: 8px; }
.cal-num { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; font-size: 1.0625rem; font-variant-numeric: tabular-nums; }
.cal-dots { display: flex; gap: 3px; height: 7px; }
.dot { display: block; width: 7px; height: 7px; border-radius: 50%; }
.dot.confirmed { background: var(--blue); }
.dot.tentative { border: 1.5px solid var(--orange); }
.cal-day.is-past .cal-num { color: var(--label-2); }
.cal-day.is-today .cal-num { color: var(--red-text); font-weight: 600; }
.cal-day[aria-pressed="true"] .cal-num { background: var(--label); color: var(--surface); font-weight: 600; }
.cal-day.is-today[aria-pressed="true"] .cal-num { background: var(--today-bg); color: #fff; }
@media (hover: hover) { .cal-day:hover .cal-num { background: var(--fill); } .cal-day[aria-pressed="true"]:hover .cal-num { background: var(--label); } .cal-day.is-today[aria-pressed="true"]:hover .cal-num { background: var(--today-bg); } }
.cal-detail { border-top: .5px solid var(--separator); }
.cal-detail h3 { margin: 0; padding: 14px 16px 4px; font-size: 1.0625rem; font-weight: 600; }
.cal-empty { margin: 0; padding: 10px 16px 16px; color: var(--label-2); }
@media (forced-colors: active) {
  .cal-day[aria-pressed="true"] .cal-num, .cal-day.is-today .cal-num { outline: 2px solid Highlight; }
  .dot.confirmed { background: CanvasText; }
  .dot.tentative { border-color: CanvasText; }
}
```
(`.sr-only` is no longer used and goes away with the legacy block.)

- [ ] **Step 4: Run checks**

Run: `npm test && python3 tools/stadium.py --check`
Expected: pass / exit 0. Then `uv run pytest -q` → all pass.

- [ ] **Step 5: Visual and interaction check**

At 375px: today (30 Sep) is a red number, empty-month/day detail reads "אין אירועים ביום זה", "היום" button hidden. Tap next month → October, selection becomes 10 Oct (first event day), heading + row with ⚽ tile show, "היום" button appears, dots on event days; tap the "היום" button → back to September with today selected. Keyboard: Tab to a day, Enter selects, focus stays on that day. Repeat in English (LTR) and in dark mode. In the console (`const m = await import('/app.js')`) set `m.state.data.events.push({id:'x',date:m.state.data.generated_at.slice(0,10),...})` is not needed; instead test game-day by pushing an event dated today then `m.render()` and check red answer + lights on + today's list.

- [ ] **Step 6: Record deviations in the spec**

In `docs/superpowers/specs/2026-09-30-apple-hig-redesign-design.md` make these edits: "up to two dots" → "one dot (confirmed solid, or likely ring when the day has no confirmed event)"; selected/today styling → "today's number is red, selected non-today day is a `--label` circle with inverted text, selected today is a red circle"; "Past days at 40% opacity" → "Past days use `--label-2` number colour"; "glyph mirrored in JS" → "chevron direction via `.pt-start/.pt-end` and `[dir=rtl]` in CSS".

- [ ] **Step 7: Commit**

```bash
git add site docs
git commit -m "feat: Apple-style month calendar with dots and selected-day detail

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Contrast audit and final verification

**Files:** none expected (fixes only if the audit fails)

- [ ] **Step 1: Contrast check**

Write `$TMPDIR/hig/contrast.mjs` computing WCAG ratios and run it:

```js
const lum = (hex) => { const c = [1,3,5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => (v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4)); return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]; };
const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return ((x + .05) / (y + .05)).toFixed(2); };
const pairs = [
  ['light green-text on bg', '#1f7a37', '#f2f2f7', 3], ['light red-text on bg', '#d70015', '#f2f2f7', 3],
  ['light blue-text on surface', '#0062cc', '#ffffff', 4.5], ['light orange-text on surface', '#b35c00', '#ffffff', 4.5],
  ['white on today-bg', '#ffffff', '#dc1f2e', 4.5], ['dark green on black', '#30d158', '#000000', 3],
  ['dark blue on surface', '#0a84ff', '#1c1c1e', 4.5], ['dark orange on surface', '#ff9f0a', '#1c1c1e', 4.5],
];
for (const [name, fg, bg, min] of pairs) console.log(ratio(fg, bg) >= min ? 'ok  ' : 'FAIL', name, ratio(fg, bg), `(min ${min})`);
```
Run: `node "$TMPDIR/hig/contrast.mjs"`. Expected: every line `ok`. If one fails, darken that token in `styles.css` until it passes and re-run.

- [ ] **Step 2: Full verification**

Run: `npm test && uv run pytest -q && python3 tools/stadium.py --check`
Expected: all pass. Screenshot pass at 375px, 768px, 1280px in light and dark, Hebrew and English; check no horizontal scroll (`document.documentElement.scrollWidth <= innerWidth`) and no console errors.

- [ ] **Step 3: Commit any fixes**

```bash
git add -A site
git commit -m "fix: contrast adjustments from audit

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```
(Skip if there is nothing to commit.)
