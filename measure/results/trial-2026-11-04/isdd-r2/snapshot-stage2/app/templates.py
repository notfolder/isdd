"""画面の HTML を組み立てる。値は必ず HTML エスケープする。

画面の種類ごとに組み立て関数を分け、外からは render_page だけを呼ぶ。
"""

import html
from typing import Any, Dict, Optional

STYLE = """
:root { --fg:#1d1d1f; --bg:#ffffff; --muted:#6e6e73; --line:#d2d2d7; --accent:#0a5bd3; --danger:#b3261e; --ok:#1b6e3a; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --fg:#f5f5f7; --bg:#1c1c1e; --muted:#a1a1a6; --line:#3a3a3c; --accent:#6aa7ff; --danger:#ff8a80; --ok:#7fd29a; }
}
:root[data-theme="dark"] { --fg:#f5f5f7; --bg:#1c1c1e; --muted:#a1a1a6; --line:#3a3a3c; --accent:#6aa7ff; --danger:#ff8a80; --ok:#7fd29a; }
body { margin:0; background:var(--bg); color:var(--fg); font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif; line-height:1.6; }
header { display:flex; flex-wrap:wrap; align-items:center; gap:12px; padding:12px 16px; border-bottom:1px solid var(--line); }
header .brand { font-weight:700; color:var(--fg); text-decoration:none; }
main { padding:16px; max-width:960px; margin:0 auto; }
nav { display:flex; flex-wrap:wrap; gap:12px; align-items:center; }
a { color:var(--accent); }
button { font:inherit; padding:4px 12px; border-radius:6px; border:1px solid var(--accent); background:var(--accent); color:#fff; cursor:pointer; }
button.secondary { background:transparent; color:var(--accent); }
input, select { font:inherit; padding:6px 8px; border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--fg); max-width:100%; box-sizing:border-box; }
.field { display:flex; flex-direction:column; gap:4px; margin-bottom:12px; }
.field-error { color:var(--danger); font-size:0.9em; }
.message { color:var(--ok); }
.error { color:var(--danger); }
.current-user { font-weight:600; }
.table-wrap { overflow-x:auto; }
table { width:100%; border-collapse:collapse; }
th, td { text-align:left; padding:8px; border-bottom:1px solid var(--line); vertical-align:middle; }
td form, td .inline { display:inline-block; margin:2px 4px 2px 0; }
form.inline { display:inline; }
.lending-equipment { font-weight:600; }
.muted { color:var(--muted); }
@media (max-width:600px) { main { padding:16px; } }
"""


def _e(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def _field(ctx: Dict[str, Any], field_id: str, label: str, control: str) -> str:
    error = ctx.get("errors", {}).get(field_id)
    error_html = f'<span class="field-error">{_e(error)}</span>' if error else ""
    return (
        f'<div class="field"><label for="{_e(field_id)}">{_e(label)}</label>'
        f"{control}{error_html}</div>"
    )


def _notice(ctx: Dict[str, Any]) -> str:
    parts = []
    if ctx.get("message"):
        parts.append(f'<p class="message">{_e(ctx["message"])}</p>')
    if ctx.get("error"):
        parts.append(f'<p class="error">{_e(ctx["error"])}</p>')
    return "".join(parts)


def _header(ctx: Dict[str, Any]) -> str:
    user: Optional[dict] = ctx.get("user")
    links = []
    if user is None:
        links.append('<a href="/login/">ログイン</a>')
        links.append('<a href="/accounts/register/">アカウント登録</a>')
    else:
        links.append(f'<span class="current-user">{_e(user["name"])}</span>')
        if user["role"] == "manager":
            links.append('<a href="/equipment/new/">備品の登録</a>')
            links.append('<a href="/accounts/">アカウントの一覧</a>')
        links.append(
            '<form method="post" action="/logout/" class="inline">'
            '<button type="submit" class="secondary">ログアウト</button></form>'
        )
    return (
        '<header><a class="brand" href="/">備品台帳</a>'
        f'<nav>{"".join(links)}</nav></header>'
    )


def _lending_status(ctx: Dict[str, Any]) -> str:
    is_manager = ctx.get("user") is not None and ctx["user"]["role"] == "manager"
    head = "<th>管理番号</th><th>備品名</th><th>状態</th><th>借りている社員</th><th>貸出日</th>"
    if is_manager:
        head += "<th>操作</th>"
    rows = []
    for row in ctx.get("rows", []):
        lent = row["employee_number"] is not None
        cells = [
            f"<td>{_e(row['equipment_number'])}</td>",
            f"<td>{_e(row['name'])}</td>",
            f"<td>{'貸出中' if lent else '空き'}</td>",
            f"<td>{_e(row['borrower_name'])}</td>",
            f"<td>{_e(row['lent_on'])}</td>",
        ]
        if is_manager:
            eid = _e(row["id"])
            ops = (
                f'<form method="get" action="/equipment/{eid}/edit/"><button type="submit">修正</button></form>'
                f'<form method="post" action="/equipment/{eid}/delete/" '
                "onsubmit=\"return confirm('この備品を削除しますか？')\">"
                f'<input type="hidden" name="version" value="{_e(row["version"])}">'
                '<button type="submit" class="secondary">削除</button></form>'
            )
            if lent:
                ops += (
                    f'<form method="post" action="/equipment/{eid}/return/" '
                    "onsubmit=\"return confirm('返却を登録しますか？')\">"
                    '<button type="submit">返却</button></form>'
                )
            else:
                ops += (
                    f'<form method="get" action="/equipment/{eid}/lend/">'
                    '<button type="submit">貸出</button></form>'
                )
            cells.append(f"<td>{ops}</td>")
        rows.append(f'<tr data-equipment-number="{_e(row["equipment_number"])}">{"".join(cells)}</tr>')
    empty = "" if ctx.get("rows") else '<p class="muted">備品は登録されていません</p>'
    body = (
        "<h1>貸出状況</h1>" + _notice(ctx) + empty
        + f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )
    return body


def _register_account(ctx: Dict[str, Any]) -> str:
    values = ctx.get("values", {})
    body = (
        "<h1>アカウント登録</h1>" + _notice(ctx)
        + '<form method="post" action="/accounts/register/">'
        + _field(ctx, "id_employee_number", "社員番号（6 桁の数字）",
                 f'<input id="id_employee_number" name="employee_number" inputmode="numeric" autocomplete="off" value="{_e(values.get("employee_number"))}">')
        + _field(ctx, "id_name", "名前（30 文字以内）",
                 f'<input id="id_name" name="name" autocomplete="name" value="{_e(values.get("name"))}">')
        + _field(ctx, "id_password", "パスワード（8 文字以上）",
                 '<input id="id_password" name="password" type="password" autocomplete="new-password">')
        + '<button type="submit">登録</button></form>'
        + '<p><a href="/login/">ログインへ</a></p>'
    )
    return body


def _login(ctx: Dict[str, Any]) -> str:
    values = ctx.get("values", {})
    body = (
        "<h1>ログイン</h1>" + _notice(ctx)
        + '<form method="post" action="/login/">'
        + _field(ctx, "id_employee_number", "社員番号",
                 f'<input id="id_employee_number" name="employee_number" inputmode="numeric" autocomplete="username" value="{_e(values.get("employee_number"))}">')
        + _field(ctx, "id_password", "パスワード",
                 '<input id="id_password" name="password" type="password" autocomplete="current-password">')
        + '<button type="submit">ログイン</button></form>'
        + '<p><a href="/accounts/register/">アカウント登録</a></p>'
    )
    return body


def _equipment_form(ctx: Dict[str, Any]) -> str:
    values = ctx.get("values", {})
    version = ctx.get("version")
    hidden = f'<input type="hidden" name="version" value="{_e(version)}">' if version is not None else ""
    body = (
        f"<h1>{_e(ctx.get('heading'))}</h1>" + _notice(ctx)
        + f'<form method="post" action="{_e(ctx.get("action"))}">' + hidden
        + _field(ctx, "id_equipment_number", "管理番号（半角の英数字とハイフン、20 文字以内）",
                 f'<input id="id_equipment_number" name="equipment_number" autocomplete="off" value="{_e(values.get("equipment_number"))}">')
        + _field(ctx, "id_name", "備品名（50 文字以内）",
                 f'<input id="id_name" name="name" autocomplete="off" value="{_e(values.get("name"))}">')
        + '<button type="submit">保存</button></form>'
        + '<p><a href="/">貸出状況に戻る</a></p>'
    )
    return body


def _lending_form(ctx: Dict[str, Any]) -> str:
    equipment = ctx["equipment"]
    options = ['<option value="">選んでください</option>']
    for account in ctx.get("accounts", []):
        selected = " selected" if account["employee_number"] == ctx.get("borrower") else ""
        options.append(
            f'<option value="{_e(account["employee_number"])}"{selected}>'
            f'{_e(account["name"])}（{_e(account["employee_number"])}）</option>'
        )
    select = f'<select id="id_borrower" name="borrower">{"".join(options)}</select>'
    date_input = f'<input id="id_lent_on" name="lent_on" type="date" value="{_e(ctx.get("lent_on"))}">'
    body = (
        "<h1>貸出の登録</h1>" + _notice(ctx)
        + f'<p class="lending-equipment">備品: {_e(equipment["equipment_number"])} {_e(equipment["name"])}</p>'
        + f'<form method="post" action="/equipment/{_e(equipment["id"])}/lend/">'
        + _field(ctx, "id_borrower", "借りる社員", select)
        + _field(ctx, "id_lent_on", "貸出日（YYYY-MM-DD）", date_input)
        + '<button type="submit">登録</button></form>'
        + '<p><a href="/">貸出状況に戻る</a></p>'
    )
    return body


def _account_list(ctx: Dict[str, Any]) -> str:
    reset = ctx.get("reset")
    rows = []
    for account in ctx.get("accounts", []):
        emp = _e(account["employee_number"])
        is_manager = account["role"] == "manager"
        role_text = "担当者" if is_manager else "社員"
        ops = (
            f'<form method="post" action="/accounts/{emp}/role/" '
            f"onsubmit=\"return confirm('{'担当者から外しますか？' if is_manager else '担当者にしますか？'}')\">"
            f'<input type="hidden" name="make_manager" value="{"0" if is_manager else "1"}">'
            f'<button type="submit" class="secondary">{"担当者から外す" if is_manager else "担当者にする"}</button></form>'
            f'<form method="get" action="/accounts/"><input type="hidden" name="reset" value="{emp}">'
            '<button type="submit" class="secondary">パスワード再設定</button></form>'
            f'<form method="post" action="/accounts/{emp}/delete/" '
            "onsubmit=\"return confirm('このアカウントを削除しますか？')\">"
            '<button type="submit" class="secondary">削除</button></form>'
        )
        if reset == account["employee_number"]:
            error = ctx.get("errors", {}).get("new_password")
            error_html = f'<span class="field-error">{_e(error)}</span>' if error else ""
            ops += (
                f'<form method="post" action="/accounts/{emp}/password/">'
                '<div class="field"><label>新しいパスワード（8 文字以上）</label>'
                '<input name="new_password" type="password" autocomplete="new-password">'
                f"{error_html}</div>"
                '<button type="submit">確定</button></form>'
            )
        rows.append(
            f'<tr data-employee-number="{emp}"><td>{emp}</td><td>{_e(account["name"])}</td>'
            f"<td>{role_text}</td><td>{ops}</td></tr>"
        )
    body = (
        "<h1>アカウントの一覧</h1>" + _notice(ctx)
        + '<div class="table-wrap"><table><thead><tr><th>社員番号</th><th>名前</th><th>役割</th><th>操作</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )
    return body


_BUILDERS = {
    "lending_status": ("貸出状況", _lending_status),
    "register_account": ("アカウント登録", _register_account),
    "login": ("ログイン", _login),
    "equipment_form": ("備品の登録・修正", _equipment_form),
    "lending_form": ("貸出の登録", _lending_form),
    "account_list": ("アカウントの一覧", _account_list),
}


def render_page(screen: str, ctx: Dict[str, Any]) -> str:
    """指定の画面の HTML 全体を返す。

    Args:
        screen: 画面の種類（lending_status、register_account、login、equipment_form、lending_form、account_list）。
        ctx: 画面の内容。user（ログイン者または None）、message、error、values、errors、rows など。

    Returns:
        HTML 文書の文字列。
    """
    title, builder = _BUILDERS[screen]
    main = builder(ctx)
    return (
        "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n"
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_e(title)} - 備品台帳</title>\n<style>{STYLE}</style>\n</head>\n<body>\n"
        f"{_header(ctx)}\n<main>{main}</main>\n</body>\n</html>\n"
    )
