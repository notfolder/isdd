---
name: isdd-setup
description: >
  isdd の対応表チェック（設計 ID とコードの対応を docs/trace_map.md で管理する仕組み）をプロジェクトに導入する。
  コード用チェッカーの複製、scripts/isdd/check.sh と pre-commit の生成、AGENTS.md と CLAUDE.md への規則の追記、
  エージェント自身によるフックの設定までを行う。何度実行しても同じ状態になる。
  「isdd をセットアップして」「対応表チェックを導入して」「isdd-setup を実行して」という依頼や、
  他の isdd スキルが「scripts/isdd/check.sh が無い」「scripts/isdd/VERSION がスキルの版と違う」と判断したときに使う。
license: CC-BY-4.0
compatibility: Requires Python 3.9 or later (standard library only; tested on 3.9 to 3.15) and bash
metadata:
  version: "v2.3.0"
---

# isdd-setup — 対応表チェック導入スキル

プロジェクトに対応表チェックを組み込み、スキルを使わない人の変更でも対応表のずれに気づけるようにする。

## このスキルのファイル

スクリプトはこのスキルの `scripts/` にある。下のコマンドは `.agents/skills/` に入れた場合のパスで書いている。別の場所（`.claude/skills/`、`.github/skills/`、ホーム配下など）に入れた場合は、この SKILL.md があるディレクトリに読み替える。

| ファイル | 役割 |
|---|---|
| `scripts/isdd_setup.py` | 導入を行うスクリプト |
| `scripts/trace_map_checker.py` | 対応表チェッカー（プロジェクトの `scripts/isdd/` に複製する） |
| `scripts/dependency_checker.py` | 依存チェッカー（同上。設計書第 7 章の依存の規則で import を確かめる） |
| `scripts/implementation_completeness_checker.py` | 実装完了チェッカー（同上） |

## 何を入れるか

| 成果物 | 役割 |
|---|---|
| `scripts/isdd/trace_map_checker.py`、`dependency_checker.py`、`acceptance_checker.py`、`implementation_completeness_checker.py` | コード用チェッカーの複製。スキルを持たない人や CI でも動くよう git 管理対象にする |
| `scripts/isdd/VERSION` | 複製したチェッカーの isdd の版。各スキルはこれと自分の版を比べ、違えばこのスキルの再実行を案内する |
| `scripts/isdd/check.sh` | 対応表チェック、依存チェック、受け入れ判定の入口。エージェントのフックも pre-commit もこれを呼ぶ。`docs/active_change`（変更の実装中だけある）があれば、変更設計書を正本に重ねて判定する。対応表の粒度（`--granularity`）、E2E のディレクトリ（`--tests`）、E2E の結果の置き場所（`--junit "<E2E ディレクトリ>/results/*.xml"`）もここに固定する。受け入れ判定は既定では警告だけで、`--strict` のときに不合格・未実行・要再実行を失敗扱いにする |
| `.gitignore` の `<E2E ディレクトリ>/results/` | E2E の結果（JUnit XML）は git 管理外。スクリプトが無いときだけ足す |
| `scripts/isdd/dependencies.json` | 依存の規則（設計書第 7 章の書き写し）。スクリプトは規則が空の雛形を無いときだけ作り、このスキルが第 7 章の内容を書き写す。再実行でも上書きしない |
| `scripts/isdd/pre-commit` と `.git/hooks/pre-commit` | 対応表の壊れた参照（エラー）だけでコミットを止める。未登録（警告）は表示だけ |
| `AGENTS.md` と `CLAUDE.md` の規則ブロック | スキルが起動していない時でも、エージェントが対応表を更新しチェックを実行するようにする |
| `scripts/isdd/completeness.json` | 実装完了チェックの設定。実行形態・認証の有無・外部連携の有無を記録し、docker compose や「初期ユーザー」を要求するかを決める |
| エージェントのフック設定 | 応答終了時に `bash scripts/isdd/check.sh` を実行する。作れる環境でだけ作る |

要件・設計のチェッカー（`rq_*.py`）は各スキルが同梱版を直接実行するので、`scripts/isdd/` には複製しない。以前の版が複製したものがあれば、スクリプトが削除する。

## 手順

1. `docs/detail_design.md` から次を読み取る。設計書が無い、または記載が無い項目は、ユーザーに確認する。
   - ソースディレクトリ: コード設計章のディレクトリ構成。無ければ `src`。外部連携ライブラリ `external/[システム名]/src` があれば含める
   - 実行形態（`--runtime`）: 第 1 章の選定結果。`container`（docker compose で動かす）、`cli`、`server`（コンテナを使わないサーバー）、`desktop`、`library` のいずれか。読み取れなければ `unspecified`
   - 認証の有無（`--auth` / `--no-auth`）: セキュリティ設計にログインや利用者認証があるか
   - 外部連携の有無（`--external` / `--no-external`）: 外部システム連携の章に連携先があるか
   - 対応表の粒度（`--granularity function|class`）: 第 7 章の「対応表の粒度」。書いていなければ `function`
   - 依存の規則: 第 7 章の「依存の規則」の表（無ければ「無い」）
2. 次を bash で実行する（ソースディレクトリが複数なら `--src` を繰り返す。`--src` にはファイルも書け、大きな既存リポジトリの一部のファイルだけを対象にするときに使う。例は CLI・認証なし・外部連携なし・粒度 function の場合）。

   ```bash
   python3 .agents/skills/isdd-setup/scripts/isdd_setup.py --src src --runtime cli --no-auth --no-external --granularity function
   ```

   出力の「省略」「削除」「注意」「保持」の行は、そのまま報告に写す（`.git` が無い、既存の pre-commit がある、実行形態が未指定、`dependencies.json` が既にある、など）。
3. 第 7 章の依存の規則を `scripts/isdd/dependencies.json` に書き写す。表の 1 行を `{"from": 依存元, "allow": [依存してよい先], "deny": [依存してはいけない先], "reason": 理由}` の 1 要素にする（`allow` か `deny` の片方だけでよい）。規則が無ければ、雛形の `"rules": []` のままにする。既にファイルがあれば、第 7 章と合っているか見て、違えば第 7 章に合わせる。書き方は `dependency_checker.py` の先頭に書いてある。
4. チェッカーが動くことを確かめる。実装前で `docs/trace_map.md` が無いプロジェクトでは「対応表が見つかりません」のエラーで終わるが、スクリプトが動いたことを確認できればよい。依存チェックの結果（規則なし、合格、違反）も見る。

   ```bash
   bash scripts/isdd/check.sh
   ```

5. エージェント自身のフックを設定する。いま動いている実行環境のフック機能で、「1 回の応答（ターン）が終わる時」に `bash scripts/isdd/check.sh` を実行する設定を作る。
   - 作れるのは、実行環境にフック機能があり、応答終了時に当たるイベントがある場合。設定ファイルの置き場所と書式は、自分の実行環境のものを使う。
   - フック機能が無い、または応答終了時のイベントが無くファイル保存時のイベントしか無い場合は、設定を作らず「この環境では応答終了時のフックを設定できない」と報告する。ファイル保存時のイベントには付け替えない（保存のたびに未完成のコードを検査し、警告が出続けるため）。
   - 作った場合は、そのフックが呼ぶコマンドを手で 1 回実行し、動くことを確かめる。初回に信頼の承認を求める実行環境では、ユーザーに承認を依頼する。
   - 他のエージェント向けの設定を推測で作らない。isdd はエージェントごとの設定書式を持たないため。
6. 導入結果を報告する。

## 報告に含めること

- 複製・生成・組み込み・削除したファイルの一覧と、`scripts/isdd/VERSION` に記録した版
- `completeness.json` に記録した実行形態・認証・外部連携と、`check.sh` に固定した対応表の粒度、その根拠（設計書のどこから読んだか、またはユーザーの回答）
- `dependencies.json` に書いた規則の件数（無ければ「規則なし」）と、第 7 章のどの表から写したか
- 省略した項目とその理由（`.git` が無い、既存のフックがある、応答終了時のイベントが無い）
- エージェントのフックを作ったか。作った場合はその場所と呼び出すコマンド。作らなかった場合はその理由（応答終了時のイベントが無い環境だった、ユーザーが不要と言った、など）。途中の応答で書いていても、最終報告にもう一度書く
- チェッカーを 1 回実行した結果

## 完了条件

- `isdd_setup.py` を実行し、出力を応答に載せた
- `bash scripts/isdd/check.sh` を実行し、結果を応答に載せた
- `AGENTS.md` と `CLAUDE.md` に規則ブロックがある
- `scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書（またはユーザーの回答）と一致している
- `scripts/isdd/dependencies.json` があり、詳細設計書 第 7 章の依存の規則と一致している（規則が無ければ `"rules": []`）
- エージェントのフックについて、最終報告に「作った（場所とコマンド）」か「作らなかった（理由）」のどちらかを書いた

## 次のステップ

他のスキル（`isdd-build`・`isdd-reverse-engineering`）の途中で呼ばれた場合は、ここで応答を終えない。導入結果は呼び出し元の最終報告にまとめ、同じ応答の中で呼び出し元の作業（実装、実装後レビュー、対応表の作成）に戻る。ユーザーが頼んだのはその作業で、導入はその準備にすぎないため。

単独で呼ばれて完了を報告するときは、次のスキルを提案する。

- これから実装する場合: `isdd-build` で設計書にもとづく実装と対応表の作成を行う
- 既存コードを isdd 化している途中の場合: `isdd-reverse-engineering` の残りの手順に戻る
