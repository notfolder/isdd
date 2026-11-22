"""書籍の貸出。総務が書籍を登録し、社員への貸出と返却を記録する。"""

from flask import Blueprint

TITLE = "書籍の貸出"

SCHEMA = """
CREATE TABLE IF NOT EXISTS books_items (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS books_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    lent_on TEXT NOT NULL,
    due_on TEXT NOT NULL,
    returned_on TEXT
);
"""

bp = Blueprint("books", __name__, url_prefix="/books", template_folder="templates")

from app.modules.books import views  # noqa: E402,F401  ルートの登録のために読み込む
