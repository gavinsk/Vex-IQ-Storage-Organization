"""Write images/sizes.json: each part image's real-world size, for the Part Finder poster.

Units are VEX drawing units (~36 per 1x pitch, ~2.83 per mm), which is the scale
the official VEX SVGs are already drawn at, so their viewBox width/height is used
directly. The EES PNGs are perspective renders with no scale, so their width is
estimated below and the height follows the picture's aspect ratio.

    python3 tools/measure_images.py
"""
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Estimated on-screen width (VEX units) for images without a usable scale.
ESTIMATED_WIDTH = {
    "2x Pitch Shaft": 75, "8x Pitch Shaft": 285,
    "3x3 Plus Gusset Beam": 110, "1x3 Beam": 110, "1x3 Center Lock Plate": 110, "2x2 Lock Plate": 76,
    "4x12 Plate": 300, "Elastic Band Anchor Plate": 100,
    "North Pole Magnetic Beam": 150, "South Pole Magnetic Beam": 150,
    "XL Turntable 36 Tooth Ring Gear Bushing": 260, "XL Turntable Outer Housing": 280, "XL Turntable Plain Bushing": 240,
    "Linear Slide Bracket": 85, "Rack Gear": 200, "Cable Anchor": 75,
    "60 Tooth Gear": 195, "36 Tooth Crown Gear": 120, "Worm Bracket": 110, "Worm Gear": 50,
    "32 Tooth Sprocket": 205, "40 Tooth Sprocket": 255,
    "10mm Pulley": 35, "20mm Pulley": 60, "20mm Pulley Tire Add-On": 65, "30mm Pulley": 90, "40mm Pulley": 120,
    "Belt (2mm thick x 30mm dia)": 85, "Belt (2mm thick x 40mm dia)": 115,
    "Belt (2mm thick x 50mm dia)": 145, "Belt (2mm thick x 60mm dia)": 170,
    # Linear Motion Pack (228-7887): 36 units per pitch
    "1x5 Linear Motion Beam": 180, "1x6 Linear Motion Beam": 216, "1x8 Linear Motion Beam": 288,
    "1x6 Linear Motion Rack Gear": 230, "1x6 Continuous Linear Motion Rack Gear": 216, "1x20 Linear Motion Rack Gear": 720,
    "2x Pitch Linear Motion Bracket (Side Mount)": 75, "1x Pitch Linear Motion Bracket (Snap Mount)": 45,
    "0x3 Idler Pin": 52, "1x2 Idler Pin": 52, "0.5x Pitch Spacer": 40, "Shaft Bushing": 40,
}


def svg_size(path):
    head = path.read_text(errors="replace")[:3000]
    tag = re.search(r"<svg[^>]*>", head, re.S).group(0)
    vb = re.search(r'viewBox="([^"]+)"', tag)
    if vb:
        _, _, w, h = (float(v) for v in vb.group(1).replace(",", " ").split())
        return w, h
    return (float(re.search(rf'\s{k}="([\d.]+)', tag).group(1)) for k in ("width", "height"))


def raster_aspect(path):
    data = path.read_bytes()
    if path.suffix == ".png":
        w, h = struct.unpack(">II", data[16:24])
    elif path.suffix == ".webp" and data[12:16] == b"VP8X":
        w = int.from_bytes(data[24:27], "little") + 1
        h = int.from_bytes(data[27:30], "little") + 1
    elif path.suffix == ".webp" and data[12:16] == b"VP8 ":
        w, h = (struct.unpack("<H", data[26 + i:28 + i])[0] & 0x3FFF for i in (0, 2))
    elif path.suffix == ".webp" and data[12:16] == b"VP8L":
        b = int.from_bytes(data[21:25], "little")
        w, h = (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    else:
        return None
    return h / w


parts = json.loads((ROOT / "data/parts.json").read_text())
sizes, missing = {}, []
for p in parts:
    img = p.get("image")
    if not img:
        continue
    path = ROOT / img
    if path.suffix == ".svg" and p["name"] not in ESTIMATED_WIDTH:
        w, h = svg_size(path)
    elif p["name"] in ESTIMATED_WIDTH:
        aspect = raster_aspect(path) if path.suffix != ".svg" else (lambda s: s[1] / s[0])(tuple(svg_size(path)))
        w = ESTIMATED_WIDTH[p["name"]]
        h = w * aspect
    else:
        missing.append(p["name"])
        continue
    sizes[img] = [round(w, 1), round(h, 1)]

out = ROOT / "images/sizes.json"
out.write_text("{\n" + ",\n".join(f"  {json.dumps(k)}: {json.dumps(v)}" for k, v in sizes.items()) + "\n}\n")
print(f"Wrote {out.relative_to(ROOT)} ({len(sizes)} images)")
if missing:
    print("No size (add to ESTIMATED_WIDTH):", ", ".join(missing))
