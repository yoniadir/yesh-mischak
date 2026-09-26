# Stadium pixel art — design

A pixel-art Bloomfield Stadium above today's answer: floodlights **on** when there is a
confirmed event today (game or not), **off** when there is none.

## Decisions

- Hand-coded inline SVG, no MCP, no image files, no new dependencies.
- Lights on for any confirmed event today (`vm.today.busy`), football or concert alike.
- Decorative only: the text answer stays the source of truth for assistive tech.

## Placement and wiring

- `site/index.html`: new `<figure id="stadium" class="stadium" aria-hidden="true" hidden>`
  directly before `#today`, containing the inline SVG.
- `site/app.js` `renderAnswer(vm)`: un-hide the figure and set
  `data-lights="on"` when `vm.today.busy`, else `"off"`.
- The figure stays hidden until data loads and stays hidden on load error, so "lights off"
  never implies "no game" when we simply don't know.

## Drawing

- `viewBox="0 0 64 32"`, `shape-rendering="crispEdges"`, pixels as `<rect>`s; scales to the
  column width (max 40rem) with a fixed aspect ratio.
- Night scene: sky, curved roof canopy over the two long stands, end stands, a strip of
  pitch, 4 floodlight masts with lamp heads.
- Classes drive the states: `.shade` (one night overlay over the whole scene), `.beam`,
  `.lamp`, `.window`, `.stars`.
- Seat accents in Tel Aviv yellow / blue / red.

## States (CSS only, in `site/styles.css`)

| Part | Off | On |
|---|---|---|
| Shade overlay | opacity .55 — stands, pitch and sky dimmed | opacity 0 — everything lit |
| Lamps | dark grey | warm yellow |
| Beams | opacity 0 | semi-transparent light falling onto the pitch |
| Facade windows | dark | warm yellow |
| Stars | bright | faded (light pollution) |

- Short transition between states.
- Slow, subtle lamp flicker when on, only under `prefers-reduced-motion: no-preference`.
- The scene is always night; only the surrounding card follows the page's light/dark tokens.

## Testing

- The lights state is `vm.today.busy`, already covered by `site/view.test.js`. Tests run
  in plain Node without a DOM, so no DOM test is added.
- Visual check in a browser: both states forced, mobile (375px) and desktop widths,
  light and dark schemes; no horizontal scroll; figure hidden before load and on load error.
