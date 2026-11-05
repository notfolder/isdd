"""HTML rendering for every screen. All user-supplied text is escaped."""

from html import escape

NAV_ITEMS = [
    ("home", "Home", "/"),
    ("barbers", "Barbers", "/barbers"),
    ("services", "Services", "/services"),
    ("notify", "Notify", "/notify"),
]

SNOW_FLAKE_COUNT = 40


def _snow_html():
    """Return the falling snow elements (pure CSS animation, no script)."""
    parts = []
    for i in range(SNOW_FLAKE_COUNT):
        left = (i * 37) % 100
        delay = (i * 0.7) % 9
        duration = 8 + (i * 1.3) % 7
        size = 0.6 + (i % 5) * 0.2
        parts.append(
            '<span class="snowflake" style="left:%d%%;animation-delay:%.1fs;'
            'animation-duration:%.1fs;font-size:%.1fem">&#10052;</span>'
            % (left, delay, duration, size)
        )
    return "".join(parts)


def render_layout(title, active, body):
    """Wrap a page body in the shared layout (menu, snow background, colors).

    Args:
        title: page title shown in the header and the browser tab.
        active: key of the current menu item (home, barbers, services, notify).
        body: HTML for the main area.
    Returns:
        a complete HTML document as a string.
    """
    nav = []
    for key, label, href in NAV_ITEMS:
        current = ' aria-current="page" class="active"' if key == active else ""
        nav.append('<a href="%s"%s>%s</a>' % (href, current, label))
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%(title)s · Barber Shop</title>\n"
        '<link rel="stylesheet" href="/static/style.css">\n'
        "</head>\n<body>\n"
        '<div class="snow" aria-hidden="true">%(snow)s</div>\n'
        '<header class="site-header">\n'
        '<div class="brand">Barber Shop Manager</div>\n'
        '<nav class="site-nav" aria-label="Main">%(nav)s</nav>\n'
        "</header>\n"
        '<main class="content">\n<h1>%(title)s</h1>\n%(body)s\n</main>\n'
        "</body>\n</html>\n"
    ) % {
        "title": escape(title),
        "snow": _snow_html(),
        "nav": "".join(nav),
        "body": body,
    }


def _errors_html(errors):
    """Return the error box for a form, or an empty string when there are no errors."""
    if not errors:
        return ""
    items = "".join("<li>%s</li>" % escape(e) for e in errors)
    return '<div class="errors" role="alert"><p>Please fix the following:</p><ul>%s</ul></div>' % items


def _price_text(price_cents):
    """Format cents as a plain number with two decimals (no currency symbol, D13)."""
    return "%d.%02d" % (price_cents // 100, price_cents % 100)


def render_home(barber_count, service_count):
    """Render the Home screen with links to the three features.

    Args:
        barber_count: number of barbers stored.
        service_count: number of services stored.
    Returns:
        HTML string.
    """
    body = (
        '<div class="cards">'
        '<a class="card" href="/barbers"><h2>Barbers</h2>'
        "<p>%d barber(s). Browse and add staff.</p></a>"
        '<a class="card" href="/services"><h2>Services</h2>'
        "<p>%d service(s). Browse and add the menu.</p></a>"
        '<a class="card" href="/notify"><h2>Notify</h2>'
        "<p>Prepare WhatsApp messages for clients.</p></a>"
        "</div>"
    ) % (barber_count, service_count)
    return render_layout("Home", "home", body)


def render_barber_list(barbers):
    """Render the Barbers list screen.

    Args:
        barbers: list of dicts with name, specialty, phone.
    Returns:
        HTML string.
    """
    if barbers:
        rows = "".join(
            "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (escape(b["name"]), escape(b["specialty"]) or "&mdash;", escape(b["phone"]) or "&mdash;")
            for b in barbers
        )
        table = (
            '<table><thead><tr><th>Name</th><th>Specialty</th><th>Phone</th></tr></thead>'
            "<tbody>%s</tbody></table>" % rows
        )
    else:
        table = '<p class="empty">No barbers yet.</p>'
    body = '<p class="actions"><a class="button" href="/barbers/new">Add barber</a></p>' + table
    return render_layout("Barbers", "barbers", body)


def render_barber_form(values, errors):
    """Render the Add barber form.

    Args:
        values: dict with name, specialty, phone (as typed, for re-display).
        errors: list of English error messages (may be empty).
    Returns:
        HTML string.
    """
    form = (
        '<form method="post" action="/barbers" class="form">'
        '<label>Name <span class="req">*</span>'
        '<input name="name" maxlength="200" required value="%(name)s"></label>'
        '<label>Specialty <input name="specialty" maxlength="200" value="%(specialty)s"></label>'
        '<label>Phone <input name="phone" maxlength="40" value="%(phone)s" '
        'placeholder="+1 555 0100"></label>'
        '<p class="hint">Phone: 8 to 15 digits, with country code. Optional.</p>'
        '<div class="actions"><button type="submit">Save barber</button> '
        '<a href="/barbers">Cancel</a></div></form>'
    ) % {
        "name": escape(values.get("name", ""), quote=True),
        "specialty": escape(values.get("specialty", ""), quote=True),
        "phone": escape(values.get("phone", ""), quote=True),
    }
    return render_layout("Add barber", "barbers", _errors_html(errors) + form)


def render_service_list(services):
    """Render the Services list screen.

    Args:
        services: list of dicts with name, price_cents, duration_min, description.
    Returns:
        HTML string.
    """
    if services:
        rows = "".join(
            "<tr><td>%s</td><td class=\"num\">%s</td><td class=\"num\">%d min</td><td>%s</td></tr>"
            % (
                escape(s["name"]),
                _price_text(s["price_cents"]),
                s["duration_min"],
                escape(s["description"]) or "&mdash;",
            )
            for s in services
        )
        table = (
            "<table><thead><tr><th>Name</th><th>Price</th><th>Duration</th><th>Description</th></tr></thead>"
            "<tbody>%s</tbody></table>" % rows
        )
    else:
        table = '<p class="empty">No services yet.</p>'
    body = '<p class="actions"><a class="button" href="/services/new">Add service</a></p>' + table
    return render_layout("Services", "services", body)


def render_service_form(values, errors):
    """Render the Add service form.

    Args:
        values: dict with name, price, duration_min, description (as typed).
        errors: list of English error messages (may be empty).
    Returns:
        HTML string.
    """
    form = (
        '<form method="post" action="/services" class="form">'
        '<label>Name <span class="req">*</span>'
        '<input name="name" maxlength="200" required value="%(name)s"></label>'
        '<label>Price <span class="req">*</span>'
        '<input name="price" inputmode="decimal" required value="%(price)s" placeholder="25.00"></label>'
        '<label>Duration (minutes) <span class="req">*</span>'
        '<input name="duration_min" inputmode="numeric" required value="%(duration_min)s" '
        'placeholder="30"></label>'
        '<label>Description <textarea name="description" rows="3" maxlength="600">%(description)s</textarea></label>'
        '<p class="hint">Price: 0 to 10000, up to 2 decimals (no currency symbol). '
        "Duration: 5 to 480 minutes.</p>"
        '<div class="actions"><button type="submit">Save service</button> '
        '<a href="/services">Cancel</a></div></form>'
    ) % {
        "name": escape(values.get("name", ""), quote=True),
        "price": escape(values.get("price", ""), quote=True),
        "duration_min": escape(values.get("duration_min", ""), quote=True),
        "description": escape(values.get("description", ""), quote=False),
    }
    return render_layout("Add service", "services", _errors_html(errors) + form)


def render_notify_form(values, errors=None, links=None):
    """Render the Notify screen: the form, and the WhatsApp links after a send.

    Args:
        values: dict with phones and message (as typed, for re-display).
        errors: list of English error messages (may be empty or None).
        links: list of (digits, url) pairs to show after a successful submit, or None.
    Returns:
        HTML string.
    """
    result = ""
    if links:
        items = "".join(
            '<li><span class="number">+%s</span> <a class="button" href="%s" target="_blank" '
            'rel="noopener">Open in WhatsApp</a></li>' % (escape(digits), escape(url, quote=True))
            for digits, url in links
        )
        result = (
            '<section class="result"><h2>WhatsApp links</h2>'
            "<p>Open each link, then press send in WhatsApp.</p><ul>%s</ul></section>" % items
        )
    form = (
        '<form method="post" action="/notify" class="form">'
        '<label>Phone numbers <span class="req">*</span>'
        '<textarea name="phones" rows="4" required placeholder="+1 555 0101&#10;+81 90 5555 0103">%(phones)s</textarea></label>'
        '<label>Message <span class="req">*</span>'
        '<textarea name="message" rows="4" maxlength="600" required>%(message)s</textarea></label>'
        '<p class="hint">One number per line or separated by commas. Include the country code. '
        "Up to 20 numbers. Message: up to 500 characters.</p>"
        '<div class="actions"><button type="submit">Create WhatsApp links</button></div></form>'
    ) % {
        "phones": escape(values.get("phones", ""), quote=False),
        "message": escape(values.get("message", ""), quote=False),
    }
    return render_layout("Notify clients", "notify", _errors_html(errors or []) + form + result)
