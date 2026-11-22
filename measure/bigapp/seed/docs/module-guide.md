# 機能の足し方

機能は `app/modules/<slug>/` のパッケージとして足す。`app/__init__.py` が起動時に自動で読み込む。

パッケージの `__init__.py` が次の 3 つを公開する。

- `bp`: Flask の Blueprint。名前は slug、`url_prefix` は `/<slug>`。
- `TITLE`: 画面に出す機能の名前。
- `SCHEMA`: この機能のテーブルを作る SQL（`CREATE TABLE IF NOT EXISTS`）。テーブル名は slug で始める。

共通の部品:

- `app.core.db.get_db()`: SQLite の接続（`sqlite3.Row`）。
- `app.core.auth.current_user()`、`login_required`、`staff_required`。
- `app.core.clock.today()`: 今日の日付。日付の判定には必ずこれを使う（`datetime.date.today()` を直接使わない）。
- `app.core.audit.record(module, action, target)`: 操作の記録。commit は呼び出し側で行う。
- 社員は `employees` テーブル（`employee_no`、`name`、`dept`、`role`、`status`）。

画面は `base.html` を継承する。機能のテンプレートは `app/modules/<slug>/templates/<slug>/` に置く。

どの機能も `GET /<slug>/status.json` で、今の状態を JSON で返す（ほかのシステムからの確認用）。

入力を受け付けないときは、HTTP 400 で、理由を `class="error"` の要素に出す。データは変えない。成功したら `/<slug>/` へリダイレクトする。

テストは `tests/test_<slug>.py` に置く。部品は `tests/conftest.py`（`admin`、`make_employee`、`set_today`）。
