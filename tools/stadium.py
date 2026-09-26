"""Generate the pixel-art Bloomfield Stadium as site/stadium.svg.

The stadium is modelled in metres (x east, y north, z up, origin at the centre spot),
projected from an elevated camera south of the ground looking north, and sampled onto a
pixel grid. A second, translucent layer holds the floodlight beams.

Every colour is a CSS custom property (`--st-<key>`) with an "off" and an "on" value. The
page references the art with `<use href="stadium.svg#art">`; custom properties inherit
into it, so `#stadium[data-lights]` in styles.css switches the lights. Besides the SVG,
this writes the <use> snippet in index.html and the colour block in styles.css, each
between `stadium:start` / `stadium:end` markers.

    uv run python tools/stadium.py           # rewrite the three generated parts
    uv run python tools/stadium.py --check   # exit 1 if any of them is out of date
"""
import math
import sys
from pathlib import Path

ELEVATION = math.radians(48)   # camera angle above the horizon
DISTANCE = 260                 # camera distance in metres, for mild perspective
SCALE = 0.6                    # grid pixels per metre
MARGIN = 2                     # empty pixels around the stadium

# (lights off, lights on)
LIT = {
    'roof': ('#4a505d', '#f1f3f7'), 'roof2': ('#3a3f4b', '#cdd3dd'),
    'glow': ('#2b2f3a', '#ffd98a'), 'column': ('#1f222a', '#c49a5e'),
    'seat': ('#262c3a', '#5673a8'), 'seat2': ('#212633', '#46608f'), 'walk': ('#30353f', '#b8c0cc'),
    'runoff': ('#17281c', '#3e9a3a'), 'pitch1': ('#1f3526', '#6dcb4e'), 'pitch2': ('#1b2f21', '#5ab742'),
    'line': ('#2c4131', '#f0fae8'),
    'truss': ('#5d6373', '#ffffff'), 'truss2': ('#353a46', '#aab2c0'), 'flood': ('#353a46', '#fff3b0'),
    # Floodlight beams (light layer): invisible when off.
    'beam': ('rgb(255 244 190 / 0)', 'rgb(255 244 190 / .28)'),
    'beam2': ('rgb(255 244 190 / 0)', 'rgb(255 250 215 / .5)'),
}

Point = tuple[float, float, float]
Flat = list[tuple[float, float]]
Grid = list[list[str | None]]


def project(p: Point) -> tuple[float, float]:
    x, y, z = p
    s, c = math.sin(ELEVATION), math.cos(ELEVATION)
    f = DISTANCE / (DISTANCE + y * c - z * s)
    return x * f * SCALE, -(y * s + z * c) * f * SCALE


def outline(a: float, b: float, n: float, z: float, steps: int = 72) -> list[Point]:
    """Counter-clockwise superellipse |x/a|^n + |y/b|^n = 1 at height z."""
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        c, s = math.cos(t), math.sin(t)
        pts.append((a * math.copysign(abs(c) ** (2 / n), c), b * math.copysign(abs(s) ** (2 / n), s), z))
    return pts


def lerp(p: Point, q: Point, t: float) -> Point:
    return tuple(a + (b - a) * t for a, b in zip(p, q))


def checker(a, b):
    return lambda gx, gy: a if (gx + gy) % 2 else b


def columns(gx, gy):
    return 'column' if gx % 3 == 0 else 'glow'


class Scene:
    """Shapes in paint order: filled polygons and 1px lines, in projected coordinates."""

    LAYERS = ('base', 'light')

    def __init__(self):
        self.shapes: list[tuple[str, str, Flat, object]] = []

    def fill(self, pts: list[Point], key, layer: str = 'base') -> None:
        self.shapes.append((layer, 'fill', [project(p) for p in pts], key))

    def line(self, pts: list[Point], key, width: float = 1.1) -> None:
        flat = [project(p) for p in pts]
        for a, b in zip(flat, flat[1:]):
            self.shapes.append(('base', 'line', [a, b], (key, width)))

    def rasterize(self) -> list[Grid]:
        """One grid per layer, all the same size."""
        xs = [x for *_, pts, _ in self.shapes for x, _ in pts]
        ys = [y for *_, pts, _ in self.shapes for _, y in pts]
        x0, y0 = math.floor(min(xs)) - MARGIN, math.floor(min(ys)) - MARGIN
        w, h = math.ceil(max(xs)) + MARGIN - x0, math.ceil(max(ys)) + MARGIN - y0
        grids: dict[str, Grid] = {layer: [[None] * w for _ in range(h)] for layer in self.LAYERS}
        for layer, kind, pts, key in self.shapes:
            grid = grids[layer]
            pts = [(x - x0, y - y0) for x, y in pts]
            if kind == 'fill':
                test = lambda x, y, pts=pts: in_poly(x, y, pts)
            else:
                key, width = key
                test = lambda x, y, pts=pts, width=width: near_segment(x, y, *pts[0], *pts[1], width)
            bx0, bx1 = int(min(p[0] for p in pts)) - 1, int(max(p[0] for p in pts)) + 2
            by0, by1 = int(min(p[1] for p in pts)) - 1, int(max(p[1] for p in pts)) + 2
            for gy in range(max(by0, 0), min(by1, h)):
                for gx in range(max(bx0, 0), min(bx1, w)):
                    if test(gx + 0.5, gy + 0.5):
                        grid[gy][gx] = key(gx, gy) if callable(key) else key
        return [grids[layer] for layer in self.LAYERS]


def in_poly(x: float, y: float, pts: Flat) -> bool:
    inside = False
    j = len(pts) - 1
    for i, (xi, yi) in enumerate(pts):
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def near_segment(x, y, ax, ay, bx, by, width) -> bool:
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(x - (ax + t * dx), y - (ay + t * dy)) <= width / 2


def build() -> Scene:
    sc = Scene()
    shell_top, shell_base = outline(74, 94, 3.2, 24), outline(74, 94, 3.2, 0)
    stand_top, stand_foot = (66, 86, 3.2, 22), (38, 57, 6, 1)

    # Roof rim of the faceted shell (the bowl is painted over its middle).
    sc.fill(shell_top, 'roof')

    # Seating bowl as concentric rows, top tier to front row, with a walkway ring.
    rows = 12
    for i in range(rows):
        t = i / rows
        a, b, n, z = (o + (f - o) * t for o, f in zip(stand_top, stand_foot))
        sc.fill(outline(a, b, n, z), 'walk' if i == 5 else ('seat' if i % 2 else 'seat2'))

    # Pitch: run-off, mowing bands along its length, markings.
    sc.fill(outline(38, 57, 6, 0.5), 'runoff')
    for i in range(10):
        y0, y1 = -52.5 + i * 10.5, -52.5 + (i + 1) * 10.5
        sc.fill([(-34, y0, 0), (34, y0, 0), (34, y1, 0), (-34, y1, 0)], 'pitch1' if i % 2 else 'pitch2')
    sc.line([(-34, -52.5, 0), (34, -52.5, 0), (34, 52.5, 0), (-34, 52.5, 0), (-34, -52.5, 0)], 'line')
    sc.line([(-34, 0, 0), (34, 0, 0)], 'line')
    circle = [(9.15 * math.cos(t / 12 * math.pi), 9.15 * math.sin(t / 12 * math.pi), 0) for t in range(25)]
    sc.line(circle, 'line')
    for end in (-1, 1):
        g, box = 52.5 * end, (52.5 - 16.5) * end
        sc.line([(-20.15, g, 0), (-20.15, box, 0), (20.15, box, 0), (20.15, g, 0)], 'line')

    # Partial roof over the west stand.
    sc.fill([(-74, -76, 25), (-74, 76, 25), (-44, 64, 21), (-44, -64, 21)], 'roof')
    sc.line([(-44, -64, 21), (-44, 64, 21)], 'roof2')

    # South-facing outer wall: lit concourse on pillars, faceted white skin above.
    for i, (p, q) in enumerate(zip(shell_base, shell_base[1:] + shell_base[:1])):
        if q[0] - p[0] <= 0:          # faces away from the camera
            continue
        pt, qt = shell_top[i], shell_top[(i + 1) % len(shell_top)]
        pm, qm = lerp(p, pt, 0.3), lerp(q, qt, 0.3)
        sc.fill([p, q, qm, pm], columns)
        light, shade = ('roof', 'roof2') if (i // 4) % 2 else ('roof2', 'roof')
        sc.fill([pm, qm, qt], light)
        sc.fill([pm, qt, pt], shade)

    # The two arched box trusses along the long sides, carrying the floodlights.
    # Triangular section: two top chords, one bottom chord, lattice between.
    for x in (-54, 54):
        ys = [-94 + 188 * i / 46 for i in range(47)]
        arch = [(y, 28 + 26 * (1 - (y / 94) ** 2)) for y in ys]
        bottom = [(x, y, z - 10) for y, z in arch]
        for side in (-4, 4):
            top = [(x + side, y, z) for y, z in arch]
            sc.fill(top + bottom[::-1], checker('truss', 'truss2'))
            sc.line(top, 'truss', 1.3)
        sc.line(bottom, 'truss', 1.3)
        for y, z in (arch[0], arch[-1]):
            sc.fill([(x - 4, y, z), (x + 4, y, z), (x + 4, y, 22), (x - 4, y, 22)], 'truss')
        for px, py, pz in bottom[5:-5:6]:
            sc.line([(px, py, pz), (px, py, pz - 0.1)], 'flood', 1.8)

    # Floodlight beams: wedges from under each truss down to the pitch, with a brighter core.
    for x, aim in ((-54, -8), (54, 8)):
        for y in (-39, -13, 13, 39):
            z = 18 + 26 * (1 - (y / 94) ** 2)
            sc.fill([(x, y - 1.5, z), (x, y + 1.5, z), (aim, y + 9, 0), (aim, y - 9, 0)], 'beam', 'light')
            sc.fill([(x, y - 0.6, z), (x, y + 0.6, z), (aim, y + 3, 0), (aim, y - 3, 0)], 'beam2', 'light')
    return sc


def paths(grid: Grid) -> list[str]:
    runs: dict[str, list[str]] = {}
    for gy, row in enumerate(grid):
        gx = 0
        while gx < len(row):
            key, start = row[gx], gx
            while gx < len(row) and row[gx] == key:
                gx += 1
            if key:
                runs.setdefault(key, []).append(f'M{start} {gy}h{gx - start}v1h-{gx - start}z')
    # Colours come from the page; the fallback is the lights-off colour.
    return [f'    <path style="fill:var(--st-{k},{LIT[k][0]})" d="{"".join(d)}"/>' for k, d in runs.items()]


def to_svg(grids: list[Grid]) -> str:
    h, w = len(grids[0]), len(grids[0][0])
    body = '\n'.join(p for grid in grids for p in paths(grid))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'shape-rendering="crispEdges">\n'
            f'  <!-- Generated by tools/stadium.py; do not edit by hand. -->\n'
            f'  <symbol id="art" viewBox="0 0 {w} {h}">\n{body}\n  </symbol>\n'
            f'  <use href="#art"/>\n</svg>\n')


def use_snippet(grids: list[Grid]) -> str:
    h, w = len(grids[0]), len(grids[0][0])
    return (f'      <svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" shape-rendering="crispEdges" '
            f'focusable="false"><use href="stadium.svg#art"/></svg>\n')


def css_block() -> str:
    # Registered as colours so the variables themselves can fade between off and on.
    props = ''.join(f"@property --st-{k} {{ syntax: '<color>'; inherits: true; initial-value: transparent; }}\n"
                    for k in LIT)
    off = ' '.join(f'--st-{k}: {v[0]};' for k, v in LIT.items())
    on = ' '.join(f'--st-{k}: {v[1]};' for k, v in LIT.items())
    fade = ', '.join(f'--st-{k} .6s' for k in LIT)
    return (f'{props}#stadium {{ {off} transition: {fade}; }}\n'
            f'#stadium[data-lights="on"] {{ {on} }}\n')


def splice(text: str, start: str, end: str, body: str) -> str:
    head, rest = text.split(start)
    _, tail = rest.split(end)
    return head + start + body + end + tail


def main() -> int:
    site = Path(__file__).resolve().parent.parent / 'site'
    grids = build().rasterize()
    outputs = {
        site / 'stadium.svg': lambda _: to_svg(grids),
        site / 'index.html': lambda text: splice(
            text, '<!-- stadium:start -->\n', '      <!-- stadium:end -->', use_snippet(grids)),
        site / 'styles.css': lambda text: splice(
            text, '/* stadium:start — generated by tools/stadium.py */\n', '/* stadium:end */', css_block()),
    }
    stale = []
    for path, update in outputs.items():
        current = path.read_text() if path.exists() else ''
        updated = update(current)
        if updated != current:
            stale.append(path.name)
            if '--check' not in sys.argv:
                path.write_text(updated)
    if '--check' in sys.argv and stale:
        print(f'out of date: {", ".join(stale)}; run `uv run python tools/stadium.py`')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
