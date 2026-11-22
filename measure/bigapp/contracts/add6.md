
## 依頼 6 で足す接点（期限を過ぎた貸出の件数）

- 画面の URL は `/overdue-summary/`、JSON の URL は `/overdue-summary.json`。どちらも総務の担当者だけが見られる。
- JSON の形: `{"summary": {"<貸出の機能の slug>": <期限を過ぎた扱いの貸出の件数>, …}}`。貸出の機能をすべて入れる（0 件の機能も入れる）。
