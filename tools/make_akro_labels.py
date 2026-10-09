"""Akro-Mils drawer labels on Avery 5195 (2/3" x 1-3/4", 60 per letter sheet, 4 x 15).

    python3 tools/make_akro_labels.py

Writes labels/akro-mils-5195.html and (with Google Chrome installed)
labels/akro-mils-5195.pdf. One label per drawer that has parts, in drawer
order, built from data/parts.json: drawer number, drawer label, and a picture.
Drawers holding plastic + metal versions of a shaft show the metal one.
Motor and capped shafts are shown as a close-up of their distinctive end (the
colored ring or the cap) with a zigzag "break" line, drawn into labels/img/.
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


# Close-ups: keep the left end of the shaft (where the colored ring / cap is),
# the same zoom for every shaft, and cut it with a zigzag break line.
CLOSEUP_TYPES = {"Motor Shafts", "Capped Shafts"}
CLOSEUP_ASPECT = 3.2      # kept length = 3.2 x shaft height


def closeup(part):
    src = (ROOT / part["image"]).read_text()
    root = re.search(r"<svg\b[^>]*>", src).group(0)
    x, y, w, h = (float(v) for v in re.search(r'viewBox="([^"]+)"', root).group(1).replace(",", " ").split())
    keep = CLOSEUP_ASPECT * h
    if keep >= 0.85 * w:              # already short: nothing to cut
        return part["image"]
    inner = src[src.index(root) + len(root):src.rindex("</svg>")]
    cut, amp, teeth = x + keep, 0.12 * h, 4
    ys = [y + h * i / (teeth * 2) for i in range(teeth * 2 + 1)]
    zig = [(cut - (amp if i % 2 else 0), yy) for i, yy in enumerate(ys)]
    pts = lambda ps: " ".join(f"{a:.2f},{b:.2f}" for a, b in ps)
    clip = [(x - 1, y - 1)] + [(zx, zy) for zx, zy in zig] + [(x - 1, y + h + 1)]
    clip[1] = (zig[0][0], y - 1)
    clip[-2] = (zig[-1][0], y + h + 1)
    out = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x:.2f} {y:.2f} {keep + 1:.2f} {h:.2f}">'
           f'<clipPath id="keep"><polygon points="{pts(clip)}"/></clipPath>'
           f'<g clip-path="url(#keep)">{inner}</g>'
           f'<polyline points="{pts(zig)}" fill="none" stroke="#000" stroke-width="1" stroke-linejoin="round"/></svg>')
    dest = ROOT / "labels" / "img" / Path(part["image"]).name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out)
    return dest.relative_to(ROOT).as_posix()


def label_html(drawer, contents, i):
    col, row = i % COLS, (i // COLS) % ROWS
    num = int(drawer[len(prefix):])
    text = contents[0]["binLabel"] or " + ".join(p["name"] for p in contents)
    main, _, sub = text.partition(" (")
    sub = f'<span class="sub">({html.escape(sub)}</span>' if sub else ""
    pic = picture(contents)
    img = closeup(pic) if pic.get("type") in CLOSEUP_TYPES else pic["image"]
    return f"""
  <div class="label" style="left:{LEFT + col * PITCH_X:.4f}in;top:{TOP + row * PITCH_Y:.4f}in">
    <div class="pic"><img src="../{html.escape(img)}" alt=""></div>
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
  .pic img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
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
