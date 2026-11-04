# 対応表（docs/trace_map.md）のルール

設計 ID（`DS-*`）とソースコードの対応は、コードにコメントを書かず、対応表 `docs/trace_map.md` で管理する。
要件 ID（`RQ-*`）との対応は設計書の「要件と設計の対応表」の章で持つため、対応表には書かない。

---

## 書式

Markdown の表で、列は「DS-ID」「修飾名」「備考」の 3 列に固定する。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-HELLO-MODULE` | `src/hello.py` | モジュール |
| `DS-CL-HELLO-WORLD-PRINTER` | `src/hello.py::HelloWorldPrinter` | クラス |
| `DS-FN-GET-HELLO-MESSAGE` | `src/hello.py::HelloWorldPrinter.get_hello_message` | メソッド |
| `DS-FN-PRINT-HELLO-WORLD` | `src/hello.py::HelloWorldPrinter.print_hello_world` | メソッド |

- 1 行に 1 対応。同じ DS-ID が複数行に現れてよい（1 つの設計要素を複数の関数で実現する場合）。
- 同じ修飾名が複数行に現れてよい（1 つの関数が複数の設計要素を実現する場合）。
- 備考は自由記述。空でもよい。

## 修飾名の文法

| 形 | 対象 | 例 |
|---|---|---|
| `<ファイルパス>` | モジュール（ファイル）単位。`DS-MD-*` にだけ使う | `src/app/order.py` |
| `<ファイルパス>::<名前>` | トップレベルのクラスまたは関数 | `src/app/order.py::OrderService` |
| `<ファイルパス>::<クラス名>.<名前>` | メソッド | `src/app/order.py::OrderService.create_order` |

- ファイルパスはプロジェクトルートからの相対パスで、区切りは `/`。
- `DS-MD-*` の行はファイルパスだけを書く。`DS-MD-*` 以外の行は `::` を含める。

## 載せる粒度

- ソースファイル（`DS-MD-*`）、クラス（`DS-CL-*`）、公開関数とメソッド（`DS-FN-*`。API の入口なら `DS-IF-*`、バッチの入口なら `DS-BT-*` でもよい）。ソースファイルはチェッカーが走査するプログラム言語のファイルだけで、起動スクリプト・HTML テンプレート・CSS・設定ファイルは対応表に載せない（設計書 7 章の規則）。
- 粒度は設計書第 7 章で決め、`isdd-setup` の `--granularity` で `check.sh` に渡す。
  - `function`（既定）: ファイル・クラス・公開関数・メソッドのすべてを載せる。
  - `class`: ファイルとクラスを載せる。公開関数とメソッドは、設計書に `DS-FN-*` があるものだけ載せる（設計書にある `DS-FN` は粒度にかかわらず対応表に要る）。クラスかファイルが登録済みなら、載せていない公開関数は未登録の警告にならない。
- E2E シナリオ（`DS-TS-*`）は、テストディレクトリ（`e2e`）のテスト関数に結ぶ。修飾名は `e2e/test_order.py::test_cancel_order` の形（テストファイルそのものでもよい）。テストファイルを指せるのは `DS-TS` の行だけで、`DS-TS` の行はテスト以外を指せない。モック（`external/[システム名]/mock/`）の `DS-TS` は載せない。
- 設計書第 7 章の「実現する設計 ID」列に書いた設計 ID（`DS-IF`・`DS-BT`・`DS-EV`、データクラスの `DS-SC` など）は、そのファイルのクラスや関数として載せる。チェッカーは、この列の ID が対応表に無ければ警告する。
- 次の設計 ID は、第 7 章の「実現する設計 ID」に書いていなければ、対応表に載せなくてよい（チェッカーも未登録の警告を出さない）。
  - `DS-SC-*`（データモデル）: DB のテーブル定義やファイル形式は修飾名で表せないため。データクラスとして実装した場合は、第 7 章に書いて載せる
  - `DS-OP-*`（運用）: compose ファイル、設定ファイル、運用手順などはソースコードではないため
  - `DS-EV-*`（イベント）: イベントを処理するクラスや関数を `DS-CL-*`・`DS-FN-*` で載せる
- アンダースコア始まりの内部関数と、`__init__` などのダンダーメソッドは載せない。
- テストファイル（`test_*.py`、`*_test.py`、`*.spec.ts`、`*.test.ts`、`*_test.go`、`*Test.java`、`*Tests.cs` など）とテストディレクトリの中のファイルは、`DS-TS` の行でだけ載せる。

## チェッカー

`trace_map_checker.py` が、詳細設計書・対応表・コードの 3 者を突き合わせる。

```bash
python3 scripts/isdd/trace_map_checker.py docs/detail_design.md docs/trace_map.md src [--strict] [--active-change docs/active_change] [--tests e2e] [--granularity function|class]
```

`scripts/isdd/check.sh` は `--active-change docs/active_change`、`--tests`（E2E のディレクトリ）、`--granularity`（第 7 章の粒度）を付けて呼び、続けて依存チェック（下の「依存の規則」）と受け入れ判定（下の「受け入れ判定」）も実行する。

### 進行中の変更（変更フロー）

- `isdd-spec` は変更フローで正本を書き換えず、変更のディレクトリ（`.history/[YYYYMMDD]-[タスク名]/`）を `docs/active_change` の 1 行目に書く。
- `docs/active_change` があれば、チェッカーはそのディレクトリの `change_detail_design.md` を正本の詳細設計書に重ねて判定する。有効な設計 ID は「正本 ＋ 変更設計書の ID − 変更設計書で削除する ID」。削除する ID は「[削除] の行にだけ現れる ID」で、要件との対応だけを差し替える要素（第 11 章で同じ ID を [削除] と [追加] の 2 行に書くもの）や、「変更なし（既存）」の行にもある ID は削除とみなさない。[追加] と [削除] が同じ行にあると判定できないので警告になる（行を分ける）。出力の冒頭に「進行中の変更」の行が出る。
- 実装後に `isdd-build` の実装後レビューが変更を正本へ反映し、`docs/active_change` を消す。以後は正本だけで判定する。

| 区分 | 内容 | 扱い |
|---|---|---|
| エラー | 対応表の DS-ID が設計書に無い。対応表の修飾名がコードに無い（改名・削除の見落とし）。`DS-MD-*` と修飾名の形が合わない。テストファイルを `DS-TS` 以外の行が指している | 終了コード 1。pre-commit で止まる |
| 警告 | コードのファイル・クラス・公開関数が対応表に無い（粒度 `class` では公開関数を緩める）。設計書の `DS-MD-*` `DS-CL-*` `DS-FN-*` と、第 7 章の「実現する設計 ID」が対応表に無い（未実装の可能性）。テストディレクトリがあるのに 8-2 の `DS-TS-*` が対応表に無い（テストが無い可能性）。進行中の変更で [削除] にした DS-ID が対応表に残っている | 既定では終了コード 0。`--strict` で終了コード 1 |
| 確認対象外 | 記号を抽出できない言語のファイルを指す `::名前` の行。ファイルの存在だけ確認する | 件数を表示するだけ。終了コードに影響しない |

### 言語ごとの確認の深さ

| 言語 | 確認できること | 方法 |
|---|---|---|
| Python | ファイル、クラス、関数、メソッド | 構文木（ast）で正確に抽出する |
| TypeScript / JavaScript、Java、Go | ファイル、クラス、関数、メソッド | 正規表現で近似抽出する。TypeScript / JavaScript はアロー関数（`const f = () =>`）も関数として拾う。クラス所属の判定は近似 |
| C#、Ruby、PHP、Kotlin、Swift、Rust、C / C++、Scala、Dart、Vue、Svelte、シェルなど | ファイルの存在だけ | `::名前` の行は「確認対象外」として数え、エラーにも警告にもしない。未登録ファイルの警告は出る |
| 上記以外の拡張子 | 何も確認しない | 対応表の行は「ファイルが見つかりません」のエラーになる。必要なら `trace_map_checker.py` の `FILE_ONLY_LANGS` に拡張子を足す |

- `isdd-build` の実装の段階の完了条件は `--strict` で合格すること（エラーも警告も 0 件）。
- pre-commit はエラーだけで止める。スキルを使わずにコードを変えた人が関数を足しても止まらない。その抜けは `isdd-build` の実装後レビューで対応表と設計書に取り込む。

## 受け入れ判定（acceptance_checker.py）

対応表は「テストがあるか」までしか見ない。「要件が実装されたか」は E2E の結果で見る。`check.sh` は `acceptance_checker.py` を次の形で呼ぶ。

```bash
python3 scripts/isdd/acceptance_checker.py docs/requirements.md docs/detail_design.md docs/trace_map.md --junit "e2e/results/*.xml" [--strict] [--active-change docs/active_change] [--tests e2e] [--src src]
```

- 読むもの: 要件定義書 第 7 章の「検証する要件ID」（`RQ-FT`・`RQ-UI`・`RQ-EX`・`RQ-NF` → `RQ-TS`）、設計書 第 11 章（`DS-TS` → `RQ-TS`、または `RQ-NF` へ直接）と 11-1（除外要件）、対応表の `DS-TS` 行、JUnit XML の testcase。`docs/active_change` があれば変更要件定義書と変更設計書の [追加] の行を重ね、[削除] の行は読まない。
- `DS-TS` ごとの判定: 合格（結んだ testcase が全部通った）、不合格（1 件以上失敗・エラー）、未実行（結べる testcase が無い、または skipped だけ）、要再実行（XML の timestamp が `--src`・`--tests` の最新の更新時刻より古い）。
- 照合: 対応表の `e2e/test_x.py::test_y` は、testcase の名前（pytest のパラメータ `[...]`、go のサブテスト `/...` を除いた部分）が `test_y` で、ファイルが分かる形式（pytest の classname、`file` 属性）ならファイルも一致するもの。`e2e/.../OrderTest.java::OrderTest.testCancel` は classname の末尾のクラス名とメソッド名。テストファイルだけを指す行は、そのファイルの testcase 全部。jest 系はファイル単位の行で結ぶ。
- 要件ごとの判定: `RQ-FT`・`RQ-UI`・`RQ-EX`（と「検証する要件ID」か第 11 章に現れる `RQ-NF`）ごとに、それを確かめる `RQ-TS` → `DS-TS` の結果をまとめ、全部合格なら「実装済み」、1 件でも不合格なら「不合格」、1 件も実行されていなければ「未検証」。除外要件（11-1）は対象外。Markdown の表で出す（`isdd-build` の実装後レビューはこの表を応答に載せる）。
- E2E の実行コマンド（8-4）は JUnit XML を `e2e/results/` に出す。pytest が無い Python なら、`isdd-setup` が複製する `scripts/isdd/unittest_junit.py`（標準ライブラリだけで unittest を実行して XML を書く）を使う。テストディレクトリが無いときは判定を省く（E2E の有無は `implementation_completeness_checker.py` が確かめる）。
- 終了コード: 既定では警告だけで 0。`--strict` では、不合格・未実行・要再実行の `DS-TS` か、未検証・不合格の要件が 1 件でもあれば 1。XML が 1 つも無ければ「未実行」として扱う。pre-commit は `--strict` を付けないので止まらない。

## 依存の規則（dependency_checker.py）

設計書第 7 章の「依存の規則」を `scripts/isdd/dependencies.json` に書き写し、`check.sh` が `dependency_checker.py` で import を確かめる。対応表は「設計要素がコードにあるか」を見るが、設計の構造（層の越境、連携ライブラリを通さない外部呼び出し）は見ないので、その穴を埋める。

```json
{
  "rules": [
    {"from": "src", "deny": ["external/crm/src", "requests"], "reason": "外部 API は連携ライブラリを通して呼ぶ"},
    {"from": "external/crm/src", "deny": ["src"], "reason": "連携ライブラリに業務ロジックを入れない"},
    {"from": "src/ui", "allow": ["src/service"], "reason": "画面層は業務層だけに依存する"}
  ]
}
```

- `from`: 規則を当てるディレクトリ。`deny`: 依存してはいけない先（プロジェクト内のパス、または外部モジュール名。先頭一致）。`allow`: 依存してよいプロジェクト内のディレクトリ（書くと `from` 自身と `allow` 以外への依存は違反。外部モジュールは `deny` でだけ制限する）。
- 違反はエラー（終了コード 1、pre-commit で止まる）。規則が空なら合格。
- import を読める言語は Python（ast）、TypeScript / JavaScript、Java、Go。それ以外は確認対象外として数える。
- `isdd-setup` は雛形（規則なし）を無いときだけ作り、再実行でも上書きしない。設計を変えて規則が変わったら、`isdd-build` が第 7 章と同じ内容に書き直す。

## 外部連携ライブラリの扱い

- 走査の範囲は `isdd-setup` の `--src` で決める。`--src` にはディレクトリだけでなくファイルも書ける。大きな既存リポジトリの一部のファイルだけを isdd の対象にするときは、対象のファイルを `--src` に並べる（例: `--src mlflow/server/security.py --src mlflow/server/security_utils.py`）。走査から外すものは `trace_map_checker.py` の `--exclude <相対パスのグロブ>`（例: `--exclude src/vendor`）。範囲の外のファイルは未登録の警告にならず、対応表の行が範囲の外を指すと「見つからない」のエラーになる（2026-11-05、計測 3 で範囲をディレクトリ単位でしか指定できず止まったため）
- `isdd-build` が作る外部連携ライブラリ `external/[システム名]/src/` はプロジェクトのコードなので、`isdd-setup` の `--src` に含めて対応表に載せる（例: `--src src --src external/foo/src`）。
- `external/[システム名]/mock/` は載せない。`e2e/` は `DS-TS` の行でだけ載せる。

## 更新のタイミング

- クラス・公開関数・ファイルを追加、改名、削除したら、同じ作業の中で対応表を更新する。
- 設計要素を増やす必要があれば、先に設計書（変更フローでは変更設計書）を更新して DS-ID を採番し、それから対応表に行を足す。実装中に ID を作らない。
