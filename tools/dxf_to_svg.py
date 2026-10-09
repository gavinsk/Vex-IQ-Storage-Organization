"""Convert a DXF line drawing (e.g. an isometric view) into an SVG part image.

    python3 tools/dxf_to_svg.py "docs/Rubber Shaft Collar.dxf" images/shafts-rotation/rubber-shaft-collar.svg

Needs ezdxf (pip install ezdxf; use a scratch virtualenv). Every entity —
lines, arcs, ellipses, splines, polylines — is flattened to a polyline and
drawn as black line art on a transparent background. Afterwards update the
part's `image` in data/parts.json and images/manifest.json, add the part to
ESTIMATED_WIDTH in tools/measure_images.py (a DXF has no VEX scale), and run
python3 tools/measure_images.py.
"""
import sys
from pathlib import Path

import ezdxf
from ezdxf import path as ezpath

SCALE = 100        # SVG units per drawing unit
PAD = 0.04         # margin around the drawing, in drawing units
STROKE = 5         # line width, SVG units


def convert(dxf_file, svg_file):
    msp = ezdxf.readfile(dxf_file).modelspace()
    lines = []
    for e in msp:
        try:
            lines.append([(v.x, v.y) for v in ezpath.make_path(e).flattening(0.002)])
        except (TypeError, ValueError):
            print(f"  skipped {e.dxftype()} (no geometry)")
    xs = [x for pts in lines for x, _ in pts]
    ys = [y for pts in lines for _, y in pts]
    x0, y1 = min(xs), max(ys)
    w = (max(xs) - x0 + 2 * PAD) * SCALE
    h = (y1 - min(ys) + 2 * PAD) * SCALE
    poly = lambda pts: " ".join(f"{(x - x0 + PAD) * SCALE:.1f},{(y1 - y + PAD) * SCALE:.1f}" for x, y in pts)
    body = "".join(f'<polyline points="{poly(pts)}"/>' for pts in lines)
    Path(svg_file).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.1f}" height="{h:.1f}" viewBox="0 0 {w:.1f} {h:.1f}">'
        f"<!-- converted from {Path(dxf_file).name} -->"
        f'<g fill="none" stroke="#1d1d1d" stroke-width="{STROKE}" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>'
    )
    print(f"Wrote {svg_file} ({len(lines)} lines, {w:.0f} x {h:.0f})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    convert(sys.argv[1], sys.argv[2])
