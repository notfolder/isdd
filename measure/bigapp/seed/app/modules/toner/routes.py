"""トナーの申請の画面。"""

from flask import abort, jsonify, redirect, render_template, request

from app.core.auth import current_user, login_required, staff_required
from app.modules.toner import bp, repo, service
from app.modules.toner.service import RejectedError


def _page(state="", error=None, status=200):
    rows = repo.list_requests(state or None)
    return render_template("toner/index.html", rows=rows, state=state, error=error, states=service.STATES), status


@bp.route("/")
@login_required
def index():
    state = request.args.get("state", "").strip()
    try:
        service.check_state(state)
    except RejectedError as e:
        return _page("", str(e), 400)
    return _page(state)


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    try:
        service.apply(form.get("employee_no"), form.get("quantity"), form.get("unit_price"))
    except RejectedError as e:
        return _page(error=str(e), status=400)
    return redirect("/toner/")


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    try:
        service.approve(request.form.get("request_id"), current_user())
    except RejectedError as e:
        return _page(error=str(e), status=400)
    return redirect("/toner/")


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    try:
        service.reject(request.form.get("request_id"))
    except RejectedError as e:
        return _page(error=str(e), status=400)
    return redirect("/toner/")


@bp.route("/detail")
@login_required
def detail():
    text = request.args.get("request_id", "").strip()
    row = repo.get_request(int(text)) if text.isascii() and text.isdigit() else None
    if row is None:
        abort(404)
    return render_template("toner/detail.html", r=row)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify({"requests": [
        {
            "id": r["id"],
            "employee": r["employee_no"],
            "quantity": r["quantity"],
            "unit_price": r["unit_price"],
            "amount_incl_tax": r["amount_incl_tax"],
            "state": r["state"],
        }
        for r in repo.list_requests()
    ]})
