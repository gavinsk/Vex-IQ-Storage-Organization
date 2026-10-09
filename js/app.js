"use strict";

// VEX IQ Parts Locator
// All part/location data comes from data/parts.json.
// Physical geometry (cart rows/cols, Akro-Mils drawer count) comes from data/storage-layout.json.
// Part Finder section order and widths come from data/categories.json; true-scale image sizes from images/sizes.json.

const state = {
  parts: [],
  layout: null,
  categories: [],       // from categories.json
  sizes: {},            // image path -> [width, height] in VEX drawing units (images/sizes.json)
  finderCat: null,      // category open in the Part Finder (null = all categories)
  bins: new Map(),      // bin ID -> [parts]  (a part with extraLocations is listed in each of its bins)
  category: "All",
  view: "parts",
};

const $ = id => document.getElementById(id);
const grid = $("grid");
const search = $("search");
const dlg = $("dialog");

// ---------------------------------------------------------------------------
// Small helpers

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, m => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[m]));
}

// Short text for placeholder tiles: "36 Tooth Gear" -> "36T Gear", drop parenthetical detail.
function shortName(name) {
  return name.replace(/\s*\(.*$/, "").replace(/(\d+) Tooth\b/, "$1T").replace(/\bConnector\b/, "Conn.");
}

function colorFor(text) {
  let h = 0;
  for (const ch of text) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return `hsl(${h} 42% 42%)`;
}

// Image if one is set in parts.json, otherwise (or if it fails to load) a placeholder tile.
function partImage(p, size = "") {
  const ph = `<div class="placeholder ${size}" style="background:${colorFor(p.category)}" ${p.image ? "hidden" : ""}>
      <span>${esc(shortName(p.name))}</span><small>Image coming soon</small></div>`;
  if (!p.image) return ph;
  return `<img loading="lazy" src="${esc(p.image)}" alt="${esc(p.name)}"
            onerror="this.hidden=true;this.nextElementSibling.hidden=false">${ph}`;
}

function compact(s) {
  return String(s ?? "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

// "AK03" / "ak3" / "B1-3" / "b13" all compare equal.
function locKey(s) {
  return compact(s).replace(/([a-z])0+(\d)/g, "$1$2");
}

// ---------------------------------------------------------------------------
// Locations

function formatId(fmt, vals) {
  return fmt.replace(/\{(\w+)\}/g, (_, k) => vals[k]);
}

function akroId(n) {
  return state.layout.akroMils.prefix + String(n).padStart(2, "0");
}

function parseLocation(loc) {
  const L = state.layout;
  if (!loc) return { zone: "none" };
  let m = new RegExp(`^${L.akroMils.prefix}(\\d+)$`).exec(loc);
  if (m) return { zone: "akro", num: +m[1] };
  m = /^([A-Z])(\d+)-(\d+)$/.exec(loc);
  if (m && L.cart.sides.some(s => s.id === m[1])) {
    const row = +m[2], col = +m[3];
    const group = L.cart.binGroups.find(g => row >= g.firstRow && row <= g.lastRow && col <= g.cols);
    if (group) return { zone: "cart", side: m[1], row, col, group };
  }
  m = /^([A-Z]+)(\d+)$/.exec(loc);
  const zone = m && L.zones.find(z => z.prefix === m[1]);
  if (zone) return { zone: "other", def: zone, num: +m[2] };
  return { zone: "unknown" };
}

function describeLocation(loc) {
  const p = parseLocation(loc);
  const side = p.side && state.layout.cart.sides.find(s => s.id === p.side);
  switch (p.zone) {
    case "cart":   return `Rolling cart · ${side.name} · Row ${p.row}, position ${p.col} (${p.group.label.toLowerCase().replace(/s$/, "")})`;
    case "akro":   return `${state.layout.akroMils.name} · Drawer ${p.num}`;
    case "other":  return p.def.name;
    default:       return "";
  }
}

// "AK07" -> "drawer 7 (AK07)", matching the printed drawer labels; other bins unchanged.
function placeName(loc) {
  const p = parseLocation(loc);
  return p.zone === "akro" ? `drawer ${p.num} (${loc})` : loc;
}

function binLabel(loc) {
  const parts = state.bins.get(loc);
  return parts ? parts[0].binLabel || parts.map(p => p.name).join(" + ") : "Empty / reserve";
}

// Every bin a part lives in: its main `location` plus any `extraLocations` (high-volume parts split across bins).
function locationsOf(p) {
  return [p.location, ...(p.extraLocations || [])].filter(Boolean);
}

// `hits`: bin IDs to highlight (array or Set).
function binButton(id, hits) {
  const filled = state.bins.has(id);
  const label = filled ? binLabel(id) : "";
  const hit = hits && new Set(hits).has(id);
  return `<button class="bin ${filled ? "filled" : ""} ${hit ? "hit" : ""}" data-bin="${esc(id)}"
            title="${esc(id + (filled ? " — " + label : " — empty"))}">
            <span>${esc(id)}</span>${filled ? `<span class="bin-label">${esc(label)}</span>` : ""}</button>`;
}

// One side of the cart: rows 1–4 are small bins, rows 5–7 medium bins, numbered continuously.
function cartSide(sideId, hits) {
  const cart = state.layout.cart;
  const side = cart.sides.find(s => s.id === sideId);
  return `<div>${cart.binGroups.map(g => {
    let cells = "";
    for (let r = g.firstRow; r <= g.lastRow; r++)
      for (let c = 1; c <= g.cols; c++) cells += binButton(formatId(cart.idFormat, { side: sideId, row: r, col: c }), hits);
    return `<div class="cart-title">${esc(side.name)} — ${esc(g.label.toLowerCase())} (rows ${g.firstRow}–${g.lastRow})</div>
      <div class="cart" style="--cols:${g.cols}">${cells}</div>`;
  }).join("")}</div>`;
}

function akroGrid(hits) {
  const a = state.layout.akroMils;
  let cells = "";
  for (let n = 1; n <= a.drawers; n++) cells += binButton(akroId(n), hits);
  return `<div class="cart" style="--cols:${a.cols}">${cells}</div>`;
}

function zoneList(zone, hits) {
  const ids = [...state.bins.keys()]
    .filter(id => { const p = parseLocation(id); return p.zone === "other" && p.def === zone; })
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  return `<div class="zone-list">${ids.map(id => binButton(id, hits)).join("")}</div>`;
}

// Mini map shown inside the part / bin dialog: one map per area the highlighted bins are in.
function miniMap(locs) {
  const sections = new Map();
  for (const loc of locs) {
    const p = parseLocation(loc);
    if (p.zone === "cart") sections.set("cart" + p.side, () => cartSide(p.side, locs));
    else if (p.zone === "akro") sections.set("akro", () => `<div class="cart-title">${esc(state.layout.akroMils.name)}</div>${akroGrid(locs)}`);
    else if (p.zone === "other") sections.set(p.def.prefix, () => `<div class="cart-title">${esc(p.def.name)}</div>${zoneList(p.def, locs)}`);
  }
  if (!sections.size) return "";
  const note = locs.length > 1 ? "Highlighted = this part's bins." : "Highlighted = this location.";
  return `<div class="mini-map">${[...sections.values()].map(f => f()).join("")}<div class="note">${note} Click any bin to see what's in it.</div></div>`;
}

// ---------------------------------------------------------------------------
// Search
//
// Forgiving by design: word order doesn't matter, plurals and typos are tolerated,
// "36 tooth" = "36T" = "36t", "2 x 4" = "2x4", "60 degree" = "60°", part numbers
// match with or without dashes, and bin IDs match with or without dashes.

const STOP_WORDS = new Set("the a an of and for with where is it its my i to in does do go goes find part parts piece".split(" "));
const SYNONYMS = { axle: "shaft", axel: "shaft", peg: "pin", light: "led", screen: "brain", remote: "controller" };

function normalizeText(s) {
  return String(s ?? "").toLowerCase()
    .replace(/[°º]/g, " deg ")
    .replace(/ø/g, " ")
    .replace(/(\d)\s*(?:x|by)\s*(?=\d)/g, "$1x")                    // 2 x 4 -> 2x4
    .replace(/(\d+)\s*(?:t|tooth|teeth)\b/g, "$1t")                 // 36 tooth -> 36t
    .replace(/(\d+)\s*(?:deg|degree|degrees)\b/g, "$1deg")          // 60 degree -> 60deg
    .replace(/(\d)\s+mm\b/g, "$1mm");
}

function stem(t) {
  if (/\d/.test(t) || t.length <= 3) return t;
  if (t.endsWith("ies")) return t.slice(0, -3) + "y";
  if (t.endsWith("ches") || t.endsWith("shes") || t.endsWith("xes")) return t.slice(0, -2);
  if (t.endsWith("s") && !t.endsWith("ss")) return t.slice(0, -1);
  return t;
}

function tokenize(s, dropStopWords = false) {
  return normalizeText(s)
    .replace(/[^a-z0-9.]+/g, " ")
    .replace(/(?<!\d)\.|\.(?!\d)/g, " ")
    .split(/\s+/)
    .filter(t => t && !(dropStopWords && STOP_WORDS.has(t)))
    .map(t => stem(SYNONYMS[t] || t));
}

// Optimal-string-alignment edit distance (a swap of two letters counts as 1).
function editDistance(a, b, max) {
  if (Math.abs(a.length - b.length) > max) return max + 1;
  const d = Array.from({ length: a.length + 1 }, (_, i) => [i]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1);
    }
  }
  return d[a.length][b.length];
}

function buildIndex(p) {
  const tokens = new Map(); // token -> weight
  const add = (text, w) => tokenize(text).forEach(t => tokens.set(t, Math.max(tokens.get(t) || 0, w)));
  add(p.name, 3);
  add(p.binLabel, 1.5);
  add(p.category, 1);
  add(p.section, 1);
  add(p.storage, 0.5);
  p.partNumbers.forEach(pn => add(pn, 1));
  p._tokens = [...tokens];
  p._pns = p.partNumbers.map(compact);
  p._locs = locationsOf(p).map(locKey);
  p._nameLen = tokenize(p.name).length;
}

function tokenScore(q, tokens) {
  const numeric = /^\d+(\.\d+)?$/.test(q);
  const maxTypos = q.length >= 7 ? 2 : q.length >= 4 ? 1 : 0;
  let best = 0;
  for (const [t, w] of tokens) {
    let s = 0;
    if (t === q) s = 1;
    else if (numeric) {
      // "36" matches "36t" but not "360"
      if (t.startsWith(q) && !/[\d.]/.test(t[q.length])) s = 0.8;
    } else if (t.startsWith(q) && q.length >= 2) s = 0.85;
    else if (q.length >= 4 && t.includes(q)) s = 0.6;
    else if (maxTypos && !/\d/.test(q)) {
      if (editDistance(q, t, maxTypos) <= maxTypos) s = 0.55;
      else if (t.length > q.length && editDistance(q, t.slice(0, q.length), maxTypos) <= maxTypos) s = 0.45;
    }
    best = Math.max(best, s * w);
  }
  return best;
}

// Returns { results: [part], mode: "all" | "location" | "partNumber" | "words" | "closest" }
function runSearch(raw, pool) {
  const q = raw.trim();
  if (!q) return { results: pool, mode: "all" };

  // Exact bin / drawer ID, e.g. "B1-3", "bm11", "AK3"
  const key = locKey(q);
  if (/^[a-z]+\d/.test(key)) {
    const inBin = pool.filter(p => p._locs.includes(key));
    if (inBin.length) return { results: inBin, mode: "location", location: locationsOf(inBin[0]).find(l => locKey(l) === key) };
  }

  // Akro-Mils drawer by its printed label number: "7", "#7", "drawer 7" -> AK07.
  // A bare number could also mean a part ("24" tooth gear), so the drawer comes first, then other matches.
  const dm = /^(drawer|drw)?\s*#?\s*(\d{1,2})$/i.exec(q);
  if (dm && +dm[2] >= 1 && +dm[2] <= state.layout.akroMils.drawers) {
    const id = akroId(+dm[2]);
    const inDrawer = pool.filter(p => p._locs.includes(locKey(id)));
    if (inDrawer.length) {
      if (dm[1]) return { results: inDrawer, mode: "location", location: id };
      const others = wordSearch(q, pool).results.filter(p => !inDrawer.includes(p));
      return { results: [...inDrawer, ...others], mode: "drawer", location: id };
    }
  }

  // Part number, full or partial, with or without dashes
  if (/^[\d\s-]+$/.test(q) && compact(q).length >= 3) {
    const c = compact(q);
    const hits = pool
      .map(p => ({ p, s: p._pns.some(n => n === c) ? 3 : p._pns.some(n => n.endsWith(c)) ? 2 : p._pns.some(n => n.includes(c)) ? 1 : 0 }))
      .filter(x => x.s)
      .sort((a, b) => b.s - a.s);
    if (hits.length) return { results: hits.map(x => x.p), mode: "partNumber" };
  }

  return wordSearch(q, pool);
}

function wordSearch(q, pool) {
  let words = tokenize(q, true);
  if (!words.length) words = tokenize(q);
  const scored = pool.map(p => {
    const scores = words.map(w => tokenScore(w, p._tokens));
    return { p, matched: scores.filter(s => s > 0).length, score: scores.reduce((a, b) => a + b, 0) };
  });
  // Ties go to the shorter name ("36 Tooth Gear" before "XL Turntable 36 Tooth Ring Gear Bushing").
  const byScore = (a, b) => b.matched - a.matched || b.score - a.score || a.p._nameLen - b.p._nameLen;

  const all = scored.filter(x => x.matched === words.length).sort(byScore);
  if (all.length) return { results: all.map(x => x.p), mode: "words" };

  // Nothing matched every word: show parts that matched most of them.
  const need = Math.max(1, Math.ceil(words.length / 2));
  const closest = scored.filter(x => x.matched >= need).sort(byScore).slice(0, 40);
  return { results: closest.map(x => x.p), mode: "closest" };
}

// ---------------------------------------------------------------------------
// Main page rendering

function renderFilters() {
  const cats = ["All", ...new Set(state.parts.map(p => p.category).sort())];
  $("filters").innerHTML = cats.map(c =>
    `<button class="filter ${c === state.category ? "active" : ""}" data-cat="${esc(c)}">${esc(c)}</button>`).join("");
}

function renderCards() {
  const pool = state.parts.filter(p => state.category === "All" || p.category === state.category);
  const { results, mode, location } = runSearch(search.value, pool);

  const note = $("fuzzyNote");
  note.hidden = !(mode === "closest" || mode === "location" || mode === "drawer");
  if (mode === "closest") note.textContent = "No exact match — showing the closest matches.";
  if (mode === "location") note.innerHTML = `Showing everything in <b>${esc(placeName(location))}</b>. <button class="location" data-bin="${esc(location)}">Open bin view</button>`;
  if (mode === "drawer") note.innerHTML = `Everything in <b>${esc(placeName(location))}</b> is shown first, then other matches for “${esc(search.value.trim())}”. <button class="location" data-bin="${esc(location)}">Open drawer</button>`;

  $("count").textContent = `${results.length} part${results.length === 1 ? "" : "s"}`;
  $("empty").hidden = results.length > 0;
  grid.innerHTML = results.map(partCard).join("");
}

function partCard(p) {
  return `
    <article class="card" data-part="${state.parts.indexOf(p)}" tabindex="0">
      <div class="imagebox">${partImage(p)}</div>
      <div class="card-body">
        <h3 class="name">${esc(p.name)}</h3>
        <div class="meta">${esc(p.partNumbers.join(" · "))}</div>
        ${locationsOf(p).map(l => `<button class="location" data-bin="${esc(l)}" title="See everything in this bin">${esc(l)}</button>`).join(" ") || `<span class="location">Not assigned</span>`}
      </div>
    </article>`;
}

function renderMap() {
  const L = state.layout;
  $("storageMap").innerHTML = `
    <section class="map-section">
      <h2>${esc(L.cart.name)}</h2>
      <p>${L.cart.sides.map(s => `<b>${esc(s.name)}:</b> ${esc(s.purpose)}`).join(" &nbsp;·&nbsp; ")}</p>
      <div class="cart-sides">${L.cart.sides.map(s => cartSide(s.id)).join("")}</div>
    </section>
    <section class="map-section">
      <h2>${esc(L.akroMils.name)}</h2>
      <p>${L.akroMils.drawers} drawers, ${esc(L.akroMils.prefix)}01–${esc(akroId(L.akroMils.drawers))}</p>
      ${akroGrid()}
    </section>
    ${L.zones.map(z => `
      <section class="map-section">
        <h2>${esc(z.name)}</h2><p>${esc(z.description || "")}</p>
        ${zoneList(z)}
      </section>`).join("")}`;
}

// ---------------------------------------------------------------------------
// Part Finder: browse by type (category tiles -> parts grouped by `type`)

// Categories in categories.json order, then any others found in parts.json.
function finderCategories() {
  const used = new Set(state.parts.map(p => p.category));
  const listed = state.categories.filter(c => used.has(c.name));
  const extra = [...used].filter(n => !listed.some(c => c.name === n)).sort().map(name => ({ name }));
  return [...listed, ...extra];
}

// Sizes first ("0.25x" < "0.5x" < "1x"), then natural order ("1x2" < "1x10").
function bySize(a, b) {
  const num = p => { const m = /^\d+(\.\d+)?/.exec(p.name); return m ? +m[0] : Infinity; };
  return num(a) - num(b) || a.name.localeCompare(b.name, undefined, { numeric: true });
}

// Parts of one category, split into its `type` groups in categories.json order.
function typeGroups(cat) {
  const parts = state.parts.filter(p => p.category === cat.name).sort(bySize);
  const order = cat.types || [];
  const rank = t => order.indexOf(t) + 1 || 999;
  return [...new Set(parts.map(p => p.type || "Other"))]
    .sort((a, b) => rank(a) - rank(b) || a.localeCompare(b))
    .map(type => ({ type, parts: parts.filter(p => (p.type || "Other") === type) }));
}

// One picture on the poster, drawn at its real relative size (like VEX's kit poster).
function posterItem(p) {
  const [w, h] = state.sizes[p.image] || [80, 80];
  const tip = `${p.name} · ${locationsOf(p).join(" + ")}`;
  const pic = p.image
    ? `<img loading="lazy" src="${esc(p.image)}" alt="" style="--w:${w};--h:${h}">`
    : `<span class="poster-missing">${esc(shortName(p.name))}</span>`;
  return `<button class="poster-part" data-part="${state.parts.indexOf(p)}" data-tip="${esc(tip)}" aria-label="${esc(tip)}">${pic}</button>`;
}

function posterPanel(cat) {
  return `
    <section class="poster-panel" data-span="${cat.span || 1}">
      <h2><button data-finder="${esc(cat.name)}">${esc(cat.name)} <span>›</span></button></h2>
      ${typeGroups(cat).map(g => `<div class="poster-group" title="${esc(g.type)}">${g.parts.map(posterItem).join("")}</div>`).join("")}
    </section>`;
}

// Masonry: each panel spans its columns and as many 8px rows as its height needs.
function layoutPoster() {
  const poster = document.querySelector(".poster");
  if (!poster || poster.offsetParent === null) return;
  const cols = getComputedStyle(poster).gridTemplateColumns.split(" ").length;
  const row = parseFloat(getComputedStyle(poster).gridAutoRows);
  const gap = 14;
  for (const panel of poster.children) {
    panel.style.gridColumn = `span ${Math.min(+panel.dataset.span, cols)}`;
    panel.style.gridRowEnd = `span ${Math.ceil((panel.getBoundingClientRect().height + gap) / row)}`;
  }
}

function renderFinder() {
  const cats = finderCategories();
  const cat = cats.find(c => c.name === state.finderCat);
  const box = $("finderView");

  if (!cat) {
    box.innerHTML = `
      <h2 class="finder-title">Explore the VEX IQ parts</h2>
      <p class="finder-help">Click a part to see its name and where it goes. Click a section title to see that section as a list.</p>
      <div class="poster">${cats.map(posterPanel).join("")}</div>`;
    layoutPoster();
    return;
  }

  const groups = typeGroups(cat);
  box.innerHTML = `
    <nav class="crumbs"><button data-finder="">‹ Back to all parts</button><span>›</span><b>${esc(cat.name)}</b></nav>
    <div class="filters finder-chips">${cats.map(c =>
      `<button class="filter ${c === cat ? "active" : ""}" data-finder="${esc(c.name)}">${esc(c.name)}</button>`).join("")}</div>
    ${groups.map(g => `<section class="type-group">
        ${groups.length > 1 ? `<h3>${esc(g.type)} <span>${g.parts.length}</span></h3>` : ""}
        <div class="grid">${g.parts.map(partCard).join("")}</div>
      </section>`).join("")}`;
}

// Navigate via the URL hash so the browser Back button works (#finder, #finder=Gears).
function goFinder(cat) {
  const hash = cat ? "finder=" + encodeURIComponent(cat) : "finder";
  if (location.hash.slice(1) === hash) showFinder(cat);
  else location.hash = hash;
}

function showFinder(cat) {
  state.finderCat = cat || null;
  setView("finder");
  window.scrollTo(0, 0);
}

function setView(view) {
  state.view = view;
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.view === view));
  $("partsView").hidden = view !== "parts";
  $("mapView").hidden = view !== "map";
  $("finderView").hidden = view !== "finder";
  $("filters").hidden = view !== "parts";
  $("count").hidden = view !== "parts";
  if (view === "map") renderMap();
  if (view === "finder") renderFinder();
  // Leaving the finder: drop its hash so a reload doesn't jump back into it.
  else if (location.hash.includes("finder")) history.replaceState(null, "", location.pathname + location.search);
}

// ---------------------------------------------------------------------------
// Dialog: part detail and bin contents

let dialogStack = [];
let currentView = null;

function showDialog(view) {
  if (dlg.open && currentView) dialogStack.push(currentView);
  else dialogStack = [];
  renderDialog(view);
}

function renderDialog(view) {
  currentView = view;
  $("backBtn").hidden = dialogStack.length === 0;
  if (view.type === "part") renderPart(view.part);
  else renderBin(view.loc);
  if (!dlg.open) dlg.showModal();
  dlg.scrollTop = 0;
}

// RETURN TO block: one big button, or (for parts split across bins) one button per bin.
function returnTo(p) {
  const locs = locationsOf(p);
  if (locs.length <= 1) return `
    <button class="big-location" data-bin="${esc(p.location)}">
      <small>RETURN TO</small><b>${esc(p.location || "Not assigned")}</b>
      <div>${esc(describeLocation(p.location) || p.storage)}</div>
      <div class="hint">Click to see everything in this bin ›</div>
    </button>`;
  return `
    <div class="big-location multi">
      <small>RETURN TO — ANY OF THESE ${locs.length} BINS</small>
      <div class="multi-bins">${locs.map(l => `
        <button data-bin="${esc(l)}"><b>${esc(l)}</b><span>${esc(describeLocation(l))}</span></button>`).join("")}
      </div>
      <div class="hint">This part is split across ${locs.length} bins. Click a bin to see what's in it ›</div>
    </div>`;
}

function renderPart(p) {
  $("dialogTitle").textContent = "Part location";
  $("dialogBody").innerHTML = `
    <div class="detail">
      <div class="detail-image">${partImage(p, "large")}</div>
      <div>
        <h2>${esc(p.name)}</h2>
        <div><button class="badge badge-link" data-finder="${esc(p.category)}" title="See all ${esc(p.category)}">${esc(p.category)} ›</button><span class="badge">${esc(p.storage)}</span></div>
        ${returnTo(p)}
        <div class="fact-grid">
          <div class="fact"><small>Bin / drawer label</small><b>${esc(p.binLabel || "—")}</b></div>
          <div class="fact"><small>Classroom quantity</small><b>${Number(p.quantity || 0).toLocaleString()}</b></div>
          <div class="fact"><small>VEX part number(s)</small><b>${esc(p.partNumbers.join(", ") || "—")}</b></div>
          ${p.use ? `<div class="fact use"><small>How it's used</small><p>${esc(p.use)}</p></div>` : ""}
        </div>
        ${miniMap(locationsOf(p))}
      </div>
    </div>`;
}

function renderBin(loc) {
  const parts = state.bins.get(loc) || [];
  const desc = describeLocation(loc);
  $("dialogTitle").textContent = parseLocation(loc).zone === "akro" ? `Drawer ${parseLocation(loc).num} (${loc})` : `Bin ${loc}`;
  $("dialogBody").innerHTML = `
    <div class="bin-view detail-like">
      <div class="big-location">
        <small>${parts.length ? "IN THIS BIN" : "EMPTY BIN"}</small><b>${esc(loc)}</b>
        <div>${esc(desc)}</div>
      </div>
      ${parts.length ? `<div class="fact"><small>Bin label</small><b>${esc(binLabel(loc))}</b></div>` : ""}
      <div class="bin-list">
        ${parts.length ? parts.map(p => `
          <button class="bin-item" data-part="${state.parts.indexOf(p)}">
            <div class="thumb">${partImage(p, "tiny")}</div>
            <div class="info"><b>${esc(p.name)}</b><small>${esc(p.partNumbers.join(" · "))}</small>
              ${locationsOf(p).length > 1 ? `<small class="also">Also in ${esc(locationsOf(p).filter(l => l !== loc).join(", "))}</small>` : ""}</div>
            <div class="qty">× ${Number(p.quantity || 0).toLocaleString()}</div>
          </button>`).join("")
        : `<p class="note">Nothing is assigned to this location yet — it's available as reserve / overflow.</p>`}
      </div>
      ${miniMap([loc])}
    </div>`;
}

// ---------------------------------------------------------------------------
// Events

document.addEventListener("click", e => {
  const bin = e.target.closest("[data-bin]");
  if (bin) { e.stopPropagation(); if (bin.dataset.bin) showDialog({ type: "bin", loc: bin.dataset.bin }); return; }
  const finder = e.target.closest("[data-finder]");
  if (finder) { if (dlg.open) dlg.close(); goFinder(finder.dataset.finder); return; }
  const part = e.target.closest("[data-part]");
  if (part) { showDialog({ type: "part", part: state.parts[+part.dataset.part] }); return; }
  const cat = e.target.closest("[data-cat]");
  if (cat) { state.category = cat.dataset.cat; renderFilters(); renderCards(); return; }
  const tab = e.target.closest("[data-view]");
  if (tab) tab.dataset.view === "finder" ? goFinder(null) : setView(tab.dataset.view);
});

grid.addEventListener("keydown", e => {
  const card = e.target.closest(".card");
  if (card && e.key === "Enter" && e.target === card) showDialog({ type: "part", part: state.parts[+card.dataset.part] });
});

search.addEventListener("input", () => {
  if (state.view !== "parts") setView("parts");
  renderCards();
});

$("closeBtn").addEventListener("click", () => dlg.close());
$("backBtn").addEventListener("click", () => { if (dialogStack.length) renderDialog(dialogStack.pop()); });
dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close(); });
dlg.addEventListener("close", () => { dialogStack = []; currentView = null; });

// ---------------------------------------------------------------------------
// Startup

function validate() {
  for (const p of state.parts) {
    if (!p.location) console.warn("No location:", p.name);
    for (const loc of locationsOf(p))
      if (["none", "unknown"].includes(parseLocation(loc).zone)) console.warn("Unrecognized location:", loc, p.name);
  }
}

// Optional deep links (e.g. for QR codes on bins): #bin=B1-3, #q=36 tooth, #view=map, #finder=Gears
function handleHash() {
  const params = new URLSearchParams(location.hash.slice(1));
  if (params.has("finder")) { showFinder(params.get("finder")); return; }
  if (!location.hash && state.view === "finder") setView("parts");
  if (params.get("view")) setView(params.get("view") === "map" ? "map" : "parts");
  if (params.get("q")) { search.value = params.get("q"); renderCards(); }
  if (params.get("bin")) showDialog({ type: "bin", loc: params.get("bin").toUpperCase() });
}

async function init() {
  try {
    const [parts, layout, categories, sizes] = await Promise.all([
      fetch("data/parts.json").then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }),
      fetch("data/storage-layout.json").then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }),
      // Optional: without it the finder still works, with categories in alphabetical order.
      fetch("data/categories.json").then(r => r.ok ? r.json() : []).catch(() => []),
      fetch("images/sizes.json").then(r => r.ok ? r.json() : {}).catch(() => ({})),
    ]);
    state.parts = parts;
    state.layout = layout;
    state.categories = categories;
    state.sizes = sizes;
  } catch (err) {
    $("partsView").hidden = true;
    const box = $("loadError");
    box.hidden = false;
    box.innerHTML = `Couldn't load the parts data (${esc(err.message)}).<br>
      If you opened index.html directly from your computer, preview it with a local web server instead
      (VS Code "Live Server", or <code>python3 -m http.server</code>).`;
    return;
  }
  for (const p of state.parts) {
    buildIndex(p);
    for (const loc of locationsOf(p)) {
      if (!state.bins.has(loc)) state.bins.set(loc, []);
      state.bins.get(loc).push(p);
    }
  }
  validate();
  renderFilters();
  renderCards();
  handleHash();
}

window.addEventListener("hashchange", handleHash);
let resizeFrame = 0;
window.addEventListener("resize", () => { cancelAnimationFrame(resizeFrame); resizeFrame = requestAnimationFrame(layoutPoster); });
init();
