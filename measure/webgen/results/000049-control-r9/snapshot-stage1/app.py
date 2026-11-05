#!/usr/bin/env python3
"""Frost & Fade Barbershop management website.

Standard library only (http.server + sqlite3), so no packages are needed.
Environment:
  PORT      port to listen on (default 8000), served on 127.0.0.1
  DATA_DIR  directory holding the SQLite database (default ./data)
"""
import datetime
import html
import math
import os
import re
import sqlite3
import sys
import traceback
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR") or os.path.join(BASE_DIR, "data")
PORT = int(os.environ.get("PORT") or "8000")
DB_PATH = os.path.join(DATA_DIR, "barbershop.db")

SHOP_NAME = "Frost & Fade Barbershop"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SERVICE_CATEGORIES = ["Haircut", "Beard", "Shave", "Hair coloring", "Treatment", "Package"]
NOTICES = {
    "barber_added": "The new barber was added.",
    "service_added": "The new service was added.",
    "client_added": "The new client was added.",
}
TEMPLATES = [
    ("Custom message", ""),
    ("Appointment reminder",
     "Hi {name}, this is a friendly reminder of your appointment at Frost & Fade Barbershop. See you soon!"),
    ("New promotion",
     "Hi {name}! This week only: 15% off all beard services at Frost & Fade. Book your chair today."),
    ("Thank you",
     "Thanks for visiting Frost & Fade, {name}! We hope you love your new look."),
    ("Holiday hours",
     "Hi {name}, Frost & Fade has special holiday hours this season. Reply to this message to book your slot."),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS barbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    specialty TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    years_experience INTEGER NOT NULL DEFAULT 0,
    working_days TEXT NOT NULL DEFAULT '',
    bio TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    duration_min INTEGER NOT NULL DEFAULT 30,
    price REAL NOT NULL DEFAULT 0,
    description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notification_recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id INTEGER NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    client_id INTEGER,
    client_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    text TEXT NOT NULL
);
"""

SAMPLE_BARBERS = [
    ("Marcus Reed", "Classic cuts and hot towel shaves", "+1 555 010 1001", 12,
     "Mon, Tue, Wed, Thu, Fri",
     "Marcus has been cutting hair for over a decade and is known for precise tapers."),
    ("Lena Ortiz", "Color and modern styles", "+1 555 010 1002", 7,
     "Tue, Wed, Thu, Sat",
     "Lena specializes in balayage, color corrections and textured crops."),
    ("Dev Patel", "Beard grooming and fades", "+1 555 010 1003", 5,
     "Wed, Thu, Fri, Sat",
     "Dev designs beard lines and skin fades with a sharp eye for detail."),
]
SAMPLE_SERVICES = [
    ("Classic Haircut", "Haircut", 30, 25.0,
     "Scissor or clipper cut, finished with a wash and style."),
    ("Skin Fade", "Haircut", 40, 32.0,
     "Gradual fade blended down to the skin, with a line-up."),
    ("Beard Trim and Shape", "Beard", 20, 15.0,
     "Beard shaped and lined with clippers and trimmer."),
    ("Hot Towel Shave", "Shave", 35, 28.0,
     "Traditional razor shave with a hot towel and aftercare balm."),
    ("Color Refresh", "Hair coloring", 60, 65.0,
     "Full-head color or gloss with a conditioning finish."),
    ("Groom Package", "Package", 75, 85.0,
     "Haircut, beard trim, hot towel shave and a face mask."),
]
SAMPLE_CLIENTS = [
    ("Jordan Blake", "+1 555 020 2001", "Prefers afternoon slots."),
    ("Sam Carter", "+1 555 020 2002", "Regular, skin fade every three weeks."),
    ("Priya Shah", "+1 555 020 2003", ""),
    ("Mateo Rivera", "+1 555 020 2004", "Interested in the Groom Package."),
]


# ---------------------------------------------------------------- database

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with get_db() as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM barbers").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO barbers (name, specialty, phone, years_experience, working_days, bio) "
                "VALUES (?, ?, ?, ?, ?, ?)", SAMPLE_BARBERS)
        if conn.execute("SELECT COUNT(*) FROM services").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO services (name, category, duration_min, price, description) "
                "VALUES (?, ?, ?, ?, ?)", SAMPLE_SERVICES)
        if conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO clients (name, phone, notes) VALUES (?, ?, ?)", SAMPLE_CLIENTS)


# ---------------------------------------------------------------- helpers

def e(value):
    return html.escape(str(value), quote=True)


def val(form, name):
    """First stripped value of a form/query field ('' when missing)."""
    values = form.get(name) or [""]
    return values[0].strip()


def clean_phone(raw):
    """Return the phone as typed if it looks like a phone number, else None."""
    if not re.fullmatch(r"\+?[0-9 ()\-]{7,25}", raw):
        return None
    digits = re.sub(r"\D", "", raw)
    if not 7 <= len(digits) <= 15:
        return None
    return raw


def parse_int(raw, low, high):
    try:
        number = int(raw)
    except ValueError:
        return None
    return number if low <= number <= high else None


def parse_price(raw):
    try:
        number = float(raw)
    except ValueError:
        return None
    if not math.isfinite(number) or number < 0 or number > 10000:
        return None
    return round(number, 2)


def wa_link(phone, text):
    """WhatsApp click-to-chat link (free, no API): opens a chat with the message filled in."""
    digits = re.sub(r"\D", "", phone)
    return "https://wa.me/" + digits + "?text=" + quote(text, safe="")


def ok(body, status=200):
    return status, [("Content-Type", "text/html; charset=utf-8")], body.encode("utf-8")


def redirect(location):
    return 303, [("Location", location)], b""


def errors_html(errors):
    if not errors:
        return ""
    items = "".join("<li>" + e(err) + "</li>" for err in errors)
    return '<div class="error" role="alert"><ul>' + items + "</ul></div>"


def notice_html(query):
    key = (query.get("notice") or [""])[0]
    if key in NOTICES:
        return '<div class="notice" role="status">' + e(NOTICES[key]) + "</div>"
    return ""


def page_head(title, subtitle, action_href=None, action_label=None):
    button = ""
    if action_href:
        button = '<a class="btn" href="' + e(action_href) + '">' + e(action_label) + "</a>"
    return ('<div class="page-head"><div><h1>' + e(title) + '</h1><p class="muted">'
            + e(subtitle) + "</p></div>" + button + "</div>")


def search_form(action, q, placeholder):
    clear = ""
    if q:
        clear = '<a class="btn secondary" href="' + e(action) + '">Clear</a>'
    return ('<form class="search" method="get" action="' + e(action) + '">'
            '<input type="search" name="q" value="' + e(q) + '" placeholder="' + e(placeholder)
            + '" aria-label="Search">'
            '<button class="btn" type="submit">Search</button>' + clear + "</form>")


def empty_state(text):
    return '<p class="card muted">' + e(text) + "</p>"


# ---------------------------------------------------------------- layout

NAV = [
    ("home", "/", "Home"),
    ("barbers", "/barbers", "Barbers"),
    ("services", "/services", "Services"),
    ("clients", "/clients", "Clients"),
    ("notifications", "/notifications", "WhatsApp Notifications"),
]


def layout(title, active, content):
    links = []
    for key, href, label in NAV:
        cls = ' class="active" aria-current="page"' if key == active else ""
        links.append('<a href="' + href + '"' + cls + ">" + label + "</a>")
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<link rel="icon" href="data:,">'
        "<title>" + e(title) + " | " + e(SHOP_NAME) + "</title>"
        "<style>" + CSS + "</style></head>\n"
        "<body>\n"
        '<div class="snow" aria-hidden="true"></div>\n'
        '<header class="topbar"><div class="brand"><a href="/">' + e(SHOP_NAME) + "</a></div>\n"
        '<nav class="menu" aria-label="Main navigation">' + "".join(links) + "</nav></header>\n"
        '<main class="content">' + content + "</main>\n"
        "<footer>" + e(SHOP_NAME) + " management. WhatsApp messages open in your own WhatsApp"
        " so you press Send yourself.</footer>\n"
        "<script>" + JS + "</script>\n"
        "</body></html>\n"
    )


CSS = """
:root { --gray: #696969; --gray-dark: #4f4f4f; --gray-light: #e8e8e8; --ink: #2b2b2b; }
* { box-sizing: border-box; }
html, body { margin: 0; }
body {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--ink); background: #fffafa; min-height: 100vh; position: relative;
}
.snow { position: fixed; inset: 0; overflow: hidden; pointer-events: none; z-index: 0; }
.flake { position: absolute; top: -40px; color: #aab4bc; animation-name: fall;
  animation-timing-function: linear; animation-iteration-count: infinite; user-select: none; }
@keyframes fall {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(30px, 110vh, 0); }
}
.topbar { position: sticky; top: 0; z-index: 10; background: var(--gray); color: #fff;
  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;
  gap: 8px 20px; padding: 10px 24px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2); }
.brand a { color: #fff; font-weight: 700; font-size: 1.2rem; text-decoration: none; }
.menu { display: flex; flex-wrap: wrap; gap: 4px; }
.menu a { color: #fff; text-decoration: none; padding: 8px 12px; border-radius: 6px; }
.menu a:hover { background: #7b7b7b; }
.menu a.active { background: var(--gray-dark); box-shadow: inset 0 -3px 0 #fff; }
.content { position: relative; z-index: 1; max-width: 1100px; margin: 0 auto; padding: 24px; }
.content a { color: var(--gray-dark); font-weight: 600; }
.content a:hover { color: #222; }
.content h1 { color: var(--gray-dark); margin: 8px 0 4px; font-size: 1.9rem; }
.content h2 { color: var(--gray-dark); margin: 28px 0 12px; }
.content h3 { margin: 0 0 6px; color: var(--gray-dark); }
.page-head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
  gap: 12px; margin-bottom: 16px; }
.page-head p { margin: 0; }
.card { background: rgba(255, 255, 255, 0.94); border: 1px solid #cfcfcf; border-radius: 10px;
  padding: 18px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }
.hero { display: block; }
.hero p { font-size: 1.05rem; margin: 6px 0 14px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; }
.stats { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 16px;
  margin-top: 18px; }
.stat { text-decoration: none; color: var(--ink); text-align: center; }
.stat:hover { border-color: var(--gray); }
.stat .num { display: block; font-size: 2.2rem; font-weight: 700; color: var(--gray); }
.price { font-weight: 700; color: var(--gray-dark); white-space: nowrap; }
.row-between { display: flex; justify-content: space-between; gap: 8px; align-items: baseline; }
.tag { display: inline-block; background: var(--gray-light); color: var(--gray-dark);
  border-radius: 999px; padding: 2px 10px; font-size: 0.85rem; margin: 0 0 8px; }
.muted { color: #6b6b6b; }
.actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 14px; }
.btn { display: inline-block; background: var(--gray); color: #fff; border: 1px solid var(--gray);
  border-radius: 6px; padding: 9px 16px; cursor: pointer; text-decoration: none; font: inherit;
  font-weight: 600; }
.btn:hover { background: var(--gray-dark); border-color: var(--gray-dark); }
.btn.secondary { background: #fff; color: var(--gray-dark); border-color: var(--gray); }
.btn.secondary:hover { background: var(--gray-light); }
.btn.small { padding: 6px 12px; font-size: 0.9rem; }
.search { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.search input { flex: 1 1 260px; }
.form { max-width: 720px; }
.form label { display: block; font-weight: 600; color: var(--gray-dark); margin-top: 14px; }
.form label.check, .check { display: inline-flex; align-items: center; gap: 6px; font-weight: 400;
  color: var(--ink); margin: 6px 14px 0 0; }
.form input[type="text"], .form input[type="number"], .form input[type="tel"],
.form input[type="search"], .form input:not([type]), .form select, .form textarea,
.search input {
  display: block; width: 100%; margin-top: 5px; padding: 9px 10px; border: 1px solid #aaa;
  border-radius: 6px; font: inherit; background: #fff; color: var(--ink);
}
.form textarea { resize: vertical; }
input:focus, select:focus, textarea:focus, button:focus, a:focus {
  outline: 3px solid #9a9a9a; outline-offset: 2px;
}
.form fieldset { border: 1px solid #cfcfcf; border-radius: 6px; margin: 14px 0 0; padding: 10px 12px; }
.form legend { font-weight: 600; color: var(--gray-dark); padding: 0 4px; }
.form small { display: block; margin-top: 4px; }
.table-wrap { overflow-x: auto; border-radius: 10px; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); }
table { width: 100%; border-collapse: collapse; background: #fff; }
th { background: var(--gray); color: #fff; text-align: left; padding: 10px 12px; }
td { padding: 10px 12px; border-bottom: 1px solid #e3e3e3; vertical-align: top; }
td.msg { max-width: 420px; }
.notice { background: #efefef; border-left: 6px solid var(--gray); padding: 10px 14px;
  border-radius: 6px; margin-bottom: 16px; }
.error { background: #f6e7e7; border-left: 6px solid #8b3a3a; padding: 10px 14px;
  border-radius: 6px; margin-bottom: 16px; }
.error ul { margin: 0; padding-left: 18px; }
.hero-note { margin-top: 10px; }
.checks { display: flex; flex-wrap: wrap; }
.client-list { max-height: 320px; overflow-y: auto; padding: 4px 0; }
.client-list .check { display: flex; margin: 4px 0; }
.preview { white-space: pre-wrap; background: #f7f7f7; border: 1px dashed #aaa; border-radius: 6px;
  padding: 10px; }
footer { position: relative; z-index: 1; text-align: center; color: var(--gray); font-size: 0.9rem;
  padding: 24px 16px 32px; }
@media (max-width: 640px) {
  .topbar { padding: 10px 14px; }
  .content { padding: 16px; }
  .page-head { flex-direction: column; align-items: flex-start; }
}
"""

JS = """
(function () {
  var box = document.querySelector('.snow');
  if (box) {
    for (var i = 0; i < 70; i++) {
      var flake = document.createElement('span');
      flake.className = 'flake';
      flake.textContent = '❄';
      flake.style.left = (Math.random() * 100) + 'vw';
      flake.style.fontSize = (8 + Math.random() * 14) + 'px';
      flake.style.animationDuration = (8 + Math.random() * 12) + 's';
      flake.style.animationDelay = (-Math.random() * 20) + 's';
      flake.style.opacity = (0.35 + Math.random() * 0.65).toFixed(2);
      box.appendChild(flake);
    }
  }
  var template = document.getElementById('template');
  var message = document.getElementById('message');
  if (template && message) {
    template.addEventListener('change', function () {
      if (template.value) { message.value = template.value; message.focus(); }
    });
  }
  var all = document.getElementById('select-all');
  if (all) {
    all.addEventListener('change', function () {
      var boxes = document.querySelectorAll('input[name="client_ids"]');
      for (var j = 0; j < boxes.length; j++) { boxes[j].checked = all.checked; }
    });
  }
})();
"""


# ---------------------------------------------------------------- cards

def barber_card(b):
    days = b["working_days"] or "By appointment"
    return f"""<article class="card barber">
<h3>{e(b['name'])}</h3>
<span class="tag">{e(b['specialty'] or 'General grooming')}</span>
<p><strong>Experience:</strong> {b['years_experience']} years</p>
<p><strong>Working days:</strong> {e(days)}</p>
<p><strong>Phone:</strong> {e(b['phone'] or '-')}</p>
<p class="muted">{e(b['bio'])}</p>
</article>"""


def service_card(s):
    return f"""<article class="card service">
<div class="row-between"><h3>{e(s['name'])}</h3><span class="price">${s['price']:.2f}</span></div>
<span class="tag">{e(s['category'] or 'General')} &middot; {s['duration_min']} min</span>
<p class="muted">{e(s['description'])}</p>
</article>"""


# ---------------------------------------------------------------- pages

def page_home():
    with get_db() as conn:
        counts = {}
        for table in ("barbers", "services", "clients", "notifications"):
            counts[table] = conn.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
        barbers = conn.execute("SELECT * FROM barbers ORDER BY id LIMIT 3").fetchall()
    stats = (
        f'<a class="card stat" href="/barbers"><span class="num">{counts["barbers"]}</span>Barbers</a>'
        f'<a class="card stat" href="/services"><span class="num">{counts["services"]}</span>Services</a>'
        f'<a class="card stat" href="/clients"><span class="num">{counts["clients"]}</span>Clients</a>'
        f'<a class="card stat" href="/notifications"><span class="num">{counts["notifications"]}</span>'
        "Notifications sent</a>"
    )
    cards = "".join(barber_card(b) for b in barbers) or empty_state("No barbers yet.")
    content = f"""<section class="card hero">
<h1>Welcome to {e(SHOP_NAME)}</h1>
<p>Manage your barbers, your service menu and your client messages from one place.</p>
<div class="actions">
<a class="btn" href="/barbers/new">+ Add barber</a>
<a class="btn" href="/services/new">+ Add service</a>
<a class="btn secondary" href="/notifications">Send WhatsApp notification</a>
</div>
</section>
<section class="stats">{stats}</section>
<h2>Meet the team</h2>
<div class="grid">{cards}</div>
<p class="hero-note"><a href="/barbers">See all barbers</a> &middot; <a href="/services">See the service menu</a></p>
"""
    return ok(layout("Home", "home", content))


def page_barbers(query):
    q = val(query, "q")
    with get_db() as conn:
        if q:
            like = "%" + q + "%"
            rows = conn.execute(
                "SELECT * FROM barbers WHERE name LIKE ? OR specialty LIKE ? ORDER BY name",
                (like, like)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM barbers ORDER BY name").fetchall()
    grid = '<div class="grid">' + "".join(barber_card(b) for b in rows) + "</div>" if rows \
        else empty_state("No barbers match your search.")
    content = (notice_html(query)
               + page_head("Barbers", "Browse our barbers and add new team members.",
                           "/barbers/new", "+ Add barber")
               + search_form("/barbers", q, "Search by name or specialty")
               + grid)
    return ok(layout("Barbers", "barbers", content))


def page_services(query):
    q = val(query, "q")
    with get_db() as conn:
        if q:
            like = "%" + q + "%"
            rows = conn.execute(
                "SELECT * FROM services WHERE name LIKE ? OR category LIKE ? OR description LIKE ? "
                "ORDER BY category, name", (like, like, like)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM services ORDER BY category, name").fetchall()
    grid = '<div class="grid">' + "".join(service_card(s) for s in rows) + "</div>" if rows \
        else empty_state("No services match your search.")
    content = (notice_html(query)
               + page_head("Services", "Our menu of cuts, shaves and treatments.",
                           "/services/new", "+ Add service")
               + search_form("/services", q, "Search by name, category or description")
               + grid)
    return ok(layout("Services", "services", content))


def barber_form_html(values, errors):
    days_selected = values.get("days", [])
    checks = "".join(
        '<label class="check"><input type="checkbox" name="days" value="' + d + '"'
        + (" checked" if d in days_selected else "") + "> " + d + "</label>"
        for d in WEEKDAYS)
    return f"""<h1>Add a barber</h1>
<p class="muted">Fill in the details of the new team member.</p>
{errors_html(errors)}
<form class="card form" method="post" action="/barbers/new">
<label for="name">Name *</label>
<input type="text" id="name" name="name" required maxlength="80" value="{e(val(values, 'name'))}">
<label for="specialty">Specialty</label>
<input type="text" id="specialty" name="specialty" maxlength="120" value="{e(val(values, 'specialty'))}" placeholder="e.g. Skin fades and beard design">
<label for="phone">Phone</label>
<input type="tel" id="phone" name="phone" maxlength="25" value="{e(val(values, 'phone'))}" placeholder="+1 555 010 1234">
<label for="years">Years of experience</label>
<input type="number" id="years" name="years_experience" min="0" max="80" value="{e(val(values, 'years_experience') or '0')}">
<fieldset><legend>Working days</legend><div class="checks">{checks}</div></fieldset>
<label for="bio">Short bio</label>
<textarea id="bio" name="bio" rows="4" maxlength="500">{e(val(values, 'bio'))}</textarea>
<div class="actions">
<button class="btn" type="submit">Save barber</button>
<a class="btn secondary" href="/barbers">Cancel</a>
</div>
</form>"""


def page_barber_new(values, errors):
    return ok(layout("Add barber", "barbers", barber_form_html(values, errors)))


def save_barber(form):
    errors = []
    name = val(form, "name")
    phone = val(form, "phone")
    if not name:
        errors.append("Name is required.")
    elif len(name) > 80:
        errors.append("Name must be 80 characters or fewer.")
    if phone and clean_phone(phone) is None:
        errors.append("Phone must contain 7 to 15 digits and may start with +.")
    years = parse_int(val(form, "years_experience") or "0", 0, 80)
    if years is None:
        errors.append("Years of experience must be a number from 0 to 80.")
    bio = val(form, "bio")
    if len(bio) > 500:
        errors.append("Bio must be 500 characters or fewer.")
    if errors:
        return page_barber_new(form, errors)
    days = [d for d in WEEKDAYS if d in form.get("days", [])]
    with get_db() as conn:
        conn.execute(
            "INSERT INTO barbers (name, specialty, phone, years_experience, working_days, bio) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name, val(form, "specialty"), phone, years, ", ".join(days), bio))
    return redirect("/barbers?notice=barber_added")


def service_form_html(values, errors):
    current = val(values, "category")
    options = "".join(
        '<option value="' + c + '"' + (" selected" if c == current else "") + ">" + c + "</option>"
        for c in SERVICE_CATEGORIES)
    return f"""<h1>Add a service</h1>
<p class="muted">Add a new item to the service menu.</p>
{errors_html(errors)}
<form class="card form" method="post" action="/services/new">
<label for="name">Service name *</label>
<input type="text" id="name" name="name" required maxlength="80" value="{e(val(values, 'name'))}" placeholder="e.g. Kids Haircut">
<label for="category">Category</label>
<select id="category" name="category">{options}</select>
<label for="duration">Duration (minutes)</label>
<input type="number" id="duration" name="duration_min" min="5" max="480" required value="{e(val(values, 'duration_min') or '30')}">
<label for="price">Price ($)</label>
<input type="number" id="price" name="price" min="0" max="10000" step="0.01" required value="{e(val(values, 'price') or '0')}">
<label for="description">Description</label>
<textarea id="description" name="description" rows="4" maxlength="500">{e(val(values, 'description'))}</textarea>
<div class="actions">
<button class="btn" type="submit">Save service</button>
<a class="btn secondary" href="/services">Cancel</a>
</div>
</form>"""


def page_service_new(values, errors):
    return ok(layout("Add service", "services", service_form_html(values, errors)))


def save_service(form):
    errors = []
    name = val(form, "name")
    category = val(form, "category")
    if not name:
        errors.append("Service name is required.")
    elif len(name) > 80:
        errors.append("Service name must be 80 characters or fewer.")
    if category not in SERVICE_CATEGORIES:
        errors.append("Choose a category from the list.")
    duration = parse_int(val(form, "duration_min"), 5, 480)
    if duration is None:
        errors.append("Duration must be a whole number of minutes from 5 to 480.")
    price = parse_price(val(form, "price"))
    if price is None:
        errors.append("Price must be a number from 0 to 10000.")
    description = val(form, "description")
    if len(description) > 500:
        errors.append("Description must be 500 characters or fewer.")
    if errors:
        return page_service_new(form, errors)
    with get_db() as conn:
        conn.execute(
            "INSERT INTO services (name, category, duration_min, price, description) "
            "VALUES (?, ?, ?, ?, ?)", (name, category, duration, price, description))
    return redirect("/services?notice=service_added")


def page_clients(query):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    if rows:
        body_rows = "".join(
            "<tr><td>" + e(c["name"]) + "</td><td>" + e(c["phone"]) + "</td><td>"
            + e(c["notes"] or "-") + '</td><td><a class="btn secondary small" href="/notifications?client='
            + str(c["id"]) + '">Send message</a></td></tr>' for c in rows)
        table = ('<div class="table-wrap"><table><thead><tr><th>Name</th><th>Phone</th>'
                 "<th>Notes</th><th>Action</th></tr></thead><tbody>" + body_rows
                 + "</tbody></table></div>")
    else:
        table = empty_state("No clients yet. Add one to start sending messages.")
    content = (notice_html(query)
               + page_head("Clients", "People you can send WhatsApp messages to.",
                           "/clients/new", "+ Add client")
               + table)
    return ok(layout("Clients", "clients", content))


def client_form_html(values, errors):
    return f"""<h1>Add a client</h1>
<p class="muted">Clients need a phone number that includes the country code, such as +1 555 010 1234.</p>
{errors_html(errors)}
<form class="card form" method="post" action="/clients/new">
<label for="name">Name *</label>
<input type="text" id="name" name="name" required maxlength="80" value="{e(val(values, 'name'))}">
<label for="phone">WhatsApp phone *</label>
<input type="tel" id="phone" name="phone" required maxlength="25" value="{e(val(values, 'phone'))}" placeholder="+1 555 010 1234">
<label for="notes">Notes</label>
<textarea id="notes" name="notes" rows="3" maxlength="300">{e(val(values, 'notes'))}</textarea>
<div class="actions">
<button class="btn" type="submit">Save client</button>
<a class="btn secondary" href="/clients">Cancel</a>
</div>
</form>"""


def page_client_new(values, errors):
    return ok(layout("Add client", "clients", client_form_html(values, errors)))


def save_client(form):
    errors = []
    name = val(form, "name")
    phone = val(form, "phone")
    notes = val(form, "notes")
    if not name:
        errors.append("Name is required.")
    elif len(name) > 80:
        errors.append("Name must be 80 characters or fewer.")
    if not phone:
        errors.append("WhatsApp phone is required.")
    elif clean_phone(phone) is None:
        errors.append("Phone must contain 7 to 15 digits and may start with +.")
    if len(notes) > 300:
        errors.append("Notes must be 300 characters or fewer.")
    if errors:
        return page_client_new(form, errors)
    with get_db() as conn:
        conn.execute("INSERT INTO clients (name, phone, notes) VALUES (?, ?, ?)",
                     (name, phone, notes))
    return redirect("/clients?notice=client_added")


def page_notifications(query, errors=None, values=None):
    values = values or {}
    pre = val(query, "client")
    with get_db() as conn:
        clients = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
        history = conn.execute(
            "SELECT n.id, n.title, n.created_at, COUNT(r.id) AS recipients FROM notifications n "
            "LEFT JOIN notification_recipients r ON r.notification_id = n.id "
            "GROUP BY n.id ORDER BY n.id DESC LIMIT 20").fetchall()
    if "client_ids" in values:
        selected = set(values["client_ids"])
    elif pre.isdigit():
        selected = {pre}
    else:
        selected = set()
    options = "".join(
        '<option value="' + e(text) + '">' + e(label) + "</option>" for label, text in TEMPLATES)
    if clients:
        client_checks = "".join(
            '<label class="check"><input type="checkbox" name="client_ids" value="' + str(c["id"]) + '"'
            + (" checked" if str(c["id"]) in selected else "") + "> " + e(c["name"])
            + ' <span class="muted">' + e(c["phone"]) + "</span></label>" for c in clients)
        recipients = (
            '<fieldset><legend>Recipients *</legend>'
            '<label class="check"><input type="checkbox" id="select-all"> Select all clients</label>'
            '<div class="client-list">' + client_checks + "</div></fieldset>")
    else:
        recipients = empty_state("No clients yet. Add a client before sending a notification.")
    compose = f"""<section class="card form">
<h2 style="margin-top:0">Compose a notification</h2>
<p class="muted">Each message opens in WhatsApp with the text already filled in. You press Send in WhatsApp.</p>
{errors_html(errors or [])}
<form method="post" action="/notifications">
<label for="template">Start from a template</label>
<select id="template">{options}</select>
<label for="title">Title</label>
<input type="text" id="title" name="title" maxlength="80" value="{e(val(values, 'title'))}" placeholder="e.g. Holiday hours">
<label for="message">Message *</label>
<textarea id="message" name="message" rows="5" maxlength="1000" required>{e(val(values, 'message'))}</textarea>
<small class="muted">Use <code>{{name}}</code> to insert the client's first name.</small>
{recipients}
<div class="actions">
<button class="btn" type="submit">Prepare WhatsApp messages</button>
</div>
</form>
</section>"""
    if history:
        rows = "".join(
            "<tr><td>" + e(n["created_at"]) + "</td><td>" + e(n["title"]) + "</td><td>"
            + str(n["recipients"]) + '</td><td><a class="btn secondary small" href="/notifications/'
            + str(n["id"]) + '">View</a></td></tr>' for n in history)
        past = ('<h2>Recent notifications</h2><div class="table-wrap"><table><thead><tr>'
                "<th>Date</th><th>Title</th><th>Recipients</th><th></th></tr></thead><tbody>"
                + rows + "</tbody></table></div>")
    else:
        past = '<h2>Recent notifications</h2>' + empty_state("No notifications sent yet.")
    content = (
        page_head("WhatsApp Notifications", "Write a message and send it to one or more clients.")
        + notice_html(query) + compose + past)
    return ok(layout("WhatsApp Notifications", "notifications", content))


def create_notification(form):
    title = val(form, "title") or "Message"
    message = val(form, "message")
    ids = [int(x) for x in form.get("client_ids", []) if x.isdigit()]
    errors = []
    if not message:
        errors.append("Message is required.")
    elif len(message) > 1000:
        errors.append("Message must be 1000 characters or fewer.")
    if len(title) > 80:
        errors.append("Title must be 80 characters or fewer.")
    if not ids:
        errors.append("Choose at least one recipient.")
    if errors:
        return page_notifications({}, errors, form)
    with get_db() as conn:
        placeholders = ",".join("?" * len(ids))
        clients = conn.execute(
            "SELECT * FROM clients WHERE id IN (" + placeholders + ") ORDER BY name", ids).fetchall()
        if not clients:
            return page_notifications({}, ["None of the chosen clients exist any more."], form)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        cur = conn.execute(
            "INSERT INTO notifications (title, message, created_at) VALUES (?, ?, ?)",
            (title, message, now))
        nid = cur.lastrowid
        for client in clients:
            first_name = client["name"].split()[0]
            text = message.replace("{name}", first_name)
            conn.execute(
                "INSERT INTO notification_recipients "
                "(notification_id, client_id, client_name, phone, text) VALUES (?, ?, ?, ?, ?)",
                (nid, client["id"], client["name"], client["phone"], text))
    return redirect("/notifications/" + str(nid))


def page_notification_detail(nid):
    with get_db() as conn:
        note = conn.execute("SELECT * FROM notifications WHERE id = ?", (nid,)).fetchone()
        if note is None:
            return page_not_found()
        recipients = conn.execute(
            "SELECT * FROM notification_recipients WHERE notification_id = ? ORDER BY id",
            (nid,)).fetchall()
    rows = []
    for r in recipients:
        link = wa_link(r["phone"], r["text"])
        rows.append(
            "<tr><td>" + e(r["client_name"]) + "</td><td>" + e(r["phone"]) + '</td><td class="msg">'
            + e(r["text"]) + '</td><td><a class="btn small" href="' + e(link)
            + '" target="_blank" rel="noopener">Open in WhatsApp</a></td></tr>')
    content = f"""<p><a href="/notifications">&larr; Back to notifications</a></p>
{page_head(note['title'], 'Sent on ' + note['created_at'] + ' to ' + str(len(recipients)) + ' client(s).')}
<section class="card">
<h2 style="margin-top:0">Message</h2>
<div class="preview">{e(note['message'])}</div>
<p class="muted">Click &ldquo;Open in WhatsApp&rdquo; for each client. WhatsApp opens with the
message filled in, then press Send.</p>
</section>
<h2>Recipients</h2>
<div class="table-wrap"><table><thead><tr><th>Client</th><th>Phone</th><th>Message</th><th></th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="actions"><a class="btn secondary" href="/notifications">Send another notification</a></p>"""
    return ok(layout("Notification " + str(nid), "notifications", content))


def page_not_found():
    content = ('<h1>Page not found</h1><p>That page does not exist.</p>'
               '<p><a class="btn" href="/">Go to the home page</a></p>')
    return ok(layout("Not found", "", content), 404)


# ---------------------------------------------------------------- routing

def route(method, path, query, form):
    if method == "GET":
        if path == "/":
            return page_home()
        if path == "/barbers":
            return page_barbers(query)
        if path == "/barbers/new":
            return page_barber_new({}, [])
        if path == "/services":
            return page_services(query)
        if path == "/services/new":
            return page_service_new({}, [])
        if path == "/clients":
            return page_clients(query)
        if path == "/clients/new":
            return page_client_new({}, [])
        if path == "/notifications":
            return page_notifications(query)
        match = re.fullmatch(r"/notifications/(\d+)", path)
        if match:
            return page_notification_detail(int(match.group(1)))
    elif method == "POST":
        if path == "/barbers/new":
            return save_barber(form)
        if path == "/services/new":
            return save_service(form)
        if path == "/clients/new":
            return save_client(form)
        if path == "/notifications":
            return create_notification(form)
    return page_not_found()


class Handler(BaseHTTPRequestHandler):
    server_version = "FrostFade/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def dispatch(self, method):
        url = urlparse(self.path)
        path = url.path.rstrip("/") or "/"
        query = parse_qs(url.query, keep_blank_values=True)
        form = {}
        if method == "POST":
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            length = min(max(length, 0), 1000000)
            body = self.rfile.read(length).decode("utf-8", "replace")
            form = parse_qs(body, keep_blank_values=True)
        try:
            status, headers, payload = route(method, path, query, form)
        except Exception:
            traceback.print_exc()
            status, headers, payload = ok(
                layout("Error", "", "<h1>Something went wrong</h1>"
                       "<p>Please try again. <a href='/'>Go home</a></p>"), 500)
        self.send_response(status)
        for name, value in headers:
            self.send_header(name, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if method != "HEAD":
            self.wfile.write(payload)


def main():
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("%s running at http://127.0.0.1:%d (data: %s)" % (SHOP_NAME, PORT, DATA_DIR), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
