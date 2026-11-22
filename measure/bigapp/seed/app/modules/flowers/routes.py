"""生花の申請の画面。"""

from flask import abort, jsonify, redirect, render_template, request, url_for

from app.core.auth import login_required, staff_required
from app.modules.flowers import bp, repo, service


def _list_page(error=None, status=200):
    state = request.values.get("state", "")
    return (
        render_template(
            "flowers/index.html",
            requests=service.list_requests(state),
            states=repo.STATES,
            state=state,
            error=error,
        ),
        status,
    )


def _run(action, *args):
    """操作を実行する。受け付けなければ 400 で理由を出し、成功すれば一覧へ戻す。"""
    try:
        action(*args)
    except service.RejectedInput as e:
        return _list_page(error=str(e), status=400)
    return redirect(url_for("flowers.index"))


@bp.route("/")
@login_required
def index():
    return _list_page()


@bp.route("/apply", methods=["POST"])
@staff_required
def apply():
    form = request.form
    return _run(service.apply, form.get("employee_no"), form.get("quantity"), form.get("unit_price"))


@bp.route("/approve", methods=["POST"])
@staff_required
def approve():
    return _run(service.approve, request.form.get("request_id"))


@bp.route("/reject", methods=["POST"])
@staff_required
def reject():
    return _run(service.reject, request.form.get("request_id"))


@bp.route("/detail")
@login_required
def detail():
    found = service.get_request(request.args.get("request_id"))
    if found is None:
        abort(404)
    return render_template("flowers/detail.html", r=found)


@bp.route("/status.json")
@login_required
def status_json():
    return jsonify(
        {
            "requests": [
                {
                    "id": r.id,
                    "employee": r.employee_no,
                    "quantity": r.quantity,
                    "unit_price": r.unit_price,
                    "amount_incl_tax": r.amount_incl_tax,
                    "state": r.state,
                }
                for r in service.list_requests("")
            ]
        }
    )
