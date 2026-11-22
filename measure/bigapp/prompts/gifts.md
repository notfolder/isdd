# 依頼: 総務システムに機能「贈答品の申請」（slug: `gifts`）を 1 つ足す

あなたの作業フォルダは `/Users/notfolder/isdd-measure-work/bigapp-gen/gifts` 。この中だけを変更する。ほかの場所のファイルは変えない。git の操作はしない。
作業フォルダには総務システムの土台（`app/core/`、`tests/conftest.py`、`docs/`）が入っている。**土台のファイルは変更しない**（`app/core/`、`app/__init__.py`、`tests/conftest.py`、`tests/test_core.py`、`docs/`、`requirements.txt`、`run.sh`、`setup.sh`、`wsgi.py`）。
まず `docs/module-guide.md`、`docs/soumu-rules.md`、`app/__init__.py`、`app/core/` の全ファイル、`tests/conftest.py` を読むこと。

作るもの:
- `app/modules/gifts/`（パッケージ。テンプレートは `app/modules/gifts/templates/gifts/`）
- `tests/test_gifts.py`（下の「きまり」を 1 つずつ確かめるテストを 12 本以上。境界の値も確かめる）

テストの実行: 作業フォルダで `/Users/notfolder/Documents/isdd/measure/bigapp/seed/.venv/bin/python -m pytest -q` を実行し、`tests/test_core.py` と `tests/test_gifts.py` が全部通ること。

## 画面と URL（この形を守る。採点は別のテストがこの URL と入力欄の名前で行う）

共通:
- データを変える操作（POST）は総務の担当者（`staff_required`）だけができる。
- 受け付けないときは HTTP 400 を返し、理由を `<p class="error">…</p>` に出す。データは変えない。
- 成功したら `/gifts/` へリダイレクト（302）する。
- データを変える操作は `app.core.audit.record("gifts", <操作名>, <対象>)` で 1 行残す（操作名は下の表のとおり）。
- 日付の判定は必ず `app.core.clock.today()` を使う。
- 社員は `employees` テーブルから読む。対象にできるのは在籍している社員だけ（退職した社員と、存在しない社員番号は 400）。

### 申請の機能

きまり: 申請は数量（1 以上 30 以下の整数）と税抜きの単価（1 以上 100000 以下の整数、円）を記録する。税込みの金額は 数量 × 単価 に消費税 10% を足し、1 円未満を切り捨てる。申請の状態は `pending`（申請中）→ `approved`（承認）か `rejected`（却下）。承認と却下は申請中のものにだけできる。承認する人（ログインしている担当者）が申請した本人のときは、承認できない（却下はできる）。

| URL | 入力欄 | 中身 | 操作名 |
|---|---|---|---|
| `GET /gifts/` | `state`（任意。その状態の申請だけ出す） | 申請の一覧の画面と、申請・承認・却下のフォーム | — |
| `POST /gifts/apply` | `employee_no`（申請する社員）、`quantity`、`unit_price` | 申請する | `apply` |
| `POST /gifts/approve` | `request_id` | 承認する | `approve` |
| `POST /gifts/reject` | `request_id` | 却下する | `reject` |
| `GET /gifts/detail` | `request_id` | 申請 1 件の画面（数量、単価、税抜き、税込み、状態、申請した社員） | — |
| `GET /gifts/status.json` | — | 下の形の JSON（ログインしていれば誰でも見られる） | — |

`status.json` の形: `{"requests": [{"id": 1, "employee": "100001", "quantity": 3, "unit_price": 333, "amount_incl_tax": 1098, "state": "pending"|"approved"|"rejected"}]}`（id の昇順）。


## 書き方の指定（必ず守る。この機能はこの書き方で作る）

- ファイルの分け方: すべてを `__init__.py` の 1 ファイルに書く（関数だけ）
- 税込みの計算は SQL の INSERT の中で `CAST(? * ? * 110 / 100 AS INTEGER)` として行う。Python 側では計算しない
- 在籍の判定は「退職していない」で書く（`status != 'retired'`）
- コメントと docstring は日本語で、普通の業務システムとして自然な量にする。
- ほかの機能と共通の関数を `app/core/` に足さない。判定はこの機能の中に書く。
- 画面は実務で使える程度に作る（一覧の表、登録や操作のフォーム、エラーの表示）。CSS は `base.html` のものだけでよい。

## 終わったら

日本語で 5 行以内で報告する: 作ったファイルと行数、テストの本数と結果、書き方の指定をどう実装したか（延滞・在籍・金額・時間の単位の判定を書いた場所の `ファイル:関数名`）。
