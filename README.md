# VEX IQ Parts Locator

A static website that helps students find a VEX IQ part and see where it goes back.

## Files

| File | What it is |
|---|---|
| `data/parts.json` | **The source of truth.** Every part: name, part numbers, location, quantity, category, image. |
| `data/storage-layout.json` | Physical geometry: cart sides, bin rows/columns, Akro-Mils drawer count, other zones. |
| `index.html` | Page structure only (no data). |
| `css/style.css` | Styling. |
| `js/app.js` | Search, part cards, bin views, storage map. |
| `images/` | Part images (add as they become available). |
| `docs/` | Storage-plan workbook, EES PDFs, saved VEX pages. **On Gavin's Mac only** (in `.gitignore`), not on GitHub. |

## Common edits

**Move a part:** change its `location` in `data/parts.json`. A part kept in several bins also has `extraLocations`, e.g. `"extraLocations": ["B4-6"]`. Every card, map highlight, and bin view updates automatically.
If the new bin has a different label, update `binLabel` too (it should match the other parts in that bin).

**Move many parts:** open `tools/bin-assignments.xlsx` in Excel (one row per bin; type in a Part column and Excel suggests matching names).
Save, then run `python3 tools/apply_bin_sheet.py` to preview and `python3 tools/apply_bin_sheet.py --apply` to update `data/parts.json`.
After editing `parts.json` by hand, regenerate the sheet with `tools/make_bin_sheet.py` (needs `openpyxl`).

**Add an image:** save it under `images/<category>/`, then set the part's `image` field, e.g.
`"image": "images/gears/36-tooth-gear.svg"`. Parts with an empty `image` show a placeholder tile.
SVG or PNG both work; SVGs scale cleanly. `images/manifest.json` records where each image came from.

**Quantity:** `quantity` is the combined classroom total for that part.

**Part Finder groups:** each part's `category` picks its tile and `type` picks its group on that tile's page (e.g. Gears → Spur Gears).
`data/categories.json` sets the order of the poster panels, how wide each is (`span`, out of 4 columns), and the order of groups.
After adding or changing an image, run `python3 tools/measure_images.py` so the poster draws it at the right size.

**Akro-Mils drawer labels:** `python3 tools/make_akro_labels.py` rebuilds `labels/akro-mils-5195.pdf` (Avery 5195) from `parts.json`.
Print it at **100% / Actual size** (not "Fit to page"). Test on plain paper first and hold it against a label sheet to check alignment.

## Location IDs

| Format | Meaning |
|---|---|
| `A1-1` … `A4-8`, `B1-1` … `B4-8` | Rolling cart small bins (rows 1–4, 8 per row): side, row, position |
| `A5-1` … `A7-5`, `B5-1` … `B7-5` | Rolling cart medium bins (rows 5–7, 5 per row) |
| `AK01` … `AK64` | Akro-Mils drawers |
| `V01`… | Vertical hangers (long beams, cables) |
| `E01`… | External / protected storage |

## Previewing locally

The site loads JSON with `fetch`, so opening `index.html` by double-clicking won't work. Use one of these instead:

- VS Code **Live Server** extension → right-click `index.html` → *Open with Live Server*
- Terminal: `python3 -m http.server` in this folder, then open http://localhost:8000

## Deep links

- `index.html#bin=B1-3` opens the contents of bin B1-3 (handy for QR codes on bins)
- `index.html#q=36 tooth` pre-fills a search
- `index.html#view=map` opens the storage map
- `index.html#finder` opens the Part Finder; `index.html#finder=Gears` opens one part type

## Publishing

Live site: **https://gavinsk.github.io/Vex-IQ-Storage-Organization/** (repository `gavinsk/Vex-IQ-Storage-Organization`, GitHub Pages from `main`, root folder).

To publish a change: preview it locally, then in VS Code **Source Control** → write a message → **Commit** → **Sync Changes**. The live site updates about a minute later. All paths are relative, so nothing else needs changing.
