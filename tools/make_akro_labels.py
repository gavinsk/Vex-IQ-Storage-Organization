"""Akro-Mils drawer labels on Avery 5195 (2/3" x 1-3/4", 60 per letter sheet, 4 x 15).

    python3 tools/make_akro_labels.py

Writes labels/akro-mils-5195.html and (with Google Chrome installed)
labels/akro-mils-5195.pdf. One label per drawer that has parts, in drawer
order, built from data/parts.json: drawer number, drawer label, and a picture.
Drawers holding plastic + metal versions of a shaft show the metal one.
Motor and capped shafts are shown as a close-up of their distinctive end (the
colored ring or the cap) with a zigzag "break" line; motor-shaft drawers show
the metal and plastic shafts stacked. Long standoffs show both snap ends with
break lines and a small gap. Close-ups are drawn into labels/img/.
Print the PDF at 100% / "Actual size" — not "Fit to page".
"""
import html
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "labels" / "akro-mils-5195.html"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Avery 5195 geometry, inches.
COLS, ROWS = 4, 15
LABEL_W, LABEL_H = 1.75, 2 / 3
LEFT, TOP = 0.3, 0.5
PITCH_X, PITCH_Y = 2.05, 2 / 3

parts = json.loads((ROOT / "data/parts.json").read_text())
PIC_W = 0.66                      # picture box width, inches
prefix = json.loads((ROOT / "data/storage-layout.json").read_text())["akroMils"]["prefix"]

drawers = defaultdict(list)
for p in parts:
    for loc in [p["location"], *p.get("extraLocations", [])]:
        if re.fullmatch(prefix + r"\d+", loc):
            drawers[loc].append(p)


def picture(contents):
    """The part to show: the metal version when a drawer mixes plastic and metal."""
    metal = [p for p in contents if "plastic" not in p["name"].lower()]
    return (metal or contents)[0]


# Close-ups for long thin parts, cut with zigzag "break" lines (labels only):
#  - motor / capped shafts: the left end (colored ring or cap), same zoom for all
#  - standoffs: both snap ends with a small gap between them, so the end details
#    show instead of the length (the label text gives the length)
SHAFT_TYPES = {"Motor Shafts", "Capped Shafts"}
SHAFT_KEEP = 3.2          # kept length = 3.2 x part height
STANDOFF_END = 1.25       # each standoff end = 1.25 x part height
GAP = 0.075               # white gap between standoff ends, x part height


def zigzag(x, y, h, inward):
    """Break line at x from top to bottom; teeth point `inward` (+1 right, -1 left)."""
    amp, teeth = 0.12 * h, 4
    return [(x + (inward * amp if i % 2 else 0), y + h * i / (teeth * 2)) for i in range(teeth * 2 + 1)]


def broken_svg(part, pieces, name):
    """pieces: [(x0, x1, cut_left, cut_right)] in the source viewBox; laid out left to right."""
    src = (ROOT / part["image"]).read_text()
    root = re.search(r"<svg\b[^>]*>", src).group(0)
    x, y, w, h = (float(v) for v in re.search(r'viewBox="([^"]+)"', root).group(1).replace(",", " ").split())
    inner = src[src.index(root) + len(root):src.rindex("</svg>")]
    pts = lambda ps: " ".join(f"{a:.2f},{b:.2f}" for a, b in ps)
    body, cursor = [], 0.0
    for n, (x0, x1, cut_l, cut_r) in enumerate(pieces):
        left = zigzag(x0, y, h, +1) if cut_l else [(x0 - 1, y + h * i / 8) for i in range(9)]
        right = zigzag(x1, y, h, -1) if cut_r else [(x1 + 1, y + h * i / 8) for i in range(9)]
        clip = [(left[0][0], y - 1)] + left + [(left[-1][0], y + h + 1), (right[-1][0], y + h + 1)] \
               + right[::-1] + [(right[0][0], y - 1)]
        lines = "".join(f'<polyline points="{pts(z)}" fill="none" stroke="#000" stroke-width="1" stroke-linejoin="round"/>'
                        for z, on in ((left, cut_l), (right, cut_r)) if on)
        dx = cursor - (x0 - x)
        body.append(f'<clipPath id="c{n}"><polygon points="{pts(clip)}"/></clipPath>'
                    f'<g transform="translate({dx:.2f},0)"><g clip-path="url(#c{n})">{inner}</g>{lines}</g>')
        cursor += (x1 - x0) + GAP * h
    width = cursor - GAP * h
    out = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x - 0.5:.2f} {y:.2f} {width + 1:.2f} {h:.2f}">{"".join(body)}</svg>'
    dest = ROOT / "labels" / "img" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    return dest.relative_to(ROOT).as_posix()


def label_picture(part):
    """Image path for a part on a label: a broken-line close-up for long shafts/standoffs."""
    if not part["image"].endswith(".svg"):
        return part["image"]
    vb = re.search(r'viewBox="([^"]+)"', (ROOT / part["image"]).read_text())
    if not vb:
        return part["image"]
    x, y, w, h = (float(v) for v in vb.group(1).replace(",", " ").split())
    name = Path(part["image"]).name
    if part.get("type") in SHAFT_TYPES and SHAFT_KEEP * h < 0.85 * w:
        return broken_svg(part, [(x, x + SHAFT_KEEP * h, False, True)], name)
    if part.get("type") == "Standoffs" and w > (2 * STANDOFF_END + 0.8) * h:
        end = STANDOFF_END * h
        return broken_svg(part, [(x, x + end, False, True), (x + w - end, x + w, True, False)], name)
    return part["image"]


def label_pictures(contents):
    """Motor-shaft drawers show every shaft stacked (metal first); others show one picture."""
    if len(contents) > 1 and all(p.get("type") == "Motor Shafts" for p in contents):
        ordered = sorted(contents, key=lambda p: "plastic" in p["name"].lower())
        return [label_picture(p) for p in ordered]
    return [label_picture(picture(contents))]


def label_html(drawer, contents, i):
    col, row = i % COLS, (i // COLS) % ROWS
    num = int(drawer[len(prefix):])
    text = contents[0]["binLabel"] or " + ".join(p["name"] for p in contents)
    main, _, sub = text.partition(" (")
    sub = f'<span class="sub">({html.escape(sub)}</span>' if sub else ""
    imgs = "".join(f'<img src="../{html.escape(img)}" alt="">' for img in label_pictures(contents))
    return f"""
  <div class="label" style="left:{LEFT + col * PITCH_X:.4f}in;top:{TOP + row * PITCH_Y:.4f}in">
    <div class="pic">{imgs}</div>
    <div class="text"><span class="num">{num}</span><span class="main">{html.escape(main)}</span>{sub}</div>
  </div>"""


ordered = sorted(drawers, key=lambda d: int(d[len(prefix):]))
per_page = COLS * ROWS
pages = [ordered[i:i + per_page] for i in range(0, len(ordered), per_page)]
body = "".join(
    '<section class="page">' + "".join(label_html(d, drawers[d], i) for i, d in enumerate(page)) + "</section>"
    for page in pages
)

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Akro-Mils labels (Avery 5195)</title>
<style>
  @page {{ size: letter; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; color: #000; }}
  .page {{ position: relative; width: 8.5in; height: 11in; page-break-after: always; overflow: hidden; }}
  .label {{ position: absolute; width: {LABEL_W}in; height: {LABEL_H:.4f}in; display: flex; align-items: center;
           gap: 0.05in; padding: 0.04in 0.08in; }}
  .pic {{ flex: 0 0 {PIC_W}in; height: 0.56in; display: flex; align-items: center; justify-content: center; }}
  .pic {{ flex-direction: column; gap: 0.05in; }}
  .pic img {{ max-width: 100%; max-height: 100%; min-height: 0; object-fit: contain; }}
  .text {{ flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; line-height: 1.08; }}
  .num {{ font-size: 6.5pt; font-weight: 700; color: #444; }}
  .main {{ font-size: 8.5pt; font-weight: 800; }}
  .sub {{ font-size: 6.5pt; color: #333; }}
  /* On screen only: show the label outlines to check alignment. */
  @media screen {{ body {{ background: #ddd; }} .page {{ background: #fff; margin: 0.25in auto; }}
                   .label {{ outline: 1px dashed #bbb; border-radius: 4px; }} }}
</style></head><body>{body}</body></html>
""")
print(f"Wrote {OUT.relative_to(ROOT)}: {len(ordered)} labels on {len(pages)} sheet(s)")

pdf = OUT.with_suffix(".pdf")
try:
    subprocess.run(["perl", "-e", "alarm 30; exec @ARGV", CHROME, "--headless=new", "--disable-gpu",
                    "--no-pdf-header-footer", f"--print-to-pdf={pdf}", OUT.as_uri()],
                   check=False, capture_output=True)
    print(f"Wrote {pdf.relative_to(ROOT)}" if pdf.exists() else "PDF not written; print the HTML from Chrome instead.")
except FileNotFoundError:
    print("Chrome not found; open the HTML in Chrome and print it (Margins: None, Scale: 100%).")
