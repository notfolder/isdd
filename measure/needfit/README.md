# 題材 needfit: 課題とずれた依頼と、作りすぎ

`measure/results/EVALUATION-REVIEW.md` の評価 A1（課題とずれた依頼を直せるか）と A2（作りすぎを防げるか）を、1 つの題材で測る。

## 題材の作り

- 依頼（`stages/stage1.md`）: Excel の在庫台帳をアプリにする。依頼者は「在庫数が 10 以下の品目に要発注の印を付ける」と頼む。業務の問題は書いていない。「ついでに付けてほしいこと」が 4 つある。
- 依頼者だけが知っていること（`ledger.md`）: 先月ネジが切れてラインが止まった。品目ごとに使う速さと納期が違い、10 個では間に合わない品目と、印が付きっぱなしになる品目がある。品目ごとに数を入力するのは無理で、台帳の列から計算してほしい。依頼者は、理由や困りごとを聞かれて初めて話す。「ついで」の 4 つのうち 3 つは無くても困らず、1 つは無いと困る。
- 契約（`contracts/stage1.md`）: 起動方法と、採点が使う JSON の API だけ。画面、技術、構成は自由。印は一覧の `reorder` で見る（依頼どおりの実装でも、正しい実装でも同じ接点）。「ついで」の機能は、作らないと決めたら 404 でよい。
- 採点（`score.py`、`hidden/`）: 標準ライブラリだけで API を呼ぶ。

## 台帳の事実と、どのテストで確かめるか

| 事実 | どうすれば出るか | 実装に入ったかを確かめるテスト |
|---|---|---|
| F1 ネジが切れてラインが止まった | 目的や困りごとを聞く | （F2 の入口。単独のテストは無い） |
| F2 品目ごとに使う速さと納期が違う。台帳の列から計算する | 「10」の根拠や、全品目同じでよいかを聞く | `test_need_scenario_line_does_not_stop`（主な指標）、`test_need_fast_item_is_flagged_above_10`、`test_need_slow_item_is_not_flagged_at_8`、`test_need_flag_follows_issue_and_receive` |
| F3 基準は 1 日の使用量 ×（納期日数 ＋ 3）。同じ数でも付ける | 計算のしかたや余裕を聞く。式の案を確認する | `test_need_margin_of_3_days`、`test_need_boundary` |
| F4 在庫数 ＋ 発注中の数で判定する | 注文したあとの印の扱いを聞く | `test_need_on_order_is_counted` |
| F5 使用量が 0 の品目には付けない | 使っていない品目の扱いを聞く | `test_need_unused_item_is_not_flagged` |
| F6〜F8 月別の金額、CSV、写真は無くても困らない | 無いと何が困るかを聞く | `test_probe_unneeded_features`（作ったかの記録。合否ではない） |
| F9 出庫の履歴と使った人は無いと困る | 同上 | `test_keep_issue_history_with_person` |

`test_base_*`（10 件）は依頼文に書いてある機能で、どのやり方でも通るはずのもの。

## 採点結果の読み方

| 項目 | 意味 |
|---|---|
| `scenario` | 主な指標。業務のシナリオ（ネジは切れる前に印が付き、替刃は足りているあいだ付かない）が通ったか |
| `categories.need` | 業務の問題に関わるテスト 8 件の合格数 |
| `categories.base` | 基本の機能 10 件の合格数 |
| `categories.keep` | 無いと困る「ついで」の機能（1 件）。0 なら削りすぎ |
| `unneeded.count` | 無くても困らない機能を作った数（0〜3） |
| `overbuild` | 行数や公開関数の数。参考値 |

## テストを確かめた結果（2026-11-23）

`reference/app.py` を `MODE` を替えて採点した。

| 実装 | 基本 10 | 業務 8 | シナリオ | 無いと困る機能 | 不要な機能 |
|---|---|---|---|---|---|
| 正しい実装（correct） | 10 | 8 | 通る | 1 | 0 |
| 依頼どおりの実装（literal） | 10 | 0 | 落ちる | 1 | 3 |
| 作りすぎた実装（overbuilt） | 10 | 8 | 通る | 1 | 3 |
| 削りすぎた実装（cutall） | 10 | 8 | 通る | 0 | 0 |

## 回し方

```
python3 measure/run.py --arm control --run 1 --model claude-opus-5-5 --work ~/isdd-measure-work --task needfit --stages 1 \
  --responder measure/needfit/ledger.md --max-rounds 20 --path-prefix /tmp/isdd-measure/bin        # バイブコーディング
…同じ引数に --ask-first                                                                           # 一文つき
…--arm isdd                                                                                       # isdd
```

本番の規則は `PROTOCOL.md`。
