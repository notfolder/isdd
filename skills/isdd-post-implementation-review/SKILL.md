---
name: isdd-post-implementation-review
description: >
  実装の後に、要件定義書・詳細設計書・対応表（docs/trace_map.md）・実装コードの整合を逆引きで確かめ、
  正本を整合した状態に戻す。未マッピング要件の一覧化、要件の聞き直しと更新、要件 ID の整理、設計への伝播、再チェックまで行う。
  「実装後に仕様整合を確認したい」「実装差分を要件と設計に反映したい」「実装後の逆引きレビューをしたい」
  「proposals.md を正本に反映して」といった依頼や、isdd-traceable-coding の完了後に使う。
  設計スキルの途中で見つかった要件の不足は対象にしない（設計スキル自身が扱う）。
license: CC-BY-4.0
metadata:
  version: "v2.0.0"
---

# isdd-post-implementation-review — 実装後逆引き整合スキル

要件・設計・実装の差分を見つけ、正本（`docs/requirements.md`・`docs/detail_design.md`・`docs/trace_map.md`）を整合した状態に戻す。

## このスキルのファイル

参照ファイルはこのスキルの `references/`、チェッカーは `scripts/` にある。下のコマンドは `.agents/skills/` に入れた場合のパスで書いている。別の場所（`.claude/skills/`、`.github/skills/`、ホーム配下など）に入れた場合は、この SKILL.md があるディレクトリに読み替える。

| ファイル | 使う場面 |
|---|---|
| `references/trace-map-rules.md` | 対応表の書式と、チェッカーのエラー・警告の意味 |
| `references/id-definitions.md` | 要件 ID・設計 ID の採番と変更管理 |
| `references/document-rules.md` | 正本を書き換えるときの書き方 |
| `scripts/rq_ds_link_checker.py` | 要件 ID と設計 ID の対応チェック |

対応表チェックは、`isdd-setup` がプロジェクトに入れた `scripts/isdd/check.sh` を使う（pre-commit と同じものを動かすため）。`scripts/isdd/check.sh` が無ければ、先に `isdd-setup` を実行する。

版を比べる。`cat scripts/isdd/VERSION` の出力と、この SKILL.md の先頭（frontmatter）にある `metadata.version` の値（`v` で始まる版番号）を、1 文字ずつ同じか比べる。

- 同じなら次へ進む。
- VERSION が無いか、違う場合は、作業を始める前に「scripts/isdd/VERSION（読んだ値）とスキルの版（metadata.version の値）が違うため、isdd-setup を再実行します」と報告し、`isdd-setup` を再実行してから進める。古いチェッカーで判定すると、規則の変更を見落とすため。`isdd-setup` は何度実行しても同じ状態になる。
- 比べた結果（両方の値と、再実行したか）を最終報告に書く。

## 扱う範囲

- 実装が原因の要件・設計の差分だけを扱う。設計スキル（`isdd-design` / `isdd-change-design`）が確定した要件の更新は、判定し直さない。
- 更新先は `docs/requirements.md`、`docs/detail_design.md`、`docs/trace_map.md` だけ。`change_requirements.md` は要求意図を確かめるための参照に使い、書き換えない。
- 見つけた差分を、新しい変更要件に回さない。正本を直接直す（正本と実装のずれを残さないため）。
- `docs/proposals.md` は実装中の一時ファイル。正本へ反映したか「反映不要」と決めたかにかかわらず、完了時に削除する。
- 証跡ファイルは残さない。完了時に正本だけが最新になっている状態にする。

## 入力

- 実装差分（直近のコミット差分、またはワークツリーの差分）
- `docs/requirements.md`、`docs/detail_design.md`
- `docs/trace_map.md`（無ければ未作成として扱い、このスキルの中で作る）
- `docs/proposals.md`（ある場合）
- `.history/[YYYYMMDD]-[タスク名]/change_requirements.md`（変更フローの場合）

## 手順

1. 対象コード、要件定義書、詳細設計書、直近の差分を読む。`docs/proposals.md` があれば読む。変更フローなら `change_requirements.md` も読む。
2. 実装差分の影響範囲をまとめる。
3. 要件 ID と設計 ID の対応を確かめる。

   ```bash
   python3 .agents/skills/isdd-post-implementation-review/scripts/rq_ds_link_checker.py docs/requirements.md docs/detail_design.md
   ```

   このチェッカーが見るのは、要件定義書と設計書の文書間の対応だけ。「実装にあるのに要件が無い」ことや、「`change_requirements.md` の要求が正本に反映されていない」ことは検出できないので、合格しても手順 4 以降を続ける。
4. 対応表とコードのずれを確かめる。

   ```bash
   bash scripts/isdd/check.sh
   ```

   - エラー（対応表が指す関数がコードに無い、DS-ID が設計書に無い）は、改名・削除の反映漏れなので、対応表を直す。
   - 警告「コードにあって対応表に無い」は、スキルを使わずに追加されたコードの可能性があるので、手順 6 の未マッピング一覧に入れる。
   - 警告「設計書にあって対応表に無い」は、未実装か登録漏れかをコードで確かめる。登録漏れなら対応表に足し、未実装ならユーザーに示す。
5. 変更フローの場合は、`change_requirements.md`、`docs/proposals.md`、実装差分の 3 つを突き合わせる。
   - 正本への反映は `isdd-change-design` が済ませているはずで、この手順はその反映漏れを拾うためにある。
   - `change_requirements.md` の要件 ID が `docs/requirements.md` に反映されているかを確かめる（チェッカーでは確かめられない）。
   - 未反映の要件 ID は確定済みの変更なので、ユーザーへの聞き直しは要らない。手順 6・7 を飛ばし、`docs/requirements.md` と `docs/detail_design.md` を直接更新して手順 9 に進む。
   - 更新するときは両文書を全章通読し、変更前の挙動を前提にした本文（例: 「固定文字列を出力するのみ」「データを保持しない」といった説明、旧関数名・旧画面名への言及、用語定義）も書き換える。ID の表が新しくても、本文が旧仕様のままなら未反映とみなす。
6. 実装の全関数・処理から逆にたどり、対応表に設計 ID が無いもの、対応する要件 ID が `docs/requirements.md` に無いものを未マッピング一覧にする。チェッカーが合格していても行う。
   応答には Markdown の見出し `### 未マッピング一覧` を置き、その直下に次の表を出す。太字の行は見出しの代わりにならない。列名は下の表の見出し行をそのまま写し、省略も言い換えもしない（「実装要素」ではなく「実装要素（修飾名）」）。該当が無い場合も見出しと表を出し、行に「該当なし」と書く。ユーザーが表で 1 件ずつ判断できるようにするため、文章だけで済ませない。

   | 実装要素（修飾名） | 対応表の DS-ID | 設計書に DS-ID があるか | 対応する RQ-ID | 要件定義書に RQ-ID があるか | 状態 |
   |---|---|---|---|---|---|
   | `src/hello.py::HelloWorldPrinter.get_hello_message` | `DS-FN-GET-HELLO-MESSAGE-FT-GET-HELLO-MESSAGE` | あり | `RQ-FT-GET-HELLO-MESSAGE` | なし | 要件未定義 |

   状態は「要件未定義」「設計未定義」「対応表未登録」「整合」のどれか。「整合」の行は省略してよいが、未マッピングの行は省略しない。
7. 未マッピングを 1 件ずつユーザーに聞き、「削除」「修正」「分割」「統合」「追加」のどれにするかを決める。
8. 決めた内容を `docs/requirements.md` に反映する。反映後は手順 5 と同じく全章を通読し、旧仕様を前提にした本文を書き換える。
9. 更新した要件 ID を設計書へ伝え、設計を直す。新しい設計 ID に対応するコードを `docs/trace_map.md` に登録する。
10. `rq_ds_link_checker.py` と `bash scripts/isdd/check.sh --strict` をもう一度実行し、出力で未整合ゼロ（エラー 0 件・警告 0 件）を確かめる。未整合が残れば手順 6 に戻る。
11. `docs/proposals.md` があれば削除する。

## 完了条件

- `rq_ds_link_checker.py` と `bash scripts/isdd/check.sh --strict` の実行ログを応答に載せ、未整合がゼロ（対応表のエラー 0 件・警告 0 件を含む）
- Markdown の見出し `### 未マッピング一覧` と、手順 6 の 6 列（列名は省略しない）の表を応答に載せた（該当なしの場合も）
- 要件の更新が必要だった場合、1 件ずつ聞き直して反映し、設計 ID と対応表に伝えた
- `docs/proposals.md` が無い
- 変更フローの場合、`change_requirements.md` の要求意図と正本の内容（ID の表だけでなく、データ章・用語定義・概要などの本文も）が矛盾していない

## 報告

次を報告する。

- 実装後逆引き整合の結果（未整合ゼロか、残っている未整合）
- 未マッピング一覧
- 要件の更新結果と、設計 ID・対応表への伝播結果

未整合が残っている場合は、新規開発なら `isdd-design`、変更開発なら `isdd-change-design` で設計を直すよう案内する。

未整合がゼロになった場合は、確定した成果物と今後の進め方を案内する。

- `docs/requirements.md`: 確定した要件定義書。次の変更要件定義の起点になる
- `docs/detail_design.md`: 確定した詳細設計書。要件との対応をたどれる
- `docs/trace_map.md`: 設計 ID とファイル・クラス・公開関数の対応表。コードに ID を書かずに仕様とコードを結ぶ
- `e2e/`: 実装を検証する E2E テスト。詳細設計書 8-4 の実行コマンドで動かす（外部連携がある場合は mock と real の 2 モード）
- 新しい要求は `isdd-change-req` から始める
- 既存の実装にバグや仕様誤りが見つかった場合は、`docs/requirements.md` を直し、`isdd-design` で設計を更新してから `isdd-traceable-coding` で直す
