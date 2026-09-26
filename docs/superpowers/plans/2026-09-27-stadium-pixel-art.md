# Stadium Pixel Art Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show a pixel-art Bloomfield Stadium above today's answer whose floodlights are on when there is a confirmed event today and off otherwise.

**Architecture:** A hand-coded 64×32 inline SVG lives in `site/index.html` inside a hidden `<figure id="stadium">`. `renderAnswer` in `site/app.js` un-hides it and sets `data-lights="on|off"` from `vm.today.busy`. All on/off visuals are CSS in `site/styles.css` keyed on that attribute.

**Tech Stack:** Static HTML/CSS/vanilla ES modules, GitHub Pages. Tests: `node --test` (no DOM) via `npm test`.

**Spec:** `docs/superpowers/specs/2026-09-26-stadium-pixel-art-design.md`

## Global Constraints

- No new dependencies, no image files, no build step.
- Lights on iff `vm.today.busy` (any confirmed event today, football or not).
- Figure is decorative: `aria-hidden="true"`; the text answer is unchanged.
- Figure stays `hidden` until data loads and stays hidden if the first load fails.
- Scene is always night; only the card border uses the page's theme tokens.
- Flicker animation only under `prefers-reduced-motion: no-preference`.
- Mobile: no horizontal scroll at 375px.
- Do not set `display` on `.stadium` (it would defeat the `hidden` attribute).

---

### Task 1: Stadium figure, lights states and wiring

**Files:**
- Modify: `site/index.html` (insert figure before `<section id="today" …>`)
- Modify: `site/styles.css` (append stadium rules)
- Modify: `site/app.js` (`renderAnswer`, top of function)

**Interfaces:**
- Consumes: `vm.today.busy` (boolean) from `viewModel()` in `site/view.js`, already tested in `site/view.test.js`.
- Produces: `#stadium` element with `data-lights` = `"on"` | `"off"`; SVG classes `.shade`, `.beam`, `.lamp`, `.window`, `.stars`.

There is no DOM test harness (tests run in plain Node), and the lights logic is exactly `vm.today.busy`, which existing tests cover. Verification for this task is the existing suite plus the browser checks in Task 2.

- [ ] **Step 1: Add the figure to `site/index.html`**

Insert directly before `<section id="today" class="today" aria-live="polite"></section>`:

```html
    <figure id="stadium" class="stadium" aria-hidden="true" hidden>
      <svg viewBox="0 0 64 32" width="64" height="32" shape-rendering="crispEdges" focusable="false" xmlns="http://www.w3.org/2000/svg">
        <rect width="64" height="32" fill="#141b3d"/>
        <path class="stars" d="M3 5h1v1H3z M14 2h1v1h-1z M27 4h1v1h-1z M35 1h1v1h-1z M50 3h1v1h-1z M62 6h1v1h-1z M46 6h1v1h-1z"/>
        <path fill="#6b7280" d="M6 3h1v10H6z M22 3h1v10h-1z M41 3h1v10h-1z M57 3h1v10h-1z"/>
        <!-- far stand: curved roof over three seat sections -->
        <path fill="#dfe3ea" d="M20 6h24v1H20z M12 7h40v1H12z M6 8h52v1H6z"/>
        <rect x="8" y="9" width="16" height="8" fill="#c62828"/>
        <rect x="24" y="9" width="16" height="8" fill="#1e5bb8"/>
        <rect x="40" y="9" width="16" height="8" fill="#f2c230"/>
        <path fill="#000" fill-opacity=".2" d="M8 10h48v1H8z M8 12h48v1H8z M8 14h48v1H8z M8 16h48v1H8z"/>
        <path fill="#9aa1ad" d="M16 9h1v8h-1z M32 9h1v8h-1z M48 9h1v8h-1z"/>
        <!-- pitch with mowing stripes, halfway line and goals -->
        <g class="pitch">
          <rect x="4" y="17" width="56" height="6" fill="#3a9d45"/>
          <path fill="#33903e" d="M8 17h4v6H8z M16 17h4v6h-4z M24 17h4v6h-4z M32 17h4v6h-4z M40 17h4v6h-4z M48 17h4v6h-4z M56 17h4v6h-4z"/>
          <path fill="#e8f5e9" d="M31 17h1v6h-1z M4 19h1v2H4z M59 19h1v2h-1z"/>
        </g>
        <!-- near stand: curved roof edge and facade with windows -->
        <path fill="#dfe3ea" d="M8 22h48v1H8z M0 23h64v1H0z"/>
        <rect y="24" width="64" height="8" fill="#4a505c"/>
        <path class="window" d="M3 26h2v1H3z M7 26h2v1H7z M11 26h2v1h-2z M15 26h2v1h-2z M19 26h2v1h-2z M23 26h2v1h-2z M27 26h2v1h-2z M31 26h2v1h-2z M35 26h2v1h-2z M39 26h2v1h-2z M43 26h2v1h-2z M47 26h2v1h-2z M51 26h2v1h-2z M55 26h2v1h-2z M59 26h2v1h-2z M3 29h2v1H3z M7 29h2v1H7z M11 29h2v1h-2z M15 29h2v1h-2z M19 29h2v1h-2z M23 29h2v1h-2z M27 29h2v1h-2z M31 29h2v1h-2z M35 29h2v1h-2z M39 29h2v1h-2z M43 29h2v1h-2z M47 29h2v1h-2z M51 29h2v1h-2z M55 29h2v1h-2z M59 29h2v1h-2z"/>
        <!-- night overlay, then light on top of it -->
        <rect class="shade" width="64" height="32"/>
        <g class="beam">
          <polygon points="5,3 8,3 30,20 16,20"/>
          <polygon points="21,3 24,3 36,20 22,20"/>
          <polygon points="40,3 43,3 42,20 28,20"/>
          <polygon points="56,3 59,3 48,20 34,20"/>
        </g>
        <path class="lamp" d="M5 1h3v2H5z M21 1h3v2h-3z M40 1h3v2h-3z M56 1h3v2h-3z"/>
      </svg>
    </figure>
```

- [ ] **Step 2: Append stadium styles to `site/styles.css`**

```css
.stadium { max-width: 30rem; margin: 16px auto 0; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; background: #070a1c; }
.stadium svg { display: block; width: 100%; height: auto; }
.stadium .shade { fill: #070a1c; opacity: .55; }
.stadium .beam { fill: #fff6c2; opacity: 0; }
.stadium .lamp { fill: #3b4150; }
.stadium .window { fill: #262b36; }
.stadium .stars { fill: #fff; opacity: .9; }
.stadium .shade, .stadium .beam, .stadium .lamp, .stadium .window, .stadium .stars { transition: opacity .6s, fill .6s; }
.stadium[data-lights="on"] .shade { opacity: 0; }
.stadium[data-lights="on"] .beam { opacity: .22; }
.stadium[data-lights="on"] .lamp { fill: #ffe066; }
.stadium[data-lights="on"] .window { fill: #ffd966; }
.stadium[data-lights="on"] .stars { opacity: .35; }
@media (prefers-reduced-motion: no-preference) {
  .stadium[data-lights="on"] .lamp { animation: flicker 3.2s ease-in-out infinite; }
}
@keyframes flicker { 50% { opacity: .82; } }
```

- [ ] **Step 3: Wire the state in `site/app.js`**

At the top of `renderAnswer(vm)`, before `const today = $('today');`:

```js
  const stadium = $('stadium');
  stadium.hidden = false;
  stadium.dataset.lights = vm.today.busy ? 'on' : 'off';
```

- [ ] **Step 4: Run the existing suites**

Run: `npm test && uv run pytest -q`
Expected: all pass (no behaviour change to `viewModel` or the refresh pipeline).

- [ ] **Step 5: Commit**

```bash
git add site/index.html site/styles.css site/app.js
git commit -m "feat: pixel-art stadium with floodlights for today's answer"
```

### Task 2: Visual verification

**Files:** none (fix-ups go back into the Task 1 files and get their own commit).

- [ ] **Step 1: Serve the site**

Run in background: `python3 -m http.server 8000 -d site`, then open `http://localhost:8000/` in the browser pane.

- [ ] **Step 2: Check both states**

In the page console: `document.getElementById('stadium').dataset.lights = 'on'`, screenshot; then `'off'`, screenshot.
Expected: off — dim scene, dark lamps, no beams, dark windows, bright stars. On — lit stands and green pitch, yellow lamps, visible beams onto the pitch, yellow windows, faded stars. The real state matches today's data (`events.json`).

- [ ] **Step 3: Check sizes and themes**

Resize to mobile (375×812) and desktop; switch color scheme light/dark.
Expected: pixels crisp (not blurred), no horizontal scroll (`document.documentElement.scrollWidth <= innerWidth`), card border follows theme, answer text still visible without excessive scrolling on mobile.

- [ ] **Step 4: Check hidden-before-load and load-error**

Copy `site/` to the scratchpad without `events.json`, serve on port 8001, open it.
Expected: `#stadium` has `hidden`, load-error text is shown.

- [ ] **Step 5: Commit any fix-ups**

```bash
git add site/
git commit -m "fix: stadium visual tweaks"
```
(Skip if nothing changed.)
