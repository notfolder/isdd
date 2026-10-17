# 対応表（docs/trace_map.md）のルール

設計 ID（`DS-*`）とソースコードの対応は、コードにコメントを書かず、対応表 `docs/trace_map.md` で管理する。
要件 ID（`RQ-*`）との対応は設計 ID の末尾略称で表すため、対応表には書かない。

---

## 書式

Markdown の表で、列は「DS-ID」「修飾名」「備考」の 3 列に固定する。

| DS-ID | 修飾名 | 備考 |
|---|---|---|
| `DS-MD-HELLO-MODULE-FT-PRINT-HELLO-WORLD` | `src/hello.py` | モジュール |
| `DS-CL-HELLO-WORLD-PRINTER-FT-PRINT-HELLO-WORLD` | `src/hello.py::HelloWorldPrinter` | クラス |
| `DS-FN-GET-HELLO-MESSAGE-FT-GET-HELLO-MESSAGE` | `src/hello.py::HelloWorldPrinter.get_hello_message` | メソッド |
| `DS-FN-PRINT-HELLO-WORLD-FT-PRINT-HELLO-WORLD` | `src/hello.py::HelloWorldPrinter.print_hello_world` | メソッド |

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

- ソースファイル（`DS-MD-*`）、クラス（`DS-CL-*`）、公開関数とメソッド（`DS-FN-*`。API の入口なら `DS-IF-*`、バッチの入口なら `DS-BT-*` でもよい）。
- アンダースコア始まりの内部関数と、`__init__` などのダンダーメソッドは載せない。
- テストファイル（`test_*.py`、`*_test.py`、`*.spec.ts`、`*.test.ts`）は載せない。

## チェッカー

`trace_map_checker.py` が、詳細設計書・対応表・コードの 3 者を突き合わせる。

```bash
python3 scripts/isdd/trace_map_checker.py docs/detail_design.md docs/trace_map.md src [--strict]
```

| 区分 | 内容 | 扱い |
|---|---|---|
| エラー | 対応表の DS-ID が設計書に無い。対応表の修飾名がコードに無い（改名・削除の見落とし）。`DS-MD-*` と修飾名の形が合わない | 終了コード 1。pre-commit で止まる |
| 警告 | コードのファイル・クラス・公開関数が対応表に無い。設計書の `DS-MD-*` `DS-CL-*` `DS-FN-*` が対応表に無い（未実装の可能性） | 既定では終了コード 0。`--strict` で終了コード 1 |

- 実装スキル（`isdd-traceable-coding`）の完了条件は `--strict` で合格すること（エラーも警告も 0 件）。
- pre-commit はエラーだけで止める。スキルを使わずにコードを変えた人が関数を足しても止まらない。その抜けは `isdd-post-implementation-review` で対応表と設計書に取り込む。

## 更新のタイミング

- クラス・公開関数・ファイルを追加、改名、削除したら、同じ作業の中で対応表を更新する。
- 設計要素を増やす必要があれば、先に設計書を更新して DS-ID を採番し、それから対応表に行を足す。実装中に ID を作らない。
