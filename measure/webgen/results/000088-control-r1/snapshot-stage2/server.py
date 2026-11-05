#!/usr/bin/env python3
"""Species Biological Information Database.

Standard library only (http.server + sqlite3). Server-rendered HTML, so every
feature works in a plain Chromium browser without any JavaScript framework.

Environment variables:
  PORT      port to listen on (default 8000), bound to 127.0.0.1
  DATA_DIR  directory for the SQLite database (created if missing)
"""
import html
import os
import re
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

PORT = int(os.environ.get("PORT", "8000"))
DATA_DIR = os.environ.get(
    "DATA_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
)
DB_PATH = os.path.join(DATA_DIR, "species.db")
WRITE_LOCK = threading.Lock()

KINGDOMS = ["Animalia", "Plantae", "Fungi", "Protista", "Bacteria", "Archaea"]
STATUSES = [
    "Least Concern",
    "Near Threatened",
    "Vulnerable",
    "Endangered",
    "Critically Endangered",
    "Extinct in the Wild",
    "Extinct",
    "Data Deficient",
]
THREATENED = {"Vulnerable", "Endangered", "Critically Endangered"}
HABITATS = [
    "Marine",
    "Freshwater",
    "Terrestrial",
    "Forest",
    "Grassland",
    "Desert",
    "Wetland",
    "Mountain",
    "Arctic",
    "Host-associated",
]
DIETS = [
    "Carnivore",
    "Herbivore",
    "Omnivore",
    "Detritivore",
    "Photosynthetic",
    "Parasitic",
    "Symbiotic",
]
SORTS = {
    "name": ("Common name (A-Z)", "COALESCE(NULLIF(common_name, ''), scientific_name) COLLATE NOCASE"),
    "scientific": ("Scientific name (A-Z)", "scientific_name COLLATE NOCASE"),
    "length": ("Longest first", "typical_length_cm IS NULL, typical_length_cm DESC"),
    "lifespan": ("Longest-lived first", "lifespan_years IS NULL, lifespan_years DESC"),
}

# (name, label, kind, required, choices)
FIELDS = [
    ("scientific_name", "Scientific name", "text", True, None),
    ("common_name", "Common name", "text", False, None),
    ("kingdom", "Kingdom", "select", True, KINGDOMS),
    ("class_name", "Class", "text", False, None),
    ("family", "Family", "text", False, None),
    ("habitat", "Habitat", "select", False, HABITATS),
    ("diet", "Diet", "select", False, DIETS),
    ("conservation_status", "Conservation status", "select", True, STATUSES),
    ("typical_length_cm", "Typical length (cm)", "number", False, None),
    ("lifespan_years", "Lifespan (years)", "number", False, None),
    ("description", "Description", "textarea", False, None),
]
TEXT_FIELDS = [f[0] for f in FIELDS]
NUMERIC_FIELDS = ["typical_length_cm", "lifespan_years"]

FLASH = {
    "created": "The species record was created.",
    "updated": "The species record was updated.",
    "deleted": "The species record was deleted.",
}

SAMPLE_SPECIES = [
    # scientific, common, kingdom, class, family, habitat, diet, status, length_cm, lifespan_years, description
    ("Panthera leo", "African Lion", "Animalia", "Mammalia", "Felidae", "Grassland", "Carnivore",
     "Vulnerable", 250, 14,
     "Large social cat living in prides in African savannas. Males are recognised by their manes."),
    ("Ailuropoda melanoleuca", "Giant Panda", "Animalia", "Mammalia", "Ursidae", "Forest", "Herbivore",
     "Vulnerable", 150, 20,
     "Bamboo specialist from the mountain forests of central China with a distinctive black and white coat."),
    ("Balaenoptera musculus", "Blue Whale", "Animalia", "Mammalia", "Balaenopteridae", "Marine", "Carnivore",
     "Endangered", 2700, 80,
     "The largest animal known to have ever lived. Feeds mainly on krill filtered through baleen plates."),
    ("Aptenodytes forsteri", "Emperor Penguin", "Animalia", "Aves", "Spheniscidae", "Arctic", "Carnivore",
     "Near Threatened", 115, 20,
     "The tallest and heaviest penguin. Males incubate the single egg through the Antarctic winter."),
    ("Ursus maritimus", "Polar Bear", "Animalia", "Mammalia", "Ursidae", "Arctic", "Carnivore",
     "Vulnerable", 240, 25,
     "Marine mammal of the Arctic sea ice that depends on seals as its main prey."),
    ("Chelonia mydas", "Green Sea Turtle", "Animalia", "Reptilia", "Cheloniidae", "Marine", "Herbivore",
     "Endangered", 110, 80,
     "Sea turtle whose adults graze on seagrass and algae in tropical and subtropical waters."),
    ("Vulpes zerda", "Fennec Fox", "Animalia", "Mammalia", "Canidae", "Desert", "Omnivore",
     "Least Concern", 40, 14,
     "Small nocturnal fox with very large ears that help release body heat in the Sahara."),
    ("Ambystoma mexicanum", "Axolotl", "Animalia", "Amphibia", "Ambystomatidae", "Freshwater", "Carnivore",
     "Critically Endangered", 23, 15,
     "Neotenic salamander that keeps its gills and aquatic life throughout adulthood."),
    ("Apis mellifera", "Western Honey Bee", "Animalia", "Insecta", "Apidae", "Grassland", "Herbivore",
     "Least Concern", 1.5, 0.2,
     "Social pollinator that forms colonies of tens of thousands of workers and stores honey."),
    ("Quercus robur", "English Oak", "Plantae", "Magnoliopsida", "Fagaceae", "Forest", "Photosynthetic",
     "Least Concern", 2500, 800,
     "Long-lived deciduous tree that supports hundreds of insect and bird species."),
    ("Rafflesia arnoldii", "Corpse Flower", "Plantae", "Magnoliopsida", "Rafflesiaceae", "Forest", "Parasitic",
     "Endangered", 100, 1,
     "Parasitic plant with the largest single flower in the world. It has no leaves, stems or roots."),
    ("Amanita muscaria", "Fly Agaric", "Fungi", "Agaricomycetes", "Amanitaceae", "Forest", "Symbiotic",
     "Least Concern", 20, 1,
     "Mycorrhizal mushroom that forms partnerships with birch and pine roots. Toxic if eaten."),
    ("Escherichia coli", "Gut Bacterium (E. coli)", "Bacteria", "Gammaproteobacteria", "Enterobacteriaceae",
     "Host-associated", "Symbiotic", "Least Concern", 0.002, 0.01,
     "Common bacterium of the vertebrate gut. Many strains are harmless and some help digestion."),
]


# ---------------------------------------------------------------- database

def db_connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with db_connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS species (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scientific_name TEXT NOT NULL UNIQUE,
                common_name TEXT NOT NULL DEFAULT '',
                kingdom TEXT NOT NULL,
                class_name TEXT NOT NULL DEFAULT '',
                family TEXT NOT NULL DEFAULT '',
                habitat TEXT NOT NULL DEFAULT '',
                diet TEXT NOT NULL DEFAULT '',
                conservation_status TEXT NOT NULL,
                typical_length_cm REAL,
                lifespan_years REAL,
                description TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM species").fetchone()[0]
        if count == 0:
            cols = TEXT_FIELDS
            conn.executemany(
                "INSERT INTO species (" + ", ".join(cols) + ") VALUES ("
                + ", ".join("?" for _ in cols) + ")",
                [tuple(row) for row in SAMPLE_SPECIES],
            )


# ---------------------------------------------------------------- helpers

def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def fmt_num(value):
    if value is None:
        return "&mdash;"
    return esc(f"{value:g}")


def options_html(choices, selected, empty_label):
    parts = [f'<option value=""{" selected" if not selected else ""}>{esc(empty_label)}</option>']
    for choice in choices:
        sel = " selected" if choice == selected else ""
        parts.append(f'<option value="{esc(choice)}"{sel}>{esc(choice)}</option>')
    return "".join(parts)


def status_badge(status):
    return f'<span class="badge">{esc(status)}</span>'


def display_name(row):
    return row["common_name"] or row["scientific_name"]


def page(title, body, active="", flash_key=""):
    nav_items = [
        ("/", "Home", "home"),
        ("/species", "Browse &amp; Search", "browse"),
        ("/species/new", "Add Species", "add"),
        ("/about", "About", "about"),
    ]
    nav_parts = []
    for href, label, key in nav_items:
        current = ' class="active" aria-current="page"' if key == active else ""
        nav_parts.append(f'<a href="{href}"{current}>{label}</a>')
    nav = "".join(nav_parts)
    flash = f'<div class="flash" role="status">{esc(FLASH[flash_key])}</div>' if flash_key in FLASH else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | Species Database</title>
<style>{CSS}</style>
</head>
<body>
<header class="site">
  <a class="brand" href="/">Species Database</a>
  <nav class="menu" aria-label="Main navigation">{nav}</nav>
</header>
<main>
{flash}
{body}
</main>
<footer class="site-footer">Species Biological Information Database</footer>
</body>
</html>
"""


CSS = """
:root {
  --honeydew: #F0FFF0;
  --olive: #556B2F;
  --olive-dark: #3B4B1F;
  --ink: #1F2A14;
  --card: #FFFFFF;
  --line: #C3D1A8;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--honeydew);
  color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
a { color: var(--olive); }
header.site {
  background: var(--olive);
  color: var(--honeydew);
  padding: 14px 24px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
header.site .brand { color: var(--honeydew); font-size: 1.4rem; font-weight: 700; text-decoration: none; }
nav.menu { display: flex; flex-wrap: wrap; gap: 6px; }
nav.menu a {
  color: var(--honeydew);
  text-decoration: none;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 6px;
  border: 2px solid transparent;
}
nav.menu a:hover { border-color: var(--honeydew); }
nav.menu a.active { background: var(--honeydew); color: var(--olive); }
main { flex: 1; width: 100%; max-width: 1120px; margin: 0 auto; padding: 24px 20px; }
footer.site-footer {
  background: var(--olive);
  color: var(--honeydew);
  text-align: center;
  padding: 12px;
  font-size: 0.9rem;
}
h1, h2, h3 { color: var(--olive); line-height: 1.2; }
h1 { font-size: 2rem; margin: 0.2em 0; }
h2 { font-size: 1.35rem; margin-top: 1.2em; }
.subtitle { font-style: italic; color: var(--ink); margin-top: 0; }
.card {
  background: var(--card);
  border: 2px solid var(--olive);
  border-radius: 10px;
  padding: 18px;
  margin-bottom: 18px;
}
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 14px; margin: 18px 0; }
.stat .number { font-size: 2.2rem; font-weight: 700; color: var(--olive); }
.stat .label { font-weight: 600; }
.btn {
  display: inline-block;
  background: var(--olive);
  color: var(--honeydew);
  border: 2px solid var(--olive);
  border-radius: 6px;
  padding: 8px 16px;
  font: inherit;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
}
.btn:hover, .btn:focus { background: var(--olive-dark); border-color: var(--olive-dark); color: var(--honeydew); }
.btn.outline { background: transparent; color: var(--olive); }
.btn.outline:hover, .btn.outline:focus { background: var(--olive); color: var(--honeydew); }
.actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin: 14px 0; }
form.inline { display: inline; margin: 0; }
.badge {
  display: inline-block;
  background: var(--olive);
  color: var(--honeydew);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}
.flash {
  background: var(--olive);
  color: var(--honeydew);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 18px;
  font-weight: 600;
}
.error-box {
  background: var(--olive);
  color: var(--honeydew);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 18px;
}
.error-box ul { margin: 4px 0 0 18px; padding: 0; }
.filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; align-items: end; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px 18px; }
.form-grid .wide { grid-column: 1 / -1; }
label { display: block; font-weight: 600; color: var(--olive); margin-bottom: 4px; }
input, select, textarea {
  width: 100%;
  padding: 8px 10px;
  border: 2px solid var(--olive);
  border-radius: 6px;
  background: #fff;
  color: var(--ink);
  font: inherit;
}
textarea { min-height: 110px; resize: vertical; }
input:focus, select:focus, textarea:focus { outline: 3px solid #9CB36B; outline-offset: 1px; }
.required::after { content: " *"; color: var(--olive-dark); }
table { width: 100%; border-collapse: collapse; background: var(--card); border: 2px solid var(--olive); border-radius: 10px; overflow: hidden; }
thead th {
  background: var(--olive);
  color: var(--honeydew);
  text-align: left;
  padding: 10px 12px;
  font-weight: 700;
}
tbody td { padding: 10px 12px; border-bottom: 1px solid var(--line); vertical-align: top; }
tbody tr:hover { background: #E4EFD7; }
table.kv th {
  width: 240px;
  text-align: left;
  background: var(--olive);
  color: var(--honeydew);
  padding: 9px 12px;
  vertical-align: top;
}
table.kv td { padding: 9px 12px; border-bottom: 1px solid var(--line); }
table.kv tr:last-child th, table.kv tr:last-child td { border-bottom: none; }
.scroll { overflow-x: auto; }
.count { font-weight: 600; margin: 8px 0; }
.kingdom-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; padding: 0; list-style: none; }
.kingdom-list a {
  display: flex;
  justify-content: space-between;
  background: var(--card);
  border: 2px solid var(--olive);
  border-radius: 8px;
  padding: 10px 14px;
  text-decoration: none;
  color: var(--olive);
  font-weight: 700;
}
.kingdom-list a:hover { background: var(--olive); color: var(--honeydew); }
.empty { padding: 24px; text-align: center; }
.breadcrumb { font-size: 0.95rem; }
"""


# ---------------------------------------------------------------- pages

def page_home():
    with db_connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM species").fetchone()[0]
        threatened = conn.execute(
            "SELECT COUNT(*) FROM species WHERE conservation_status IN (?, ?, ?)",
            tuple(sorted(THREATENED)),
        ).fetchone()[0]
        kingdom_rows = conn.execute(
            "SELECT kingdom, COUNT(*) AS n FROM species GROUP BY kingdom ORDER BY kingdom"
        ).fetchall()
        featured = conn.execute(
            "SELECT * FROM species ORDER BY RANDOM() LIMIT 3"
        ).fetchall()

    kingdoms_html = "".join(
        f'<li><a href="/species?{urlencode({"kingdom": r["kingdom"]})}">'
        f'<span>{esc(r["kingdom"])}</span><span>{r["n"]}</span></a></li>'
        for r in kingdom_rows
    ) or '<li class="empty">No species recorded yet.</li>'

    featured_html = "".join(
        f'<div class="card"><h3><a href="/species/{r["id"]}">{esc(display_name(r))}</a></h3>'
        f'<p class="subtitle">{esc(r["scientific_name"])}</p>'
        f'<p>{status_badge(r["conservation_status"])}</p>'
        f'<p>{esc((r["description"] or "")[:140])}{"..." if len(r["description"] or "") > 140 else ""}</p></div>'
        for r in featured
    )

    body = f"""
<h1>Biological Information Database</h1>
<p class="subtitle">Browse, search, filter and manage biological information for species across the tree of life.</p>
<div class="actions">
  <a class="btn" href="/species">Browse &amp; Search species</a>
  <a class="btn outline" href="/species/new">Add a species</a>
</div>
<div class="stats">
  <div class="card stat"><div class="number">{total}</div><div class="label">Species records</div></div>
  <div class="card stat"><div class="number">{threatened}</div><div class="label">Threatened species</div></div>
  <div class="card stat"><div class="number">{len(kingdom_rows)}</div><div class="label">Kingdoms represented</div></div>
</div>
<h2>Browse by kingdom</h2>
<ul class="kingdom-list">{kingdoms_html}</ul>
<h2>Featured species</h2>
<div class="stats">{featured_html or '<p>No species yet. <a href="/species/new">Add the first one</a>.</p>'}</div>
"""
    return page("Home", body, active="home")


def read_filters(qs):
    filters = {
        "q": qs.get("q", "").strip(),
        "kingdom": qs.get("kingdom", ""),
        "conservation_status": qs.get("conservation_status", ""),
        "habitat": qs.get("habitat", ""),
        "diet": qs.get("diet", ""),
        "sort": qs.get("sort", "name"),
    }
    if filters["kingdom"] not in KINGDOMS:
        filters["kingdom"] = ""
    if filters["conservation_status"] not in STATUSES:
        filters["conservation_status"] = ""
    if filters["habitat"] not in HABITATS:
        filters["habitat"] = ""
    if filters["diet"] not in DIETS:
        filters["diet"] = ""
    if filters["sort"] not in SORTS:
        filters["sort"] = "name"
    return filters


def page_browse(qs):
    f = read_filters(qs)
    where, params = [], []
    if f["q"]:
        like = f"%{f['q']}%"
        # Search matches the species name only (common or scientific name).
        where.append("(scientific_name LIKE ? OR common_name LIKE ?)")
        params.extend([like] * 2)
    for column in ("kingdom", "conservation_status", "habitat", "diet"):
        if f[column]:
            where.append(f"{column} = ?")
            params.append(f[column])
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    order_sql = SORTS[f["sort"]][1]

    with db_connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM species").fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM species {where_sql} ORDER BY {order_sql}, id", params
        ).fetchall()

    def select(name, label, choices, current, empty_label):
        return (
            f'<div><label for="{name}">{esc(label)}</label>'
            f'<select id="{name}" name="{name}">{options_html(choices, current, empty_label)}</select></div>'
        )

    sort_choices = "".join(
        f'<option value="{k}"{" selected" if k == f["sort"] else ""}>{esc(v[0])}</option>'
        for k, v in SORTS.items()
    )
    filter_form = f"""
<form class="card" method="get" action="/species" role="search">
  <div class="filters">
    <div><label for="q">Search text</label>
      <input id="q" type="search" name="q" value="{esc(f['q'])}"
             placeholder="Common or scientific name"></div>
    {select("kingdom", "Kingdom", KINGDOMS, f["kingdom"], "All kingdoms")}
    {select("conservation_status", "Conservation status", STATUSES, f["conservation_status"], "All statuses")}
    {select("habitat", "Habitat", HABITATS, f["habitat"], "All habitats")}
    {select("diet", "Diet", DIETS, f["diet"], "All diets")}
    <div><label for="sort">Sort by</label>
      <select id="sort" name="sort">{sort_choices}</select></div>
  </div>
  <div class="actions">
    <button class="btn" type="submit">Apply filters</button>
    <a class="btn outline" href="/species">Clear all</a>
  </div>
</form>
"""

    if rows:
        body_rows = "".join(
            f"""<tr>
  <td><a href="/species/{r['id']}"><strong>{esc(display_name(r))}</strong></a></td>
  <td><em>{esc(r['scientific_name'])}</em></td>
  <td>{esc(r['kingdom'])}</td>
  <td>{esc(r['class_name']) or '&mdash;'}</td>
  <td>{esc(r['habitat']) or '&mdash;'}</td>
  <td>{esc(r['diet']) or '&mdash;'}</td>
  <td>{status_badge(r['conservation_status'])}</td>
  <td>{fmt_num(r['typical_length_cm'])}</td>
  <td>{fmt_num(r['lifespan_years'])}</td>
</tr>"""
            for r in rows
        )
        results = f"""
<div class="scroll"><table>
<thead><tr>
  <th>Common name</th><th>Scientific name</th><th>Kingdom</th><th>Class</th>
  <th>Habitat</th><th>Diet</th><th>Conservation status</th><th>Length (cm)</th><th>Lifespan (years)</th>
</tr></thead>
<tbody>{body_rows}</tbody>
</table></div>"""
    else:
        results = """<div class="card empty"><p>No species match these filters.</p>
<p><a class="btn outline" href="/species">Clear all filters</a></p></div>"""

    body = f"""
<div class="actions" style="justify-content: space-between;">
  <h1 style="margin:0;">Browse &amp; Search</h1>
  <a class="btn" href="/species/new">Add a species</a>
</div>
{filter_form}
<p class="count" aria-live="polite">Showing {len(rows)} of {total} species</p>
{results}
"""
    return page("Browse & Search", body, active="browse")


def page_detail(species_id, flash_key=""):
    with db_connect() as conn:
        row = conn.execute("SELECT * FROM species WHERE id = ?", (species_id,)).fetchone()
    if row is None:
        return None
    body = f"""
<p class="breadcrumb"><a href="/species">Browse &amp; Search</a> &rsaquo; {esc(display_name(row))}</p>
<h1>{esc(display_name(row))}</h1>
<p class="subtitle"><em>{esc(row['scientific_name'])}</em> &middot; {status_badge(row['conservation_status'])}</p>
<div class="actions">
  <a class="btn" href="/species/{row['id']}/edit">Edit record</a>
  <form class="inline" method="post" action="/species/{row['id']}/delete"
        onsubmit="return confirm('Delete this species record? This cannot be undone.');">
    <button class="btn outline" type="submit">Delete record</button>
  </form>
  <a class="btn outline" href="/species">Back to list</a>
</div>
<div class="card">
<table class="kv">
  <tr><th>Common name</th><td>{esc(row['common_name']) or '&mdash;'}</td></tr>
  <tr><th>Scientific name</th><td><em>{esc(row['scientific_name'])}</em></td></tr>
  <tr><th>Kingdom</th><td><a href="/species?{urlencode({'kingdom': row['kingdom']})}">{esc(row['kingdom'])}</a></td></tr>
  <tr><th>Class</th><td>{esc(row['class_name']) or '&mdash;'}</td></tr>
  <tr><th>Family</th><td>{esc(row['family']) or '&mdash;'}</td></tr>
  <tr><th>Habitat</th><td>{esc(row['habitat']) or '&mdash;'}</td></tr>
  <tr><th>Diet</th><td>{esc(row['diet']) or '&mdash;'}</td></tr>
  <tr><th>Conservation status</th><td>{status_badge(row['conservation_status'])}</td></tr>
  <tr><th>Typical length (cm)</th><td>{fmt_num(row['typical_length_cm'])}</td></tr>
  <tr><th>Lifespan (years)</th><td>{fmt_num(row['lifespan_years'])}</td></tr>
  <tr><th>Record created</th><td>{esc(row['created_at'])} UTC</td></tr>
</table>
</div>
<h2>Description</h2>
<div class="card"><p>{esc(row['description']) or 'No description recorded.'}</p></div>
"""
    return page(display_name(row), body, active="browse", flash_key=flash_key)


def species_form(title, action, values, errors, cancel_href):
    fields_html = []
    for name, label, kind, required, choices in FIELDS:
        value = values.get(name, "")
        req = " required" if required else ""
        label_cls = ' class="required"' if required else ""
        if kind == "select":
            control = (
                f'<select id="{name}" name="{name}"{req}>'
                f'{options_html(choices, value, "— Select —")}</select>'
            )
        elif kind == "textarea":
            control = f'<textarea id="{name}" name="{name}">{esc(value)}</textarea>'
        elif kind == "number":
            control = (
                f'<input id="{name}" type="number" name="{name}" step="any" min="0" '
                f'value="{esc(value)}">'
            )
        else:
            control = f'<input id="{name}" type="text" name="{name}" value="{esc(value)}"{req}>'
        wide = " wide" if kind == "textarea" else ""
        fields_html.append(
            f'<div class="{wide.strip()}"><label for="{name}"{label_cls}>{esc(label)}</label>{control}</div>'
        )

    error_html = ""
    if errors:
        items = "".join(f"<li>{esc(e)}</li>" for e in errors)
        error_html = f'<div class="error-box" role="alert"><strong>Please fix the following:</strong><ul>{items}</ul></div>'

    body = f"""
<p class="breadcrumb"><a href="/species">Browse &amp; Search</a> &rsaquo; {esc(title)}</p>
<h1>{esc(title)}</h1>
<p class="subtitle">Fields marked with * are required.</p>
{error_html}
<form class="card" method="post" action="{esc(action)}">
  <div class="form-grid">
    {''.join(fields_html)}
  </div>
  <div class="actions">
    <button class="btn" type="submit">Save species</button>
    <a class="btn outline" href="{esc(cancel_href)}">Cancel</a>
  </div>
</form>
"""
    return body


def clean_species(form, species_id=None):
    """Return (values, errors). values are ready for SQL."""
    values = {name: form.get(name, "").strip() for name in TEXT_FIELDS}
    errors = []
    for name, label, kind, required, choices in FIELDS:
        raw = values[name]
        if required and not raw:
            errors.append(f"{label} is required.")
        elif choices is not None and raw and raw not in choices:
            errors.append(f"{label} must be one of the listed options.")
        if name in NUMERIC_FIELDS:
            if raw:
                try:
                    number = float(raw)
                    if number < 0:
                        errors.append(f"{label} cannot be negative.")
                    values[name] = number
                except ValueError:
                    errors.append(f"{label} must be a number.")
                    values[name] = None
            else:
                values[name] = None
    if values["scientific_name"]:
        with db_connect() as conn:
            clash = conn.execute(
                "SELECT id FROM species WHERE scientific_name = ? COLLATE NOCASE AND id IS NOT ?",
                (values["scientific_name"], species_id),
            ).fetchone()
        if clash:
            errors.append("Another record already uses this scientific name.")
    return values, errors


def page_form_new(values=None, errors=None):
    body = species_form(
        "Add a species", "/species/new", values or {}, errors or [], "/species"
    )
    return page("Add a species", body, active="add")


def page_form_edit(species_id, values=None, errors=None):
    with db_connect() as conn:
        row = conn.execute("SELECT * FROM species WHERE id = ?", (species_id,)).fetchone()
    if row is None:
        return None
    if values is None:
        values = {k: ("" if row[k] is None else row[k]) for k in TEXT_FIELDS}
        for k in NUMERIC_FIELDS:
            values[k] = "" if row[k] is None else f"{row[k]:g}"
    body = species_form(
        f"Edit {display_name(row)}",
        f"/species/{species_id}/edit",
        values,
        errors or [],
        f"/species/{species_id}",
    )
    return page("Edit species", body, active="browse")


def page_about():
    body = f"""
<h1>About this database</h1>
<p class="subtitle">A small, self-contained store of biological information about species.</p>
<div class="card">
  <h2 style="margin-top:0;">What is recorded</h2>
  <p>Each species record holds a scientific name, common name, kingdom, class, family,
     habitat, diet, IUCN-style conservation status, typical length, typical lifespan and a
     short description.</p>
  <h2>How to use it</h2>
  <ul>
    <li><a href="/species">Browse &amp; Search</a> lists every record. Type in the search box to match
        common or scientific names only, and use the filters to narrow the list by kingdom,
        conservation status, habitat or diet.</li>
    <li><a href="/species/new">Add Species</a> creates a new record.</li>
    <li>Open any species to view its full details, then use <em>Edit record</em> or
        <em>Delete record</em> to manage it.</li>
  </ul>
  <h2>Data storage</h2>
  <p>Records are stored in a SQLite database inside the configured data directory. When the
     database is empty on start-up, sample species are loaded so every feature can be tried right away.</p>
</div>
"""
    return page("About", body, active="about")


def page_not_found():
    body = """<div class="card empty"><h1>Page not found</h1>
<p>The page you asked for does not exist.</p>
<p><a class="btn" href="/">Go to the home page</a></p></div>"""
    return page("Not found", body)


# ---------------------------------------------------------------- routing

SPECIES_RE = re.compile(r"^/species/(\d+)(/edit|/delete)?$")


def dispatch(method, path, qs, form):
    """Return (status, html, headers)."""
    redirect = lambda location: (303, "", {"Location": location})

    if method == "GET":
        if path == "/":
            return 200, page_home(), {}
        if path == "/species":
            return 200, page_browse(qs), {}
        if path == "/species/new":
            return 200, page_form_new(), {}
        if path == "/about":
            return 200, page_about(), {}
        m = SPECIES_RE.match(path)
        if m and m.group(2) in (None, "/edit"):
            species_id = int(m.group(1))
            if m.group(2) is None:
                out = page_detail(species_id, flash_key=qs.get("msg", ""))
            else:
                out = page_form_edit(species_id)
            if out is None:
                return 404, page_not_found(), {}
            return 200, out, {}
        return 404, page_not_found(), {}

    if method == "POST":
        if path == "/species/new":
            values, errors = clean_species(form)
            if errors:
                return 200, page_form_new(values, errors), {}
            cols = TEXT_FIELDS
            with WRITE_LOCK, db_connect() as conn:
                cur = conn.execute(
                    "INSERT INTO species (" + ", ".join(cols) + ") VALUES ("
                    + ", ".join("?" for _ in cols) + ")",
                    [values[c] for c in cols],
                )
                new_id = cur.lastrowid
            return redirect(f"/species/{new_id}?msg=created")
        m = SPECIES_RE.match(path)
        if m:
            species_id = int(m.group(1))
            action = m.group(2)
            with db_connect() as conn:
                exists = conn.execute("SELECT 1 FROM species WHERE id = ?", (species_id,)).fetchone()
            if not exists:
                return 404, page_not_found(), {}
            if action == "/edit":
                values, errors = clean_species(form, species_id)
                if errors:
                    return 200, page_form_edit(species_id, values, errors), {}
                cols = TEXT_FIELDS
                assignments = ", ".join(f"{c} = ?" for c in cols)
                with WRITE_LOCK, db_connect() as conn:
                    conn.execute(
                        f"UPDATE species SET {assignments} WHERE id = ?",
                        [values[c] for c in cols] + [species_id],
                    )
                return redirect(f"/species/{species_id}?msg=updated")
            if action == "/delete":
                with WRITE_LOCK, db_connect() as conn:
                    conn.execute("DELETE FROM species WHERE id = ?", (species_id,))
                return redirect("/species?msg=deleted")
        return 404, page_not_found(), {}

    return 405, page_not_found(), {}


class Handler(BaseHTTPRequestHandler):
    server_version = "SpeciesDB/1.0"

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def _handle(self, method):
        url = urlparse(self.path)
        path = url.path.rstrip("/") or "/"
        qs = {k: v[-1] for k, v in parse_qs(url.query, keep_blank_values=True).items()}
        form = {}
        if method == "POST":
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            raw = self.rfile.read(min(length, 1_000_000)).decode("utf-8", "replace")
            form = {k: v[-1] for k, v in parse_qs(raw, keep_blank_values=True).items()}
        try:
            status, body, headers = dispatch(method, path, qs, form)
        except Exception as exc:  # keep the server alive, show a readable error
            status = 500
            body = page(
                "Error",
                f'<div class="error-box"><strong>Something went wrong.</strong><br>{esc(exc)}</div>'
                '<p><a class="btn" href="/">Go to the home page</a></p>',
            )
            headers = {}
        payload = body.encode("utf-8")
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        if status != 303:
            self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if method != "HEAD" and payload:
            self.wfile.write(payload)

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}", flush=True)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    init_db()
    httpd = Server(("127.0.0.1", PORT), Handler)
    print(f"Species Database serving on http://127.0.0.1:{PORT} (data: {DATA_DIR})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
