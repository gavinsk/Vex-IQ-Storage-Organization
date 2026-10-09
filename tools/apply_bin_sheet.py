"""Apply tools/bin-assignments.xlsx to data/parts.json.

    python3 tools/apply_bin_sheet.py           # preview the changes
    python3 tools/apply_bin_sheet.py --apply   # write data/parts.json

Only location, extraLocations, binLabel, and storage change. A part typed into
several bins (high-volume parts) gets the first as `location` and the rest as
`extraLocations`. Nothing is written if the sheet has an unknown part, a missing
part, or a bad bin ID.
Standard library only, so it runs with the Mac's built-in python3.
"""
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "tools" / "bin-assignments.xlsx"
PARTS = ROOT / "data" / "parts.json"
LAYOUT = ROOT / "data" / "storage-layout.json"

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def read_sheet(path, name):
    """Return the named worksheet as a list of rows (lists of strings)."""
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        sheet = next((s for s in wb.find("m:sheets", NS) if s.get("name") == name), None)
        if sheet is None:
            raise SystemExit(f"No '{name}' tab in {path.name}")
        rid = sheet.get(f"{{{NS['r']}}}id")
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels.findall("rel:Relationship", NS) if r.get("Id") == rid)
        target = target.lstrip("/") if target.startswith("/") else "xl/" + target
        root = ET.fromstring(z.read(target))

    rows = []
    for row in root.iter(f"{{{NS['m']}}}row"):
        values = {}
        for c in row.findall("m:c", NS):
            col = 0
            for ch in re.match(r"[A-Z]+", c.get("r")).group():
                col = col * 26 + ord(ch) - 64
            t, v = c.get("t"), c.find("m:v", NS)
            if t == "s" and v is not None:
                text = shared[int(v.text)]
            elif t == "inlineStr":
                text = "".join(x.text or "" for x in c.iter(f"{{{NS['m']}}}t"))
            else:
                text = v.text if v is not None and v.text else ""
            values[col - 1] = text.strip()
        rows.append([values.get(i, "") for i in range(max(values, default=-1) + 1)])
    return rows


def storage_for(bin_id, current):
    """Storage type implied by a bin ID; keeps the existing subtype for V/E zones."""
    if m := re.fullmatch(r"[AB](\d)-\d", bin_id):
        return "Rolling - Small" if int(m.group(1)) <= 4 else "Rolling - Medium"
    if bin_id.startswith("AK"):
        return "Akro-Mils Drawer"
    if bin_id.startswith("V"):
        return current if current.startswith("Vertical") else "Vertical Hanger"
    if bin_id.startswith("E"):
        return current if current.startswith(("External", "Tool")) else "External / Protected"
    return current


def valid_bin(bin_id, layout):
    if m := re.fullmatch(r"([A-Z])(\d+)-(\d+)", bin_id):
        side, row, col = m.group(1), int(m.group(2)), int(m.group(3))
        if side not in {s["id"] for s in layout["cart"]["sides"]}:
            return False
        return any(g["firstRow"] <= row <= g["lastRow"] and 1 <= col <= g["cols"] for g in layout["cart"]["binGroups"])
    ak = layout["akroMils"]
    if m := re.fullmatch(ak["prefix"] + r"(\d+)", bin_id):
        return 1 <= int(m.group(1)) <= ak["drawers"]
    return any(re.fullmatch(z["prefix"] + r"\d+", bin_id) for z in layout["zones"])


def main():
    apply = "--apply" in sys.argv
    parts = json.loads(PARTS.read_text())
    layout = json.loads(LAYOUT.read_text())
    by_name = {p["name"].casefold(): p for p in parts}

    rows = read_sheet(SHEET, "Bins")
    header = rows[0]
    bin_col = header.index("Bin")
    label_col = header.index("Bin Label")
    part_cols = [i for i, h in enumerate(header) if h.startswith("Part")]

    errors, warnings = [], []
    placed = {}  # part name -> [bins], in sheet order
    labels = {}  # bin -> label
    for n, row in enumerate(rows[1:], start=2):
        row = row + [""] * (len(header) - len(row))
        bin_id = row[bin_col].upper()
        names = [row[i] for i in part_cols if row[i]]
        if not names:
            continue
        if not valid_bin(bin_id, layout):
            errors.append(f"Row {n}: '{row[bin_col]}' is not a valid bin ID")
            continue
        found = []
        for name in names:
            p = by_name.get(name.casefold())
            if p is None:
                errors.append(f"{bin_id}: unknown part '{name}'")
            elif bin_id in placed.get(p["name"], []):
                warnings.append(f"{bin_id}: '{p['name']}' is listed twice in this bin")
            else:
                placed.setdefault(p["name"], []).append(bin_id)
                found.append(p)
        labels[bin_id] = row[label_col] or " + ".join(p["name"] for p in found)
        if len(found) > 1 and any(p["category"] == "Sensors" for p in found):
            warnings.append(f"{bin_id}: sensor shares a bin ({', '.join(p['name'] for p in found)})")

    for p in parts:
        if p["name"] not in placed:
            errors.append(f"'{p['name']}' is not in any bin")

    multi = {name: bins for name, bins in placed.items() if len(bins) > 1}
    for name, bins in multi.items():
        if len({labels[b] for b in bins}) > 1:
            warnings.append(f"'{name}' is in {', '.join(bins)}, but those bins have different labels (the first is used)")

    changes = []
    for i, p in enumerate(parts):
        bins = placed.get(p["name"])
        if not bins:
            continue
        new = {"location": bins[0], "extraLocations": bins[1:], "binLabel": labels[bins[0]],
               "storage": storage_for(bins[0], p["storage"])}
        old = {k: p.get(k, [] if k == "extraLocations" else None) for k in new}
        diff = {k: (old[k], v) for k, v in new.items() if old[k] != v}
        if diff:
            changes.append((p["name"], diff))
            # Rebuild so extraLocations sits right after location, and is left out when empty.
            rebuilt = {}
            for k, v in p.items():
                if k == "extraLocations":
                    continue
                rebuilt[k] = new.get(k, v)
                if k == "location" and new["extraLocations"]:
                    rebuilt["extraLocations"] = new["extraLocations"]
            parts[i] = rebuilt

    for name, diff in changes:
        print(f"• {name}")
        for k, (old, new) in diff.items():
            print(f"    {k}: {old}  →  {new}")
    if multi:
        print("\nIn more than one bin:")
        for name, bins in multi.items():
            print(f"    {name}: {', '.join(bins)}")
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"\n{len(changes)} part(s) changed, {len(warnings)} warning(s), {len(errors)} error(s).")

    if errors:
        print("Nothing written — fix the errors in the sheet first.")
        sys.exit(1)
    if not changes:
        return
    if apply:
        PARTS.write_text(json.dumps(parts, indent=2, ensure_ascii=False) + "\n")
        print("Wrote data/parts.json. Refresh the site to check the Storage map.")
    else:
        print("Preview only. Run again with --apply to write data/parts.json.")


if __name__ == "__main__":
    main()
