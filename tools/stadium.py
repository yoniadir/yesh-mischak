"""Generate the pixel-art Bloomfield Stadium and inline it into site/index.html.

The scene is drawn as shapes in the coordinates of a 1024px aerial reference photo,
then sampled onto a coarse pixel grid. Stadium colours have an "off" and an "on" value;
the page flips between them with `data-lights` on the #stadium figure.

    uv run python tools/stadium.py           # rewrite site/index.html
    uv run python tools/stadium.py --check   # exit 1 if index.html is out of date
"""
import math
import random
import sys
from pathlib import Path

W, H = 128, 100          # grid size in pixels
S = 8                    # photo px per grid pixel
Y0 = 90                  # photo y of the grid's top edge

# Colours that don't depend on the lights.
FIXED = {
    'sky1': '#2f2f52', 'sky2': '#5b4a6e', 'sky3': '#a0677a', 'sky4': '#e0935f', 'sky5': '#f2b872',
    'sea': '#34476b', 'sea2': '#4b5f86',
    'ground': '#2a2a33', 'city1': '#34343f', 'city2': '#3f3f4a', 'city3': '#4a4852',
    'tower': '#454c60', 'tower2': '#353b4d', 'cwin': '#f6c56f', 'cwin2': '#b98b52',
    'tree': '#1d3326', 'road': '#23232b', 'lamp': '#ffcc66',
}
# Stadium colours: (lights off, lights on).
LIT = {
    'roof': ('#4a505d', '#eef1f6'), 'roof2': ('#3a3f4b', '#c6ccd7'),
    'mesh': ('#30353f', '#8e97a8'), 'mesh2': ('#282c35', '#737d90'),
    'truss': ('#5d6373', '#ffffff'), 'truss2': ('#3a3f4c', '#b9c0cd'),
    'seat': ('#252a35', '#a6b1c7'), 'seat2': ('#20242e', '#8f9bb3'),
    'pitch1': ('#1f3526', '#6dcb4e'), 'pitch2': ('#1b2f21', '#5ab742'),
    'line': ('#2c4131', '#eef9e6'),
    'glow': ('#2b2f3a', '#ffd98a'), 'column': ('#21242d', '#b8894a'),
}

Grid = list[list[str]]


def centre(gx: int, gy: int) -> tuple[float, float]:
    return (gx + 0.5) * S, Y0 + (gy + 0.5) * S


def in_poly(x: float, y: float, pts: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(pts) - 1
    for i, (xi, yi) in enumerate(pts):
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def paint(grid: Grid, test, key) -> None:
    """Set every cell whose centre passes `test(x, y)`; `key` is a colour or f(gx, gy)."""
    for gy in range(H):
        for gx in range(W):
            x, y = centre(gx, gy)
            if test(x, y):
                grid[gy][gx] = key(gx, gy) if callable(key) else key


def poly(pts):
    return lambda x, y: in_poly(x, y, pts)


def ellipse(cx, cy, rx, ry):
    return lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1


def rect(x0, y0, x1, y1):
    return lambda x, y: x0 <= x < x1 and y0 <= y < y1


def near_segment(ax, ay, bx, by, width):
    def test(x, y):
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(x - (ax + t * dx), y - (ay + t * dy)) <= width / 2
    return test


def checker(a, b):
    return lambda gx, gy: a if (gx + gy) % 2 else b


def sky(grid: Grid) -> None:
    bands = [(110, 'sky1'), (125, 'sky2'), (138, 'sky3'), (150, 'sky4'), (10_000, 'sky5')]
    for gy in range(H):
        for gx in range(W):
            _, y = centre(gx, gy)
            for i, (limit, key) in enumerate(bands):
                if y < limit:
                    # Dither the last pixel row of each band into the next one.
                    if i + 1 < len(bands) and y > limit - S and (gx + gy) % 2:
                        key = bands[i + 1][1]
                    grid[gy][gx] = key
                    break


def city(grid: Grid) -> None:
    coast = [(0, 150), (1024, 150), (1024, 1020), (0, 1020)]
    sea = [(0, 150), (560, 150), (430, 196), (300, 222), (90, 262), (0, 285)]
    paint(grid, poly(coast), 'ground')
    paint(grid, poly(sea), lambda gx, gy: 'sea2' if gy % 3 == 0 and gx % 5 == 1 else 'sea')
    paint(grid, near_segment(0, 280, 560, 150, 4), 'sea2')

    rng = random.Random(7)
    land = lambda x, y: y > 150 and not in_poly(x, y, sea)
    # Rooftop blocks, back to front.
    for _ in range(420):
        gx, gy = rng.randrange(W), rng.randrange(6, H)
        w, h = rng.randint(2, 5), rng.randint(2, 4)
        key = rng.choice(['city1', 'city2', 'city2', 'city3'])
        for yy in range(gy, min(gy + h, H)):
            for xx in range(gx, min(gx + w, W)):
                if land(*centre(xx, yy)):
                    grid[yy][xx] = key
        if rng.random() < 0.3:
            wx, wy = gx + rng.randrange(w), gy + rng.randrange(h)
            if wx < W and wy < H and land(*centre(wx, wy)):
                grid[wy][wx] = rng.choice(['cwin', 'cwin2'])
    # High-rise towers on the skyline.
    towers = [(795, 98, 840), (838, 120, 868), (870, 150, 900), (655, 132, 685), (990, 128, 1024),
              (372, 145, 408), (290, 172, 330), (420, 135, 445), (700, 160, 730), (930, 160, 965)]
    for x0, top, x1 in towers:
        paint(grid, rect(x0, top, x1, 300), lambda gx, gy: 'tower2' if gx % 3 == 0 else 'tower')
        paint(grid, rect(x0 + 8, top + 12, x1 - 4, 290),
              lambda gx, gy: 'cwin2' if (gx * 7 + gy * 3) % 11 == 0 else grid[gy][gx])
    # Coastal boulevard lights.
    paint(grid, near_segment(0, 300, 330, 240, 5), lambda gx, gy: 'lamp' if gx % 2 else 'road')
    # Trees and the road in front of the stadium.
    for cx, cy, r in [(70, 620, 45), (40, 700, 40), (960, 700, 50), (990, 800, 40), (330, 860, 35), (430, 850, 30)]:
        paint(grid, ellipse(cx, cy, r, r * 0.8), 'tree')
    paint(grid, poly([(0, 850), (1024, 830), (1024, 880), (0, 905)]), 'road')
    paint(grid, poly([(0, 868), (1024, 848), (1024, 856), (0, 876)]),
          lambda gx, gy: 'lamp' if gx % 3 == 0 else 'road')


def stadium(grid: Grid) -> None:
    stripes = lambda a, b, period=2: (lambda gx, gy: a if (gy // period) % 2 else b)
    columns = lambda gx, gy: 'column' if gx % 4 == 0 else 'glow'

    # Outer shell: lit concourse and pillars around the whole footprint.
    shell = [(110, 590), (170, 530), (330, 470), (720, 462), (860, 505), (935, 580), (940, 700),
             (905, 790), (800, 838), (255, 838), (150, 790), (105, 700)]
    paint(grid, poly(shell), 'roof2')
    paint(grid, lambda x, y: y > 610 and in_poly(x, y, shell), columns)
    # Seating bowl.
    bowl = [(270, 585), (360, 520), (705, 512), (790, 545), (835, 640), (815, 725), (705, 765),
            (370, 765), (285, 740), (262, 650)]
    paint(grid, poly(bowl), stripes('seat', 'seat2', 1))
    # Back-stand roof edge and left-hand canopy (flat white panel + glazed strip).
    paint(grid, poly([(410, 488), (725, 482), (722, 516), (412, 522)]), 'roof')
    paint(grid, poly([(170, 548), (258, 502), (340, 500), (318, 585), (178, 590)]), 'roof')
    paint(grid, poly([(340, 500), (392, 505), (372, 585), (318, 585)]), 'roof2')
    # Right-hand stand under its translucent mesh roof.
    paint(grid, poly([(735, 470), (820, 492), (895, 535), (932, 590), (935, 665), (905, 705),
                      (830, 705), (790, 590)]), checker('mesh', 'mesh2'))
    # Pitch with mowing stripes, touchlines, halfway line, centre circle and boxes.
    pitch = [(385, 598), (690, 598), (700, 752), (370, 752)]
    paint(grid, poly(pitch), stripes('pitch1', 'pitch2'))
    edge = lambda x, y: in_poly(x, y, pitch) and not in_poly(x, y, [(393, 605), (682, 605), (691, 745), (379, 745)])
    paint(grid, edge, 'line')
    paint(grid, rect(531, 598, 539, 752), 'line')
    paint(grid, lambda x, y: 0.72 <= ((x - 535) / 48) ** 2 + ((y - 675) / 28) ** 2 <= 1.28, 'line')
    paint(grid, lambda x, y: in_poly(x, y, [(385, 640), (432, 640), (432, 712), (380, 712)])
          and not in_poly(x, y, [(385, 648), (424, 648), (424, 704), (380, 704)]), 'line')
    paint(grid, lambda x, y: in_poly(x, y, [(648, 640), (693, 640), (697, 712), (648, 712)])
          and not in_poly(x, y, [(656, 648), (693, 648), (697, 704), (656, 704)]), 'line')
    # Near-side roof sweeping across the front, with a darker underside edge.
    front = [(232, 700), (370, 758), (705, 758), (835, 700), (838, 740), (800, 792), (255, 792), (228, 745)]
    paint(grid, poly(front), 'roof')
    paint(grid, poly([(255, 776), (800, 776), (800, 792), (255, 792)]), 'roof2')
    # The two white truss arches over the end stands.
    for a, b in [((352, 462), (262, 702)), ((728, 458), (812, 702))]:
        paint(grid, near_segment(*a, *b, 22), checker('truss', 'truss2'))
        paint(grid, near_segment(*a, *b, 9), 'truss')


def render() -> Grid:
    grid: Grid = [['sky1'] * W for _ in range(H)]
    sky(grid)
    city(grid)
    stadium(grid)
    return grid


def to_svg(grid: Grid) -> str:
    runs: dict[str, list[str]] = {}
    for gy, row in enumerate(grid):
        gx = 0
        while gx < W:
            key, start = row[gx], gx
            while gx < W and row[gx] == key:
                gx += 1
            runs.setdefault(key, []).append(f'M{start} {gy}h{gx - start}v1h-{gx - start}z')
    style = ' '.join(
        f'#stadium .k-{k}{{fill:{off}}} #stadium[data-lights="on"] .k-{k}{{fill:{on}}}'
        for k, (off, on) in LIT.items())
    paths = '\n'.join(
        f'        <path class="k-{k}" d="{"".join(d)}"/>' if k in LIT else
        f'        <path fill="{FIXED[k]}" d="{"".join(d)}"/>'
        for k, d in runs.items())
    return (f'      <svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" shape-rendering="crispEdges" '
            f'focusable="false" xmlns="http://www.w3.org/2000/svg">\n'
            f'        <style>{style}</style>\n{paths}\n      </svg>\n')


START, END = '<!-- stadium:start -->\n', '      <!-- stadium:end -->'


def inline(html: str, svg: str) -> str:
    head, rest = html.split(START)
    _, tail = rest.split(END)
    return head + START + svg + END + tail


def main() -> int:
    index = Path(__file__).resolve().parent.parent / 'site' / 'index.html'
    html = index.read_text()
    updated = inline(html, to_svg(render()))
    if '--check' in sys.argv:
        if updated != html:
            print('site/index.html is out of date: run `uv run python tools/stadium.py`')
            return 1
        return 0
    index.write_text(updated)
    return 0


if __name__ == '__main__':
    sys.exit(main())
