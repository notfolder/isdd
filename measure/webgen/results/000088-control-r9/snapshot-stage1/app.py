#!/usr/bin/env python3
"""SpeciesBase: a species biological information database.

Standard library only (sqlite3 + http.server), so no packages are needed.
Environment:
  PORT      port to listen on (default 8000), bound to 127.0.0.1
  DATA_DIR  directory for the SQLite database (default ./data)
"""
import html
import json
import math
import os
import re
import sqlite3
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote_plus, urlencode, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "species.db")
PORT = int(os.environ.get("PORT") or "8000")
PAGE_SIZE = 12

KINGDOMS = ["Animalia", "Plantae", "Fungi", "Protista", "Bacteria", "Archaea"]
HABITATS = ["Terrestrial", "Freshwater", "Marine", "Polar", "Wetland", "Host-associated"]
DIETS = ["Herbivore", "Carnivore", "Omnivore", "Filter feeder", "Decomposer", "Autotroph", "Parasite", "Other"]
STATUSES = [
    ("LC", "Least Concern"),
    ("NT", "Near Threatened"),
    ("VU", "Vulnerable"),
    ("EN", "Endangered"),
    ("CR", "Critically Endangered"),
    ("EW", "Extinct in the Wild"),
    ("EX", "Extinct"),
    ("DD", "Data Deficient"),
    ("NE", "Not Evaluated"),
]
STATUS_CODES = [code for code, _ in STATUSES]
STATUS_NAME = dict(STATUSES)
THREATENED = ("VU", "EN", "CR")

FIELD_NAMES = [
    "scientific_name", "common_name", "kingdom", "class_name", "family",
    "habitat", "diet", "conservation_status", "lifespan_years",
    "body_length_cm", "body_mass_kg", "reproduction", "distribution", "description",
]
NUMERIC_FIELDS = {
    "lifespan_years": "Average lifespan (years)",
    "body_length_cm": "Typical body length (cm)",
    "body_mass_kg": "Typical body mass (kg)",
}
SORTS = {
    "name": ("scientific_name COLLATE NOCASE, id", "Scientific name (A–Z)"),
    "common": ("common_name COLLATE NOCASE, id", "Common name (A–Z)"),
    "lifespan": ("lifespan_years DESC, id", "Lifespan (longest first)"),
    "length": ("body_length_cm DESC, id", "Body length (largest first)"),
    "newest": ("id DESC", "Recently added"),
}
FILTER_KEYS = ["q", "kingdom", "habitat", "diet", "status", "min_life", "max_life", "sort"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name TEXT NOT NULL UNIQUE,
    common_name TEXT,
    kingdom TEXT NOT NULL,
    class_name TEXT,
    family TEXT,
    habitat TEXT,
    diet TEXT,
    conservation_status TEXT,
    lifespan_years REAL,
    body_length_cm REAL,
    body_mass_kg REAL,
    reproduction TEXT,
    distribution TEXT,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_species_kingdom ON species(kingdom);
CREATE INDEX IF NOT EXISTS idx_species_habitat ON species(habitat);
"""

# Sample records, in FIELD_NAMES order. Used only when the database is empty.
SAMPLE_SPECIES = [
    ("Panthera leo", "Lion", "Animalia", "Mammalia", "Felidae", "Terrestrial", "Carnivore", "VU",
     14, 190, 190, "Viviparous; litters of 1–6 cubs; lives in social groups called prides",
     "Sub-Saharan Africa and a small population in the Gir Forest, India",
     "A large social cat that hunts in coordinated groups. Males are recognised by their mane, "
     "and lions are the only cats that live in permanent family groups."),
    ("Ailuropoda melanoleuca", "Giant panda", "Animalia", "Mammalia", "Ursidae", "Terrestrial", "Herbivore", "VU",
     20, 150, 100, "Viviparous; usually one or two cubs born in summer after delayed implantation",
     "Mountain forests of central China (Sichuan, Shaanxi and Gansu)",
     "A bamboo specialist: more than 99 per cent of its diet is bamboo. Its status was improved "
     "from Endangered to Vulnerable in 2016 thanks to habitat protection."),
    ("Balaenoptera musculus", "Blue whale", "Animalia", "Mammalia", "Balaenopteridae", "Marine", "Filter feeder", "EN",
     80, 2400, 150000, "Viviparous; calves are nursed for about seven months",
     "Oceans worldwide, from polar feeding grounds to tropical breeding waters",
     "The largest animal known to have lived. It feeds mainly on krill, taking in large volumes "
     "of water and filtering it through baleen plates."),
    ("Sequoia sempervirens", "Coast redwood", "Plantae", "Pinopsida", "Cupressaceae", "Terrestrial", "Autotroph", "LC",
     2000, 11500, None, "Seeds from cones; also resprouts from burls and stumps",
     "A narrow coastal strip of northern California and south-western Oregon, USA",
     "The tallest living tree species. Fog drip from the coastal air supplies water to the canopy."),
    ("Agaricus bisporus", "Button mushroom", "Fungi", "Agaricomycetes", "Agaricaceae", "Terrestrial", "Decomposer", "NE",
     None, 10, None, "Spores released from the gills; cultivated commercially",
     "Cultivated worldwide; wild relatives occur in grassland",
     "The most widely cultivated mushroom in the world. It breaks down dead organic matter and "
     "recycles nutrients into the soil."),
    ("Escherichia coli", "E. coli", "Bacteria", "Gammaproteobacteria", "Enterobacteriaceae", "Host-associated", "Other", "NE",
     None, 0.0002, None, "Binary fission; can divide roughly every 20 minutes under good conditions",
     "Worldwide, in the intestines of humans and other warm-blooded animals",
     "A rod-shaped bacterium that lives in the lower intestine. Most strains are harmless, "
     "but some cause disease."),
    ("Chelonia mydas", "Green sea turtle", "Animalia", "Reptilia", "Cheloniidae", "Marine", "Herbivore", "EN",
     80, 110, 150, "Oviparous; females nest on sandy tropical beaches, laying about 100 eggs per clutch",
     "Tropical and subtropical seas worldwide",
     "Juveniles are omnivorous, while adults graze mainly on seagrass and algae, which gives "
     "their body fat its greenish colour."),
    ("Ursus maritimus", "Polar bear", "Animalia", "Mammalia", "Ursidae", "Polar", "Carnivore", "VU",
     25, 250, 400, "Viviparous; one to three cubs born in a snow den during winter",
     "Arctic sea-ice regions of Canada, Alaska, Russia, Greenland, Norway and Svalbard",
     "Depends on sea ice to hunt seals. Its black skin under translucent fur helps it absorb heat."),
    ("Apis mellifera", "Western honey bee", "Animalia", "Insecta", "Apidae", "Terrestrial", "Herbivore", "DD",
     0.15, 1.5, 0.0001, "Eusocial colonies with one queen, sterile workers and seasonal drones",
     "Native to Europe, Africa and western Asia; kept by beekeepers worldwide",
     "A major pollinator of crops and wild plants. Foragers communicate the location of food "
     "sources through the waggle dance."),
    ("Salmo salar", "Atlantic salmon", "Animalia", "Actinopterygii", "Salmonidae", "Freshwater", "Carnivore", "LC",
     8, 90, 15, "Oviparous; spawns in gravel nests in rivers after returning from the sea",
     "North Atlantic Ocean and rivers of Europe and north-eastern North America",
     "Hatches in freshwater rivers, spends years at sea, then returns to its birth river to spawn. "
     "Many populations have declined because of dams and pollution."),
    ("Aptenodytes forsteri", "Emperor penguin", "Animalia", "Aves", "Spheniscidae", "Polar", "Carnivore", "NT",
     20, 115, 30, "Oviparous; a single egg is laid in winter and incubated by the males",
     "Coastal sea ice around Antarctica",
     "The largest penguin species. It breeds through the Antarctic winter, and the males huddle "
     "together to conserve warmth."),
    ("Quercus robur", "English oak", "Plantae", "Magnoliopsida", "Fagaceae", "Terrestrial", "Autotroph", "LC",
     800, 3500, None, "Monoecious and wind-pollinated; acorns are spread mainly by jays and squirrels",
     "Western, central and northern Europe, from Iberia to Scandinavia",
     "A long-lived deciduous tree that supports hundreds of invertebrate species. Individual "
     "trees can exceed 800 years."),
    ("Dionaea muscipula", "Venus flytrap", "Plantae", "Magnoliopsida", "Droseraceae", "Wetland", "Autotroph", "NE",
     None, 10, None, "Seeds and vegetative offsets; flowers are pollinated by insects",
     "Coastal North and South Carolina, USA",
     "A carnivorous plant that supplements photosynthesis by trapping insects in hinged leaves. "
     "The trap closes when two trigger hairs are touched in quick succession."),
    ("Octopus vulgaris", "Common octopus", "Animalia", "Cephalopoda", "Octopodidae", "Marine", "Carnivore", "LC",
     1.5, 60, 3, "Oviparous; females brood tens of thousands of eggs and die soon after they hatch",
     "Tropical to temperate coastal waters worldwide",
     "An intelligent cephalopod with three hearts and blue blood. It can change its skin colour "
     "and texture within a fraction of a second."),
    ("Canis lupus", "Gray wolf", "Animalia", "Mammalia", "Canidae", "Terrestrial", "Carnivore", "LC",
     7, 130, 40, "Viviparous; packs usually have one dominant breeding pair and litters of 4–6 pups",
     "North America, Europe and Asia; reintroduced in parts of Western Europe and the USA",
     "The largest wild member of the dog family. Wolves hunt large hoofed animals such as deer, "
     "elk and moose in family packs."),
    ("Delphinus delphis", "Common dolphin", "Animalia", "Mammalia", "Delphinidae", "Marine", "Carnivore", "LC",
     25, 230, 80, "Viviparous; a single calf after a gestation of about 10–11 months",
     "Temperate and tropical oceans worldwide",
     "A fast and highly social dolphin often seen in large groups. It feeds on small schooling "
     "fish and squid."),
    ("Panthera tigris", "Tiger", "Animalia", "Mammalia", "Felidae", "Terrestrial", "Carnivore", "EN",
     15, 190, 180, "Viviparous; litters of 2–4 cubs",
     "Forests and grasslands of South and South-East Asia and eastern Russia",
     "The largest cat species. Each tiger holds a territory and relies on dense cover to ambush "
     "its prey."),
]


# ---------------------------------------------------------------- database

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = get_db()
    try:
        conn.executescript(SCHEMA)
        count = conn.execute("SELECT COUNT(*) FROM species").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO species (%s) VALUES (%s)" % (
                    ", ".join(FIELD_NAMES), ", ".join("?" * len(FIELD_NAMES))),
                SAMPLE_SPECIES,
            )
        conn.commit()
    finally:
        conn.close()


def scalar(conn, sql, args=()):
    return conn.execute(sql, args).fetchone()[0]


# ---------------------------------------------------------------- helpers

def h(value):
    return html.escape("" if value is None else str(value), quote=True)


def to_float(value):
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def fmt_num(value):
    f = float(value)
    if f.is_integer():
        return f"{int(f):,}"
    return f"{f:,.4g}"


def measure(value, unit):
    if value is None:
        return "&mdash;"
    return f"{fmt_num(value)} {unit}"


def dash_or(value):
    return "&mdash;" if value in (None, "") else h(value)


def form_value(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else repr(value)
    return str(value)


def status_badge(code):
    if not code:
        return ""
    name = STATUS_NAME.get(code, code)
    return f'<span class="badge" title="{h(name)}">{h(code)}</span>'


def status_text(code):
    if not code:
        return "&mdash;"
    return f"{h(code)} &ndash; {h(STATUS_NAME.get(code, code))}"


def options_html(options, selected, placeholder):
    out = []
    if placeholder is not None:
        sel = " selected" if selected == "" else ""
        out.append(f'<option value=""{sel}>{h(placeholder)}</option>')
    for value, label in options:
        sel = " selected" if value == selected else ""
        out.append(f'<option value="{h(value)}"{sel}>{h(label)}</option>')
    return "".join(out)


def flat(query_string):
    return {k: v[0] for k, v in parse_qs(query_string, keep_blank_values=True).items()}


def parse_page(p):
    try:
        return max(1, int(p.get("page") or "1"))
    except ValueError:
        return 1


def build_filters(p):
    clauses, args = [], []
    q = (p.get("q") or "").strip()
    if q:
        clauses.append(
            "(scientific_name LIKE ? OR common_name LIKE ? OR family LIKE ? "
            "OR class_name LIKE ? OR description LIKE ? OR distribution LIKE ?)")
        args.extend([f"%{q}%"] * 6)
    for param, column, allowed in (
        ("kingdom", "kingdom", KINGDOMS),
        ("habitat", "habitat", HABITATS),
        ("diet", "diet", DIETS),
        ("status", "conservation_status", STATUS_CODES),
    ):
        value = p.get(param, "")
        if value in allowed:
            clauses.append(f"{column} = ?")
            args.append(value)
    low = to_float(p.get("min_life"))
    if low is not None:
        clauses.append("lifespan_years >= ?")
        args.append(low)
    high = to_float(p.get("max_life"))
    if high is not None:
        clauses.append("lifespan_years <= ?")
        args.append(high)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, args


def query_species(conn, p):
    where, args = build_filters(p)
    matched = scalar(conn, f"SELECT COUNT(*) FROM species{where}", args)
    total = scalar(conn, "SELECT COUNT(*) FROM species")
    pages = max(1, math.ceil(matched / PAGE_SIZE))
    page = min(parse_page(p), pages)
    order = SORTS.get(p.get("sort", "name"), SORTS["name"])[0]
    rows = conn.execute(
        f"SELECT * FROM species{where} ORDER BY {order} LIMIT ? OFFSET ?",
        [*args, PAGE_SIZE, (page - 1) * PAGE_SIZE],
    ).fetchall()
    return {"rows": rows, "matched": matched, "total": total, "pages": pages, "page": page}


def species_card(row):
    name = row["common_name"] or row["scientific_name"]
    return f"""
<a class="card" href="/species/{row['id']}">
  <h3>{h(name)}</h3>
  <p class="sci"><em>{h(row['scientific_name'])}</em></p>
  <p>{badge_for_kingdom(row)}{status_badge(row['conservation_status'])}</p>
</a>"""


def badge_for_kingdom(row):
    parts = [row["kingdom"], row["habitat"]]
    return "".join(f'<span class="badge">{h(x)}</span>' for x in parts if x)


# ---------------------------------------------------------------- layout

CSS = """
:root{--linen:#FAF0E6;--maroon:#800000;--maroon-dark:#5C0000;--ink:#2A1212;--line:rgba(128,0,0,.25)}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--linen);color:var(--ink);line-height:1.55;min-height:100vh;display:flex;flex-direction:column}
main{flex:1;width:100%;max-width:1120px;margin:0 auto;padding:24px 20px 48px}
.inner{max-width:1120px;margin:0 auto;padding:14px 20px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px}
header.site,footer.site{background:var(--maroon);color:var(--linen)}
header.site a.brand{color:var(--linen);font-size:1.5rem;font-weight:700;text-decoration:none;letter-spacing:.02em}
nav.main ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px}
nav.main a{color:var(--linen);text-decoration:none;padding:6px 12px;border-radius:6px;border:2px solid transparent;display:inline-block}
nav.main a:hover,nav.main a:focus,nav.main a.active{background:var(--linen);color:var(--maroon)}
nav.main a.active{font-weight:700}
footer.site{font-size:.9rem;margin-top:24px}
footer.site .inner{justify-content:center;text-align:center}
h1,h2,h3{color:var(--maroon);line-height:1.2}
h1{font-size:2rem;margin:.3em 0 .4em}
h2{font-size:1.35rem;margin:1.2em 0 .5em}
a{color:var(--maroon)}
.card{background:var(--linen);border:2px solid var(--maroon);border-radius:12px;padding:18px 20px;margin:16px 0;color:var(--ink);text-decoration:none;display:block}
.muted{color:#6b4a4a}
.crumbs{font-size:.9rem;margin:0}
.sci{font-size:1.1rem;margin:0 0 .5rem}
.badge{display:inline-block;background:var(--maroon);color:var(--linen);border-radius:999px;padding:2px 10px;font-size:.85rem;margin:2px 4px 2px 0;font-weight:600}
.btn{display:inline-block;background:var(--maroon);color:var(--linen);border:2px solid var(--maroon);border-radius:8px;padding:8px 16px;font:inherit;font-weight:600;text-decoration:none;cursor:pointer}
.btn:hover,.btn:focus{background:var(--maroon-dark);border-color:var(--maroon-dark);color:var(--linen)}
.btn.secondary{background:transparent;color:var(--maroon)}
.btn.secondary:hover,.btn.secondary:focus{background:var(--maroon);color:var(--linen)}
.btn-row{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
form.inline{display:inline;margin:0}
input,select,textarea{font:inherit;width:100%;padding:8px 10px;border:2px solid var(--maroon);border-radius:8px;background:#fff;color:var(--ink)}
textarea{min-height:110px;resize:vertical}
label{display:block;font-weight:600;color:var(--maroon);font-size:.95rem}
label input,label select,label textarea{font-weight:400;margin-top:4px}
input:focus,select:focus,textarea:focus{outline:3px solid rgba(128,0,0,.35);outline-offset:1px}
.filters,.form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px 18px}
.form-grid .wide{grid-column:1/-1}
.actions{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.hint{display:block;font-weight:400;font-size:.85rem;color:#6b4a4a}
.table-wrap{overflow-x:auto;border:2px solid var(--maroon);border-radius:12px;background:var(--linen)}
table{width:100%;border-collapse:collapse}
th,td{padding:10px 12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
thead th{background:var(--maroon);color:var(--linen)}
tbody tr:nth-child(even){background:rgba(128,0,0,.06)}
tbody tr:hover{background:rgba(128,0,0,.14)}
td a{font-weight:600}
.notice{border:2px solid var(--maroon);background:rgba(128,0,0,.1);border-radius:10px;padding:10px 14px;margin:0 0 16px;font-weight:600}
.errors{background:var(--maroon);color:var(--linen);border-radius:10px;padding:10px 16px 10px 32px;margin:0 0 16px}
.hero{padding:24px}
.hero p{font-size:1.05rem}
.searchbar{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}
.searchbar input{flex:1;min-width:240px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin:16px 0}
.tile{background:var(--maroon);color:var(--linen);border-radius:12px;padding:16px;text-align:center}
.tile strong{display:block;font-size:2rem;line-height:1.1}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}
.cards .card{margin:0}
.cards .card h3{margin:0 0 4px;font-size:1.1rem}
.cards .card:hover{background:rgba(128,0,0,.1)}
.facts{display:grid;grid-template-columns:minmax(160px,220px) 1fr;gap:8px 16px;margin:0}
.facts dt{font-weight:700;color:var(--maroon)}
.facts dd{margin:0}
.bar-track{background:rgba(128,0,0,.15);border-radius:6px;height:14px;min-width:120px;overflow:hidden}
.bar{background:var(--maroon);height:100%}
.pager{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin:18px 0}
.pager a,.pager span{padding:6px 12px;border:2px solid var(--maroon);border-radius:8px;text-decoration:none;color:var(--maroon);font-weight:600}
.pager span.current{background:var(--maroon);color:var(--linen)}
.pager a:hover{background:var(--maroon);color:var(--linen)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chips a{border:2px solid var(--maroon);border-radius:999px;padding:4px 12px;text-decoration:none;font-weight:600}
.chips a:hover{background:var(--maroon);color:var(--linen)}
.chips span.n{font-weight:400}
.count{font-weight:600}
@media (max-width:640px){.facts{grid-template-columns:1fr}h1{font-size:1.6rem}}
"""

NAV = [
    ("home", "Home", "/"),
    ("browse", "Browse &amp; Search", "/species"),
    ("add", "Add Species", "/species/new"),
    ("stats", "Statistics", "/statistics"),
    ("api", "JSON API", "/api/species"),
]


def layout(title, body, active="", notice="", error=False):
    items = []
    for key, label, href in NAV:
        cls = ' class="active"' if key == active else ""
        items.append(f'<li><a href="{href}"{cls}>{label}</a></li>')
    notice_html = ""
    if notice:
        cls = "notice error" if error else "notice"
        notice_html = f'<div class="{cls}" role="status">{h(notice)}</div>'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{h(title)} · SpeciesBase</title>
<style>{CSS}</style>
</head>
<body>
<header class="site">
  <div class="inner">
    <a class="brand" href="/">SpeciesBase</a>
    <nav class="main" aria-label="Main navigation"><ul>{"".join(items)}</ul></nav>
  </div>
</header>
<main>
{notice_html}
{body}
</main>
<footer class="site">
  <div class="inner"><span>SpeciesBase – Species Biological Information Database</span></div>
</footer>
</body>
</html>"""


def html_response(body, status=200):
    return status, "text/html; charset=utf-8", body.encode("utf-8"), {}


def redirect(location):
    return 303, "text/plain; charset=utf-8", b"", {"Location": location}


def json_response(obj, status=200):
    data = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
    return status, "application/json; charset=utf-8", data, {}


def not_found(notice=""):
    body = "<h1>Page not found</h1><p>The page you asked for does not exist.</p><p><a class=\"btn\" href=\"/\">Go to home</a></p>"
    return html_response(layout("Not found", body, notice=notice), 404)


# ---------------------------------------------------------------- pages

def page_home(p):
    conn = get_db()
    try:
        total = scalar(conn, "SELECT COUNT(*) FROM species")
        threatened = scalar(conn, "SELECT COUNT(*) FROM species WHERE conservation_status IN (?,?,?)", THREATENED)
        habitat_count = scalar(conn, "SELECT COUNT(DISTINCT habitat) FROM species WHERE habitat IS NOT NULL AND habitat <> ''")
        kingdom_rows = conn.execute(
            "SELECT kingdom, COUNT(*) AS c FROM species GROUP BY kingdom").fetchall()
        kingdom_counts = {r["kingdom"]: r["c"] for r in kingdom_rows}
        habitat_rows = conn.execute(
            "SELECT habitat, COUNT(*) AS c FROM species WHERE habitat IS NOT NULL AND habitat <> '' "
            "GROUP BY habitat ORDER BY c DESC, habitat").fetchall()
        featured = conn.execute("SELECT * FROM species ORDER BY id LIMIT 6").fetchall()
    finally:
        conn.close()

    kingdom_chips = "".join(
        f'<a href="/species?kingdom={h(k)}">{h(k)} <span class="n">({kingdom_counts[k]})</span></a>'
        for k in KINGDOMS if k in kingdom_counts)
    habitat_chips = "".join(
        f'<a href="/species?habitat={h(r["habitat"])}">{h(r["habitat"])} <span class="n">({r["c"]})</span></a>'
        for r in habitat_rows)
    featured_cards = "".join(species_card(r) for r in featured)

    body = f"""
<section class="card hero">
  <h1>Species Biological Information Database</h1>
  <p>Browse, search and manage biological profiles for {total} species: taxonomy, habitat, diet,
  conservation status, lifespan and body size.</p>
  <form class="searchbar" method="get" action="/species" role="search">
    <input type="search" name="q" placeholder="Search by scientific or common name, family or description" aria-label="Search species">
    <button class="btn" type="submit">Search</button>
  </form>
  <div class="btn-row">
    <a class="btn" href="/species">Browse all species</a>
    <a class="btn secondary" href="/species/new">Add a species</a>
    <a class="btn secondary" href="/statistics">View statistics</a>
  </div>
</section>

<section class="tiles" aria-label="Summary">
  <div class="tile"><strong>{total}</strong>Species recorded</div>
  <div class="tile"><strong>{len(kingdom_counts)}</strong>Kingdoms represented</div>
  <div class="tile"><strong>{threatened}</strong>Vulnerable or endangered</div>
  <div class="tile"><strong>{habitat_count}</strong>Habitat types</div>
</section>

<h2>Explore by kingdom</h2>
<div class="chips">{kingdom_chips or '<span class="muted">No species yet.</span>'}</div>

<h2>Explore by habitat</h2>
<div class="chips">{habitat_chips or '<span class="muted">No habitats recorded.</span>'}</div>

<h2>Featured species</h2>
<div class="cards">{featured_cards or '<p class="muted">No species yet. <a href="/species/new">Add the first one</a>.</p>'}</div>
<p><a href="/species">See every species &rarr;</a></p>
"""
    return html_response(layout("Home", body, active="home", notice=p.get("notice", "")))


def pager_html(p, page, pages):
    if pages <= 1:
        return ""
    base = {k: p[k] for k in FILTER_KEYS if p.get(k)}

    def link(n, label=None, current=False):
        if current:
            return f'<span class="current" aria-current="page">{n}</span>'
        query = dict(base, page=str(n))
        return f'<a href="/species?{h(urlencode(query))}">{label or n}</a>'

    parts = []
    if page > 1:
        parts.append(link(page - 1, "&laquo; Prev"))
    shown = sorted({1, pages, *range(max(1, page - 2), min(pages, page + 2) + 1)})
    previous = 0
    for n in shown:
        if n - previous > 1:
            parts.append("<span>&hellip;</span>")
        parts.append(link(n, current=(n == page)))
        previous = n
    if page < pages:
        parts.append(link(page + 1, "Next &raquo;"))
    return f'<nav class="pager" aria-label="Pages">{"".join(parts)}</nav>'


def page_browse(p):
    conn = get_db()
    try:
        result = query_species(conn, p)
    finally:
        conn.close()
    rows, page, pages = result["rows"], result["page"], result["pages"]
    matched, total = result["matched"], result["total"]

    q = p.get("q", "")
    min_life = p.get("min_life", "")
    max_life = p.get("max_life", "")
    sort = p.get("sort", "name")
    filters_html = f"""
<section class="card" aria-label="Search and filter">
<form method="get" action="/species" class="filters">
  <label>Search
    <input type="search" name="q" value="{h(q)}" placeholder="Name, family, description…">
  </label>
  <label>Kingdom
    <select name="kingdom">{options_html([(k, k) for k in KINGDOMS], p.get('kingdom', ''), 'Any kingdom')}</select>
  </label>
  <label>Habitat
    <select name="habitat">{options_html([(x, x) for x in HABITATS], p.get('habitat', ''), 'Any habitat')}</select>
  </label>
  <label>Diet
    <select name="diet">{options_html([(x, x) for x in DIETS], p.get('diet', ''), 'Any diet')}</select>
  </label>
  <label>Conservation status
    <select name="status">{options_html([(c, f'{c} – {n}') for c, n in STATUSES], p.get('status', ''), 'Any status')}</select>
  </label>
  <label>Min lifespan (years)
    <input type="number" name="min_life" min="0" step="any" value="{h(min_life)}">
  </label>
  <label>Max lifespan (years)
    <input type="number" name="max_life" min="0" step="any" value="{h(max_life)}">
  </label>
  <label>Sort by
    <select name="sort">{options_html([(k, v[1]) for k, v in SORTS.items()], sort, None)}</select>
  </label>
  <div class="actions">
    <button class="btn" type="submit">Apply filters</button>
    <a class="btn secondary" href="/species">Clear all</a>
    <a class="btn secondary" href="/species/new">Add a species</a>
  </div>
</form>
</section>
"""
    if rows:
        start = (page - 1) * PAGE_SIZE + 1
        end = start + len(rows) - 1
        table_rows = []
        for r in rows:
            table_rows.append(
                "<tr>"
                f'<td><a href="/species/{r["id"]}"><em>{h(r["scientific_name"])}</em></a></td>'
                f"<td>{dash_or(r['common_name'])}</td>"
                f"<td>{dash_or(r['kingdom'])}</td>"
                f"<td>{dash_or(r['habitat'])}</td>"
                f"<td>{dash_or(r['diet'])}</td>"
                f"<td>{status_badge(r['conservation_status']) or '&mdash;'}</td>"
                f"<td>{'&mdash;' if r['lifespan_years'] is None else fmt_num(r['lifespan_years'])}</td>"
                "</tr>")
        results = f"""
<p class="muted"><span class="count">Showing {start}–{end} of {matched}</span> matching species
({total} in the database).</p>
<div class="table-wrap"><table>
<thead><tr><th>Scientific name</th><th>Common name</th><th>Kingdom</th><th>Habitat</th>
<th>Diet</th><th>Status</th><th>Lifespan (years)</th></tr></thead>
<tbody>{"".join(table_rows)}</tbody>
</table></div>
{pager_html(p, page, pages)}
"""
    else:
        results = f"""
<p class="notice">No species match these filters.
<a href="/species">Clear all filters</a> or <a href="/species/new">add a new species</a>.</p>
"""
    body = f"""
<h1>Browse &amp; Search Species</h1>
<p class="muted">Use the search box and filters to narrow the list, then select a species to see its full profile.</p>
{filters_html}
{results}
"""
    return html_response(layout("Browse species", body, active="browse", notice=p.get("notice", "")))


def page_detail(species_id, p):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM species WHERE id = ?", (species_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return not_found(p.get("notice", ""))
    name = row["common_name"] or row["scientific_name"]
    facts = [
        ("Scientific name", f"<em>{h(row['scientific_name'])}</em>"),
        ("Common name", dash_or(row["common_name"])),
        ("Kingdom", dash_or(row["kingdom"])),
        ("Class", dash_or(row["class_name"])),
        ("Family", dash_or(row["family"])),
        ("Habitat", dash_or(row["habitat"])),
        ("Diet", dash_or(row["diet"])),
        ("Conservation status", status_text(row["conservation_status"])),
        ("Average lifespan", measure(row["lifespan_years"], "years")),
        ("Typical body length", measure(row["body_length_cm"], "cm")),
        ("Typical body mass", measure(row["body_mass_kg"], "kg")),
        ("Reproduction", dash_or(row["reproduction"])),
        ("Distribution", dash_or(row["distribution"])),
    ]
    facts_html = "".join(f"<dt>{label}</dt><dd>{value}</dd>" for label, value in facts)
    confirm = json.dumps(f"Delete {name}? This cannot be undone.")
    body = f"""
<p class="crumbs"><a href="/species">Browse species</a> &rsaquo; {h(name)}</p>
<h1>{h(name)}</h1>
<p class="sci"><em>{h(row['scientific_name'])}</em></p>
<p>{badge_for_kingdom(row)}{status_badge(row['conservation_status'])}</p>

<section class="card" aria-label="Biological information">
  <dl class="facts">{facts_html}</dl>
</section>

<section class="card">
  <h2>Description</h2>
  <p>{dash_or(row['description'])}</p>
  <p class="muted">Record #{row['id']} · last updated {h(row['updated_at'])}</p>
</section>

<section class="card">
  <h2>Manage this record</h2>
  <div class="btn-row">
    <a class="btn" href="/species/{row['id']}/edit">Edit record</a>
    <form class="inline" method="post" action="/species/{row['id']}/delete" onsubmit="return confirm({h(confirm)});">
      <button class="btn secondary" type="submit">Delete record</button>
    </form>
    <a class="btn secondary" href="/species">Back to browse</a>
  </div>
</section>
"""
    return html_response(layout(name, body, active="browse", notice=p.get("notice", "")))


def blank_values():
    return {name: "" for name in FIELD_NAMES}


def render_form(species_id, raw, errors):
    is_edit = species_id is not None
    title = "Edit species" if is_edit else "Add a species"
    action = f"/species/{species_id}/edit" if is_edit else "/species/new"
    error_html = ""
    if errors:
        items = "".join(f"<li>{h(e)}</li>" for e in errors)
        error_html = f'<ul class="errors" role="alert">{items}</ul>'
    v = lambda key: h(raw[key])  # noqa: E731 - short escaped accessor for the template
    body = f"""
<p class="crumbs"><a href="/species">Browse species</a> &rsaquo; {title}</p>
<h1>{title}</h1>
<p class="muted">Fields marked * are required. Numeric values are approximate typical adult values.</p>
{error_html}
<form class="card" method="post" action="{action}">
  <div class="form-grid">
    <label>Scientific name *
      <input name="scientific_name" required maxlength="150" value="{v('scientific_name')}" placeholder="e.g. Panthera leo">
    </label>
    <label>Common name
      <input name="common_name" maxlength="150" value="{v('common_name')}" placeholder="e.g. Lion">
    </label>
    <label>Kingdom *
      <select name="kingdom" required>{options_html([(k, k) for k in KINGDOMS], raw['kingdom'], 'Choose a kingdom…')}</select>
    </label>
    <label>Class
      <input name="class_name" maxlength="100" value="{v('class_name')}" placeholder="e.g. Mammalia">
    </label>
    <label>Family
      <input name="family" maxlength="100" value="{v('family')}" placeholder="e.g. Felidae">
    </label>
    <label>Habitat
      <select name="habitat">{options_html([(x, x) for x in HABITATS], raw['habitat'], 'Choose a habitat…')}</select>
    </label>
    <label>Diet
      <select name="diet">{options_html([(x, x) for x in DIETS], raw['diet'], 'Choose a diet…')}</select>
    </label>
    <label>Conservation status
      <select name="conservation_status">{options_html([(c, f'{c} – {n}') for c, n in STATUSES], raw['conservation_status'], 'Not set')}</select>
    </label>
    <label>Average lifespan (years)
      <input type="number" name="lifespan_years" min="0" step="any" value="{v('lifespan_years')}">
    </label>
    <label>Typical body length (cm)
      <input type="number" name="body_length_cm" min="0" step="any" value="{v('body_length_cm')}">
    </label>
    <label>Typical body mass (kg)
      <input type="number" name="body_mass_kg" min="0" step="any" value="{v('body_mass_kg')}">
    </label>
    <label class="wide">Reproduction
      <input name="reproduction" maxlength="300" value="{v('reproduction')}" placeholder="e.g. Viviparous; litters of 1–6 cubs">
    </label>
    <label class="wide">Distribution
      <input name="distribution" maxlength="300" value="{v('distribution')}" placeholder="Where the species lives">
    </label>
    <label class="wide">Description
      <textarea name="description" maxlength="5000">{v('description')}</textarea>
    </label>
    <div class="actions">
      <button class="btn" type="submit">Save species</button>
      <a class="btn secondary" href="{'/species/' + str(species_id) if is_edit else '/species'}">Cancel</a>
    </div>
  </div>
</form>
"""
    return html_response(layout(title, body, active="add" if not is_edit else "browse", error=bool(errors)),
                         400 if errors else 200)


def page_new_form():
    return render_form(None, blank_values(), [])


def page_edit_form(species_id, p):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM species WHERE id = ?", (species_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return not_found()
    raw = {name: form_value(row[name]) for name in FIELD_NAMES}
    return render_form(species_id, raw, [])


def validate_species(form):
    raw = {name: (form.get(name) or "").strip() for name in FIELD_NAMES}
    errors = []
    if not raw["scientific_name"]:
        errors.append("Scientific name is required.")
    elif len(raw["scientific_name"]) > 150:
        errors.append("Scientific name must be 150 characters or fewer.")
    if raw["kingdom"] not in KINGDOMS:
        errors.append("Please choose a kingdom.")
    if raw["habitat"] and raw["habitat"] not in HABITATS:
        errors.append("Habitat is not one of the listed options.")
    if raw["diet"] and raw["diet"] not in DIETS:
        errors.append("Diet is not one of the listed options.")
    if raw["conservation_status"] and raw["conservation_status"] not in STATUS_CODES:
        errors.append("Conservation status is not one of the listed options.")
    for name, label in NUMERIC_FIELDS.items():
        if raw[name]:
            number = to_float(raw[name])
            if number is None or number < 0:
                errors.append(f"{label} must be a number of zero or more.")
    return raw, errors


def save_species(species_id, form):
    raw, errors = validate_species(form)
    if errors:
        return render_form(species_id, raw, errors)
    values = []
    for name in FIELD_NAMES:
        value = raw[name]
        if name in NUMERIC_FIELDS:
            values.append(to_float(value))
        else:
            values.append(value or None)
    conn = get_db()
    try:
        if species_id is None:
            cur = conn.execute(
                "INSERT INTO species (%s) VALUES (%s)" % (
                    ", ".join(FIELD_NAMES), ", ".join("?" * len(FIELD_NAMES))), values)
            target, notice = cur.lastrowid, "Species added."
        else:
            assignments = ", ".join(f"{name} = ?" for name in FIELD_NAMES)
            cur = conn.execute(
                f"UPDATE species SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values + [species_id])
            if cur.rowcount == 0:
                conn.rollback()
                return not_found()
            target, notice = species_id, "Species updated."
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        errors.append("Another species already uses this scientific name.")
        return render_form(species_id, raw, errors)
    finally:
        conn.close()
    return redirect(f"/species/{target}?notice={quote_plus(notice)}")


def delete_species(species_id):
    conn = get_db()
    try:
        cur = conn.execute("DELETE FROM species WHERE id = ?", (species_id,))
        conn.commit()
        deleted = cur.rowcount
    finally:
        conn.close()
    if not deleted:
        return not_found()
    return redirect("/species?notice=" + quote_plus("Species deleted."))


STAT_DIMENSIONS = [
    ("kingdom", "By kingdom", "kingdom", lambda v: v),
    ("habitat", "By habitat", "habitat", lambda v: v),
    ("diet", "By diet", "diet", lambda v: v),
    ("conservation_status", "By conservation status", "status",
     lambda v: f"{v} – {STATUS_NAME.get(v, v)}"),
]


def page_stats(p):
    conn = get_db()
    try:
        total = scalar(conn, "SELECT COUNT(*) FROM species")
        sections = []
        for column, title, param, label in STAT_DIMENSIONS:
            rows = conn.execute(
                f"SELECT {column} AS v, COUNT(*) AS c FROM species "
                f"WHERE {column} IS NOT NULL AND {column} <> '' "
                f"GROUP BY {column} ORDER BY c DESC, v").fetchall()
            biggest = max([r["c"] for r in rows] or [1])
            lines = []
            for r in rows:
                width = round(100.0 * r["c"] / biggest, 1)
                lines.append(
                    "<tr>"
                    f'<td><a href="/species?{param}={h(r["v"])}">{h(label(r["v"]))}</a></td>'
                    f"<td>{r['c']}</td>"
                    f'<td><div class="bar-track" aria-hidden="true"><div class="bar" style="width:{width}%"></div></div></td>'
                    "</tr>")
            table = (
                '<div class="table-wrap"><table><thead><tr><th>Value</th><th>Species</th><th>Share of largest group</th></tr></thead>'
                f"<tbody>{''.join(lines) or '<tr><td colspan=3>No data</td></tr>'}</tbody></table></div>")
            sections.append(f"<h2>{title}</h2>{table}")
        summary = conn.execute(
            "SELECT kingdom, COUNT(*) AS c, AVG(lifespan_years) AS avg_life, MAX(body_length_cm) AS max_len "
            "FROM species GROUP BY kingdom ORDER BY c DESC, kingdom").fetchall()
    finally:
        conn.close()
    summary_rows = "".join(
        "<tr>"
        f'<td><a href="/species?kingdom={h(r["kingdom"])}">{h(r["kingdom"])}</a></td>'
        f"<td>{r['c']}</td>"
        f"<td>{'&mdash;' if r['avg_life'] is None else fmt_num(round(r['avg_life'], 1))}</td>"
        f"<td>{'&mdash;' if r['max_len'] is None else measure(r['max_len'], 'cm')}</td>"
        "</tr>" for r in summary)
    body = f"""
<h1>Statistics</h1>
<p class="muted">Overview of the {total} species in the database. Select a value to browse those species.</p>
<h2>Summary by kingdom</h2>
<div class="table-wrap"><table>
<thead><tr><th>Kingdom</th><th>Species</th><th>Average lifespan (years)</th><th>Largest recorded body length</th></tr></thead>
<tbody>{summary_rows or '<tr><td colspan=4>No data</td></tr>'}</tbody>
</table></div>
{''.join(sections)}
"""
    return html_response(layout("Statistics", body, active="stats", notice=p.get("notice", "")))


# ---------------------------------------------------------------- JSON API

def api_list(p):
    conn = get_db()
    try:
        result = query_species(conn, p)
    finally:
        conn.close()
    return json_response({
        "total": result["total"],
        "matched": result["matched"],
        "page": result["page"],
        "pages": result["pages"],
        "page_size": PAGE_SIZE,
        "results": [dict(r) for r in result["rows"]],
    })


def api_one(species_id):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM species WHERE id = ?", (species_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return json_response({"error": "not found"}, 404)
    return json_response(dict(row))


# ---------------------------------------------------------------- routing

ID_RE = re.compile(r"^/species/(\d+)$")
EDIT_RE = re.compile(r"^/species/(\d+)/edit$")
DELETE_RE = re.compile(r"^/species/(\d+)/delete$")
API_ONE_RE = re.compile(r"^/api/species/(\d+)$")


def handle_get(path, p):
    if path == "/":
        return page_home(p)
    if path == "/species":
        return page_browse(p)
    if path == "/species/new":
        return page_new_form()
    if path == "/statistics":
        return page_stats(p)
    if path == "/api/species":
        return api_list(p)
    m = ID_RE.match(path)
    if m:
        return page_detail(int(m.group(1)), p)
    m = EDIT_RE.match(path)
    if m:
        return page_edit_form(int(m.group(1)), p)
    m = API_ONE_RE.match(path)
    if m:
        return api_one(int(m.group(1)))
    if path == "/favicon.ico":
        return 204, "text/plain", b"", {}
    return not_found()


def handle_post(path, form):
    if path == "/species/new":
        return save_species(None, form)
    m = EDIT_RE.match(path)
    if m:
        return save_species(int(m.group(1)), form)
    m = DELETE_RE.match(path)
    if m:
        return delete_species(int(m.group(1)))
    return not_found()


class Handler(BaseHTTPRequestHandler):
    server_version = "SpeciesBase/1.0"

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def route(self, method):
        url = urlparse(self.path)
        path = url.path if url.path == "/" else url.path.rstrip("/")
        try:
            if method == "GET":
                response = handle_get(path, flat(url.query))
            else:
                length = int(self.headers.get("Content-Length") or 0)
                form = flat(self.rfile.read(length).decode("utf-8", errors="replace"))
                response = handle_post(path, form)
        except Exception as exc:  # keep the server running; report the error
            traceback.print_exc()
            body = layout("Server error",
                          f"<h1>Something went wrong</h1><p>{h(exc)}</p>"
                          "<p><a class=\"btn\" href=\"/\">Go to home</a></p>")
            response = html_response(body, 500)
        status, content_type, data, headers = response
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        if method != "HEAD" and data:
            self.wfile.write(data)

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"SpeciesBase running at http://127.0.0.1:{PORT}  (data: {DB_PATH})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
