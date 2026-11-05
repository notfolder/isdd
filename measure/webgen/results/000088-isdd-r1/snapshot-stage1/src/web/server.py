"""HTTP サーバーの起動と経路の振り分け。

環境変数 PORT（既定 8000）と DATA_DIR（既定はプロジェクトの data）を読み、
127.0.0.1 だけで待ち受ける。認証は無い。
"""

import http.server
import os
import re
import sqlite3
import sys
import traceback
import urllib.parse

from src.core.store import SpeciesStore
from src.core.validation import FORM_FIELDS, read_filter_conditions, validate_species_input
from src.web import views

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DEFAULT_PORT = 8000

SPECIES_PATH = re.compile(r"^/species/(\d+)$")
EDIT_PATH = re.compile(r"^/species/(\d+)/edit$")
DELETE_PATH = re.compile(r"^/species/(\d+)/delete$")


def _first_values(parsed_query):
    """parse_qs の結果（値のリスト）を、項目名から最初の値の辞書にする。"""
    return {key: values[0] for key, values in parsed_query.items()}


def _form_values(species):
    """保存された生物種を、フォームに表示する文字列の辞書にする。"""
    values = {}
    for field in FORM_FIELDS:
        value = species.get(field)
        if value is None:
            values[field] = ""
        elif field == "body_mass_kg":
            values[field] = f"{value:g}"
        else:
            values[field] = str(value)
    return values


def _blank_form_values():
    """登録画面の空の入力値。"""
    return {field: "" for field in FORM_FIELDS}


class SpeciesRequestHandler(http.server.BaseHTTPRequestHandler):
    """経路を振り分け、画面の生成と保存クラスの呼び出しを行う。

    store は main が設定したクラス属性（SpeciesStore）。
    """

    store = None
    server_version = "SpeciesBiologyDatabase"

    def do_GET(self):
        """画面（一覧・詳細・登録修正・スタイルシート）を返す。"""
        try:
            parsed = urllib.parse.urlsplit(self.path)
            path = parsed.path
            params = _first_values(urllib.parse.parse_qs(parsed.query, keep_blank_values=True))
            if path == "/":
                conditions = read_filter_conditions(params)
                rows = self.store.list_species(conditions)
                self._send_html(200, views.render_list_page(rows, conditions))
            elif path == "/species/new":
                self._send_form(200, "Add species", _blank_form_values(), [], "/species/new")
            elif path == "/static/style.css":
                self._send_file(os.path.join(STATIC_DIR, "style.css"), "text/css; charset=utf-8")
            elif SPECIES_PATH.match(path):
                species = self._find(SPECIES_PATH.match(path).group(1))
                if species is None:
                    self._send_not_found("Species not found")
                else:
                    self._send_html(200, views.render_detail_page(species))
            elif EDIT_PATH.match(path):
                species = self._find(EDIT_PATH.match(path).group(1))
                if species is None:
                    self._send_not_found("Species not found")
                else:
                    species_id = species["id"]
                    self._send_form(
                        200,
                        "Edit species",
                        _form_values(species),
                        [],
                        f"/species/{species_id}/edit",
                        f"/species/{species_id}",
                    )
            else:
                self._send_not_found("Page not found")
        except Exception:
            self._send_server_error()

    def do_POST(self):
        """登録・修正・削除を行い、結果の画面へ移動させる（Post/Redirect/Get）。"""
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length).decode("utf-8", errors="replace")
            form = _first_values(urllib.parse.parse_qs(body, keep_blank_values=True))
            path = urllib.parse.urlsplit(self.path).path
            if path == "/species/new":
                self._save(None, form)
            elif EDIT_PATH.match(path):
                species_id = int(EDIT_PATH.match(path).group(1))
                if self.store.get_species(species_id) is None:
                    self._send_not_found("Species not found")
                else:
                    self._save(species_id, form)
            elif DELETE_PATH.match(path):
                species_id = int(DELETE_PATH.match(path).group(1))
                if self.store.delete_species(species_id):
                    self._redirect("/")
                else:
                    self._send_not_found("Species not found")
            else:
                self._send_not_found("Page not found")
        except Exception:
            self._send_server_error()

    def _find(self, raw_id):
        """文字列の ID から生物種を返す。無ければ None。"""
        return self.store.get_species(int(raw_id))

    def _save(self, species_id, form):
        """登録（species_id が None）または修正を行う。入力エラーは同じ画面に返す。"""
        values = {field: form.get(field, "") for field in FORM_FIELDS}

        def is_name_taken(name):
            return self.store.is_scientific_name_taken(name, species_id)

        cleaned, errors = validate_species_input(values, is_name_taken)
        if not errors:
            try:
                if species_id is None:
                    new_id = self.store.create_species(cleaned)
                    self._redirect(f"/species/{new_id}")
                    return
                if self.store.update_species(species_id, cleaned):
                    self._redirect(f"/species/{species_id}")
                    return
                self._send_not_found("Species not found")
                return
            except sqlite3.IntegrityError:
                errors = ["Scientific name already exists."]

        if species_id is None:
            self._send_form(200, "Add species", values, errors, "/species/new", "/")
        else:
            self._send_form(
                200,
                "Edit species",
                values,
                errors,
                f"/species/{species_id}/edit",
                f"/species/{species_id}",
            )

    def _send_form(self, status, title, values, errors, action, cancel_href="/"):
        """登録・修正画面を返す。"""
        html = views.render_form_page(title, values, errors, action, cancel_href)
        self._send_html(status, html)

    def _send_not_found(self, message):
        """404 画面を返す。"""
        self._send_raw(404, views.render_not_found_page(message).encode("utf-8"), "text/html; charset=utf-8")

    def _send_server_error(self):
        """想定外の例外。原因は標準エラーに出し、利用者には簡素な応答を返す。"""
        traceback.print_exc(file=sys.stderr)
        body = b"Internal server error"
        self._send_raw(500, body, "text/plain; charset=utf-8")

    def _send_html(self, status, html):
        """組み立て済みの HTML 全体を返す。"""
        self._send_raw(status, html.encode("utf-8"), "text/html; charset=utf-8")

    def _send_file(self, path, content_type):
        """ファイルをそのまま返す。"""
        with open(path, "rb") as handle:
            self._send_raw(200, handle.read(), content_type)

    def _send_raw(self, status, body, content_type):
        """ステータスと本文を返す。"""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location):
        """303 で別の画面へ移動させる。"""
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()


def main():
    """サーバーを起動する。戻り値は終了コード。"""
    try:
        port = int(os.environ.get("PORT") or DEFAULT_PORT)
    except ValueError:
        print("PORT must be a whole number.", file=sys.stderr)
        return 1
    data_dir = os.environ.get("DATA_DIR") or os.path.join(PROJECT_ROOT, "data")
    store = SpeciesStore(os.path.join(data_dir, "species.db"))
    try:
        store.initialize()
    except (OSError, sqlite3.Error) as error:
        print(f"Cannot open the database in {data_dir}: {error}", file=sys.stderr)
        return 1

    handler = type("ConfiguredSpeciesRequestHandler", (SpeciesRequestHandler,), {"store": store})
    try:
        server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as error:
        print(f"Cannot listen on 127.0.0.1:{port}: {error}", file=sys.stderr)
        return 1
    print(f"Species Biology Database: http://127.0.0.1:{port}/ (data: {data_dir})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
