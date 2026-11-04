"""経路と画面の処理。画面の処理は SQLite を直接扱わず、リポジトリを通す。"""

from __future__ import annotations

import sqlite3
from typing import Any

from flask import Blueprint, current_app, g, redirect, render_template, request, url_for, abort

from app.constants import CONSERVATION_STATUSES, DIETS, HABITATS, KINGDOMS
from app.repository import SpeciesRepository
from app.sorting import DEFAULT_SORT_ORDER, SORT_ORDERS, sort_species_rows
from app.validation import (
    DUPLICATE_SCIENTIFIC_NAME_MESSAGE,
    FIELD_NAMES,
    SpeciesForm,
    parse_species_form,
    validate_species_form,
)

bp = Blueprint("species", __name__)

# 一覧の絞り込みで受け付ける値（列名と選択肢）
FILTER_OPTIONS: dict[str, tuple[str, ...]] = {
    "kingdom": KINGDOMS,
    "habitat": HABITATS,
    "diet": DIETS,
    "conservation_status": tuple(CONSERVATION_STATUSES),
}


def read_sort_order() -> str:
    """クエリの sort を読む。未指定や SORT_ORDERS に無い値は既定の名前の昇順にする。"""
    value = request.args.get("sort", "")
    return value if value in SORT_ORDERS else DEFAULT_SORT_ORDER


def _repository() -> SpeciesRepository:
    """リクエストごとに 1 つのリポジトリを返す。接続の開き方は create_app が OPEN_REPOSITORY として渡す。"""
    if "repository" not in g:
        g.repository = current_app.config["OPEN_REPOSITORY"]()
    return g.repository


@bp.teardown_request
def _close_connection(_error: BaseException | None) -> None:
    repository = g.pop("repository", None)
    if repository is not None:
        repository.close()


def _choices() -> dict[str, Any]:
    """選択欄に出す値と表示名。"""
    return {
        "kingdoms": KINGDOMS,
        "habitats": HABITATS,
        "diets": DIETS,
        "statuses": CONSERVATION_STATUSES,
    }


def _render_form(form: SpeciesForm, title: str, action: str, status: int = 200) -> tuple[str, int]:
    """登録・修正の入力画面を描画する。"""
    html = render_template("species_form.html", form=form, title=title, action=action, **_choices())
    return html, status


@bp.errorhandler(404)
def _not_found(_error: Any) -> tuple[str, int]:
    """存在しない種の画面（見出しは「Species not found.」）。"""
    html = render_template("species_detail.html", species=None, saved=False, **_choices())
    return html, 404


@bp.get("/")
def list_species() -> str:
    """一覧・検索・絞り込み画面。"""
    keyword = request.args.get("q", "").strip()
    criteria: dict[str, str] = {}
    selected: dict[str, str] = {}
    for name, allowed in FILTER_OPTIONS.items():
        value = request.args.get(name, "")
        selected[name] = value if value in allowed else ""
        if selected[name]:
            criteria[name] = selected[name]
    sort = read_sort_order()
    rows = sort_species_rows(_repository().search(keyword, criteria), sort)
    return render_template(
        "species_list.html",
        rows=rows,
        keyword=keyword,
        selected=selected,
        sort=sort,
        sort_options=SORT_ORDERS,
        notice=request.args.get("notice", ""),
        **_choices(),
    )


@bp.get("/species/<int:species_id>")
def show_species_detail(species_id: int) -> str:
    """詳細画面。"""
    row = _repository().get(species_id)
    if row is None:
        abort(404)
    return render_template(
        "species_detail.html", species=row, saved=request.args.get("saved") == "1", **_choices()
    )


@bp.get("/species/new")
def show_create_form() -> tuple[str, int]:
    """登録画面の表示。"""
    return _render_form(SpeciesForm(), "Add species", url_for("species.submit_create_form"))


@bp.post("/species/new")
def submit_create_form() -> Any:
    """登録の保存。"""
    repository = _repository()
    form = parse_species_form(request.form)
    validate_species_form(form, repository)
    if not form.errors:
        try:
            new_id = repository.insert(form.field_values())
        except sqlite3.IntegrityError:
            form.errors["scientific_name"] = DUPLICATE_SCIENTIFIC_NAME_MESSAGE
        else:
            return redirect(url_for("species.show_species_detail", species_id=new_id, saved=1))
    return _render_form(form, "Add species", url_for("species.submit_create_form"), 200)


@bp.get("/species/<int:species_id>/edit")
def show_edit_form(species_id: int) -> Any:
    """修正画面の表示。"""
    row = _repository().get(species_id)
    if row is None:
        abort(404)
    values = {name: "" if row[name] is None else str(row[name]) for name in FIELD_NAMES}
    return _render_form(
        SpeciesForm(**values), "Edit species", url_for("species.submit_edit_form", species_id=species_id)
    )


@bp.post("/species/<int:species_id>/edit")
def submit_edit_form(species_id: int) -> Any:
    """修正の保存。"""
    repository = _repository()
    if repository.get(species_id) is None:
        abort(404)
    form = parse_species_form(request.form)
    validate_species_form(form, repository, exclude_id=species_id)
    action = url_for("species.submit_edit_form", species_id=species_id)
    if not form.errors:
        try:
            repository.update(species_id, form.field_values())
        except sqlite3.IntegrityError:
            form.errors["scientific_name"] = DUPLICATE_SCIENTIFIC_NAME_MESSAGE
        else:
            return redirect(url_for("species.show_species_detail", species_id=species_id, saved=1))
    return _render_form(form, "Edit species", action, 200)


@bp.get("/species/<int:species_id>/delete")
def show_delete_confirm(species_id: int) -> str:
    """削除確認画面。"""
    row = _repository().get(species_id)
    if row is None:
        abort(404)
    return render_template("species_delete_confirm.html", species=row)


@bp.post("/species/<int:species_id>/delete")
def submit_delete(species_id: int) -> Any:
    """削除の実行。"""
    repository = _repository()
    if repository.get(species_id) is None:
        abort(404)
    repository.delete(species_id)
    return redirect(url_for("species.list_species", notice="deleted"))
