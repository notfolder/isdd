"""ソフトウェア購入申請の処理。数量・単価・税込み金額・状態の判定をここに置く。"""

from dataclasses import dataclass

# 対象にできない社員の状態（退職した社員は申請の対象にしない）
EXCLUDED_STATUSES = {"retired"}

MIN_QUANTITY, MAX_QUANTITY = 1, 10
MIN_UNIT_PRICE, MAX_UNIT_PRICE = 1, 100000
TAX_PERCENT = 10

PENDING, APPROVED, REJECTED = "pending", "approved", "rejected"
STATE_LABELS = {PENDING: "申請中", APPROVED: "承認", REJECTED: "却下"}


class RequestError(Exception):
    """申請を受け付けない理由。画面にそのまま出す。"""


@dataclass
class PurchaseRequest:
    id: int
    employee_no: str
    employee_name: str
    quantity: int
    unit_price: int
    state: str

    @property
    def subtotal(self) -> int:
        return self.quantity * self.unit_price

    @property
    def total(self) -> int:
        return total(self.quantity, self.unit_price)

    @property
    def state_label(self) -> str:
        return STATE_LABELS.get(self.state, self.state)


def total(quantity: int, unit_price: int) -> int:
    """税込みの金額。税額を先に出して足す（1 円未満は切り捨て）。"""
    subtotal = quantity * unit_price
    tax = subtotal * TAX_PERCENT // 100
    return subtotal + tax


def parse_int(text, label, low, high) -> int:
    """整数の入力を読み、範囲外なら RequestError。"""
    text = (text or "").strip()
    if not (text.isascii() and text.isdigit()):
        raise RequestError(f"{label}は整数で入力してください")
    value = int(text)
    if not low <= value <= high:
        raise RequestError(f"{label}は {low} 以上 {high} 以下で入力してください")
    return value


def find_active_employee(conn, employee_no):
    """在籍している社員の行。退職者・存在しない番号は RequestError。"""
    row = conn.execute("SELECT * FROM employees WHERE employee_no = ?", (employee_no,)).fetchone()
    if row is None:
        raise RequestError("社員が見つかりません")
    if row["status"] in EXCLUDED_STATUSES:
        raise RequestError("退職した社員は申請の対象にできません")
    return row


def _to_request(row) -> PurchaseRequest:
    return PurchaseRequest(row["id"], row["employee_no"], row["name"], row["quantity"], row["unit_price"], row["state"])


_SELECT = """SELECT r.id, r.employee_no, e.name, r.quantity, r.unit_price, r.state
FROM software_requests r JOIN employees e ON e.employee_no = r.employee_no"""


def list_requests(conn, state=None):
    """申請の一覧（id の昇順）。state を指定するとその状態だけ。"""
    if state:
        rows = conn.execute(_SELECT + " WHERE r.state = ? ORDER BY r.id", (state,)).fetchall()
    else:
        rows = conn.execute(_SELECT + " ORDER BY r.id").fetchall()
    return [_to_request(r) for r in rows]


def get_request(conn, request_id):
    """申請 1 件。無ければ None。"""
    text = str(request_id or "").strip()
    if not (text.isascii() and text.isdigit()):
        return None
    row = conn.execute(_SELECT + " WHERE r.id = ?", (int(text),)).fetchone()
    return _to_request(row) if row else None


def apply(conn, employee_no, quantity_text, unit_price_text) -> int:
    """申請を登録して id を返す。"""
    employee = find_active_employee(conn, (employee_no or "").strip())
    quantity = parse_int(quantity_text, "数量", MIN_QUANTITY, MAX_QUANTITY)
    unit_price = parse_int(unit_price_text, "単価", MIN_UNIT_PRICE, MAX_UNIT_PRICE)
    cur = conn.execute(
        "INSERT INTO software_requests (employee_no, quantity, unit_price, state) VALUES (?, ?, ?, ?)",
        (employee["employee_no"], quantity, unit_price, PENDING),
    )
    return cur.lastrowid


def _pending_request(conn, request_id) -> PurchaseRequest:
    req = get_request(conn, request_id)
    if req is None:
        raise RequestError("申請が見つかりません")
    if req.state != PENDING:
        raise RequestError("申請中の申請だけが対象です")
    return req


def approve(conn, request_id, approver_no) -> PurchaseRequest:
    """承認する。申請中のものだけ。申請した本人は承認できない。"""
    req = _pending_request(conn, request_id)
    if req.employee_no == approver_no:
        raise RequestError("自分の申請は承認できません")
    conn.execute("UPDATE software_requests SET state = ? WHERE id = ?", (APPROVED, req.id))
    return req


def reject(conn, request_id) -> PurchaseRequest:
    """却下する。申請中のものだけ（本人の申請でも却下できる）。"""
    req = _pending_request(conn, request_id)
    conn.execute("UPDATE software_requests SET state = ? WHERE id = ?", (REJECTED, req.id))
    return req
