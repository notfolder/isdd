#!/usr/bin/env python3
"""Species Biology Database: a small web app using only the Python standard library."""
import html
import math
import os
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "species.db")

KINGDOMS = ["Animalia", "Plantae", "Fungi", "Protista", "Bacteria", "Archaea"]
DIETS = ["Herbivore", "Carnivore", "Omnivore", "Insectivore", "Nectar feeder",
         "Filter feeder", "Detritivore", "Autotroph", "Saprotroph", "Parasite", "Other"]
HABITATS = ["Marine", "Freshwater", "Terrestrial", "Forest", "Grassland", "Desert",
            "Wetland", "Mountain", "Arctic", "Urban", "Other"]
STATUSES = [("LC", "Least Concern"), ("NT", "Near Threatened"), ("VU", "Vulnerable"),
            ("EN", "Endangered"), ("CR", "Critically Endangered"), ("EW", "Extinct in the Wild"),
            ("EX", "Extinct"), ("DD", "Data Deficient"), ("NE", "Not Evaluated")]
STATUS_LABEL = dict(STATUSES)
SORTS = [("name", "Common name (A-Z)"), ("scientific", "Scientific name (A-Z)"),
         ("lifespan_desc", "Lifespan (longest first)"), ("lifespan_asc", "Lifespan (shortest first)"),
         ("mass_desc", "Body mass (heaviest first)")]
SORT_SQL = {
    "name": "LOWER(common_name), scientific_name",
    "scientific": "scientific_name",
    "lifespan_desc": "average_lifespan_years IS NULL, average_lifespan_years DESC",
    "lifespan_asc": "average_lifespan_years IS NULL, average_lifespan_years ASC",
    "mass_desc": "adult_body_mass_kg IS NULL, adult_body_mass_kg DESC",
}

# Field order used by the form, the INSERT/UPDATE statements and the table.
FORM_FIELDS = ["scientific_name", "common_name", "kingdom", "class_name", "habitat", "diet",
               "conservation_status", "average_lifespan_years", "adult_body_mass_kg",
               "population_estimate", "description"]
NUMERIC_FIELDS = [("average_lifespan_years", "Average lifespan", False),
                  ("adult_body_mass_kg", "Adult body mass", False),
                  ("population_estimate", "Population estimate", True)]

SCHEMA = """
CREATE TABLE IF NOT EXISTS species (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scientific_name TEXT NOT NULL UNIQUE,
    common_name TEXT NOT NULL DEFAULT '',
    kingdom TEXT NOT NULL DEFAULT '',
    class_name TEXT NOT NULL DEFAULT '',
    habitat TEXT NOT NULL DEFAULT '',
    diet TEXT NOT NULL DEFAULT '',
    conservation_status TEXT NOT NULL DEFAULT '',
    average_lifespan_years REAL,
    adult_body_mass_kg REAL,
    population_estimate INTEGER,
    description TEXT NOT NULL DEFAULT ''
);
"""

# Sample data (shown when the database is empty). Column order follows FORM_FIELDS.
SEED = [
    ("Panthera leo", "Lion", "Animalia", "Mammalia", "Grassland", "Carnivore", "VU", 14, 190, 20000,
     "Large social cat living in prides in African savannas. Males defend territories; females hunt cooperatively."),
    ("Ailuropoda melanoleuca", "Giant panda", "Animalia", "Mammalia", "Forest", "Herbivore", "VU", 20, 100, 1864,
     "Bamboo specialist of mountain forests in southwestern China. Its wild population has been recovering slowly."),
    ("Balaenoptera musculus", "Blue whale", "Animalia", "Mammalia", "Marine", "Carnivore", "EN", 80, 120000, None,
     "The largest animal known to have lived. Feeds mainly on krill by filter feeding."),
    ("Ursus maritimus", "Polar bear", "Animalia", "Mammalia", "Arctic", "Carnivore", "VU", 25, 400, 26000,
     "Marine mammal of the Arctic sea ice. Hunts seals and depends on sea ice for access to prey."),
    ("Loxodonta africana", "African bush elephant", "Animalia", "Mammalia", "Grassland", "Herbivore", "VU", 60, 6000, 415000,
     "Largest living land animal. Uses trunk and tusks for feeding and social communication."),
    ("Aptenodytes forsteri", "Emperor penguin", "Animalia", "Aves", "Arctic", "Carnivore", "NT", 20, 30, None,
     "Largest penguin species. Breeds on sea ice during the Antarctic winter; males incubate the egg."),
    ("Apis mellifera", "Western honey bee", "Animalia", "Insecta", "Terrestrial", "Nectar feeder", "NE", 0.12, 0.0001, None,
     "Social bee that forms large colonies and produces honey. Widely managed for pollination."),
    ("Salmo salar", "Atlantic salmon", "Animalia", "Actinopterygii", "Marine", "Carnivore", "LC", 5, 5, None,
     "Anadromous fish that hatches in rivers, grows at sea and returns to freshwater to spawn."),
    ("Ambystoma mexicanum", "Axolotl", "Animalia", "Amphibia", "Freshwater", "Carnivore", "CR", 10, 0.2, None,
     "Aquatic salamander that keeps larval features as an adult. Known for regenerating limbs and organs."),
    ("Quercus robur", "English oak", "Plantae", "Magnoliopsida", "Forest", "Autotroph", "LC", 400, None, None,
     "Deciduous tree common across Europe. Supports a large number of insect and fungal species."),
    ("Amanita muscaria", "Fly agaric", "Fungi", "Agaricomycetes", "Forest", "Parasite", "LC", None, None, None,
     "Mushroom forming mycorrhizal partnerships with birch and pine trees. Toxic if eaten raw."),
    ("Escherichia coli", "Gut bacterium", "Bacteria", "Gammaproteobacteria", "Other", "Other", "NE", None, None, None,
     "Common bacterium of the vertebrate intestine. Many strains are harmless, some cause disease."),
]


def e(value):
    return html.escape("" if value is None else str(value), quote=True)


def fmt_num(value, unit="", digits=None):
    if value is None or value == "":
        return "<span class='muted'>Not recorded</span>"
    if digits is None:
        text = f"{value:,}" if isinstance(value, int) else f"{value:,.2f}".rstrip("0").rstrip(".")
    else:
        text = f"{value:,.{digits}f}"
    return e(text + (" " + unit if unit else ""))


def get1(qs, key):
    return (qs.get(key) or [""])[0].strip()


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = connect()
    try:
        with conn:
            conn.executescript(SCHEMA)
            count = conn.execute("SELECT COUNT(*) FROM species").fetchone()[0]
            if count == 0:
                conn.executemany(
                    "INSERT INTO species (" + ", ".join(FORM_FIELDS) + ") VALUES (" +
                    ", ".join(["?"] * len(FORM_FIELDS)) + ")",
                    SEED)
    finally:
        conn.close()


# ---------- layout ----------

NAV = [("/", "Home"), ("/species", "Browse and search"), ("/species/new", "Add species")]


def layout(title, body, path, notice=""):
    links = []
    for href, label in NAV:
        if href == "/species":
            active = path.startswith("/species") and path != "/species/new"
        else:
            active = path == href
        aria = " aria-current='page'" if active else ""
        links.append(f"<a href='{href}'{aria}>{e(label)}</a>")
    note = f"<p class='notice' role='status'>{e(notice)}</p>" if notice else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | Species Biology Database</title>
<style>{CSS}</style>
</head>
<body>
<header class="site">
  <div class="inner">
    <a class="brand" href="/">Species Biology Database</a>
    <nav class="main" aria-label="Main navigation">{''.join(links)}</nav>
  </div>
</header>
<main>
{note}
{body}
</main>
<footer class="site-footer"><p>Species Biology Database. Sample data is provided for trying the features.</p></footer>
</body>
</html>
"""


CSS = """
:root { --linen:#FAF0E6; --linen-dark:#F1E2CF; --maroon:#800000; --maroon-dark:#5C0000; --ink:#2A1A1A; --white:#FFFCF7; }
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; background: var(--linen); color: var(--ink); line-height: 1.5; }
header.site { background: var(--maroon); color: #fff; }
header.site .inner { max-width: 1100px; margin: 0 auto; padding: 12px 20px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; }
header.site .brand { color: #fff; font-weight: 700; font-size: 1.2rem; text-decoration: none; }
nav.main a { color: #fff; text-decoration: none; margin-left: 10px; padding: 6px 10px; border-radius: 4px; border: 1px solid transparent; }
nav.main a:hover { background: var(--maroon-dark); }
nav.main a[aria-current='page'] { background: var(--maroon-dark); border-color: #fff; }
main { max-width: 1100px; margin: 0 auto; padding: 24px 20px 48px; }
.site-footer { max-width: 1100px; margin: 0 auto; padding: 0 20px 24px; color: var(--maroon); font-size: .9rem; }
h1, h2, h3 { color: var(--maroon); line-height: 1.25; }
h1 { margin-top: 0; }
a { color: var(--maroon); }
.muted { color: #6b5b5b; font-style: italic; }
.sci { font-style: italic; color: var(--ink); font-size: 1.1rem; }
.btn { display: inline-block; background: var(--maroon); color: #fff; border: 2px solid var(--maroon); border-radius: 4px; padding: 8px 14px; font: inherit; font-weight: 600; cursor: pointer; text-decoration: none; }
.btn:hover { background: var(--maroon-dark); border-color: var(--maroon-dark); color: #fff; }
.btn.secondary { background: transparent; color: var(--maroon); }
.btn.secondary:hover { background: var(--maroon); color: #fff; }
.card { background: var(--white); border: 1px solid var(--maroon); border-top: 4px solid var(--maroon); border-radius: 6px; padding: 18px; margin-bottom: 20px; }
.filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; align-items: end; }
.field { margin-bottom: 12px; }
label { display: block; font-weight: 600; color: var(--maroon); font-size: .92rem; margin-bottom: 4px; }
input, select, textarea { width: 100%; padding: 8px; border: 1px solid var(--maroon); border-radius: 4px; background: #fff; font: inherit; color: var(--ink); }
textarea { min-height: 120px; }
.actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 12px; }
form.inline { display: inline; margin: 0; }
table { width: 100%; border-collapse: collapse; background: var(--white); border: 1px solid var(--maroon); }
th { background: var(--maroon); color: #fff; text-align: left; padding: 10px; font-weight: 600; }
td { padding: 10px; border-bottom: 1px solid #e3cdb8; vertical-align: top; }
tr:nth-child(even) td { background: var(--linen-dark); }
table a { font-weight: 600; }
.badge { display: inline-block; background: var(--maroon); color: #fff; border-radius: 999px; padding: 2px 10px; font-size: .85rem; white-space: nowrap; }
.notice { background: var(--maroon); color: #fff; padding: 10px 14px; border-radius: 4px; margin: 0 0 16px; }
.error { border: 2px solid var(--maroon); background: #fff; color: var(--maroon); padding: 10px 14px; border-radius: 4px; margin-bottom: 16px; }
.error ul { margin: 0; padding-left: 20px; }
dl.facts { display: grid; grid-template-columns: max-content 1fr; gap: 8px 22px; margin: 0; }
dl.facts dt { font-weight: 700; color: var(--maroon); }
dl.facts dd { margin: 0; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 14px; margin-bottom: 26px; }
.tile { display: block; background: var(--white); border: 1px solid var(--maroon); border-radius: 6px; padding: 14px; text-decoration: none; color: var(--ink); }
.tile:hover { background: var(--maroon); color: #fff; }
.tile:hover strong, .tile:hover span { color: #fff; }
.tile strong { display: block; color: var(--maroon); font-size: 1.7rem; }
.tile span { color: var(--maroon); font-weight: 600; }
.hero { background: var(--white); border: 1px solid var(--maroon); border-left: 8px solid var(--maroon); border-radius: 6px; padding: 20px; margin-bottom: 26px; }
.count { color: var(--maroon); font-weight: 600; margin: 12px 0; }
:focus-visible { outline: 3px solid var(--maroon); outline-offset: 2px; }
"""


# ---------- pages ----------

def page_home(conn, qs):
    total = conn.execute("SELECT COUNT(*) FROM species").fetchone()[0]
    kingdom_rows = conn.execute("SELECT kingdom, COUNT(*) AS n FROM species WHERE kingdom <> '' GROUP BY kingdom ORDER BY kingdom").fetchall()
    status_rows = conn.execute("SELECT conservation_status AS code, COUNT(*) AS n FROM species WHERE conservation_status <> '' GROUP BY conservation_status").fetchall()
    kingdom_tiles = "".join(
        f"<a class='tile' href='/species?{e(urlencode({'kingdom': r['kingdom']}))}'><strong>{r['n']}</strong><span>{e(r['kingdom'])}</span></a>"
        for r in kingdom_rows)
    status_counts = {r["code"]: r["n"] for r in status_rows}
    status_tiles = "".join(
        f"<a class='tile' href='/species?{e(urlencode({'status': code}))}'><strong>{status_counts[code]}</strong><span>{e(code)} - {e(label)}</span></a>"
        for code, label in STATUSES if status_counts.get(code))
    body = f"""
<section class="hero">
  <h1>Species Biology Database</h1>
  <p>Browse biological information for {total} species, search by name or description, filter by kingdom, habitat, diet or conservation status, and add or correct records.</p>
  <div class="actions">
    <a class="btn" href="/species">Browse and search species</a>
    <a class="btn secondary" href="/species/new">Add a species</a>
  </div>
</section>
<h2>Species by kingdom</h2>
<div class="tiles">{kingdom_tiles or '<p class="muted">No species yet.</p>'}</div>
<h2>Species by conservation status</h2>
<div class="tiles">{status_tiles or '<p class="muted">No conservation status recorded yet.</p>'}</div>
"""
    return layout("Home", body, "/")


def select_options(values, current, blank_label):
    out = [f"<option value=''>{e(blank_label)}</option>"]
    for value, label in values:
        sel = " selected" if value == current else ""
        out.append(f"<option value='{e(value)}'{sel}>{e(label)}</option>")
    return "".join(out)


def page_species_list(conn, qs):
    q = get1(qs, "q")
    kingdom = get1(qs, "kingdom")
    habitat = get1(qs, "habitat")
    diet = get1(qs, "diet")
    status = get1(qs, "status")
    sort = get1(qs, "sort")
    if sort not in SORT_SQL:
        sort = "name"

    where, params = [], []
    if q:
        where.append("(scientific_name LIKE ? OR common_name LIKE ? OR class_name LIKE ? OR habitat LIKE ? OR description LIKE ?)")
        params += [f"%{q}%"] * 5
    for value, column in ((kingdom, "kingdom"), (habitat, "habitat"), (diet, "diet"), (status, "conservation_status")):
        if value:
            where.append(f"{column} = ?")
            params.append(value)
    wsql = (" WHERE " + " AND ".join(where)) if where else ""
    rows = conn.execute(f"SELECT * FROM species{wsql} ORDER BY {SORT_SQL[sort]}", params).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM species").fetchone()[0]

    def distinct(column):
        return [r[0] for r in conn.execute(f"SELECT DISTINCT {column} FROM species WHERE {column} <> '' ORDER BY {column}").fetchall()]

    kingdom_opts = [(v, v) for v in distinct("kingdom")]
    habitat_opts = [(v, v) for v in distinct("habitat")]
    diet_opts = [(v, v) for v in distinct("diet")]
    status_opts = [(c, f"{c} - {l}") for c, l in STATUSES]

    sort_opts = "".join(f"<option value='{e(v)}'{' selected' if v == sort else ''}>{e(l)}</option>" for v, l in SORTS)

    if rows:
        trs = []
        for r in rows:
            status_code = r["conservation_status"]
            status_html = f"<span class='badge'>{e(status_code)}</span>" if status_code else "<span class='muted'>Not set</span>"
            trs.append(
                "<tr>"
                f"<td><a href='/species/{r['id']}'>{e(r['common_name'] or r['scientific_name'])}</a></td>"
                f"<td class='sci'>{e(r['scientific_name'])}</td>"
                f"<td>{e(r['kingdom']) or '<span class=muted>Not set</span>'}</td>"
                f"<td>{e(r['class_name']) or '<span class=muted>Not set</span>'}</td>"
                f"<td>{e(r['habitat']) or '<span class=muted>Not set</span>'}</td>"
                f"<td>{e(r['diet']) or '<span class=muted>Not set</span>'}</td>"
                f"<td>{status_html}</td>"
                f"<td>{fmt_num(r['average_lifespan_years'], 'years')}</td>"
                "</tr>")
        table = ("<div style='overflow-x:auto'><table><caption class='muted' style='caption-side:top;text-align:left'>"
                 "Species list</caption><thead><tr><th scope='col'>Common name</th><th scope='col'>Scientific name</th>"
                 "<th scope='col'>Kingdom</th><th scope='col'>Class</th><th scope='col'>Habitat</th><th scope='col'>Diet</th>"
                 "<th scope='col'>Status</th><th scope='col'>Lifespan</th></tr></thead><tbody>"
                 + "".join(trs) + "</tbody></table></div>")
    else:
        table = "<div class='card'><p>No species match these search terms and filters. Clear a filter or try a shorter search.</p></div>"

    body = f"""
<h1>Browse and search species</h1>
<section class="card" aria-labelledby="filter-heading">
  <h2 id="filter-heading">Search and filter</h2>
  <form method="get" action="/species">
    <div class="filters">
      <div class="field"><label for="q">Search text</label>
        <input id="q" name="q" type="search" value="{e(q)}" placeholder="Name, class, habitat or description"></div>
      <div class="field"><label for="kingdom">Kingdom</label>
        <select id="kingdom" name="kingdom">{select_options(kingdom_opts, kingdom, 'All kingdoms')}</select></div>
      <div class="field"><label for="habitat">Habitat</label>
        <select id="habitat" name="habitat">{select_options(habitat_opts, habitat, 'All habitats')}</select></div>
      <div class="field"><label for="diet">Diet</label>
        <select id="diet" name="diet">{select_options(diet_opts, diet, 'All diets')}</select></div>
      <div class="field"><label for="status">Conservation status</label>
        <select id="status" name="status">{select_options(status_opts, status, 'All statuses')}</select></div>
      <div class="field"><label for="sort">Sort by</label>
        <select id="sort" name="sort">{sort_opts}</select></div>
    </div>
    <div class="actions">
      <button class="btn" type="submit">Apply</button>
      <a class="btn secondary" href="/species">Clear all</a>
    </div>
  </form>
</section>
<p class="count" aria-live="polite">Showing {len(rows)} of {total} species.</p>
{table}
"""
    return layout("Browse and search", body, "/species")


def load_species(conn, species_id):
    return conn.execute("SELECT * FROM species WHERE id = ?", (species_id,)).fetchone()


def page_species_detail(conn, species_id, qs):
    row = load_species(conn, species_id)
    if row is None:
        return None
    status_code = row["conservation_status"]
    status_label = STATUS_LABEL.get(status_code, "")
    status_html = (f"<span class='badge'>{e(status_code)} - {e(status_label)}</span>" if status_code and status_label
                   else (f"<span class='badge'>{e(status_code)}</span>" if status_code else "<span class='muted'>Not recorded</span>"))

    def text(value):
        return e(value) if value else "<span class='muted'>Not recorded</span>"

    facts = [
        ("Scientific name", f"<em>{e(row['scientific_name'])}</em>"),
        ("Common name", text(row["common_name"])),
        ("Kingdom", text(row["kingdom"])),
        ("Class", text(row["class_name"])),
        ("Habitat", text(row["habitat"])),
        ("Diet", text(row["diet"])),
        ("Conservation status", status_html),
        ("Average lifespan", fmt_num(row["average_lifespan_years"], "years")),
        ("Adult body mass", fmt_num(row["adult_body_mass_kg"], "kg")),
        ("Population estimate", fmt_num(row["population_estimate"])),
    ]
    dl = "".join(f"<dt>{e(k)}</dt><dd>{v}</dd>" for k, v in facts)

    related = ""
    if row["habitat"]:
        others = conn.execute(
            "SELECT id, common_name, scientific_name FROM species WHERE habitat = ? AND id <> ? ORDER BY LOWER(common_name) LIMIT 6",
            (row["habitat"], species_id)).fetchall()
        if others:
            items = "".join(f"<li><a href='/species/{o['id']}'>{e(o['common_name'] or o['scientific_name'])}</a></li>" for o in others)
            related = (f"<section class='card'><h2>Other {e(row['habitat'].lower())} species</h2>"
                       f"<ul>{items}</ul>"
                       f"<p><a href='/species?habitat={e(row['habitat'])}'>See all species in this habitat</a></p></section>")

    body = f"""
<p><a href="/species">&larr; Back to browse and search</a></p>
<h1>{e(row['common_name'] or row['scientific_name'])}</h1>
<p class="sci">{e(row['scientific_name'])}</p>
<section class="card" aria-labelledby="facts-heading">
  <h2 id="facts-heading">Biological information</h2>
  <dl class="facts">{dl}</dl>
</section>
<section class="card">
  <h2>Description</h2>
  <p>{e(row['description']) if row['description'] else "<span class='muted'>No description yet.</span>"}</p>
</section>
{related}
<div class="actions">
  <a class="btn" href="/species/{species_id}/edit">Edit this species</a>
  <form class="inline" method="post" action="/species/{species_id}/delete" onsubmit="return confirm('Delete this species and its record? This cannot be undone.');">
    <button class="btn secondary" type="submit">Delete this species</button>
  </form>
</div>
"""
    return layout(row["common_name"] or row["scientific_name"], body, "/species", notice=get1(qs, "notice"))


def form_fields_html(values):
    def v(key):
        return values.get(key, "")

    habitat_list = "".join(f"<option value='{e(h)}'></option>" for h in HABITATS)
    return f"""
<div class="field"><label for="scientific_name">Scientific name (required)</label>
  <input id="scientific_name" name="scientific_name" type="text" required value="{e(v('scientific_name'))}" placeholder="e.g. Panthera leo"></div>
<div class="field"><label for="common_name">Common name</label>
  <input id="common_name" name="common_name" type="text" value="{e(v('common_name'))}"></div>
<div class="field"><label for="kingdom">Kingdom</label>
  <select id="kingdom" name="kingdom">{select_options([(k, k) for k in KINGDOMS], v('kingdom'), 'Not set')}</select></div>
<div class="field"><label for="class_name">Class</label>
  <input id="class_name" name="class_name" type="text" value="{e(v('class_name'))}" placeholder="e.g. Mammalia"></div>
<div class="field"><label for="habitat">Habitat</label>
  <input id="habitat" name="habitat" type="text" list="habitat-options" value="{e(v('habitat'))}" placeholder="Choose or type">
  <datalist id="habitat-options">{habitat_list}</datalist></div>
<div class="field"><label for="diet">Diet</label>
  <select id="diet" name="diet">{select_options([(d, d) for d in DIETS], v('diet'), 'Not set')}</select></div>
<div class="field"><label for="conservation_status">Conservation status</label>
  <select id="conservation_status" name="conservation_status">{select_options([(c, f'{c} - {l}') for c, l in STATUSES], v('conservation_status'), 'Not set')}</select></div>
<div class="field"><label for="average_lifespan_years">Average lifespan (years)</label>
  <input id="average_lifespan_years" name="average_lifespan_years" type="number" step="any" min="0" value="{e(v('average_lifespan_years'))}"></div>
<div class="field"><label for="adult_body_mass_kg">Adult body mass (kg)</label>
  <input id="adult_body_mass_kg" name="adult_body_mass_kg" type="number" step="any" min="0" value="{e(v('adult_body_mass_kg'))}"></div>
<div class="field"><label for="population_estimate">Population estimate (individuals)</label>
  <input id="population_estimate" name="population_estimate" type="number" step="1" min="0" value="{e(v('population_estimate'))}"></div>
<div class="field"><label for="description">Description</label>
  <textarea id="description" name="description" rows="5">{e(v('description'))}</textarea></div>
"""


def page_species_form(values, errors, action, heading, species_id=None):
    err_html = ""
    if errors:
        items = "".join(f"<li>{e(x)}</li>" for x in errors)
        err_html = f"<div class='error' role='alert'><strong>Please fix the following:</strong><ul>{items}</ul></div>"
    cancel = f"/species/{species_id}" if species_id else "/species"
    body = f"""
<p><a href="{cancel}">&larr; Cancel and go back</a></p>
<h1>{e(heading)}</h1>
{err_html}
<form class="card" method="post" action="{action}">
  {form_fields_html(values)}
  <div class="actions">
    <button class="btn" type="submit">Save species</button>
    <a class="btn secondary" href="{cancel}">Cancel</a>
  </div>
</form>
"""
    return layout(heading, body, "/species/new" if species_id is None else "/species")


def validate(raw):
    errors, clean = [], {}
    numeric = {key for key, _, _ in NUMERIC_FIELDS}
    for key in FORM_FIELDS:
        if key not in numeric:
            clean[key] = raw.get(key, "").strip()
    for key, label, as_int in NUMERIC_FIELDS:
        text = raw.get(key, "").strip()
        clean[key] = None
        if not text:
            continue
        try:
            value = int(text) if as_int else float(text)
        except ValueError:
            errors.append(f"{label} must be a number.")
            continue
        if not math.isfinite(value) or value < 0:
            errors.append(f"{label} must be zero or more.")
            continue
        clean[key] = value
    if not clean["scientific_name"]:
        errors.append("Scientific name is required.")
    elif len(clean["scientific_name"]) > 150:
        errors.append("Scientific name must be 150 characters or fewer.")
    if clean["conservation_status"] and clean["conservation_status"] not in STATUS_LABEL:
        errors.append("Conservation status must be one of the listed codes.")
    return clean, errors


def read_form_values(form):
    return {k: (form.get(k) or [""])[0] for k in FORM_FIELDS}


def save_species(conn, clean, species_id=None):
    cols = FORM_FIELDS
    values = [clean[c] for c in cols]
    if species_id is None:
        cur = conn.execute(
            "INSERT INTO species (" + ", ".join(cols) + ") VALUES (" + ", ".join(["?"] * len(cols)) + ")", values)
        return cur.lastrowid
    conn.execute(
        "UPDATE species SET " + ", ".join(f"{c} = ?" for c in cols) + " WHERE id = ?", values + [species_id])
    return species_id


# ---------- HTTP plumbing ----------

def html_response(body, status=200):
    return status, [("Content-Type", "text/html; charset=utf-8")], body.encode("utf-8")


def redirect(location):
    return 303, [("Location", location)], b""


def not_found(path):
    body = (f"<h1>Page not found</h1><p>There is no page at <code>{e(path)}</code>.</p>"
            "<p><a class='btn' href='/'>Go to the home page</a></p>")
    return html_response(layout("Page not found", body, ""), 404)


SPECIES_ID = re.compile(r"^/species/(\d+)$")
SPECIES_EDIT = re.compile(r"^/species/(\d+)/edit$")
SPECIES_DELETE = re.compile(r"^/species/(\d+)/delete$")


def dispatch(method, path, qs, form):
    conn = connect()
    try:
        with conn:
            if method == "GET":
                if path == "/":
                    return html_response(page_home(conn, qs))
                if path == "/species":
                    return html_response(page_species_list(conn, qs))
                if path == "/species/new":
                    return html_response(page_species_form({}, [], "/species/new", "Add a species"))
                m = SPECIES_ID.match(path)
                if m:
                    body = page_species_detail(conn, int(m.group(1)), qs)
                    return html_response(body) if body else not_found(path)
                m = SPECIES_EDIT.match(path)
                if m:
                    row = load_species(conn, int(m.group(1)))
                    if row is None:
                        return not_found(path)
                    values = {k: ("" if row[k] is None else str(row[k])) for k in FORM_FIELDS}
                    return html_response(page_species_form(
                        values, [], f"/species/{row['id']}/edit", "Edit species", row["id"]))
                return not_found(path)

            # POST
            if path == "/species/new":
                raw = read_form_values(form)
                clean, errors = validate(raw)
                if errors:
                    return html_response(page_species_form(raw, errors, "/species/new", "Add a species"))
                try:
                    new_id = save_species(conn, clean)
                except sqlite3.IntegrityError:
                    errors = ["A species with this scientific name already exists."]
                    return html_response(page_species_form(raw, errors, "/species/new", "Add a species"))
                return redirect(f"/species/{new_id}?notice=Species+added.")
            m = SPECIES_EDIT.match(path)
            if m:
                species_id = int(m.group(1))
                if load_species(conn, species_id) is None:
                    return not_found(path)
                raw = read_form_values(form)
                clean, errors = validate(raw)
                action = f"/species/{species_id}/edit"
                if errors:
                    return html_response(page_species_form(raw, errors, action, "Edit species", species_id))
                try:
                    save_species(conn, clean, species_id)
                except sqlite3.IntegrityError:
                    errors = ["A species with this scientific name already exists."]
                    return html_response(page_species_form(raw, errors, action, "Edit species", species_id))
                return redirect(f"/species/{species_id}?notice=Changes+saved.")
            m = SPECIES_DELETE.match(path)
            if m:
                species_id = int(m.group(1))
                conn.execute("DELETE FROM species WHERE id = ?", (species_id,))
                return redirect("/species?notice=Species+deleted.")
            return not_found(path)
    finally:
        conn.close()


class Handler(BaseHTTPRequestHandler):
    server_version = "SpeciesDB/1.0"

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        self.handle_request("POST")

    def handle_request(self, method):
        try:
            url = urlparse(self.path)
            path = url.path.rstrip("/") or "/"
            qs = parse_qs(url.query, keep_blank_values=True)
            form = {}
            if method == "POST":
                length = int(self.headers.get("Content-Length") or 0)
                form = parse_qs(self.rfile.read(length).decode("utf-8", "replace"), keep_blank_values=True)
            status, headers, payload = dispatch(method, path, qs, form)
        except Exception:
            status, headers = 500, [("Content-Type", "text/html; charset=utf-8")]
            payload = layout("Error", "<h1>Something went wrong</h1><p>Please go back and try again.</p>", "").encode("utf-8")
        self.send_response(status)
        for name, value in headers:
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if method != "HEAD" and payload:
            self.wfile.write(payload)


def main():
    init_db()
    port = int(os.environ.get("PORT") or "8000")
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Species Biology Database on http://127.0.0.1:{port} (data: {DB_PATH})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
