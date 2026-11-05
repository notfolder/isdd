"""HTML の組み立て。全画面を共通レイアウトで包み、利用者の入力値は必ずエスケープする。"""

from html import escape

from src.core.validation import CHOICE_FIELDS

SITE_TITLE = "Species Biology Database"


def render_layout(title, body_html):
    """共通レイアウトで本文を包んだ HTML 全体を返す。

    上部にサイト名とナビゲーション（Browse species、Add species）を置く。
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · {SITE_TITLE}</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<header class="site-header">
  <div class="site-title"><a href="/">{SITE_TITLE}</a></div>
  <nav class="site-nav" aria-label="Main">
    <a href="/">Browse species</a>
    <a href="/species/new">Add species</a>
  </nav>
</header>
<main class="container">
<h1>{escape(title)}</h1>
{body_html}
</main>
</body>
</html>
"""


def render_list_page(species_rows, conditions):
    """一覧画面。検索欄と選択欄、結果の表を含む。species_rows は生物種の辞書の一覧。"""
    selects = []
    for field, label, choices in CHOICE_FIELDS:
        options = ['<option value="">All</option>']
        for choice in choices:
            selected = " selected" if conditions.get(field, "") == choice else ""
            options.append(f'<option value="{escape(choice)}"{selected}>{escape(choice)}</option>')
        selects.append(
            f'<label class="filter"><span>{escape(label)}</span>'
            f'<select name="{field}">{"".join(options)}</select></label>'
        )

    form = (
        '<form method="get" action="/" class="search-form">'
        '<label class="filter search"><span>Search</span>'
        '<input type="search" name="q" value="' + escape(conditions.get("q", ""), quote=True) + '" '
        'placeholder="Scientific name, common name or description"></label>'
        + "".join(selects)
        + '<div class="form-actions"><button type="submit">Search</button>'
        '<a class="button-link" href="/">Clear</a></div>'
        "</form>"
    )

    if species_rows:
        rows = []
        for species in species_rows:
            rows.append(
                "<tr>"
                f'<td><a href="/species/{species["id"]}">{escape(species["common_name"])}</a></td>'
                f'<td class="sci"><em>{escape(species["scientific_name"])}</em></td>'
                f'<td>{escape(species["taxonomic_class"])}</td>'
                f'<td>{escape(species["habitat"])}</td>'
                f'<td>{escape(species["diet"])}</td>'
                f'<td>{escape(species["conservation_status"])}</td>'
                "</tr>"
            )
        results = (
            f'<p class="result-count">{len(species_rows)} species</p>'
            '<table class="species-table"><thead><tr>'
            "<th>Common name</th><th>Scientific name</th><th>Class</th>"
            "<th>Habitat</th><th>Diet</th><th>Conservation status</th>"
            "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
        )
    else:
        results = '<p class="empty">No species match the current search and filters.</p>'

    body = form + '<p class="actions"><a class="button-link" href="/species/new">Add species</a></p>' + results
    return render_layout("Browse species", body)


def _display(value):
    """空欄は Unknown と表示する。"""
    if value is None or value == "":
        return "Unknown"
    return str(value)


def render_detail_page(species):
    """詳細画面。species は生物種の辞書。全項目を表示し、修正と削除の操作を置く。"""
    mass = species["body_mass_kg"]
    mass_text = "Unknown" if mass is None else f"{mass:g}"
    items = [
        ("Common name", escape(species["common_name"])),
        ("Scientific name", f'<em>{escape(species["scientific_name"])}</em>'),
        ("Taxonomic class", escape(species["taxonomic_class"])),
        ("Habitat", escape(species["habitat"])),
        ("Diet", escape(species["diet"])),
        ("Lifespan (years)", escape(_display(species["lifespan_years"]))),
        ("Adult body mass (kg)", escape(mass_text)),
        ("Conservation status", escape(species["conservation_status"])),
        ("Description", escape(_display(species["description"]))),
    ]
    definitions = "".join(f"<div><dt>{label}</dt><dd>{value}</dd></div>" for label, value in items)
    species_id = species["id"]
    body = (
        f'<dl class="details">{definitions}</dl>'
        '<div class="actions">'
        f'<a class="button-link" href="/species/{species_id}/edit">Edit</a>'
        f'<form method="post" action="/species/{species_id}/delete" class="inline" '
        "onsubmit=\"return confirm('Delete this species?');\">"
        '<button type="submit" class="danger">Delete</button></form>'
        '<a class="button-link" href="/">Back to list</a>'
        "</div>"
    )
    return render_layout(species["common_name"], body)


def render_form_page(title, values, errors, action, cancel_href):
    """登録・修正画面。values は項目名から文字列への辞書（入力値を残すため生の値を使う）。

    errors はエラー文言のリスト。action は送信先、cancel_href は取り消しのリンク先。
    """
    error_html = ""
    if errors:
        items = "".join(f"<li>{escape(message)}</li>" for message in errors)
        error_html = f'<div class="errors" role="alert"><ul>{items}</ul></div>'

    def text_field(name, label, required=False, maxlength=None):
        required_attr = " required" if required else ""
        length_attr = f' maxlength="{maxlength}"' if maxlength else ""
        return (
            f'<label class="field"><span>{escape(label)}</span>'
            f'<input type="text" name="{name}" value="{escape(values.get(name, ""), quote=True)}"'
            f'{required_attr}{length_attr}></label>'
        )

    def choice_field(name, label, choices):
        options = ['<option value="">Select…</option>']
        for choice in choices:
            selected = " selected" if values.get(name, "") == choice else ""
            options.append(f'<option value="{escape(choice)}"{selected}>{escape(choice)}</option>')
        return (
            f'<label class="field"><span>{escape(label)}</span>'
            f'<select name="{name}" required>{"".join(options)}</select></label>'
        )

    choices = {field: (label, options) for field, label, options in CHOICE_FIELDS}
    fields = (
        text_field("scientific_name", "Scientific name *", required=True, maxlength=100)
        + text_field("common_name", "Common name *", required=True, maxlength=100)
        + choice_field("taxonomic_class", choices["taxonomic_class"][0] + " *", choices["taxonomic_class"][1])
        + choice_field("habitat", choices["habitat"][0] + " *", choices["habitat"][1])
        + choice_field("diet", choices["diet"][0] + " *", choices["diet"][1])
        + text_field("lifespan_years", "Lifespan in years (1 to 500, optional)")
        + text_field("body_mass_kg", "Adult body mass in kg (optional)")
        + choice_field(
            "conservation_status",
            choices["conservation_status"][0] + " *",
            choices["conservation_status"][1],
        )
        + '<label class="field wide"><span>Description (optional, 1000 characters or fewer)</span>'
        f'<textarea name="description" rows="6">{escape(values.get("description", ""))}</textarea></label>'
    )
    body = (
        error_html
        + f'<form method="post" action="{escape(action, quote=True)}" class="species-form">'
        + f'<div class="form-grid">{fields}</div>'
        + '<div class="form-actions"><button type="submit">Save</button>'
        + f'<a class="button-link" href="{escape(cancel_href, quote=True)}">Cancel</a></div>'
        + "</form>"
    )
    return render_layout(title, body)


def render_not_found_page(message):
    """404 画面。message は見出しと本文に使う英語の文言。"""
    body = (
        f'<p class="empty">{escape(message)}</p>'
        '<p class="actions"><a class="button-link" href="/">Browse species</a></p>'
    )
    return render_layout("Not found", body)
