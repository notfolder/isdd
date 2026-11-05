"""HTML screens of the species database.

Every value that comes from a user or from the database is escaped before it is
written into the page.
"""

from html import escape

from validation import (
    CLASS_VALUES,
    DIET_VALUES,
    HABITAT_VALUES,
    STATUS_LABELS,
)

NAV_ITEMS = (
    ("/", "Home"),
    ("/species", "Browse species"),
    ("/species/new", "Add species"),
)

FORM_FIELDS = (
    ("scientific_name", "Scientific name", "text"),
    ("common_name", "Common name", "text"),
    ("class_name", "Class", "select"),
    ("family", "Family", "text"),
    ("habitat", "Habitat", "select"),
    ("diet", "Diet", "select"),
    ("conservation_status", "Conservation status", "select"),
    ("average_lifespan_years", "Average lifespan (years)", "text"),
    ("average_adult_mass_kg", "Average adult mass (kg)", "text"),
    ("description", "Description", "textarea"),
)

SELECT_OPTIONS = {
    "class_name": tuple((value, value) for value in CLASS_VALUES),
    "habitat": tuple((value, value) for value in HABITAT_VALUES),
    "diet": tuple((value, value) for value in DIET_VALUES),
    "conservation_status": tuple((code, "%s (%s)" % (code, label)) for code, label in STATUS_LABELS.items()),
}

FILTER_FIELDS = (
    ("class_name", "Class", "All classes"),
    ("habitat", "Habitat", "All habitats"),
    ("diet", "Diet", "All diets"),
    ("conservation_status", "Conservation status", "All statuses"),
)

DELETE_CONFIRM = "Delete this species? This cannot be undone."


def render_layout(title, body, notice=None):
    """Wrap a screen body in the common page frame with the navigation menu."""
    links = "".join(
        '<li><a href="%s">%s</a></li>' % (escape(href, quote=True), escape(label)) for href, label in NAV_ITEMS
    )
    nav = (
        '<nav class="site-nav" aria-label="Main navigation">'
        '<a class="brand" href="/">Species Database</a>'
        '<ul>%s</ul></nav>' % links
    )
    notice_html = ""
    if notice:
        notice_html = '<p class="notice" role="status">%s</p>' % escape(notice)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s - Species Database</title>\n"
        '<link rel="stylesheet" href="/static/style.css">\n'
        "</head>\n"
        "<body>\n%s\n<main>\n%s%s\n</main>\n</body>\n</html>\n"
    ) % (escape(title), nav, notice_html, body)


def render_home(total_count, threatened_count):
    """Home screen: the title, two counts and the entry buttons."""
    body = (
        "<h1>Species Database</h1>\n"
        "<p>Browse, search and manage biological information for species.</p>\n"
        '<section class="stats" aria-label="Summary">\n'
        '<div class="stat"><span class="stat-label">Total species</span>'
        '<span class="stat-value" data-testid="total-species">%d</span></div>\n'
        '<div class="stat"><span class="stat-label">Threatened species (VU, EN, CR)</span>'
        '<span class="stat-value" data-testid="threatened-species">%d</span></div>\n'
        "</section>\n"
        '<p class="actions">'
        '<a class="button" href="/species">Browse species</a> '
        '<a class="button" href="/species/new">Add species</a>'
        "</p>\n"
    ) % (total_count, threatened_count)
    return render_layout("Home", body)


def render_species_list(rows, text, filters, total_count, query_string, notice=None):
    """Browse and search screen with the search box, the four filters and the result table.

    query_string is the current search query (without a leading "?"); the detail
    links keep it so that "Back to results" returns to the same list.
    """
    text_value = escape(text, quote=True)
    selects = []
    for name, label, all_label in FILTER_FIELDS:
        options = ['<option value="">%s</option>' % escape(all_label)]
        for value, option_label in SELECT_OPTIONS[name]:
            selected = " selected" if filters.get(name) == value else ""
            options.append(
                '<option value="%s"%s>%s</option>'
                % (escape(value, quote=True), selected, escape(option_label))
            )
        selects.append(
            '<div class="field"><label for="filter-%s">%s</label>'
            '<select id="filter-%s" name="%s">%s</select></div>'
            % (name, escape(label), name, name, "".join(options))
        )
    form = (
        '<form class="search" method="get" action="/species">\n'
        '<div class="field"><label for="q">Search by name</label>'
        '<input id="q" name="q" type="search" value="%s" placeholder="Scientific or common name"></div>\n'
        "%s\n"
        '<div class="form-buttons"><button type="submit">Search</button>'
        '<a class="button secondary" href="/species">Clear</a></div>\n'
        "</form>\n"
    ) % (text_value, "\n".join(selects))

    if rows:
        body_rows = []
        for row in rows:
            detail_href = "/species/%d" % row["id"]
            if query_string:
                detail_href += "?" + query_string
            body_rows.append(
                "<tr><td><a href=\"%s\">%s</a></td><td><em>%s</em></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                % (
                    escape(detail_href, quote=True),
                    escape(row["common_name"]),
                    escape(row["scientific_name"]),
                    escape(row["class_name"]),
                    escape(row["habitat"]),
                    escape(row["diet"]),
                    escape(_status_text(row["conservation_status"])),
                )
            )
        table = (
            '<div class="table-wrap"><table>\n'
            "<thead><tr><th>Common name</th><th>Scientific name</th><th>Class</th>"
            "<th>Habitat</th><th>Diet</th><th>Conservation status</th></tr></thead>\n"
            "<tbody>\n%s\n</tbody></table></div>\n"
        ) % "\n".join(body_rows)
    else:
        table = '<p class="empty">No species match your search.</p>\n'

    heading = "<h1>Browse species</h1>\n"
    count = '<p class="count">Showing %d of %d species</p>\n' % (len(rows), total_count)
    actions = '<p class="actions"><a class="button" href="/species/new">Add species</a></p>\n'
    return render_layout("Browse species", heading + form + count + table + actions, notice=notice)


def render_species_detail(species, back_query, notice=None):
    """Detail screen with every stored value, the edit link and the delete button."""
    species_id = species["id"]
    back_href = "/species" + ("?" + back_query if back_query else "")
    items = [
        ("Scientific name", "<em>%s</em>" % escape(species["scientific_name"])),
        ("Common name", escape(species["common_name"])),
        ("Class", escape(species["class_name"])),
        ("Family", _or_dash(species["family"])),
        ("Habitat", escape(species["habitat"])),
        ("Diet", escape(species["diet"])),
        ("Conservation status", escape(_status_text(species["conservation_status"]))),
        (
            "Average lifespan",
            _or_dash(species["average_lifespan_years"], suffix=" years"),
        ),
        (
            "Average adult mass",
            _or_dash(_format_mass(species["average_adult_mass_kg"]), suffix=" kg"),
        ),
        ("Description", '<span class="pre-wrap">%s</span>' % _or_dash(species["description"])),
    ]
    dl = "\n".join("<div><dt>%s</dt><dd>%s</dd></div>" % (escape(label), value) for label, value in items)
    body = (
        "<h1>%s</h1>\n"
        '<dl class="details">\n%s\n</dl>\n'
        '<p class="actions">'
        '<a class="button secondary" href="%s">Back to results</a> '
        '<a class="button" href="/species/%d/edit">Edit</a></p>\n'
        '<form method="post" action="/species/%d/delete" '
        'onsubmit="return confirm(\'%s\');">'
        '<button type="submit">Delete</button></form>\n'
    ) % (
        escape(species["common_name"]),
        dl,
        escape(back_href, quote=True),
        species_id,
        species_id,
        DELETE_CONFIRM,
    )
    return render_layout(species["common_name"], body, notice=notice)


def render_species_form(values, errors, form_action, heading, cancel_href):
    """Create and edit screen. values holds the raw input strings shown in the fields."""
    error_list = ""
    if errors:
        items = "".join("<li>%s</li>" % escape(message) for message in errors.values())
        error_list = '<div class="errors" role="alert"><p>Please fix the following:</p><ul>%s</ul></div>\n' % items

    fields_html = []
    for name, label, kind in FORM_FIELDS:
        value = values.get(name, "")
        if value is None:
            value = ""
        value = str(value)
        field_id = "field-" + name
        message = errors.get(name)
        error_html = '<p class="field-error">%s</p>' % escape(message) if message else ""
        if kind == "select":
            options = ['<option value="">Select</option>']
            for option_value, option_label in SELECT_OPTIONS[name]:
                selected = " selected" if value == option_value else ""
                options.append(
                    '<option value="%s"%s>%s</option>'
                    % (escape(option_value, quote=True), selected, escape(option_label))
                )
            control = '<select id="%s" name="%s">%s</select>' % (field_id, name, "".join(options))
        elif kind == "textarea":
            control = '<textarea id="%s" name="%s" rows="5">%s</textarea>' % (field_id, name, escape(value))
        else:
            control = '<input id="%s" name="%s" type="text" value="%s">' % (field_id, name, escape(value, quote=True))
        fields_html.append('<div class="field"><label for="%s">%s</label>%s%s</div>' % (
            field_id, escape(label), control, error_html))

    body = (
        "<h1>%s</h1>\n"
        "%s"
        '<form class="species-form" method="post" action="%s" novalidate>\n%s\n'
        '<div class="form-buttons"><button type="submit">Save</button>'
        '<a class="button secondary" href="%s">Cancel</a></div>\n'
        "</form>\n"
    ) % (
        escape(heading),
        error_list,
        escape(form_action, quote=True),
        "\n".join(fields_html),
        escape(cancel_href, quote=True),
    )
    return render_layout(heading, body)


def render_not_found():
    """Screen for an unknown species or an unknown address."""
    body = (
        "<h1>Species not found.</h1>\n"
        '<p><a class="button secondary" href="/species">Back to species list</a></p>\n'
    )
    return render_layout("Species not found", body)


def _status_text(code):
    label = STATUS_LABELS.get(code)
    return "%s (%s)" % (code, label) if label else code


def _or_dash(value, suffix=""):
    if value is None or value == "":
        return "&mdash;"
    return escape(str(value)) + escape(suffix)


def _format_mass(value):
    if value is None:
        return None
    return ("%.2f" % value).rstrip("0").rstrip(".")
