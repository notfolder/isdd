# Wheel of Fortune

Spin a wheel to win a prize, browse the prize list, and look up your own winning records. The site is in English and needs no login.

## 起動方法

```bash
bash setup.sh          # 一度だけ。Python 3.9 以上があることを確かめる（外部パッケージは無い）
PORT=8000 bash run.sh  # 起動。ブラウザで http://127.0.0.1:8000/ を開く
```

- `PORT` は待ち受けポート（既定 8000）。
- `DATA_DIR` は SQLite ファイル（`wheel.sqlite3`）の保存先（既定はプロジェクト直下の `data`）。無ければ作られる。
- 初回起動時に、景品 6 件と、名前 `Sample Player` の当選記録 3 件が入る。
- 停止は Ctrl+C。

## 画面

- Spin the Wheel（`/`）: 名前（必須）を入れて Spin を押す。名前の入力欄は Spin ボタンの隣にある。名前が空のままだと回らず、案内が出る。当選すると、景品名、名前、当選日時を表示する。
- Prize List（`/prizes`）: 景品の一覧。
- My Winnings（`/my-winnings`）: 名前で当選記録を絞り込む（大文字小文字は区別しない）。表は Player（名前）、Prize（景品名）、Date won（当選日時）の列。

## テスト

```bash
python3 -m unittest discover -s tests -t . -v                      # 単体・結合テスト
python3 scripts/isdd/unittest_junit.py -s e2e -t . -o e2e/results/e2e.xml   # E2E（実サーバーに HTTP で要求）
bash scripts/isdd/check.sh --strict                                # 対応表・依存・受け入れ判定
```

設計書は `docs/`（要件定義書、詳細設計書、対応表）にある。
