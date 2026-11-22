# 依頼: 総務システムに機能「トレーニングルームの予約」（slug: `gym`）を 1 つ足す

あなたの作業フォルダは `/Users/notfolder/isdd-measure-work/bigapp-gen/gym` 。この中だけを変更する。ほかの場所のファイルは変えない。git の操作はしない。
作業フォルダには総務システムの土台（`app/core/`、`tests/conftest.py`、`docs/`）が入っている。**土台のファイルは変更しない**（`app/core/`、`app/__init__.py`、`tests/conftest.py`、`tests/test_core.py`、`docs/`、`requirements.txt`、`run.sh`、`setup.sh`、`wsgi.py`）。
まず `docs/module-guide.md`、`docs/soumu-rules.md`、`app/__init__.py`、`app/core/` の全ファイル、`tests/conftest.py` を読むこと。

作るもの:
- `app/modules/gym/`（パッケージ。テンプレートは `app/modules/gym/templates/gym/`）
- `tests/test_gym.py`（下の「きまり」を 1 つずつ確かめるテストを 12 本以上。境界の値も確かめる）

テストの実行: 作業フォルダで `/Users/notfolder/Documents/isdd/measure/bigapp/seed/.venv/bin/python -m pytest -q` を実行し、`tests/test_core.py` と `tests/test_gym.py` が全部通ること。

## 画面と URL（この形を守る。採点は別のテストがこの URL と入力欄の名前で行う）

共通:
- データを変える操作（POST）は総務の担当者（`staff_required`）だけができる。
- 受け付けないときは HTTP 400 を返し、理由を `<p class="error">…</p>` に出す。データは変えない。
- 成功したら `/gym/` へリダイレクト（302）する。
- データを変える操作は `app.core.audit.record("gym", <操作名>, <対象>)` で 1 行残す（操作名は下の表のとおり）。
- 日付の判定は必ず `app.core.clock.today()` を使う。
- 社員は `employees` テーブルから読む。対象にできるのは在籍している社員だけ（退職した社員と、存在しない社員番号は 400）。

### 予約の機能

きまり: 予約は 30 分の単位（開始も終了も 30 分の倍数の時刻）。9:00 から 18:00 の間で、開始 < 終了。同じ部屋の同じ日に、時間が重なる予約は取れない（前の予約の終了と次の開始が同じ時刻なのは重なりではない）。1 人が同じ日に取れる予約は、この機能で 1 件まで。過去の日付は予約できない（今日はよい）。部屋の番号（code）は重複不可。

| URL | 入力欄 | 中身 | 操作名 |
|---|---|---|---|
| `GET /gym/` | `date`（任意。その日の予約だけ出す） | 予約の一覧の画面と、部屋の登録・予約・取消のフォーム | — |
| `POST /gym/rooms/new` | `code`、`name` | 部屋を登録する | `room_create` |
| `POST /gym/rooms/edit` | `code`、`name` | 名前を直す | `room_update` |
| `POST /gym/book` | `room_code`、`employee_no`、`date`（`YYYY-MM-DD`）、`start`、`end`（`HH:MM`） | 予約する | `book` |
| `POST /gym/cancel` | `booking_id` | 予約を取り消す | `cancel` |
| `GET /gym/day` | `date` | その日の部屋ごとの予約の表の画面 | — |
| `GET /gym/status.json` | — | 下の形の JSON（ログインしていれば誰でも見られる） | — |

`status.json` の形: `{"bookings": [{"id": 1, "room": "R-1", "employee": "100001", "date": "2026-06-15", "start": "09:00", "end": "10:00"}]}`（取り消した予約は入れない。id の昇順）。


## 書き方の指定（必ず守る。この機能はこの書き方で作る）

- ファイルの分け方: `web.py`（画面）と `domain.py`（判定。例外を投げて画面側で受ける）に分ける
- 時間の単位は定数にせず、判定の中に数字で直接書く
- 在籍の判定は「退職していない」で書く（`status != 'retired'`）
- コメントと docstring は日本語で、普通の業務システムとして自然な量にする。
- ほかの機能と共通の関数を `app/core/` に足さない。判定はこの機能の中に書く。
- 画面は実務で使える程度に作る（一覧の表、登録や操作のフォーム、エラーの表示）。CSS は `base.html` のものだけでよい。

## 終わったら

日本語で 5 行以内で報告する: 作ったファイルと行数、テストの本数と結果、書き方の指定をどう実装したか（延滞・在籍・金額・時間の単位の判定を書いた場所の `ファイル:関数名`）。
