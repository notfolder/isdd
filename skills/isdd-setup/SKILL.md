---
name: isdd-setup
description: >
  isdd の対応表チェック（設計 ID とコードの対応を docs/trace_map.md で管理する仕組み）をプロジェクトに導入する。
  コード用チェッカーの複製、scripts/isdd/check.sh と pre-commit の生成、AGENTS.md と CLAUDE.md への規則の追記、
  エージェント自身によるフックの設定までを行う。何度実行しても同じ状態になる。
  「isdd をセットアップして」「対応表チェックを導入して」「isdd-setup を実行して」という依頼や、
  他の isdd スキルが「scripts/isdd/check.sh が無い」「scripts/isdd/VERSION がスキルの版と違う」と判断したときに使う。
license: CC-BY-4.0
metadata:
  version: "v2.0.0"
---

# isdd-setup — 対応表チェック導入スキル

プロジェクトに対応表チェックを組み込み、スキルを使わない人の変更でも対応表のずれに気づけるようにする。

## このスキルのファイル

スクリプトはこのスキルの `scripts/` にある。下のコマンドは `.agents/skills/` に入れた場合のパスで書いている。別の場所（`.claude/skills/`、`.github/skills/`、ホーム配下など）に入れた場合は、この SKILL.md があるディレクトリに読み替える。

| ファイル | 役割 |
|---|---|
| `scripts/isdd_setup.py` | 導入を行うスクリプト |
| `scripts/trace_map_checker.py` | 対応表チェッカー（プロジェクトの `scripts/isdd/` に複製する） |
| `scripts/implementation_completeness_checker.py` | 実装完了チェッカー（同上） |

## 何を入れるか

| 成果物 | 役割 |
|---|---|
| `scripts/isdd/trace_map_checker.py`、`implementation_completeness_checker.py` | コード用チェッカーの複製。スキルを持たない人や CI でも動くよう git 管理対象にする |
| `scripts/isdd/VERSION` | 複製したチェッカーの isdd の版。各スキルはこれと自分の版を比べ、違えばこのスキルの再実行を案内する |
| `scripts/isdd/check.sh` | 対応表チェックの入口。エージェントのフックも pre-commit もこれを呼ぶ |
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
2. 次を bash で実行する（ソースディレクトリが複数なら `--src` を繰り返す。例は CLI・認証なし・外部連携なしの場合）。

   ```bash
   python3 .agents/skills/isdd-setup/scripts/isdd_setup.py --src src --runtime cli --no-auth --no-external
   ```

   出力の「省略」「削除」「注意」の行は、そのまま報告に写す（`.git` が無い、既存の pre-commit がある、実行形態が未指定、など）。
3. チェッカーが動くことを確かめる。実装前で `docs/trace_map.md` が無いプロジェクトでは「対応表が見つかりません」のエラーで終わるが、スクリプトが動いたことを確認できればよい。

   ```bash
   bash scripts/isdd/check.sh
   ```

4. エージェント自身のフックを設定する。いま動いている実行環境のフック機能で、「1 回の応答（ターン）が終わる時」に `bash scripts/isdd/check.sh` を実行する設定を作る。
   - 作れるのは、実行環境にフック機能があり、応答終了時に当たるイベントがある場合。設定ファイルの置き場所と書式は、自分の実行環境のものを使う。
   - フック機能が無い、または応答終了時のイベントが無くファイル保存時のイベントしか無い場合は、設定を作らず「この環境では応答終了時のフックを設定できない」と報告する。ファイル保存時のイベントには付け替えない（保存のたびに未完成のコードを検査し、警告が出続けるため）。
   - 作った場合は、そのフックが呼ぶコマンドを手で 1 回実行し、動くことを確かめる。初回に信頼の承認を求める実行環境では、ユーザーに承認を依頼する。
   - 他のエージェント向けの設定を推測で作らない。isdd はエージェントごとの設定書式を持たないため。
5. 導入結果を報告する。

## 報告に含めること

- 複製・生成・組み込み・削除したファイルの一覧と、`scripts/isdd/VERSION` に記録した版
- `completeness.json` に記録した実行形態・認証・外部連携と、その根拠（設計書のどこから読んだか、またはユーザーの回答）
- 省略した項目とその理由（`.git` が無い、既存のフックがある、応答終了時のイベントが無い）
- エージェントのフックを作ったか。作った場合はその場所と呼び出すコマンド
- チェッカーを 1 回実行した結果

## 完了条件

- `isdd_setup.py` を実行し、出力を応答に載せた
- `bash scripts/isdd/check.sh` を実行し、結果を応答に載せた
- `AGENTS.md` と `CLAUDE.md` に規則ブロックがある
- `scripts/isdd/completeness.json` の実行形態・認証・外部連携が詳細設計書（またはユーザーの回答）と一致している
- エージェントのフックについて、作った・作れなかったのどちらかを書いた

## 次のステップ

完了を報告するときに、次のスキルを提案する。

- これから実装する場合: `isdd-traceable-coding` で設計書にもとづく実装と対応表の作成を行う
- 既存コードを isdd 化している途中の場合: `isdd-reverse-engineering` の残りの手順に戻る
