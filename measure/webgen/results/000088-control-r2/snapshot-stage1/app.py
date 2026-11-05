#!/usr/bin/env python3
"""Species Biological Information Database.

Standard library only (http.server + sqlite3). Server-rendered HTML.
Environment variables:
  PORT      port to listen on (default 8000)
  DATA_DIR  directory for the SQLite database (default ./data)
"""
import math
import os
import re
import sqlite3
import html
import urllib.parse
from contextlib import closing
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data"))
PORT = int(os.environ.get("PORT") or "8000")
DB_PATH = os.path.join(DATA_DIR, "species.db")

KINGDOMS = ["Animalia", "Plantae", "Fungi"]
HABITATS = ["Marine", "Freshwater", "Forest", "Grassland", "Desert", "Wetland",
            "Mountain", "Polar", "Tropical Rainforest", "Urban"]
DIETS = ["Carnivore", "Herbivore", "Omnivore", "Autotroph", "Decomposer",
         "Parasite", "Symbiotic"]
STATUSES = ["Least Concern", "Near Threatened", "Vulnerable", "Endangered",
            "Critically Endangered", "Data Deficient", "Extinct"]
THREATENED = ("Vulnerable", "Endangered", "Critically Endangered")

# (query parameter / column name, label, allowed values)
FILTERS = [
    ("kingdom", "Kingdom", KINGDOMS),
    ("habitat", "Habitat", HABITATS),
    ("diet", "Feeding mode", DIETS),
    ("conservation_status", "Conservation status", STATUSES),
]
SORTS = {
    "name": ("Scientific name (A–Z)", "scientific_name COLLATE NOCASE"),
    "length": ("Average length (longest first)", "(avg_length_cm IS NULL), avg_length_cm DESC"),
    "lifespan": ("Lifespan (longest first)", "(lifespan_years IS NULL), lifespan_years DESC"),
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name TEXT NOT NULL UNIQUE,
    common_name TEXT NOT NULL DEFAULT '',
    kingdom TEXT NOT NULL,
    taxonomic_class TEXT NOT NULL DEFAULT '',
    habitat TEXT NOT NULL,
    diet TEXT NOT NULL,
    conservation_status TEXT NOT NULL,
    avg_length_cm REAL,
    lifespan_years REAL,
    description TEXT NOT NULL DEFAULT ''
)
"""

COLUMNS = ["scientific_name", "common_name", "kingdom", "taxonomic_class", "habitat",
           "diet", "conservation_status", "avg_length_cm", "lifespan_years", "description"]
INSERT_SQL = "INSERT INTO species (%s) VALUES (%s)" % (
    ", ".join(COLUMNS), ", ".join("?" for _ in COLUMNS))

# Sample data shown when the database is empty so every feature can be tried.
SAMPLE_SPECIES = [
    ("Panthera leo", "Lion", "Animalia", "Mammalia", "Grassland", "Carnivore",
     "Vulnerable", 250, 14, "Social big cat that lives in prides in African savannas."),
    ("Ailuropoda melanoleuca", "Giant panda", "Animalia", "Mammalia", "Forest", "Herbivore",
     "Vulnerable", 150, 20, "Bamboo specialist native to mountain forests of central China."),
    ("Balaenoptera musculus", "Blue whale", "Animalia", "Mammalia", "Marine", "Carnivore",
     "Endangered", 2400, 80, "The largest animal known to have lived; feeds mainly on krill."),
    ("Ursus maritimus", "Polar bear", "Animalia", "Mammalia", "Polar", "Carnivore",
     "Vulnerable", 240, 25, "Sea-ice dependent predator that hunts seals."),
    ("Apis mellifera", "Western honey bee", "Animalia", "Insecta", "Grassland", "Herbivore",
     "Least Concern", 1.5, 0.12, "Social bee that forms colonies and is a key crop pollinator."),
    ("Sequoiadendron giganteum", "Giant sequoia", "Plantae", "Pinopsida", "Forest", "Autotroph",
     "Endangered", 8000, 3000, "Very large conifer native to the Sierra Nevada of California."),
    ("Amanita muscaria", "Fly agaric", "Fungi", "Agaricomycetes", "Forest", "Symbiotic",
     "Least Concern", 20, None, "Mycorrhizal mushroom that forms partnerships with tree roots; toxic."),
    ("Oophaga pumilio", "Strawberry poison-dart frog", "Animalia", "Amphibia",
     "Tropical Rainforest", "Carnivore", "Least Concern", 2, None,
     "Small brightly colored frog whose skin toxins come from its arthropod diet."),
    ("Aptenodytes forsteri", "Emperor penguin", "Animalia", "Aves", "Polar", "Carnivore",
     "Near Threatened", 115, 20, "Largest penguin species; breeds on Antarctic sea ice in winter."),
    ("Canis lupus", "Gray wolf", "Animalia", "Mammalia", "Forest", "Carnivore",
     "Least Concern", 130, 13, "Wide-ranging pack hunter found across the Northern Hemisphere."),
    ("Loxodonta africana", "African bush elephant", "Animalia", "Mammalia", "Grassland", "Herbivore",
     "Endangered", 700, 70, "Largest living land animal; lives in savannas and forests of Africa."),
    ("Ailurus fulgens", "Red panda", "Animalia", "Mammalia", "Forest", "Herbivore",
     "Endangered", 60, 10, "Tree-dwelling bamboo eater of the Himalayas and southwest China."),
    ("Phoenicopterus roseus", "Greater flamingo", "Animalia", "Aves", "Wetland", "Omnivore",
     "Least Concern", 140, 30, "Filter-feeds on algae, brine shrimp and small invertebrates."),
    ("Carcharodon carcharias", "Great white shark", "Animalia", "Chondrichthyes", "Marine", "Carnivore",
     "Vulnerable", 500, 70, "Large apex predator of coastal and open-ocean waters."),
    ("Salmo salar", "Atlantic salmon", "Animalia", "Actinopterygii", "Freshwater", "Carnivore",
     "Least Concern", 90, 8, "Migrates from the sea back to rivers to spawn."),
    ("Rafflesia arnoldii", "Corpse flower", "Plantae", "Magnoliopsida", "Tropical Rainforest", "Parasite",
     "Data Deficient", 100, None, "Parasitic plant with a very large flower and no leaves or stems."),
    ("Vulpes zerda", "Fennec fox", "Animalia", "Mammalia", "Desert", "Omnivore",
     "Least Concern", 40, 10, "Smallest canid; large ears help release body heat."),
    ("Acinonyx jubatus", "Cheetah", "Animalia", "Mammalia", "Grassland", "Carnivore",
     "Vulnerable", 140, 12, "Fastest land animal, reaching high speeds in short bursts."),
    ("Danaus plexippus", "Monarch butterfly", "Animalia", "Insecta", "Grassland", "Herbivore",
     "Endangered", 10, 0.5, "Long-distance migrant; larvae feed on milkweed plants."),
    ("Pinus longaeva", "Great Basin bristlecone pine", "Plantae", "Pinopsida", "Mountain", "Autotroph",
     "Least Concern", 1000, 5000, "Among the oldest living non-clonal organisms."),
    ("Hydra vulgaris", "Common hydra", "Animalia", "Hydrozoa", "Freshwater", "Carnivore",
     "Least Concern", 1, None, "Small freshwater animal with a tube-shaped body and tentacles."),
    ("Pandion haliaetus", "Osprey", "Animalia", "Aves", "Wetland", "Carnivore",
     "Least Concern", 60, 15, "Fish-eating raptor that dives feet-first to catch prey."),
    ("Procyon lotor", "Common raccoon", "Animalia", "Mammalia", "Urban", "Omnivore",
     "Least Concern", 70, 3, "Adaptable mammal that thrives in towns and forest edges."),
]


# ---------------------------------------------------------------- database

def connect():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(connect()) as conn:
        conn.execute(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM species").fetchone()[0] == 0:
            conn.executemany(INSERT_SQL, SAMPLE_SPECIES)
        conn.commit()


def scalar(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()[0]


# ---------------------------------------------------------------- helpers

def e(value):
    return html.escape("" if value is None else str(value), quote=True)


def fmt(value):
    if value is None:
        return "—"
    return format(value, ",g")


def qs(query, name):
    values = query.get(name)
    return values[0].strip() if values else ""


def option_list(options, selected, placeholder="All"):
    parts = ['<option value="">%s</option>' % e(placeholder)]
    for opt in options:
        sel = " selected" if opt == selected else ""
        parts.append('<option value="%s"%s>%s</option>' % (e(opt), sel, e(opt)))
    return "".join(parts)


def badge(status):
    return '<span class="badge">%s</span>' % e(status)


def flash_html(message):
    if not message:
        return ""
    return '<div class="flash" role="status">%s</div>' % e(message)


CSS = """
:root {
  --linen: #FAF0E6;
  --maroon: #800000;
  --maroon-dark: #5C0000;
  --card: #FFFBF6;
  --stripe: #F3E3D3;
  --ink: #2B1B1B;
  --line: #D9BFAE;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--linen); color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.5; min-height: 100vh; display: flex; flex-direction: column;
}
a { color: var(--maroon); }
a:hover { color: var(--maroon-dark); }
.site-header { background: var(--maroon); color: #fff; }
.brand { padding: 0.9rem 1.5rem 0.2rem; font-size: 1.4rem; font-weight: 700; }
.brand a { color: #fff; text-decoration: none; }
.main-nav { display: flex; flex-wrap: wrap; gap: 0.25rem; padding: 0 1.2rem 0.6rem; }
.main-nav a {
  color: var(--linen); text-decoration: none; padding: 0.45rem 0.9rem;
  border-radius: 4px; border: 1px solid transparent;
}
.main-nav a:hover { border-color: var(--linen); color: #fff; }
.main-nav a.active { background: var(--linen); color: var(--maroon); font-weight: 700; }
main { flex: 1; width: 100%; max-width: 1200px; margin: 0 auto; padding: 1.5rem; }
footer {
  background: var(--maroon); color: var(--linen); text-align: center;
  padding: 0.8rem; font-size: 0.9rem;
}
h1, h2, h3 { color: var(--maroon); line-height: 1.25; }
h1 { font-size: 2rem; margin: 0.4rem 0 0.8rem; }
h2 { font-size: 1.35rem; margin: 1.6rem 0 0.7rem; }
.card {
  background: var(--card); border: 2px solid var(--maroon); border-radius: 8px;
  padding: 1.2rem 1.4rem; margin-bottom: 1.2rem;
}
.hero p { font-size: 1.05rem; max-width: 60ch; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 1rem; margin-bottom: 1.2rem; }
.stat { background: var(--maroon); color: #fff; border-radius: 8px; padding: 1rem 1.2rem; }
.stat .num { font-size: 2rem; font-weight: 700; color: #fff; }
.stat .label { color: var(--linen); }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.2rem; }
ul.links { list-style: none; padding: 0; margin: 0; }
ul.links li { border-bottom: 1px solid var(--line); padding: 0.4rem 0; display: flex; justify-content: space-between; }
.btn {
  display: inline-block; background: var(--maroon); color: #fff !important; border: 2px solid var(--maroon);
  border-radius: 4px; padding: 0.42rem 0.95rem; font: inherit; cursor: pointer; text-decoration: none;
}
.btn:hover { background: var(--maroon-dark); border-color: var(--maroon-dark); }
.btn:focus, input:focus, select:focus, textarea:focus, .main-nav a:focus {
  outline: 3px solid var(--maroon); outline-offset: 2px;
}
.btn-outline { background: transparent; color: var(--maroon) !important; }
.btn-outline:hover { background: var(--maroon); color: #fff !important; }
.btn-small { padding: 0.2rem 0.6rem; font-size: 0.9rem; }
.actions { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
form.inline { display: inline; margin: 0; }
input, select, textarea {
  font: inherit; color: var(--ink); background: #fff; border: 1px solid var(--maroon);
  border-radius: 4px; padding: 0.4rem 0.55rem; width: 100%;
}
textarea { min-height: 100px; resize: vertical; }
label { display: block; font-weight: 600; color: var(--maroon); margin-bottom: 0.9rem; }
label .hint { font-weight: 400; color: var(--ink); font-size: 0.85rem; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 0 1.2rem; }
.form-grid .wide { grid-column: 1 / -1; }
.filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 0 1rem; align-items: end; }
.filters label { margin-bottom: 0.6rem; }
.filters .buttons { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.9rem; }
.table-wrap { overflow-x: auto; border: 2px solid var(--maroon); border-radius: 8px; background: var(--card); }
table { border-collapse: collapse; width: 100%; }
th, td { padding: 0.55rem 0.7rem; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }
th { background: var(--maroon); color: #fff; white-space: nowrap; }
tbody tr:nth-child(even) td { background: var(--stripe); }
td.num, th.num { text-align: right; white-space: nowrap; }
td.nowrap { white-space: nowrap; }
.badge {
  display: inline-block; background: var(--maroon); color: #fff; border-radius: 999px;
  padding: 0.05rem 0.6rem; font-size: 0.82rem; white-space: nowrap;
}
.flash {
  background: var(--maroon); color: #fff; border-radius: 6px; padding: 0.7rem 1rem; margin-bottom: 1rem;
  font-weight: 600;
}
.errors { background: #fff; border: 2px solid var(--maroon); border-radius: 6px; padding: 0.8rem 1.1rem; margin-bottom: 1rem; }
.errors ul { margin: 0.2rem 0 0; padding-left: 1.2rem; color: var(--maroon); font-weight: 600; }
dl.details { display: grid; grid-template-columns: max-content 1fr; gap: 0.55rem 1.4rem; margin: 0; }
dl.details dt { font-weight: 700; color: var(--maroon); }
dl.details dd { margin: 0; }
.muted { color: #5a4545; }
.crumbs { font-size: 0.92rem; margin-bottom: 0.4rem; }
"""


def layout(title, body, active=""):
    nav_items = [
        ("/", "Home", "home"),
        ("/species", "Browse & Search", "browse"),
        ("/species/new", "Add Species", "add"),
        ("/about", "About", "about"),
    ]
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (href, ' class="active" aria-current="page"' if key == active else "", label)
        for href, label, key in nav_items
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>%s · Species Database</title><style>%s</style></head>\n"
        "<body>\n"
        '<header class="site-header">\n'
        '  <div class="brand"><a href="/">Species Biological Database</a></div>\n'
        '  <nav class="main-nav" aria-label="Main navigation">%s</nav>\n'
        "</header>\n"
        "<main>%s</main>\n"
        "<footer>Species Biological Information Database</footer>\n"
        "</body></html>\n"
    ) % (e(title), CSS, nav, body)


# ---------------------------------------------------------------- pages

def page_home(query):
    with closing(connect()) as conn:
        total = scalar(conn, "SELECT COUNT(*) FROM species")
        kingdoms = scalar(conn, "SELECT COUNT(DISTINCT kingdom) FROM species")
        habitats = scalar(conn, "SELECT COUNT(DISTINCT habitat) FROM species")
        threatened = scalar(
            conn, "SELECT COUNT(*) FROM species WHERE conservation_status IN (?, ?, ?)", THREATENED)
        by_habitat = conn.execute(
            "SELECT habitat, COUNT(*) AS n FROM species GROUP BY habitat ORDER BY habitat").fetchall()
        by_status = conn.execute(
            "SELECT conservation_status, COUNT(*) AS n FROM species GROUP BY conservation_status "
            "ORDER BY conservation_status").fetchall()
        featured = conn.execute(
            "SELECT id, scientific_name, common_name, kingdom FROM species "
            "ORDER BY scientific_name COLLATE NOCASE LIMIT 4").fetchall()

    habitat_links = "".join(
        '<li><a href="/species?habitat=%s">%s</a><span class="muted">%d</span></li>'
        % (urllib.parse.quote(r["habitat"]), e(r["habitat"]), r["n"]) for r in by_habitat)
    status_links = "".join(
        '<li><a href="/species?conservation_status=%s">%s</a><span class="muted">%d</span></li>'
        % (urllib.parse.quote(r["conservation_status"]), e(r["conservation_status"]), r["n"])
        for r in by_status)
    featured_links = "".join(
        '<li><a href="/species/%d">%s</a><span class="muted">%s</span></li>'
        % (r["id"], e(r["scientific_name"]), e(r["common_name"] or r["kingdom"])) for r in featured)

    body = """
<div class="card hero">
  <h1>Species Biological Information Database</h1>
  <p>Browse biological information for many species, search by name or description,
     filter by kingdom, habitat, feeding mode and conservation status, and keep the
     records up to date.</p>
  <div class="actions">
    <a class="btn" href="/species">Browse &amp; Search species</a>
    <a class="btn btn-outline" href="/species/new">Add a species</a>
  </div>
</div>

<div class="stats">
  <div class="stat"><div class="num">%(total)d</div><div class="label">Species records</div></div>
  <div class="stat"><div class="num">%(kingdoms)d</div><div class="label">Kingdoms</div></div>
  <div class="stat"><div class="num">%(habitats)d</div><div class="label">Habitats</div></div>
  <div class="stat"><div class="num">%(threatened)d</div><div class="label">Threatened species</div></div>
</div>

<div class="grid-2">
  <div class="card">
    <h2 style="margin-top:0">Browse by habitat</h2>
    <ul class="links">%(habitat_links)s</ul>
  </div>
  <div class="card">
    <h2 style="margin-top:0">Browse by conservation status</h2>
    <ul class="links">%(status_links)s</ul>
  </div>
  <div class="card">
    <h2 style="margin-top:0">Featured species</h2>
    <ul class="links">%(featured_links)s</ul>
    <p style="margin-bottom:0"><a href="/species">See all species &rarr;</a></p>
  </div>
</div>
""" % {
        "total": total, "kingdoms": kingdoms, "habitats": habitats, "threatened": threatened,
        "habitat_links": habitat_links or "<li>No data yet.</li>",
        "status_links": status_links or "<li>No data yet.</li>",
        "featured_links": featured_links or "<li>No species yet.</li>",
    }
    return layout("Home", flash_html(qs(query, "msg")) + body, "home")


def page_list(query):
    q = qs(query, "q")
    filters = {}
    for name, _label, options in FILTERS:
        value = qs(query, name)
        filters[name] = value if value in options else ""
    sort = qs(query, "sort")
    if sort not in SORTS:
        sort = "name"

    clauses, params = [], []
    if q:
        like = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        clauses.append(
            "(scientific_name LIKE ? ESCAPE '\\' OR common_name LIKE ? ESCAPE '\\' "
            "OR taxonomic_class LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\')")
        params.extend([like] * 4)
    for name, _label, _options in FILTERS:
        if filters[name]:
            clauses.append("%s = ?" % name)
            params.append(filters[name])
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    with closing(connect()) as conn:
        total = scalar(conn, "SELECT COUNT(*) FROM species")
        rows = conn.execute(
            "SELECT * FROM species %s ORDER BY %s, id" % (where, SORTS[sort][1]), params).fetchall()

    filter_selects = []
    for name, label, options in FILTERS:
        filter_selects.append(
            '<div><label for="f-%s">%s<select id="f-%s" name="%s">%s</select></label></div>'
            % (name, e(label), name, name, option_list(options, filters[name])))
    sort_options = "".join(
        '<option value="%s"%s>%s</option>' % (key, " selected" if key == sort else "", e(text))
        for key, (text, _sql) in SORTS.items())

    if rows:
        body_rows = []
        for r in rows:
            body_rows.append(
                "<tr>"
                '<td><a href="/species/%(id)d"><em>%(sci)s</em></a></td>'
                "<td>%(common)s</td><td>%(kingdom)s</td><td>%(habitat)s</td>"
                "<td>%(diet)s</td><td>%(status)s</td>"
                '<td class="num">%(length)s</td><td class="num">%(life)s</td>'
                '<td class="nowrap"><div class="actions">'
                '<a class="btn btn-small btn-outline" href="/species/%(id)d">View</a>'
                '<a class="btn btn-small btn-outline" href="/species/%(id)d/edit">Edit</a>'
                '<form class="inline" method="post" action="/species/%(id)d/delete" '
                'onsubmit="return confirm(\'Delete this species record?\');">'
                '<button class="btn btn-small" type="submit">Delete</button></form>'
                "</div></td></tr>" % {
                    "id": r["id"], "sci": e(r["scientific_name"]), "common": e(r["common_name"]),
                    "kingdom": e(r["kingdom"]),
                    "habitat": e(r["habitat"]), "diet": e(r["diet"]),
                    "status": badge(r["conservation_status"]),
                    "length": fmt(r["avg_length_cm"]) + (" cm" if r["avg_length_cm"] is not None else ""),
                    "life": fmt(r["lifespan_years"]) + (" yrs" if r["lifespan_years"] is not None else ""),
                })
        results = (
            '<div class="table-wrap"><table>'
            "<caption class=\"muted\" style=\"text-align:left;padding:.4rem .7rem\">"
            "Showing %d of %d species</caption>"
            "<thead><tr><th>Scientific name</th><th>Common name</th><th>Kingdom</th>"
            "<th>Habitat</th><th>Feeding mode</th><th>Conservation status</th>"
            '<th class="num">Avg. length</th><th class="num">Lifespan</th><th>Actions</th></tr></thead>'
            "<tbody>%s</tbody></table></div>" % (len(rows), total, "".join(body_rows)))
    else:
        results = ('<div class="card"><h2 style="margin-top:0">No matching species</h2>'
                   '<p>Nothing matches your search and filters. Try a different keyword or '
                   '<a href="/species">reset all filters</a>.</p></div>')

    body = """
<div class="crumbs"><a href="/">Home</a> &rsaquo; Browse &amp; Search</div>
<h1>Browse &amp; Search Species</h1>
<form class="card" method="get" action="/species" role="search">
  <label for="q">Search by name, class or description
    <input id="q" type="search" name="q" value="%(q)s" placeholder="e.g. panda, mammal, rainforest">
  </label>
  <div class="filters">
    %(selects)s
    <div><label for="f-sort">Sort by<select id="f-sort" name="sort">%(sort_options)s</select></label></div>
  </div>
  <div class="buttons">
    <button class="btn" type="submit">Apply search &amp; filters</button>
    <a class="btn btn-outline" href="/species">Reset</a>
  </div>
</form>
%(results)s
""" % {"q": e(q), "selects": "".join(filter_selects), "sort_options": sort_options,
       "results": results}
    return layout("Browse & Search", flash_html(qs(query, "msg")) + body, "browse")


def page_detail(species_id, query):
    with closing(connect()) as conn:
        r = conn.execute("SELECT * FROM species WHERE id = ?", (species_id,)).fetchone()
    if r is None:
        return None
    length = "%s cm" % fmt(r["avg_length_cm"]) if r["avg_length_cm"] is not None else "—"
    life = "%s years" % fmt(r["lifespan_years"]) if r["lifespan_years"] is not None else "—"
    body = """
<div class="crumbs"><a href="/">Home</a> &rsaquo; <a href="/species">Browse &amp; Search</a> &rsaquo; %(sci)s</div>
%(flash)s
<div class="card">
  <h1><em>%(sci)s</em></h1>
  <p style="font-size:1.1rem;margin-top:0">%(common)s</p>
  <dl class="details">
    <dt>Scientific name</dt><dd><em>%(sci)s</em></dd>
    <dt>Common name</dt><dd>%(common)s</dd>
    <dt>Kingdom</dt><dd>%(kingdom)s</dd>
    <dt>Class</dt><dd>%(cls)s</dd>
    <dt>Habitat</dt><dd>%(habitat)s</dd>
    <dt>Feeding mode</dt><dd>%(diet)s</dd>
    <dt>Conservation status</dt><dd>%(status)s</dd>
    <dt>Average length</dt><dd>%(length)s</dd>
    <dt>Lifespan</dt><dd>%(life)s</dd>
    <dt>Description</dt><dd>%(desc)s</dd>
  </dl>
</div>
<div class="actions">
  <a class="btn" href="/species/%(id)d/edit">Edit record</a>
  <a class="btn btn-outline" href="/species">Back to list</a>
  <form class="inline" method="post" action="/species/%(id)d/delete"
        onsubmit="return confirm('Delete this species record?');">
    <button class="btn" type="submit">Delete record</button>
  </form>
</div>
""" % {
        "id": r["id"], "sci": e(r["scientific_name"]), "common": e(r["common_name"]) or "—",
        "kingdom": e(r["kingdom"]), "cls": e(r["taxonomic_class"]) or "—",
        "habitat": e(r["habitat"]), "diet": e(r["diet"]),
        "status": badge(r["conservation_status"]), "length": length, "life": life,
        "desc": e(r["description"]) or "—", "flash": flash_html(qs(query, "msg")),
    }
    return layout(r["scientific_name"], body, "browse")


def not_found():
    body = ('<div class="card"><h1>Page not found</h1>'
            '<p>The page you asked for does not exist.</p>'
            '<p><a class="btn" href="/">Back to home</a></p></div>')
    return layout("Not found", body)


def species_form(values, errors, action, heading, submit_label, cancel_href):
    def select(name, label, options, required=True):
        current = values.get(name, "")
        return ('<label for="%s">%s%s<select id="%s" name="%s"%s>%s</select></label>' % (
            name, e(label), " *" if required else "", name, name,
            " required" if required else "",
            option_list(options, current, placeholder="Choose…")))

    def text(name, label, required=False, kind="text", hint=""):
        return ('<label for="%s">%s%s%s<input id="%s" type="%s" name="%s" value="%s"%s></label>' % (
            name, e(label), " *" if required else "",
            (' <span class="hint">%s</span>' % e(hint)) if hint else "",
            name, kind, name, e(values.get(name, "")), " required" if required else ""))

    error_block = ""
    if errors:
        error_block = '<div class="errors" role="alert"><strong>Please fix the following:</strong><ul>%s</ul></div>' % (
            "".join("<li>%s</li>" % e(err) for err in errors))

    return """
<div class="crumbs"><a href="/">Home</a> &rsaquo; <a href="/species">Browse &amp; Search</a> &rsaquo; %(heading)s</div>
<h1>%(heading)s</h1>
%(errors)s
<form class="card" method="post" action="%(action)s" novalidate>
  <div class="form-grid">
    %(sci)s
    %(common)s
    %(kingdom)s
    %(cls)s
    %(habitat)s
    %(diet)s
    %(status)s
    %(length)s
    %(life)s
    <div class="wide">%(desc)s</div>
  </div>
  <p class="muted">* required. Length and lifespan are optional numbers.</p>
  <div class="actions">
    <button class="btn" type="submit">%(submit)s</button>
    <a class="btn btn-outline" href="%(cancel)s">Cancel</a>
  </div>
</form>
""" % {
        "heading": e(heading), "errors": error_block, "action": e(action),
        "sci": text("scientific_name", "Scientific name", required=True, hint="e.g. Panthera leo"),
        "common": text("common_name", "Common name"),
        "kingdom": select("kingdom", "Kingdom", KINGDOMS),
        "cls": text("taxonomic_class", "Class", hint="e.g. Mammalia"),
        "habitat": select("habitat", "Habitat", HABITATS),
        "diet": select("diet", "Feeding mode", DIETS),
        "status": select("conservation_status", "Conservation status", STATUSES),
        "length": text("avg_length_cm", "Average length (cm)", kind="number", hint="optional").replace(
            'type="number"', 'type="number" step="any" min="0"'),
        "life": text("lifespan_years", "Lifespan (years)", kind="number", hint="optional").replace(
            'type="number"', 'type="number" step="any" min="0"'),
        "desc": ('<label for="description">Description<textarea id="description" name="description">%s</textarea></label>'
                 % e(values.get("description", ""))),
        "submit": e(submit_label), "cancel": e(cancel_href),
    }


def form_values(form):
    return {k: (v[0] if v else "") for k, v in form.items()}


def validate(values):
    errors = []
    clean = {}
    sci = values.get("scientific_name", "").strip()
    if not sci:
        errors.append("Scientific name is required.")
    elif len(sci) > 120:
        errors.append("Scientific name must be 120 characters or fewer.")
    clean["scientific_name"] = sci
    for key in ("common_name", "taxonomic_class", "description"):
        clean[key] = values.get(key, "").strip()
    choices = [("kingdom", "kingdom", KINGDOMS), ("habitat", "habitat", HABITATS),
               ("diet", "feeding mode", DIETS), ("conservation_status", "conservation status", STATUSES)]
    for key, label, options in choices:
        value = values.get(key, "").strip()
        if value not in options:
            errors.append("Please choose a valid %s." % label)
        clean[key] = value
    for key, label in (("avg_length_cm", "Average length"), ("lifespan_years", "Lifespan")):
        raw = values.get(key, "").strip()
        clean[key] = None
        if raw:
            try:
                number = float(raw)
                if not math.isfinite(number) or number < 0:
                    raise ValueError
                clean[key] = number
            except ValueError:
                errors.append("%s must be a positive number or left empty." % label)
    return clean, errors


def page_new(values=None, errors=None):
    values = values or {}
    return layout("Add Species", species_form(
        values, errors or [], "/species/new", "Add a species", "Save species", "/species"), "add")


def page_edit(species_id, values=None, errors=None):
    with closing(connect()) as conn:
        r = conn.execute("SELECT * FROM species WHERE id = ?", (species_id,)).fetchone()
    if r is None:
        return None
    if values is None:
        values = {}
        for key in COLUMNS:
            value = r[key]
            values[key] = "" if value is None else ("%g" % value if isinstance(value, float) else str(value))
    return layout("Edit " + r["scientific_name"], species_form(
        values, errors or [], "/species/%d/edit" % species_id, "Edit species record",
        "Save changes", "/species/%d" % species_id), "browse")


def page_about():
    body = """
<div class="crumbs"><a href="/">Home</a> &rsaquo; About</div>
<h1>About this database</h1>
<div class="card">
  <p>This site stores biological information for a collection of species. Each record holds
     the scientific and common name, taxonomic kingdom and class, habitat, feeding mode,
     conservation status, average length and lifespan, and a short description.</p>
  <h2>How to use it</h2>
  <ul>
    <li><strong>Browse &amp; Search</strong>: type a keyword to search names, classes and descriptions,
        then narrow the list with the kingdom, habitat, feeding mode and conservation status filters.
        Results can be sorted by name, length or lifespan.</li>
    <li><strong>View</strong> a species to see its full record.</li>
    <li><strong>Add Species</strong> to create a new record, and <strong>Edit</strong> or
        <strong>Delete</strong> records from the list or the detail page.</li>
  </ul>
  <p class="muted">The database starts with sample species so that every feature can be tried
     straight away. Data is stored in the SQLite file inside the <code>DATA_DIR</code> directory.</p>
</div>
"""
    return layout("About", body, "about")


# ---------------------------------------------------------------- routing

def html_response(status, body):
    return ("html", status, body)


def redirect(location):
    return ("redirect", location)


def save_new(form):
    values = form_values(form)
    clean, errors = validate(values)
    if errors:
        return html_response(200, page_new(values, errors))
    try:
        with closing(connect()) as conn:
            cur = conn.execute(
                INSERT_SQL, [clean[c] for c in COLUMNS])
            conn.commit()
            new_id = cur.lastrowid
    except sqlite3.IntegrityError:
        return html_response(200, page_new(values, ["A species with this scientific name already exists."]))
    return redirect("/species/%d?msg=%s" % (new_id, urllib.parse.quote("Species record added.")))


def save_edit(species_id, form):
    values = form_values(form)
    clean, errors = validate(values)
    if errors:
        return html_response(200, page_edit(species_id, values, errors))
    try:
        with closing(connect()) as conn:
            exists = conn.execute("SELECT 1 FROM species WHERE id = ?", (species_id,)).fetchone()
            if exists is None:
                return html_response(404, not_found())
            conn.execute(
                "UPDATE species SET %s WHERE id = ?" % ", ".join("%s = ?" % c for c in COLUMNS),
                [clean[c] for c in COLUMNS] + [species_id])
            conn.commit()
    except sqlite3.IntegrityError:
        return html_response(200, page_edit(species_id, values, ["A species with this scientific name already exists."]))
    return redirect("/species/%d?msg=%s" % (species_id, urllib.parse.quote("Species record updated.")))


def delete_species(species_id):
    with closing(connect()) as conn:
        conn.execute("DELETE FROM species WHERE id = ?", (species_id,))
        conn.commit()
    return redirect("/species?msg=%s" % urllib.parse.quote("Species record deleted."))


def route(method, path, query, form):
    if method == "GET":
        if path == "/":
            return html_response(200, page_home(query))
        if path == "/about":
            return html_response(200, page_about())
        if path == "/species":
            return html_response(200, page_list(query))
        if path == "/species/new":
            return html_response(200, page_new())
        m = re.fullmatch(r"/species/(\d+)", path)
        if m:
            body = page_detail(int(m.group(1)), query)
            return html_response(200, body) if body else html_response(404, not_found())
        m = re.fullmatch(r"/species/(\d+)/edit", path)
        if m:
            body = page_edit(int(m.group(1)))
            return html_response(200, body) if body else html_response(404, not_found())
    elif method == "POST":
        if path == "/species/new":
            return save_new(form)
        m = re.fullmatch(r"/species/(\d+)/edit", path)
        if m:
            return save_edit(int(m.group(1)), form)
        m = re.fullmatch(r"/species/(\d+)/delete", path)
        if m:
            return delete_species(int(m.group(1)))
    return html_response(404, not_found())


class Handler(BaseHTTPRequestHandler):
    server_version = "SpeciesBase/1.0"

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def dispatch(self, method):
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        form = {}
        if method == "POST":
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8", "replace") if length else ""
            form = urllib.parse.parse_qs(raw, keep_blank_values=True)
        try:
            result = route(method, path, query, form)
        except Exception as exc:  # keep the server alive and show a readable error
            result = html_response(500, layout(
                "Error", '<div class="card"><h1>Something went wrong</h1><p>%s</p></div>' % e(exc)))

        if result[0] == "redirect":
            self.send_response(303)
            self.send_header("Location", result[1])
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        _, status, body = result
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    init_db()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Species database running at http://127.0.0.1:%d (data: %s)" % (PORT, DATA_DIR), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
