# CLAUDE.md — VEX IQ Parts Locator & Storage Project

## Current status (Oct 2026)

**Done**
- Site split into static files: `index.html`, `css/style.css`, `js/app.js`, `data/parts.json`, `data/storage-layout.json`
- Forgiving search (typos, plurals, word order, "36 tooth" = "36T", part numbers with or without dashes, bin IDs)
- Drawer-number search: "7", "#7", "drawer 7" find Akro-Mils drawer AK07 (the printed labels show plain numbers). A bare number lists the drawer first, then other matches ("24" → drawer 24, then 24T gear); "drawer N" shows only the drawer. Drawer popups are titled "Drawer 7 (AK07)"
- Bin views: clicking any bin or location badge lists everything in that bin; **Storage map** tab shows the whole cart, Akro-Mils drawers, and other zones
- **Part Finder** tab, copied from VEX's "Explore the VEX IQ (2nd gen) Kit Contents" poster: boxed category panels in a masonry grid, every part drawn at true relative size and grouped by `type`; hover shows name + bin, click opens the part. A panel title opens that category as a list of cards. Panel order, width (`span`, of 4 columns), and type order live in `data/categories.json`; image sizes in `images/sizes.json`
- Deep links: `#bin=B1-3`, `#q=36 tooth`, `#view=map`, `#finder`, `#finder=Gears` (intended for QR codes / labels)
- Bin-assignment spreadsheet: `tools/bin-assignments.xlsx` + `tools/apply_bin_sheet.py`
- **Cart re-layout (Oct 9, 2026)**, from Gavin's edited sheet: corner connectors moved to Side A rows 1–2, beams to rows 3–5, plates and angle/special beams to Side A medium bins; lock parts, shafts, belts, rubber bands, and magnetic beams moved to Side B row 3–4; pulleys to B7-3/B7-4. Gavin confirmed all of this, including the combined sensor bin and the four shafts sharing one bin.
- **Parts in more than one bin**: `extraLocations` (e.g. 1x1 Connector Pin in B4-5 + B4-6). The site shows every bin, and the spreadsheet allows a part in several rows.
- **Akro-Mils re-layout (Oct 9, 2026)** from Gavin's sheet: washers/spacers/collars/bushing in AK01–AK07, capped shafts AK17–AK20 and motor shafts AK21–AK24 (plastic + metal of the same length share a drawer — Gavin's choice), connector/idler pins AK26–AK31, standoffs AK33–AK42. Rubber Shaft Collar, 2x and 6x Standoff each use 2 drawers.
- **Merged** the EES "Elastic Band Anchor Plate" (228-3616-157) into **Rubber Band Anchor** (same part, different color, per Gavin): qty 41, B3-8, VEX image.
- **Live on GitHub Pages (Oct 9, 2026):** public repo `gavinsk/Vex-IQ-Storage-Organization` (Gavin kept this name) → **https://gavinsk.github.io/Vex-IQ-Storage-Organization/**. Publishing = commit + Sync in VS Code. Commits use his GitHub no-reply email (repo-local git config).
- **"Works with" links** in the part popup: clickable thumbnails of related parts (rack gear ↔ slide bracket, pulleys ↔ belts, hub ↔ tire, motor shafts ↔ Smart Motor…), defined as groups in `data/related.json` (`{note, parts:[…]}` = all linked to each other; `{note, a:[…], b:[…]}` = every a ↔ every b). Links are always two-way; unknown names log a console warning. Drafted by Claude for Gavin's review.
- **Build List tab** (bill of materials + cost): teams count the parts marked `"buildList": true` (84 — Gavin's rule, Oct 19 2026: all gears incl. every rack gear but no rack/linear brackets, all sprockets, all pulleys (not the tire add-on), all beams and plates 3+ long (incl. lock beams, linear motion beams) plus the 2x2 Beam and 2x2 Round Lock Beam, lock plates, angle/tee/gusset beams, **all standoffs, all shafts (metal, motor, capped, plastic)**; smooth panel, magnetic beams, 1x1/1x2 beams, worm bracket excluded) **plus groups** from `data/build-list-groups.json` that count similar parts as one item (**"Corner Connector (any type)"** = all 17 corner connectors, $0.15 = average of the sheet's corner-connector prices). Each item shows price each, line cost, and total; **cost appears only on the Build List** (Gavin's rule). Prices: `cost` in parts.json from Gavin's EES price sheet (Google Sheet "ees_231_VEX_IQ_Price_Sheet (1)", id 1RPG5iW6fS58hwIXDCvRVARt7sMVQi7Auy6WLu5guSJg); parts not on the sheet have estimated prices following its size pattern and `"costEstimate": true` (shown with *). Lists are named by project, saved per browser in `localStorage` (several per MacBook, picker) and reopenable anywhere via **Save link** (`#bom=` base64url JSON of `{t: title, i: [[key, qty]…]}`, key = first part number, or `g:<group id>`; reopening an older link asks before replacing a same-named list). Warns when a list needs more than the room has; Copy list / Print (print shows only the list, with costs). A Build List part's popup has "+ Add to build list" (group members add to their group). No class-wide view of other teams' lists (would need a Google Sheet via Apps Script — Gavin chose to start without it).
- All 162 parts have images (see **Images** below)
- Reference files moved into `docs/`

**Next**
1. **Bin labels** — Akro-Mils drawer labels done (`tools/make_akro_labels.py` → `labels/akro-mils-5195.pdf`, Avery 5195, one per filled drawer: number, label, picture; plastic+metal drawers show the metal part; motor and capped shafts get a zoomed close-up of the colored ring / cap with a zigzag break line; motor-shaft drawers show metal and plastic stacked; 2x/4x/6x standoffs show both snap ends with break lines and a small gap (ends matter, not length). Close-ups go to `labels/img/` — labels only, the website keeps full parts). Gavin only wants labels for the Akro-Mils drawers (small parts); re-run the script after drawer changes.
2. **QR codes** for the cart / bins using the deep links
3. **Overflow pass** — partly done: Gavin split 10 high-volume parts across 2 bins (`extraLocations`). Revisit only if he wants refill bins for other parts.
4. **Akro-Mils capacity pass** — only if Gavin asks; he adjusts physical fit himself
5. Optional: lightweight edit mode for locations. Options discussed: (A) site edit mode that saves via a repo-scoped GitHub token, (B) edit on site → download `parts.json` → commit, (C) local-only edit mode that saves to disk via Chrome's File System Access API. Recommendation was A for editing at the cart, C to keep review-before-publish. For now Gavin moves parts with the bin spreadsheet.

**`docs/` is not on GitHub** (Gavin's choice, `.gitignore`d). It exists only on his Mac: saved VEX pages, EES PDFs, old workbook, image-source CSV. Never `git add -f` it.

**Open questions for Gavin**
- **1x3 Beam (A3-4, qty 8):** listed only in the 4 PLTW EES VEX IQ Kits (228-7340, 2 each). Gavin hasn't found any yet. If he can't, lower the quantity or remove the part.
- **EES Rack Gear / Linear Slide Bracket (B2-6) vs. Linear Motion Pack parts (B7-1/B7-2):** kept separate (the EES rack looks like an older design). Merge only if Gavin confirms they're identical.
- **Price sheet part-number mismatch:** the EES price sheet lists the Worm Bracket as 228-2500-220, but parts.json has 228-2500-220 on the Double 2x Wide, 2x2 Corner Connector. Not used (neither is priced individually), but check a physical part before trusting either.
- **Poster sizes:** the 42 PNG/WebP images use estimated real-world widths (`ESTIMATED_WIDTH` in `tools/measure_images.py`). Adjust any that look wrong next to their neighbors.

**Regenerating derived files after data changes**
- Changed bins by hand in `parts.json` → `tools/make_bin_sheet.py` (needs openpyxl; use a scratch venv) to rebuild the spreadsheet
- Added/replaced an image → `python3 tools/measure_images.py`, and add a `images/manifest.json` entry

---

## Project purpose

1. **Physically organize a large VEX IQ classroom inventory** into a rolling parts cart, an Akro-Mils drawer organizer, vertical hangers, and protected/external storage.
2. **Provide a student-facing website** to identify a part visually and see where it belongs — both a find-a-part tool ("Where is the 36T gear?") and a return-a-part tool ("Where does this go?").

Owner: Gavin, a high school engineering/science teacher. Students use the site on MacBooks. No login, database, backend, or paid hosting. The repository files are the source of truth, not chat transcripts.

---

## Decisions Gavin has made

- **`data/parts.json` is the single source of truth** for every part's location, label, quantity, and image. The cart map, bin views, and search all derive from it.
- **Quantities are combined totals.** All kits are pooled; `quantity` is the classroom total. No per-kit breakdowns.
- **Physical fit checks are not required** (beam length vs. bin, bulk quantity vs. drawer volume). Gavin adjusts physical fit while organizing.
- **Akro-Mils IDs use `AK`** (`AK01`–`AK64`) so they can't be confused with cart Side A.
- **Medium bins are rows 5–7** of each cart side (e.g. `B6-3`), continuing the small-bin numbering. The old `AM`/`BM` IDs are retired.
- **Images:** official VEX SVGs are preferred; EES PDF pictures are used where no VEX image exists.

---

## Inventory

Based on **11 × VEX IQ Robotics Kits + 4 × PLTW EES VEX IQ Kits + 4 × PLTW EES Supplemental Kits + 6 × Linear Motion Packs (228-7887)**. Do not revert to a one-kit assumption.

**162 normalized physical parts.** Sanity-check totals: 1x1 Connector Pin 3,391 · 1x2 Connector Pin 823 · 2x2 Connector Pin 311 · 12T Gear 234 · Washer 536 · Rubber Shaft Collar 472 · Chain Link 1,383 · each sensor 11.

If a quantity looks suspicious, verify it against `docs/VEX_IQ_Storage_Plan_Physical_Cart_Layout.xlsx` before changing it. (The workbook still uses the old `BM`/`A##` location IDs; the website doesn't read it.)

### Part normalization — critical

**Do not identify duplicate physical parts by part number alone.** VEX/PLTW use different prefixes for the same part, e.g. `228-3201-131` (EES) and `228-2500-131` (Robotics Kit) are both the 2x Wide, 2x1 Offset Corner Connector. Treat these as **one part** and keep **all** part numbers as aliases in `partNumbers`.

When reconciling:
1. Match by normalized name / physical geometry.
2. Preserve all known part numbers.
3. Use images/geometry to verify ambiguous matches.
4. Matching numeric suffixes are a hint, not proof.
5. The PDFs' **Kit** column (e.g. `228-3513`) is not a part number.

Different sizes are different parts (1x4 Beam ≠ 1x6 Beam, 12T ≠ 36T).

---

## Physical storage

| Zone | Layout | IDs |
|---|---|---|
| Rolling cart, 2 identical sides (A, B) | Rows 1–4: 8 small bins each (6.46 × 4.09 × 2.99 in). Rows 5–7: 5 medium bins each (9.37 × 5.83 × 5 in) | `A1-1`…`A7-5`, `B1-1`…`B7-5` |
| Akro-Mils organizer | 64 small drawers (layout assumed 8 across — change `cols` in `storage-layout.json` if wrong) | `AK01`…`AK64` |
| Vertical hangers | Cables (long beams moved to Side A medium bins) | `V01`… |
| External / protected | Brains, controllers, batteries, motors | `E01`… |

ID format for cart bins: side letter, row, position (`B6-3` = Side B, row 6, position 3).

**Side A — structure:** rows 1–2 all corner and chassis connectors; row 3 1x beams; row 4 2x beams; medium bins (rows 5–7) hold long beams (2x10 through 2x20), plates, the smooth panel + pin tool, and angle/tee/right-angle beams. A6-3 and A6-4 are empty.

**Side B — motion, hardware & sensors:** row 1 gears, row 2 sprockets + Optical/Distance Sensors (sharing B2-6), Bumper Switches and Touch LEDs; row 3 lock beams/plates, all four pitch shafts, belts, crank arm, worm gear, rubber bands; row 4 magnetic beams, standoff connectors, connector pins. Medium bins hold chain, XL turntable, wheels/tires/hubs, intake/traction, rope/spool, cable anchors, the EES rack gear + linear slide bracket (B6-5), Linear Motion Pack parts (B7-1, B7-2), and pulleys (B7-3, B7-4). B6-4 and B7-5 are empty.

The Linear Motion Pack parts (228-2500-14xx) are a different system from the EES **Rack Gear** (228-3196-216) and **Linear Slide Bracket** (228-3196-217) in B2-6. Don't merge them unless Gavin confirms they're identical.

For exactly what is in each bin, read `data/parts.json` or open the site's Storage map — **don't keep a separate copy of the bin list in this file**; it goes stale.

### Storage philosophy

Not "one bin per part." Priority order: **frequency of use → ease of identification → physical volume → conserving bin count.**

- **Good combinations:** visually distinct parts with a useful relationship (1x6 Beam + 6x Pitch Shaft).
- **Bad combinations:** similar shaft lengths, similar connector geometries, similar belts/pulleys, anything students often confuse.

Explicit preferences:
- All gears, all sprockets, all plates and beams that fit, and high-use connector pins → rolling small bins
- Extra-long beams → vertical storage
- Sensors: Bumper Switches and Touch LEDs each have their own small bin. **Gavin chose to put the Optical and Distance Sensors together in B2-6** (the apply script still warns about it; that's expected)

### High-volume parts

A location doesn't guarantee the whole quantity fits (1x1 Connector Pins: 3,391). A part can live in several bins: `location` is the main bin and `extraLocations` lists the others. Don't move a high-use part out of the cart just because it overflows.

---

## Repository layout

```text
index.html              page structure only — no data
css/style.css
js/app.js               search, cards, bin views, storage map, deep links
data/parts.json         source of truth (162 parts)
data/storage-layout.json  physical geometry only (cart rows/cols, Akro-Mils count, zones)
data/categories.json    Part Finder: panel order, panel width (span), order of types
data/related.json       "Works with" groups of parts that go together (by part name)
data/build-list-groups.json  Build List items that count several similar parts as one (e.g. corner connectors), with a price
images/sizes.json       true-scale image sizes for the poster (regenerate: python3 tools/measure_images.py)
images/<category>/      part images (.svg, .png, one .webp)
images/manifest.json    where every image came from and how it was identified
tools/                  bin-assignments.xlsx (Excel editing sheet) + make/apply scripts
labels/                 printable Akro-Mils drawer labels (generated; Avery 5195)
docs/                   LOCAL ONLY (.gitignore): storage workbook, EES parts-list PDFs, saved VEX pages, image-source CSV, archived prototype
README.md               how to preview, edit, and publish
```

A part record:

```json
{
  "name": "36 Tooth Gear",
  "partNumbers": ["228-2500-214", "228-3196-214"],
  "location": "B1-3",
  "extraLocations": ["B1-4"],
  "storage": "Rolling - Small",
  "binLabel": "36T Gear",
  "quantity": 106,
  "category": "Gears",
  "section": "Gears + Shafts",
  "type": "Spur Gears",
  "use": "A 36-tooth gear transfers rotation from one shaft to another. …",
  "buildList": true,
  "cost": 0.85,
  "image": "images/gears/36-tooth-gear.svg"
}
```

- `extraLocations` (optional): more bins holding the same part. Search, cards, the poster, the RETURN TO block, the mini map, and bin views all use every bin. Leave it out for single-bin parts.
- `binLabel` should be identical for every part sharing a location (the bin view uses the first one). A part in several bins uses one label for all of them.
- `use`: 1–3 student-friendly sentences on what the part does and how it connects, shown as **How it's used** in the part popup (replaced the Section line, Oct 2026). Drafted by Claude (Shaft Bushing text is Gavin's); **Gavin reviewed and approved all 162 (Oct 9, 2026)**. Write new parts' descriptions in the same style; Gavin's wording wins on any edit.
- `buildList` (optional, `true`): the part appears in the Build List tab. `cost` is its price per piece (Build List only); `costEstimate: true` marks an estimate. Build-list links key parts by their **first** part number, so don't reorder `partNumbers` on Build List parts. Parts in a `data/build-list-groups.json` group (matched by `category` or a `parts` name list) are counted as the group instead.
- `section` is from the original storage plan and no longer matches the Oct 2026 layout. It is no longer displayed; ask Gavin before relying on it.
- `type` is the Part Finder subgroup within a category (e.g. 1x Beams, Idler Pins). A new type appears automatically; add it to that category's `types` in `categories.json` to control its order.
- `storage` is the storage type (`Rolling - Small`, `Rolling - Medium`, `Akro-Mils Drawer`, `Vertical Hanger`, `Vertical Cable Hanger`, `External / …`, `Tool Storage`).
- Empty `image` shows a generated placeholder tile.
- After adding or replacing an image, run `python3 tools/measure_images.py`. VEX SVGs are already at true scale (~36 units per pitch, the viewBox size is used). PNG/WebP renders have no scale, so add an estimated width to `ESTIMATED_WIDTH` in that script.

### Architecture rules

- Static HTML/CSS/vanilla JS/JSON. No frameworks, no backend. Hosted on GitHub Pages with **relative paths**.
- Never hard-code a location in markup, the map, or a JS lookup table — everything derives from `location` in `parts.json` plus geometry from `storage-layout.json`.
- `app.js` validates locations at startup and logs unrecognized ones to the console; invalid cart IDs (e.g. `B5-6`, `B8-1`) are rejected, not drawn.
- The site loads JSON with `fetch`, so it must be served (VS Code Live Server or `python3 -m http.server`); opening `index.html` directly won't load data.

### UX requirements

- Large search box, part cards with images, category filters, responsive layout.
- Search matches name, all part numbers, category, section, bin label, and location. Must handle: `36 tooth`, `228-3196-214`, `228-2500-214`, `corner connector`, `optical`, `B1-3`.
- Part detail: name, image, quantity, all part numbers, category, storage type, bin label, how it's used, works-with links, and the most prominent element **RETURN TO → [LOCATION]**, plus a mini map with the bin highlighted.
- Every bin on every map is clickable and shows that bin's contents.

---

## Images

All 162 parts have images; provenance for each is in `images/manifest.json`.

- **118 official VEX SVGs** from the VEX IQ Gen 2 parts catalog (https://www.vexrobotics.com/parts/228-7755) — individual SVGs or parts cropped out of VEX composite SVGs.
  - Composite crops were identified by **measured geometry** (hole count, length, gear/sprocket diameter, bend angle), then cross-checked against VEX's own "listed top-down" kit-page order. The image-source CSV's composite positions were often wrong — don't trust them.
  - Corner-connector naming is easy to swap: in VEX's composites, **1x2** connectors are 2 rows of pins with stacked holes; **2x1** connectors are single-row with holes extending outward.
- **32 PNGs** extracted from the EES kit PDFs (`docs/ees-parts-lists/`, 228-7340 and 228-7341), matched to parts by table row. Low resolution (~100–220 px). Pulley pictures are scaled to fit their rows, so their sizes couldn't be cross-checked.
- **Cable Anchor**: VEX product render (WebP) supplied by Gavin.
- **Gavin's DXF drawings** (isometric line art, preferred over VEX/EES pictures for these parts at his request): Shaft Bushing, Rubber Shaft Collar, 0.5x Pitch Standoff Extender. Convert new ones with `tools/dxf_to_svg.py` (needs ezdxf in a scratch venv), add the part to `ESTIMATED_WIDTH` in `tools/measure_images.py`, update `images/manifest.json`.
- **Linear Motion Pack (8 parts, `images/linear-motion/`)**: 5 cropped from VEX Library Competition Kit diagrams (`docs/Linear Motion 1X Pictures_files/image12.png`, `docs/Gears Image with 1x Rack Gear.png`); the 1x20 rack, 1x6 rack, and 1x5 beam are cropped from the 228-7887 product photo (identified by group count and length). Replace with VEX SVGs if they become available.

Rules:
- Prefer official VEX SVGs. Replace an EES PNG with a VEX SVG if one becomes available.
- Never present a category/group image as an exact part image.
- The VEX website (not the content server) sits behind a Cloudflare bot check; command-line and headless fetches of vexrobotics.com pages fail. Ask Gavin to save pages from his browser if needed.

---

## Workflow

VS Code → edit → preview locally → commit → sync/push → GitHub Pages updates.

- Don't auto-push every save; Gavin reviews before publishing.
- Don't design workflows that need ZIP downloads, manual uploads to GitHub, or pasting big code blocks.

### Tooling notes for Claude

- **Node is not installed.** To test JS logic, use macOS JavaScriptCore: `/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc`.
- **Visual checks:** serve with `python3 -m http.server`, screenshot with headless Chrome (`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --headless=new --screenshot=… --virtual-time-budget=3000`). Chrome doesn't exit on its own here — wrap it with `perl -e 'alarm 15; exec @ARGV' …`.
- Python packages (e.g. PyMuPDF for PDFs) go in a scratch virtualenv, not the system Python.

---

## Rules for changes

Before modifying storage assignments:
1. Inspect `parts.json` and the current map.
2. Respect the storage preferences above.
3. Don't silently renormalize parts or drop part-number aliases.
4. Check whether the target bin is occupied — flag conflicts instead of creating accidental shared bins.
5. Change only the data; the site derives everything else.

### Validation after significant edits

- every part has a valid location, including each `extraLocations` entry (`app.js` warns in the console)
- every part number is still searchable
- no unrelated parts accidentally share a location
- cart IDs fit the geometry (rows 1–4 × 8, rows 5–7 × 5; sides A/B)
- sensors stay in separate bins, except Optical + Distance in B2-6 (Gavin's choice)
- every `image` path exists
- site works when served statically with relative paths

---

## Decision-making style

- Optimize for real classroom use and student success, not taxonomic neatness.
- Call out conflicts and questionable assumptions; offer better alternatives when an organization will confuse students.
- Prefer local changes over reorganizing the whole system.
- **Treat project files and inventory data as authoritative** — don't rebuild from generic VEX knowledge when project data exists.
