# Reward Wheel（報酬ルーレット）

ブラウザでルーレットを回して報酬を抽選し、報酬の一覧と自分の当選履歴を確認できる Web サイトです。
画面の文言は英語です。Python 3 の標準ライブラリと SQLite だけで動き、追加のインストールは要りません。

## 起動方法

1. 準備（最初に 1 回）

   ```bash
   bash setup.sh
   ```

2. 起動（ポートは任意の番号。省略すると 8000）

   ```bash
   PORT=8000 bash run.sh
   ```

3. ブラウザで `http://127.0.0.1:8000` を開く。停止は起動したターミナルで Ctrl+C を押す。

環境変数:

| 名前 | 用途 | 既定値 |
|---|---|---|
| `PORT` | 待ち受けポート（1〜65535） | 8000 |
| `DATA_DIR` | SQLite ファイル（`wheel.db`）の保存先。無ければ作る | リポジトリ直下の `data` |

初回起動時は報酬 7 件と、サンプルの当選記録（利用者名 `Sample Player`、2 件）が入ります。

## 画面

- Spin Wheel（`/`）: 抽選ボタン（Spin）の左隣の利用者名欄（必須）に名前を入れて Spin を押すと、ルーレットが回り結果が表示されます。名前が空欄や空白だけ、または 21 文字以上のときは回らず、入力欄の下に規則の文言が出ます。当たった報酬は当選履歴に残ります。「Try again」は当選記録に残りません。
- Reward List（`/rewards`）: 報酬の名前、説明、当選確率（%）を表示します。
- My Winning Records（`/records`）: 利用者名を入力して Show を押すと、その名前の当選履歴を新しい順に表示します。各行に、利用者名（Player）、報酬名（Reward）、当選日時（Won at）を表示します。

利用者名は 1〜20 文字（前後の空白は除く）です。ログインはありません。

## テスト

単体・結合テスト:

```bash
python3 -m unittest discover -s tests/unit -p "test_*.py"
```

E2E テスト（実サーバーを一時 DATA_DIR で起動して確かめる。結果は `e2e/results/e2e.xml`）:

```bash
python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml
```

## 構成

- `src/server.py`: 起動の入口
- `src/web/`: HTTP の振り分け（`router.py`）、API（`api.py`）、画面（`static/`）
- `src/service/`: 利用者名の検証と抽選（`validation.py`、`wheel.py`）
- `src/store/`: SQLite の接続、リポジトリ、初期データ（`database.py`、`repositories.py`、`seed.py`）
- 設計: `docs/requirements.md`（要件定義書）、`docs/detail_design.md`（詳細設計書）、`docs/trace_map.md`（設計 ID と コードの対応）
