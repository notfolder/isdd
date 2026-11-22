"""書籍の購入の申請（総務規程 第 5 条・第 6 条・第 7 条）。"""

from flask import Blueprint

TITLE = "書籍の購入の申請"

SCHEMA = """
CREATE TABLE IF NOT EXISTS book_orders_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_no TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price INTEGER NOT NULL,
    amount_incl_tax INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'pending',
    created_on TEXT NOT NULL
);
"""

bp = Blueprint("book_orders", __name__, url_prefix="/book_orders", template_folder="templates")

from app.modules.book_orders import handlers  # noqa: E402,F401  ルートの登録
