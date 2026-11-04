# 備品台帳と貸出状況の閲覧

会社の備品の台帳と貸出の記録を 1 つにまとめ、社員が「どの備品を誰が借りているか」を自分で確かめられるようにする Web アプリです。Python 3.12 と SQLite で動き、外部のサービスは使いません。

## 起動方法

1. 準備（1 回だけ）: `bash setup.sh`
2. 起動: `bash run.sh`
3. ブラウザで `http://<サーバーのアドレス>:8000/` を開く

環境変数（省略時の値）:

| 名前 | 用途 | 既定値 |
|---|---|---|
| `PORT` | 待ち受けポート | 8000 |
| `DATA_DIR` | データ（SQLite のファイル、秘密鍵）の置き場所。無ければ作る | `data` |
| `SESSION_IDLE_TIMEOUT_SECONDS` | 操作しないまま自動でログアウトするまでの秒数 | 1800 |

例: `PORT=8785 DATA_DIR=/var/lib/ledger bash run.sh`

## 導入の手順

- 初期ユーザーは無い。社員に URL を知らせる前に、担当者が最初のアカウントを登録する。最初に登録したアカウントが担当者になり、2 件目以降は社員になる。
- 担当者は「アカウントの一覧」から、社員を担当者にしたり、担当者から外したりできる。担当者が 1 人もいなくなる操作はできない。
- 備品は画面から 1 件ずつ入力する（既存の Excel からの取り込み機能は無い）。

## 使い方

- 貸出状況（トップ）は、ログインしなくても見られる。
- ログイン中の担当者は、行の「修正」「削除」「貸出」「返却」で備品を操作する。
- 削除、返却、担当者の付け外し、アカウントの削除は、確認ダイアログで「はい」を選んだときだけ行われる。

## テスト

- 単体テスト: `.venv/bin/python -m pytest tests`
- E2E テスト（Playwright の Chromium を使う）: 初回だけ `.venv/bin/python -m pip install -r e2e/requirements-e2e.txt` と `.venv/bin/python -m playwright install chromium` を実行し、`.venv/bin/python -m pytest e2e --junitxml=e2e/results/e2e.xml` で実行する。結果は `e2e/results/`（git 管理外）に出る。
